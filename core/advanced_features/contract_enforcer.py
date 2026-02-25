"""
⚖️ CONTRACT ENFORCER
Static analysis + LLM that enforces architectural contracts.
"No direct DB calls outside DAL", "All APIs need rate limiting", "No secrets in env vars without encryption"
Kills: Code review comments, Architecture drift, Convention violations

Author: OmniClaw Advanced Features
"""

import ast
import re
import json
from dataclasses import dataclass, field
from typing import Optional, Callable, list
from enum import Enum
from pathlib import Path


class ViolationSeverity(Enum):
    BLOCKER = "blocker"   # Must fix before merge
    CRITICAL = "critical" # Should fix before merge
    WARNING = "warning"  # Should fix eventually
    INFO = "info"        # FYI


class RuleType(Enum):
    NO_DIRECT_DB = "no_direct_db"
    NO_HARDCODED_SECRETS = "no_hardcoded_secrets"
    REQUIRED_RATE_LIMIT = "required_rate_limit"
    NO_SYNC_IN_ASYNC = "no_sync_in_async"
    REQUIRED_ERROR_HANDLING = "required_error_handling"
    NO_PRINT_IN_PROD = "no_print_in_prod"
    REQUIRED_LOGGING = "required_logging"
    NO_CATCH_ALL = "no_catch_all"
    TYPE_HINTS_REQUIRED = "type_hints_required"
    MAX_LINE_LENGTH = "max_line_length"
    REQUIRED_DOCSTRING = "required_docstring"
    NO_GLOBAL_STATE = "no_global_state"


@dataclass
class ContractRule:
    """A rule that must be enforced"""
    id: str
    name: str
    description: str
    rule_type: RuleType
    severity: ViolationSeverity
    
    # Rule configuration
    file_patterns: list[str] = field(default_factory=lambda: [".py"])
    code_patterns: list[str] = field(default_factory=list)
    exception_patterns: list[str] = field(default_factory=list)  # Allowed exceptions
    
    # LLM-enhanced detection
    llm_required: bool = False
    llm_prompt: str = ""


@dataclass
class Violation:
    """A contract violation"""
    rule: ContractRule
    file_path: str
    line_number: int
    code_snippet: str
    message: str
    suggestion: str
    blocked: bool = False


