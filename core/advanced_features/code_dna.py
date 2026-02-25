"""
🧬 CODEDNA INTERPRETER
Understands INTENT, not just syntax. Preserves business logic during refactoring.
Kills: Senior Code Reviewers who catch "technically correct but business-logic destroying" changes

Author: OmniClaw Advanced Features
"""

import ast
import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class IntentType(Enum):
    DATA_FETCH = "data_fetch"
    DATA_TRANSFORM = "data_transform"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    SIDE_EFFECT = "side_effect"
    CACHING = "caching"
    ERROR_HANDLING = "error_handling"
    AUTH_CHECK = "auth_check"
    NOTIFICATION = "notification"
    WORKFLOW = "workflow"
    UNKNOWN = "unknown"


@dataclass
class CodeDNA:
    """Represents the DNA/intent of a piece of code"""
    intent: IntentType
    purpose: str  # Human-readable purpose
    business_rules: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    side_effects: list[str] = field(default_factory=list)
    invariants: list[str] = field(default_factory=list)  # Things that must remain true
    hash: str = ""


@dataclass  
class IntentViolation:
    severity: str
    description: str
    original_intent: str
    suggested_preservation: str


class CodeDNAInterpreter:
    """
    Analyzes code to understand WHY it was written, not just WHAT it does.
    Preserves business logic during refactoring by tracking invariants.
    """
    
    def __init__(self, storage_path: str = "./codedna_store"):
        self.storage_path = storage_path
        self.dna_cache: dict[str, CodeDNA] = {}
        self.invariant_rules: dict[str, list[str]] = {}  # project -> rules
        
        # Intent patterns - could be enhanced with ML
        self.intent_patterns = {
            IntentType.DATA_FETCH: [
                "query", "select", "fetch", "get", "retrieve", "load",
                "db.", "sqlite", "mysql", "postgres", "redis"
            ],
            IntentType.VALIDATION: [
                "validate", "check", "verify", "assert", "is_valid",
                "schema", "type", "cast", "parse"
            ],
            IntentType.BUSINESS_LOGIC: [
                "calculate", "compute", "determine", "apply", "process",
                "rules", "policy", "discount", "price", "total"
            ],
            IntentType.AUTH_CHECK: [
                "auth", "permission", "access", "role", "allowed",
                "can_", "is_", "has_", "verify_token"
            ],
            IntentType.CACHING: [
                "cache", "memoize", "store", "put", "set_",
                "ttl", "expire", "invalidate"
            ],
            IntentType.ERROR_HANDLING: [
                "try", "catch", "except", "handle", "fallback",
                "retry", "on_error", "finally"
            ],
            IntentType.NOTIFICATION: [
                "send", "notify", "email", "sms", "push", "webhook",
                "alert", "log", "event"
            ],
            IntentType.WORKFLOW: [
                "workflow", "pipeline", "stage", "step", "task",
                "queue", "job", "worker"
            ],
        }
    
    def analyze(self, code: str, language: str = "python") -> CodeDNA:
        """
        Analyze code to extract its DNA/intent.
        
        Args:
            code: Source code to analyze
            language: Programming language
        
        Returns:
            CodeDNA object with intent and invariants
        """
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        
        # Check cache
        if code_hash in self.dna_cache:
            return self.dna_cache[code_hash]
        
        # Detect intent
        intent = self._detect_intent(code, language)
        
        # Extract business rules
        rules = self._extract_business_rules(code, language)
        
        # Find dependencies
        deps = self._extract_dependencies(code, language)
        
        # Find side effects
        side_effects = self._find_side_effects(code, language)
        
        # Extract invariants (things that must remain true)
        invariants = self._extract_invariants(code, language, intent)
        
        dna = CodeDNA(
            intent=intent,
            purpose=self._generate_purpose(code, intent),
            business_rules=rules,
            dependencies=deps,
            side_effects=side_effects,
            invariants=invariants,
            hash=code_hash
        )
        
        self.dna_cache[code_hash] = dna
        return dna
    
    def _detect_intent(self, code: str, language: str) -> IntentType:
        """Detect primary intent of code"""
        
        code_lower = code.lower()
        scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = sum(1 for p in patterns if p in code_lower)
            scores[intent_type] = score
        
        if max(scores.values()) == 0:
            return IntentType.UNKNOWN
        
        return max(scores, key=scores.get)
    
    def _extract_business_rules(self, code: str, language: str) -> list[str]:
        """Extract business rules embedded in code"""
        rules = []
        
        if language == "python":
            # Extract constants that might be business rules
            for line in code.split('\n'):
                # Magic numbers with context
                if 'if' in line and ('<' in line or '>' in line or '==' in line):
                    # Threshold comparisons are often business rules
                    rules.append(f"Threshold check: {line.strip()}")
                
                # Named constants
                if '=' in line and not '==' in line:
                    var = line.split('=')[0].strip()
                    if var.isupper() or var.startswith('MAX_') or var.startswith('MIN_'):
                        rules.append(f"Business constant: {line.strip()}")
        
        return rules
    
    def _extract_dependencies(self, code: str, language: str) -> list[str]:
        """Extract what this code depends on"""
        deps = []
        
        if language == "python":
            # Import statements
            for line in code.split('\n'):
                if line.strip().startswith(('import ', 'from ')):
                    deps.append(line.strip())
        
        return deps
    
    def _find_side_effects(self, code: str, language: str) -> list[str]:
        """Identify potential side effects"""
        side_effects = []
        
        effect_indicators = [
            'print(', 'log.', 'write(', '.send(', 'request.',
            'update(', 'delete(', 'insert(', 'exec(',
            'setTimeout', 'setInterval', 'emit('
        ]
        
        for indicator in effect_indicators:
            if indicator in code:
                side_effects.append(f"External call: {indicator}")
        
        return side_effects
    
    def _extract_invariants(self, code: str, language: str, intent: IntentType) -> list[str]:
        """
        Extract invariants - conditions that MUST remain true.
        This is the KEY feature - preserves business logic during refactoring.
        """
        invariants = []
        
        if language == "python":
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    # Find assertions - these are explicit invariants
                    if isinstance(node, ast.Assert):
                        invariants.append(f"MUST be true: {ast.unparse(node.test)}")
                    
                    # Find raises - error conditions that must be handled
                    if isinstance(node, ast.Raise):
                        invariants.append(f"MUST handle: {ast.unparse(node.exc)}")
                    
                    # Find if conditions that guard important logic
                    if isinstance(node, ast.If):
                        condition = ast.unparse(node.test)
                        if any(kw in condition for kw in ['auth', 'permission', 'valid', 'admin']):
                            invariants.append(f"Guard condition: {condition}")
            except:
                pass
        
        # Add intent-specific invariants
        if intent == IntentType.VALIDATION:
            invariants.append("Input MUST be validated before processing")
        elif intent == IntentType.AUTH_CHECK:
            invariants.append("MUST reject unauthorized access")
        elif intent == IntentType.DATA_FETCH:
            invariants.append("MUST handle empty/missing data gracefully")
        
        return invariants
    
    def _generate_purpose(self, code: str, intent: IntentType) -> str:
        """Generate human-readable purpose statement"""
        
        templates = {
            IntentType.DATA_FETCH: "Retrieves data from a data source",
            IntentType.DATA_TRANSFORM: "Transforms input data into output format",
            IntentType.VALIDATION: "Validates input meets required criteria",
            IntentType.BUSINESS_LOGIC: "Implements core business rules",
            IntentType.SIDE_EFFECT: "Performs external side effects",
            IntentType.CACHING: "Caches data for performance",
            IntentType.ERROR_HANDLING: "Handles and recovers from errors",
            IntentType.AUTH_CHECK: "Verifies user permissions",
            IntentType.NOTIFICATION: "Sends notifications or events",
            IntentType.WORKFLOW: "Executes a multi-step workflow",
            IntentType.UNKNOWN: "Performs unspecified operations"
        }
        
        return templates.get(intent, "Unknown purpose")
    
    def verify_refactoring(
        self, 
        original_code: str, 
        new_code: str,
        language: str = "python"
    ) -> dict:
        """
        Verify that refactored code preserves the original DNA/intent.
        
        Returns violations that would break business logic.
        """
        original_dna = self.analyze(original_code, language)
        new_dna = self.analyze(new_code, language)
        
        violations = []
        
        # Check intent preserved
        if original_dna.intent != new_dna.intent:
            violations.append(IntentViolation(
                severity="critical",
                description=f"Intent changed from {original_dna.intent.value} to {new_dna.intent.value}",
                original_intent=original_dna.purpose,
                suggested_preservation="Keep the same intent"
            ))
        
        # Check invariants preserved
        original_invariants = set(original_dna.invariants)
        new_invariants = set(new_dna.invariants)
        
        lost_invariants = original_invariants - new_invariants
        for inv in lost_invariants:
            violations.append(IntentViolation(
                severity="critical",
                description=f"Lost invariant: {inv}",
                original_intent=original_dna.purpose,
                suggested_preservation=f"Re-add: {inv}"
            ))
        
        # Check side effects preserved
        original_effects = set(original_dna.side_effects)
        new_effects = set(new_dna.side_effects)
        
        lost_effects = original_effects - new_effects
        for effect in lost_effects:
            if effect.startswith("External call"):
                violations.append(IntentViolation(
                    severity="warning",
                    description=f"Lost side effect: {effect}",
                    original_intent=original_dna.purpose,
                    suggested_preservation="Preserve external calls if required"
                ))
        
        # Check business rules preserved
        original_rules = set(original_dna.business_rules)
        new_rules = set(new_dna.business_rules)
        
        lost_rules = original_rules - new_rules
        for rule in lost_rules:
            violations.append(IntentViolation(
                severity="critical",
                description=f"Lost business rule: {rule}",
                original_intent=original_dna.purpose,
                suggested_preservation="Preserve business logic"
            ))
        
        return {
            "preserved": len(violations) == 0,
            "original_intent": original_dna.purpose,
            "new_intent": new_dna.purpose,
            "violations": [
                {
                    "severity": v.severity,
                    "description": v.description,
                    "fix": v.suggested_preservation
                }
                for v in violations
            ],
            "risk_score": sum(
                3 if v.severity == "critical" else 1 
                for v in violations
            )
        }
    
    def generate_preservation_guide(self, code: str, language: str = "python") -> str:
        """
        Generate a guide for preserving intent during modifications.
        """
        dna = self.analyze(code, language)
        
        guide = f"""# Code DNA Preservation Guide

## Purpose
{dna.purpose}

## Intent Type
{dna.intent.value}

## Invariants (MUST PRESERVE)
"""
        for inv in dna.invariants:
            guide += f"- {inv}\n"
        
        guide += """
## Business Rules
"""
        for rule in dna.business_rules:
            guide += f"- {rule}\n"
        
        guide += """
## Side Effects
"""
        for effect in dna.side_effects:
            guide += f"- {effect}\n"
        
        guide += """
## Dependencies
"""
        for dep in dna.dependencies:
            guide += f"- {dep}\n"
        
        return guide


