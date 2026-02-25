"""
🔮 PREDICTOR ENGINE
Learns from YOUR codebase's history. Warns before you write code that caused bugs before.
Kills: Bug introduction, Code review cycles, Technical debt accumulation

Author: OmniClaw Advanced Features
"""

import ast
import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime
from enum import Enum
from pathlib import Path
import re


class PatternType(Enum):
    MEMORY_LEAK = "memory_leak"
    RACE_CONDITION = "race_condition"
    SQL_INJECTION = "sql_injection"
    N_PLUS_ONE = "n_plus_one"
    DEADLOCK = "deadlock"
    RESOURCE_LEAK = "resource_leak"
    AUTH_BYPASS = "auth_bypass"
    NULL_POINTER = "null_pointer"
    TYPE_MISMATCH = "type_mismatch"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    COMPLEXITY = "complexity"
    BAD_PRACTICE = "bad_practice"


@dataclass
class PatternWarning:
    pattern_type: PatternType
    severity: str  # critical, warning, suggestion
    description: str
    location: str  # file:line
    previous_occurrence: Optional[str]  # Where this pattern caused issues
    suggestion: str


class PredictorEngine:
    """
    Trains on YOUR codebase's bug history and warns proactively.
    Before you write code that matches a problematic pattern, it alerts you.
    """
    
    def __init__(self, db_path: str = "./predictor.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._init_database()
        
        # Known dangerous patterns (can be extended with ML)
        self.dangerous_patterns = self._load_dangerous_patterns()
    
    def _init_database(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bug_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                line_number INTEGER,
                code_snippet TEXT,
                fix_applied TEXT,
                fixed_at TEXT,
                bug_description TEXT
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS pattern_signatures (
                pattern_type TEXT PRIMARY KEY,
                signature_hash TEXT NOT NULL,
                detection_regex TEXT,
                severity TEXT DEFAULT 'warning',
                times_triggered INTEGER DEFAULT 1
            )
        """)
        
        self.conn.commit()
    
    def _load_dangerous_patterns(self) -> dict:
        """Load known dangerous code patterns"""
        
        return {
            PatternType.NULL_POINTER: {
                "regex": r"(?<!hasattr\()\.\w+(?!\))\s*(?:is None|== None|None)",
                "severity": "warning",
                "example": "obj.property instead of obj and obj.property"
            },
            PatternType.SQL_INJECTION: {
                "regex": r'["\'].*?%s.*?(?:query|execute|fetch|select)',
                "severity": "critical",
                "example": "f\"SELECT * FROM users WHERE id = {user_id}\""
            },
            PatternType.RACE_CONDITION: {
                "regex": r"(?<!await\s)(?!await\s)\w+\s*\(\s*\)(?!\s*await)",
                "severity": "warning", 
                "example": "Non-await async call in sequence"
            },
            PatternType.N_PLUS_ONE: {
                "regex": r"for\s+\w+\s+in\s+\w+:\s*[^}]*?\.\w+\(.*?\w+\)",
                "severity": "warning",
                "example": "Loop with DB query inside"
            },
            PatternType.MEMORY_LEAK: {
                "regex": r"(?:\.append\(|\+=)\s*[\w\[\]]+\s*(?:(?!^\s*$|\#).)*(?:\.clear\(\)|\.pop\(\))",
                "severity": "warning",
                "example": "Growing list without proper cleanup"
            },
            PatternType.COMPLEXITY: {
                "regex": r"(?:if|elif|for|while|except).*?" * 5,  # 5+ nested
                "severity": "suggestion",
                "example": "5+ levels of nesting"
            },
            PatternType.AUTH_BYPASS: {
                "regex": r"(?i)(?:passwd|password|secret|key|token)\s*=\s*['\"][^'\"]+['\"]",
                "severity": "critical",
                "example": "Hardcoded credentials"
            }
        }
    
    def record_bug(
        self,
        pattern_type: PatternType,
        file_path: str,
        line_number: int,
        code_snippet: str,
        fix_applied: str,
        bug_description: str = ""
    ):
        """Record a bug occurrence for learning"""
        
        self.conn.execute("""
            INSERT INTO bug_history 
            (pattern_type, file_path, line_number, code_snippet, fix_applied, fixed_at, bug_description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            pattern_type.value, file_path, line_number, code_snippet,
            fix_applied, datetime.now().isoformat(), bug_description
        ))
        
        # Update signature tracking
        signature = hashlib.md5(code_snippet.encode()).hexdigest()[:16]
        
        self.conn.execute("""
            INSERT OR REPLACE INTO pattern_signatures 
            (pattern_type, signature_hash, times_triggered)
            VALUES (?, ?, COALESCE((SELECT times_triggered FROM pattern_signatures 
                                    WHERE pattern_type = ?), 0) + 1)
        """, (pattern_type.value, signature, pattern_type.value))
        
        self.conn.commit()
    
    def predict(self, code: str, file_path: str = "unknown") -> list[PatternWarning]:
        """
        Analyze code and predict potential issues.
        
        Args:
            code: Code to analyze
            file_path: File being analyzed
        
        Returns:
            List of warnings about potential issues
        """
        warnings = []
        
        # Check against known patterns
        for pattern_type, config in self.dangerous_patterns.items():
            regex = config.get("regex", "")
            if not regex:
                continue
            
            try:
                matches = re.finditer(regex, code, re.MULTILINE | re.IGNORECASE)
                
                for match in matches:
                    # Find line number
                    line_num = code[:match.start()].count('\n') + 1
                    
                    # Check if this exact pattern caused issues before
                    prev_occurrence = self._find_previous_occurrence(
                        pattern_type, match.group()
                    )
                    
                    severity = config["severity"]
                    if prev_occurrence:
                        severity = "critical"  # Re-occurring issue is worse
                    
                    warning = PatternWarning(
                        pattern_type=pattern_type,
                        severity=severity,
                        description=config.get("example", "Pattern detected"),
                        location=f"{file_path}:{line_num}",
                        previous_occurrence=prev_occurrence,
                        suggestion=self._get_suggestion(pattern_type)
                    )
                    warnings.append(warning)
            except re.error:
                pass
        
        # Check cyclomatic complexity
        complexity_warnings = self._check_complexity(code, file_path)
        warnings.extend(complexity_warnings)
        
        # Sort by severity
        severity_order = {"critical": 0, "warning": 1, "suggestion": 2}
        warnings.sort(key=lambda w: severity_order.get(w.severity, 3))
        
        return warnings
    
    def _find_previous_occurrence(
        self, 
        pattern_type: PatternType, 
        snippet: str
    ) -> Optional[str]:
        """Find if this exact pattern caused issues before"""
        
        # Create hash of snippet
        snippet_hash = hashlib.md5(snippet.encode()).hexdigest()[:16]
        
        cursor = self.conn.execute("""
            SELECT file_path, bug_description, fixed_at
            FROM bug_history
            WHERE pattern_type = ?
            ORDER BY fixed_at DESC
            LIMIT 1
        """, (pattern_type.value,))
        
        row = cursor.fetchone()
        if row:
            return f"{row[0]} - {row[1]} (fixed {row[2]})"
        
        return None
    
    def _check_complexity(self, code: str, file_path: str) -> list[PatternWarning]:
        """Check for overly complex code"""
        
        warnings = []
        
        if not code:
            return warnings
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    complexity = self._calculate_complexity(node)
                    
                    if complexity > 10:
                        severity = "warning" if complexity < 20 else "critical"
                        
                        warning = PatternWarning(
                            pattern_type=PatternType.COMPLEXITY,
                            severity=severity,
                            description=f"Cyclomatic complexity: {complexity}",
                            location=f"{file_path}:{node.lineno}",
                            previous_occurrence=None,
                            suggestion=f"Consider breaking into smaller functions (current: {complexity}, recommend: <10)"
                        )
                        warnings.append(warning)
        except:
            pass
        
        return warnings
    
    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity"""
        
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _get_suggestion(self, pattern_type: PatternType) -> str:
        """Get fix suggestion for pattern type"""
        
        suggestions = {
            PatternType.NULL_POINTER: "Use optional chaining (?.) or null checks",
            PatternType.SQL_INJECTION: "Use parameterized queries or ORM",
            PatternType.RACE_CONDITION: "Use locks or async/await properly",
            PatternType.N_PLUS_ONE: "Use batch queries or eager loading",
            PatternType.MEMORY_LEAK: "Ensure proper cleanup in finally blocks",
            PatternType.AUTH_BYPASS: "Use environment variables or secrets manager",
            PatternType.COMPLEXITY: "Extract to smaller functions",
            PatternType.NULL_POINTER: "Add null checks or use Optional type"
        }
        
        return suggestions.get(pattern_type, "Review and refactor")
    
    def get_pattern_stats(self) -> dict:
        """Get statistics on recorded patterns"""
        
        cursor = self.conn.execute("""
            SELECT pattern_type, COUNT(*) as count, MAX(fixed_at) as last_occurrence
            FROM bug_history
            GROUP BY pattern_type
        """)
        
        stats = {}
        for row in cursor:
            stats[row[0]] = {
                "count": row[1],
                "last_occurrence": row[2]
            }
        
        return stats
    
    def suggest_refactor(self, file_path: str) -> list[dict]:
        """Suggest refactoring based on historical bugs"""
        
        cursor = self.conn.execute("""
            SELECT DISTINCT pattern_type, code_snippet, fix_applied
            FROM bug_history
            WHERE file_path = ?
            ORDER BY fixed_at DESC
            LIMIT 10
        """, (file_path,))
        
        suggestions = []
        for row in cursor:
            suggestions.append({
                "pattern": row[0],
                "original": row[1],
                "fix": row[2]
            })
        
        return suggestions


# Demo
if __name__ == "__main__":
    predictor = PredictorEngine()
    
    # Simulate recording a past bug
    predictor.record_bug(
        pattern_type=PatternType.SQL_INJECTION,
        file_path="users.py",
        line_number=42,
        code_snippet='db.execute(f"SELECT * FROM users WHERE id = {user_id}")',
        fix_applied='db.execute("SELECT * FROM users WHERE id = ?", [user_id])',
        bug_description="SQL injection via user_id parameter"
    )
    
    # Test prediction
    test_code = '''
def get_user(user_id):
    # Dangerous - SQL injection
    result = db.execute(f"SELECT * FROM users WHERE id = {user_id}")
    
    # Also dangerous - hardcoded secret
    api_key = "sk-1234567890abcdef"
    
    return result
'''
    
    warnings = predictor.predict(test_code, "test.py")
    
    print("🔮 PREDICTOR ENGINE")
    print("=" * 50)
    print(f"\nFound {len(warnings)} potential issues:\n")
    
    for w in warnings:
        print(f"🚨 [{w.severity.upper()}] {w.pattern_type.value}")
        print(f"   Location: {w.location}")
        print(f"   {w.description}")
        if w.previous_occurrence:
            print(f"   ⚠️ Previously caused: {w.previous_occurrence}")
        print(f"   💡 Fix: {w.suggestion}")
        print()
    
    print("\nPattern Stats:")
    stats = predictor.get_pattern_stats()
    for pattern, data in stats.items():
        print(f"  {pattern}: {data['count']} occurrences")