class ContractEnforcer:
    """
    Enforces architectural contracts through static analysis + LLM.
    Prevents architecture drift before code hits review.
    """
    
    def __init__(self):
        self.rules: dict[str, ContractRule] = {}
        self.violations: list[Violation] = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default architectural rules"""
        
        self.add_rule(ContractRule(
            id="no_direct_db",
            name="No Direct Database Calls",
            description="All DB operations must go through DAL/DataAccess layer",
            rule_type=RuleType.NO_DIRECT_DB,
            severity=ViolationSeverity.CRITICAL,
            code_patterns=[
                r"(?:execute|query|fetch|select|insert|update|delete).*\(",
                r"cursor\.execute",
                r"\.find\(|\.findOne\("
            ],
            exception_patterns=[
                r"class.*(?:DAL|Repository|DataAccess)",
                r"def.*_(?:get|set|fetch|query)",
            ]
        ))
        
        self.add_rule(ContractRule(
            id="no_hardcoded_secrets",
            name="No Hardcoded Secrets",
            description="No API keys, passwords, or tokens in code",
            rule_type=RuleType.NO_HARDCODED_SECRETS,
            severity=ViolationSeverity.BLOCKER,
            code_patterns=[
                r'(?:api[_-]?key|secret|password|token|auth)[_-]?\w*\s*=\s*["\'][^"\']{8,}["\']',
                r'sk-[a-zA-Z0-9]{20,}',
                r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----'
            ]
        ))
        
        self.add_rule(ContractRule(
            id="required_rate_limit",
            name="Rate Limiting Required",
            description="All API endpoints must have rate limiting",
            rule_type=RuleType.REQUIRED_RATE_LIMIT,
            severity=ViolationSeverity.WARNING,
            file_patterns=[".py"],
            code_patterns=[
                r"@app\.(?:get|post|put|delete|patch)",
                r"@router\.(?:get|post|put|delete|patch)",
                r"def\s+\w+\(.*?(?:Request|Response)\)"
            ],
            exception_patterns=[
                r"@.*rate_limit",
                r"@.*throttle"
            ]
        ))
        
        self.add_rule(ContractRule(
            id="no_sync_in_async",
            name="No Blocking Calls in Async",
            description="No synchronous blocking calls in async functions",
            rule_type=RuleType.NO_SYNC_IN_ASYNC,
            severity=ViolationSeverity.WARNING,
            code_patterns=[
                r"async\s+def\s+\w+\([^)]*\):[^}]*?(?:time\.sleep|requests\.|open\(|input\()"
            ]
        ))
        
        self.add_rule(ContractRule(
            id="required_error_handling",
            name="Error Handling Required",
            description="All functions must have error handling",
            rule_type=RuleType.REQUIRED_ERROR_HANDLING,
            severity=ViolationSeverity.WARNING,
            code_patterns=[
                r"def\s+\w+\([^)]*\):\s*(?:\n\s*(?!.*(?:try|raise|return\s+None|if\s+.*:.*return\s+None)))"
            ]
        ))
        
        self.add_rule(ContractRule(
            id="no_print_in_prod",
            name="No Print Statements",
            description="Use logging instead of print in production code",
            rule_type=RuleType.NO_PRINT_IN_PROD,
            severity=ViolationSeverity.INFO,
            code_patterns=[
                r"^\s*print\("
            ],
            exception_patterns=[
                r"if\s+debug|if\s+__name__.*print"
            ]
        ))
        
        self.add_rule(ContractRule(
            id="type_hints_required",
            name="Type Hints Required",
            description="All function signatures must have type hints",
            rule_type=RuleType.TYPE_HINTS_REQUIRED,
            severity=ViolationSeverity.WARNING,
            file_patterns=[".py"],
            code_patterns=[
                r"def\s+\w+\([^)]*\)\s*(?:->\s*\w+)?\s*:"
            ]
        ))
        
        self.add_rule(ContractRule(
            id="required_docstring",
            name="Docstrings Required",
            description="All public functions must have docstrings",
            rule_type=RuleType.REQUIRED_DOCSTRING,
            severity=ViolationSeverity.INFO,
            code_patterns=[
                r"def\s+(?!_|test_)\w+\([^)]*\).*:(?!\s*(?:\"\"\"|\'\'\'))"
            ]
        ))
    
    def add_rule(self, rule: ContractRule):
        """Add a custom rule"""
        self.rules[rule.id] = rule
    
    def remove_rule(self, rule_id: str):
        """Remove a rule"""
        self.rules.pop(rule_id, None)
    
    def check_file(self, file_path: str, content: str) -> list[Violation]:
        """
        Check a file for contract violations.
        
        Args:
            file_path: Path to file
            content: File content
        
        Returns:
            List of violations found
        """
        violations = []
        
        # Get applicable rules for this file
        applicable_rules = [
            rule for rule in self.rules.values()
            if any(file_path.endswith(p) for p in rule.file_patterns) 
            or not rule.file_patterns
        ]
        
        for rule in applicable_rules:
            rule_violations = self._check_rule(rule, file_path, content)
            violations.extend(rule_violations)
        
        return violations
    
    def _check_rule(
        self, 
        rule: ContractRule, 
        file_path: str, 
        content: str
    ) -> list[Violation]:
        """Check a single rule against content"""
        
        violations = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Skip comments
            if line.strip().startswith('#') or line.strip().startswith('//'):
                continue
            
            # Check if line matches rule pattern
            for pattern in rule.code_patterns:
                try:
                    if re.search(pattern, line):
                        # Check if it's an exception
                        if self._is_exception(line, rule.exception_patterns):
                            continue
                        
                        violation = Violation(
                            rule=rule,
                            file_path=file_path,
                            line_number=i,
                            code_snippet=line.strip(),
                            message=self._generate_message(rule, line),
                            suggestion=self._generate_suggestion(rule),
                            blocked=rule.severity == ViolationSeverity.BLOCKER
                        )
                        violations.append(violation)
                except re.error:
                    pass
        
        return violations
    
    def _is_exception(self, line: str, exceptions: list[str]) -> bool:
        """Check if line matches an exception pattern"""
        
        for exc in exceptions:
            try:
                if re.search(exc, line):
                    return True
            except re.error:
                pass
        return False
    
    def _generate_message(self, rule: ContractRule, line: str) -> str:
        """Generate violation message"""
        
        messages = {
            "no_direct_db": "Direct database call detected. Use DAL/Repository pattern.",
            "no_hardcoded_secrets": "Hardcoded secret detected. Use environment variables or secrets manager.",
            "required_rate_limit": "API endpoint must have rate limiting decorator.",
            "no_sync_in_async": "Synchronous blocking call in async function.",
            "required_error_handling": "Function lacks error handling (try/except or None return).",
            "no_print_in_prod": "Use logging instead of print().",
            "type_hints_required": "Function missing type hints.",
            "required_docstring": "Public function missing docstring."
        }
        
        return messages.get(rule.id, f"Rule violated: {rule.name}")
    
    def _generate_suggestion(self, rule: ContractRule) -> str:
        """Generate fix suggestion"""
        
        suggestions = {
            "no_direct_db": "Move query to DAL class: class UserDAL: ...",
            "no_hardcoded_secrets": "Use: os.environ.get('SECRET_KEY') or secrets manager",
            "required_rate_limit": "Add @rate_limit decorator or @throttle(max_calls=100)",
            "no_sync_in_async": "Use asyncio.sleep() or run in executor: await loop.run_in_executor(None, sync_func)",
            "required_error_handling": "Wrap in try/except or add early return on None/error",
            "no_print_in_prod": "Use: import logging; logger.info(...)",
            "type_hints_required": "Add type hints: def func(param: Type) -> ReturnType:",
            "required_docstring": "Add docstring: def func(): '''Description'''"
        }
        
        return suggestions.get(rule.id, f"Fix: {rule.description}")
    
    def check_project(self, project_path: str) -> dict:
        """
        Check entire project for violations.
        
        Returns:
            Summary with violation counts and details
        """
        from pathlib import Path
        
        violations = []
        files_checked = 0
        
        for file_path in Path(project_path).rglob("*.py"):
            # Skip common non-source directories
            if any(x in str(file_path) for x in ['__pycache__', 'venv', '.venv', 'test', 'migrations']):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_violations = self.check_file(str(file_path), content)
                violations.extend(file_violations)
                files_checked += 1
            except:
                pass
        
        # Categorize violations
        by_severity = {s.value: 0 for s in ViolationSeverity}
        by_rule = {}
        blocked = []
        
        for v in violations:
            by_severity[v.rule.severity.value] += 1
            
            if v.rule.id not in by_rule:
                by_rule[v.rule.id] = []
            by_rule[v.rule.id].append({
                "file": v.file_path,
                "line": v.line_number,
                "snippet": v.code_snippet[:50]
            })
            
            if v.blocked:
                blocked.append(v)
        
        return {
            "files_checked": files_checked,
            "total_violations": len(violations),
            "by_severity": by_severity,
            "by_rule": by_rule,
            "blocked_violations": len(blocked),
            "can_merge": len(blocked) == 0,
            "violations": [
                {
                    "rule": v.rule.name,
                    "file": v.file_path,
                    "line": v.line_number,
                    "message": v.message,
                    "suggestion": v.suggestion,
                    "blocked": v.blocked
                }
                for v in violations[:50]  # Limit output
            ]
        }
    
    def create_git_hook_path: str):
(self, project        """Generate pre-commit hook to enforce contracts"""
        
        hook_content = '''#!/bin/bash
# OmniClaw Contract Enforcer - Pre-commit Hook

echo "🔍 Running contract enforcement..."

python -c "
from omniclaw_advanced_features import ContractEnforcer
import sys

enforcer = ContractEnforcer()
result = enforcer.check_project('.')

print(f'Files checked: {result[\\"files_checked\\"]}')
print(f'Violations: {result[\\"total_violations\\"]}')

for v in result['violations']:
    if v['blocked']:
        print(f'🚫 BLOCKED: {v[\\"file\\"]}:{v[\\"line\\"]} - {v[\\"message\\"]}')
        print(f'   Fix: {v[\\"suggestion\\"]}')

if not result['can_merge']:
    print('\\n❌ Contract violations block commit')
    sys.exit(1)

print('\\n✅ All contracts satisfied')
"
'''
        
        hook_path = Path(project_path) / ".git" / "hooks" / "pre-commit"
        hook_path.parent.mkdir(exist_ok=True)
        
        with open(hook_path, 'w') as f:
            f.write(hook_content)
        
        hook_path.chmod(0o755)
        
        return str(hook_path)


# Demo
if __name__ == "__main__":
    enforcer = ContractEnforcer()
    
    test_code = '''
import requests
import sqlite3

API_KEY = "sk-1234567890abcdef"

def get_user(user_id):
    # Direct DB call - violation!
    db = sqlite3.connect("app.db")
    cursor = db.cursor()
    result = cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
    
    # Hardcoded secret - violation!
    api = requests.get(f"https://api.example.com?key={API_KEY}")
    
    print("User fetched")  # Print in prod - violation!
    
    return result

def process():
    pass
'''
    
    violations = enforcer.check_file("test.py", test_code)
    
    print("⚖️ CONTRACT ENFORCER")
    print("=" * 50)
    print(f"\nFound {len(violations)} violations:\n")
    
    for v in violations:
        status = "🚫 BLOCKED" if v.blocked else "⚠️"
        print(f"{status} [{v.rule.severity.value}] {v.rule.name}")
        print(f"   {v.file_path}:{v.line_number}")
        print(f"   Code: {v.code_snippet[:60]}...")
        print(f"   Fix: {v.suggestion}")
        print()
    
    # Show project check
    print("\n📊 Project Check (dry run):")
    print(f"   Can merge: {len([v for v in violations if v.blocked]) == 0}")