# Demo
if __name__ == "__main__":
    interpreter = CodeDNAInterpreter()
    
    original = '''
def calculate_price(quantity, user_tier):
    if quantity < 0:
        raise ValueError("Quantity must be positive")
    
    base_price = 10.0
    
    # Business rule: Gold users get 20% discount
    if user_tier == "gold":
        base_price = base_price * 0.8
    elif user_tier == "silver":
        base_price = base_price * 0.9
    
    return quantity * base_price
'''
    
    broken_refactor = '''
def calculate_price(quantity, user_tier):
    # Removed validation - VIOLATION!
    return quantity * 10.0
'''
    
    print("🧬 CODEDNA INTERPRETER")
    print("=" * 50)
    
    # Analyze original
    dna = interpreter.analyze(original)
    print(f"\nIntent: {dna.intent.value}")
    print(f"Purpose: {dna.purpose}")
    print(f"Invariants: {dna.invariants}")
    print(f"Business Rules: {dna.business_rules}")
    
    # Verify refactoring
    result = interpreter.verify_refactoring(original, broken_refactor)
    print(f"\n{'❌ VIOLATIONS FOUND' if not result['preserved'] else '✅ PRESERVED'}")
    for v in result['violations']:
        print(f"  [{v['severity']}] {v['description']}")
        print(f"     Fix: {v['fix']}")
    print(f"\nRisk Score: {result['risk_score']}")
