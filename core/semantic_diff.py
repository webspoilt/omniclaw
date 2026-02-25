#!/usr/bin/env python3
"""
OmniClaw Semantic Diff
Understands the semantic MEANING of code changes — not just lines.
Detects behavioral changes, API contract breaks, SOLID violations,
and categorizes changes by intent.
"""

import logging
import difflib
import re
import ast
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("OmniClaw.SemanticDiff")


class ChangeCategory(Enum):
    """Categories of code changes by intent"""
    COSMETIC = "cosmetic"           # Formatting, whitespace, comments
    REFACTOR = "refactor"           # Same behavior, different structure
    BUGFIX = "bugfix"               # Fixes incorrect behavior
    FEATURE = "feature"             # Adds new functionality
    BREAKING = "breaking"           # Breaks existing contracts
    PERFORMANCE = "performance"     # Performance optimization
    SECURITY = "security"           # Security-related change
    DOCUMENTATION = "documentation" # Doc changes only
    DEPENDENCY = "dependency"       # Dependency updates
    UNKNOWN = "unknown"


@dataclass
class SemanticChange:
    """A semantically analyzed change"""
    category: ChangeCategory
    description: str
    severity: str = "low"          # "low", "medium", "high", "critical"
    confidence: float = 0.5
    details: str = ""


@dataclass
class SemanticAnalysis:
    """Complete semantic analysis of a diff"""
    file_path: str
    changes: List[SemanticChange] = field(default_factory=list)
    behavioral_changes: List[str] = field(default_factory=list)
    api_contract_changes: List[str] = field(default_factory=list)
    solid_violations: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    side_effects: List[str] = field(default_factory=list)
    summary: str = ""
    overall_risk: str = "low"
    timestamp: float = field(default_factory=time.time)


class SemanticDiff:
    """
    Analyzes code changes for semantic meaning.
    
    Goes beyond line-by-line diffing to understand WHAT changed
    in terms of behavior, contracts, and design principles.
    """
    
    def __init__(self, llm_call: Optional[Callable] = None):
        """
        Args:
            llm_call: Async function that takes a prompt and returns LLM response
        """
        self.llm_call = llm_call
        self.analysis_history: List[SemanticAnalysis] = []
        
        logger.info("SemanticDiff initialized")
    
    async def analyze_diff(self, old_code: str, new_code: str,
                            language: str = "python",
                            file_path: str = "") -> SemanticAnalysis:
        """
        Perform full semantic analysis of a code change.
        
        Args:
            old_code: Original code
            new_code: Modified code
            language: Programming language
            file_path: Path to the file
            
        Returns:
            Complete SemanticAnalysis
        """
        analysis = SemanticAnalysis(file_path=file_path)
        
        # Generate the textual diff
        diff_text = self._generate_diff(old_code, new_code, file_path)
        
        if not diff_text.strip():
            analysis.summary = "No changes detected"
            return analysis
        
        # Static analysis (fast, no LLM needed)
        static_changes = self._static_analysis(old_code, new_code, language)
        analysis.changes.extend(static_changes)
        
        # AST-based analysis for Python
        if language == "python":
            ast_changes = self._ast_analysis(old_code, new_code)
            analysis.behavioral_changes.extend(ast_changes.get("behavioral", []))
            analysis.api_contract_changes.extend(ast_changes.get("api_contract", []))
            analysis.breaking_changes.extend(ast_changes.get("breaking", []))
        
        # LLM-based deep analysis (if available)
        if self.llm_call:
            llm_analysis = await self._llm_analysis(old_code, new_code, diff_text, language)
            if llm_analysis:
                analysis.solid_violations.extend(llm_analysis.get("solid_violations", []))
                analysis.side_effects.extend(llm_analysis.get("side_effects", []))
                analysis.summary = llm_analysis.get("summary", "")
                
                # Merge LLM-detected changes
                for change_data in llm_analysis.get("changes", []):
                    try:
                        cat = ChangeCategory(change_data.get("category", "unknown"))
                    except ValueError:
                        cat = ChangeCategory.UNKNOWN
                    analysis.changes.append(SemanticChange(
                        category=cat,
                        description=change_data.get("description", ""),
                        severity=change_data.get("severity", "low"),
                        confidence=change_data.get("confidence", 0.5),
                    ))
        
        # Calculate overall risk
        analysis.overall_risk = self._calculate_risk(analysis)
        
        # Generate summary if not from LLM
        if not analysis.summary:
            analysis.summary = self._generate_summary(analysis)
        
        self.analysis_history.append(analysis)
        logger.info(f"Semantic analysis complete for {file_path}: risk={analysis.overall_risk}")
        
        return analysis
    
    def categorize_changes(self, diff_text: str) -> List[SemanticChange]:
        """
        Categorize changes from a diff using heuristics.
        
        Args:
            diff_text: Unified diff text
            
        Returns:
            List of categorized changes
        """
        changes = []
        added_lines = []
        removed_lines = []
        
        for line in diff_text.splitlines():
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:].strip())
            elif line.startswith('-') and not line.startswith('---'):
                removed_lines.append(line[1:].strip())
        
        # Detect cosmetic changes (only whitespace/comment differences)
        if self._is_cosmetic_only(added_lines, removed_lines):
            changes.append(SemanticChange(
                category=ChangeCategory.COSMETIC,
                description="Formatting or whitespace changes only",
                severity="low",
                confidence=0.9,
            ))
            return changes
        
        # Detect documentation changes
        if all(self._is_doc_line(l) for l in added_lines + removed_lines if l):
            changes.append(SemanticChange(
                category=ChangeCategory.DOCUMENTATION,
                description="Documentation changes only",
                severity="low",
                confidence=0.85,
            ))
            return changes
        
        # Detect dependency changes
        dep_patterns = ["import ", "require(", "from ", "pip install", "npm install"]
        if any(any(p in l for p in dep_patterns) for l in added_lines + removed_lines):
            changes.append(SemanticChange(
                category=ChangeCategory.DEPENDENCY,
                description="Dependency changes detected",
                severity="medium",
                confidence=0.7,
            ))
        
        # Detect potential bugfix (error handling changes)
        error_patterns = ["except", "catch", "finally", "raise", "throw", "assert"]
        if any(any(p in l for p in error_patterns) for l in added_lines):
            changes.append(SemanticChange(
                category=ChangeCategory.BUGFIX,
                description="Error handling modifications",
                severity="medium",
                confidence=0.6,
            ))
        
        # Detect new functionality
        func_patterns = ["def ", "function ", "class ", "async def "]
        new_funcs = [l for l in added_lines if any(l.strip().startswith(p) for p in func_patterns)]
        if new_funcs:
            changes.append(SemanticChange(
                category=ChangeCategory.FEATURE,
                description=f"New definitions: {', '.join(l.strip()[:50] for l in new_funcs[:3])}",
                severity="medium",
                confidence=0.75,
            ))
        
        # Detect removed functionality (potential breaking)
        removed_funcs = [l for l in removed_lines if any(l.strip().startswith(p) for p in func_patterns)]
        if removed_funcs:
            changes.append(SemanticChange(
                category=ChangeCategory.BREAKING,
                description=f"Removed definitions: {', '.join(l.strip()[:50] for l in removed_funcs[:3])}",
                severity="high",
                confidence=0.7,
            ))
        
        if not changes:
            changes.append(SemanticChange(
                category=ChangeCategory.UNKNOWN,
                description="Changes require manual review",
                severity="medium",
                confidence=0.3,
            ))
        
        return changes
    
    def generate_review_summary(self, file_path: str, 
                                  old_content: str, new_content: str) -> str:
        """
        Generate a human-readable review summary.
        
        Args:
            file_path: Path to the file
            old_content: Original content
            new_content: New content
            
        Returns:
            Formatted review summary string
        """
        diff_text = self._generate_diff(old_content, new_content, file_path)
        changes = self.categorize_changes(diff_text)
        
        # Count line changes
        added = sum(1 for l in diff_text.splitlines() if l.startswith('+') and not l.startswith('+++'))
        removed = sum(1 for l in diff_text.splitlines() if l.startswith('-') and not l.startswith('---'))
        
        lines = []
        lines.append(f"═══ Semantic Review: {os.path.basename(file_path)} ═══")
        lines.append(f"Lines: +{added} / -{removed}")
        lines.append("")
        
        for change in changes:
            icon = {
                "cosmetic": "🎨", "refactor": "♻️", "bugfix": "🐛",
                "feature": "✨", "breaking": "💥", "performance": "⚡",
                "security": "🔒", "documentation": "📝", "dependency": "📦",
                "unknown": "❓",
            }.get(change.category.value, "❓")
            
            severity_color = {
                "low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"
            }.get(change.severity, "⚪")
            
            lines.append(f"{icon} {severity_color} [{change.category.value.upper()}] "
                        f"{change.description}")
            if change.details:
                lines.append(f"   └─ {change.details}")
        
        return "\n".join(lines)
    
    # --- Private helpers ---
    
    def _generate_diff(self, old: str, new: str, file_path: str = "") -> str:
        """Generate a unified diff"""
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        return ''.join(difflib.unified_diff(
            old_lines, new_lines,
            fromfile=f"a/{os.path.basename(file_path)}",
            tofile=f"b/{os.path.basename(file_path)}",
        ))
    
    def _static_analysis(self, old_code: str, new_code: str,
                          language: str) -> List[SemanticChange]:
        """Perform static analysis on the changes"""
        changes = []
        
        old_lines = set(old_code.splitlines())
        new_lines = set(new_code.splitlines())
        
        added = new_lines - old_lines
        removed = old_lines - new_lines
        
        # Detect return type changes
        if language == "python":
            old_returns = set(re.findall(r'def\s+(\w+).*->\s*(\w+)', old_code))
            new_returns = set(re.findall(r'def\s+(\w+).*->\s*(\w+)', new_code))
            
            for func, old_type in old_returns:
                for nfunc, new_type in new_returns:
                    if func == nfunc and old_type != new_type:
                        changes.append(SemanticChange(
                            category=ChangeCategory.BREAKING,
                            description=f"Return type of '{func}' changed: {old_type} → {new_type}",
                            severity="high",
                            confidence=0.9,
                        ))
            
            # Detect function signature changes
            old_sigs = dict(re.findall(r'def\s+(\w+)\((.*?)\)', old_code))
            new_sigs = dict(re.findall(r'def\s+(\w+)\((.*?)\)', new_code))
            
            for func in set(old_sigs) & set(new_sigs):
                if old_sigs[func] != new_sigs[func]:
                    changes.append(SemanticChange(
                        category=ChangeCategory.BREAKING,
                        description=f"Signature of '{func}' changed",
                        severity="high",
                        confidence=0.85,
                        details=f"Was: ({old_sigs[func]}) → Now: ({new_sigs[func]})",
                    ))
        
        return changes
    
    def _ast_analysis(self, old_code: str, new_code: str) -> Dict[str, List[str]]:
        """AST-based analysis for Python code"""
        result = {"behavioral": [], "api_contract": [], "breaking": []}
        
        try:
            old_tree = ast.parse(old_code)
            new_tree = ast.parse(new_code)
        except SyntaxError:
            return result
        
        # Extract function/class names
        old_names = self._extract_names(old_tree)
        new_names = self._extract_names(new_tree)
        
        # Removed public names = breaking
        removed = old_names["public_functions"] - new_names["public_functions"]
        for name in removed:
            result["breaking"].append(f"Public function '{name}' was removed")
        
        removed_classes = old_names["classes"] - new_names["classes"]
        for name in removed_classes:
            result["breaking"].append(f"Class '{name}' was removed")
        
        # New functions = behavioral change
        added = new_names["public_functions"] - old_names["public_functions"]
        for name in added:
            result["behavioral"].append(f"New public function '{name}' added")
        
        # Check for changed exception handling
        old_excepts = len([n for n in ast.walk(old_tree) if isinstance(n, ast.ExceptHandler)])
        new_excepts = len([n for n in ast.walk(new_tree) if isinstance(n, ast.ExceptHandler)])
        if old_excepts != new_excepts:
            result["behavioral"].append(
                f"Exception handling changed: {old_excepts} → {new_excepts} handlers"
            )
        
        return result
    
    async def _llm_analysis(self, old_code: str, new_code: str,
                             diff_text: str, language: str) -> Optional[Dict]:
        """Deep analysis using LLM"""
        if not self.llm_call:
            return None
        
        prompt = f"""Analyze this code change semantically. Focus on MEANING, not syntax.

LANGUAGE: {language}

DIFF:
{diff_text[:3000]}

Analyze:
1. What BEHAVIOR changed? (not just what lines changed)
2. Are there any API CONTRACT violations? (changed signatures, return types, etc.)
3. Any SOLID principle violations introduced?
4. Any new SIDE EFFECTS? (I/O, state changes, network calls)
5. What CATEGORY best describes this change?

Respond in JSON:
{{
  "summary": "One-paragraph semantic summary",
  "solid_violations": ["violation 1", ...],
  "side_effects": ["side effect 1", ...],
  "changes": [
    {{
      "category": "bugfix|feature|refactor|breaking|cosmetic|performance|security",
      "description": "what changed semantically",
      "severity": "low|medium|high|critical",
      "confidence": 0.8
    }}
  ]
}}"""

        try:
            response = await self.llm_call(prompt)
            import json
            return json.loads(response)
        except Exception as e:
            logger.error(f"LLM semantic analysis failed: {e}")
            return None
    
    def _extract_names(self, tree: ast.AST) -> Dict[str, set]:
        """Extract public names from an AST"""
        names = {
            "public_functions": set(),
            "private_functions": set(),
            "classes": set(),
        }
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith('_'):
                    names["private_functions"].add(node.name)
                else:
                    names["public_functions"].add(node.name)
            elif isinstance(node, ast.ClassDef):
                names["classes"].add(node.name)
        
        return names
    
    @staticmethod
    def _is_cosmetic_only(added: List[str], removed: List[str]) -> bool:
        """Check if changes are cosmetic only (whitespace/comments)"""
        def normalize(line):
            return re.sub(r'\s+', '', line).strip()
        
        norm_added = set(normalize(l) for l in added if l.strip())
        norm_removed = set(normalize(l) for l in removed if l.strip())
        
        # If normalized versions are the same, it's cosmetic
        return norm_added == norm_removed
    
    @staticmethod
    def _is_doc_line(line: str) -> bool:
        """Check if a line is documentation"""
        stripped = line.strip()
        return (stripped.startswith('#') or 
                stripped.startswith('"""') or stripped.startswith("'''") or
                stripped.startswith('//') or stripped.startswith('/*') or
                stripped.startswith('*'))
    
    @staticmethod
    def _calculate_risk(analysis: SemanticAnalysis) -> str:
        """Calculate overall risk level"""
        if analysis.breaking_changes:
            return "critical"
        if analysis.solid_violations or any(c.severity in ("high", "critical") for c in analysis.changes):
            return "high"
        if analysis.behavioral_changes or analysis.side_effects:
            return "medium"
        return "low"
    
    @staticmethod
    def _generate_summary(analysis: SemanticAnalysis) -> str:
        """Generate a summary from analysis results"""
        parts = []
        
        cats = {}
        for c in analysis.changes:
            cats[c.category.value] = cats.get(c.category.value, 0) + 1
        
        if cats:
            cat_str = ", ".join(f"{v}x {k}" for k, v in cats.items())
            parts.append(f"Changes: {cat_str}")
        
        if analysis.breaking_changes:
            parts.append(f"⚠️ {len(analysis.breaking_changes)} breaking change(s)")
        
        if analysis.behavioral_changes:
            parts.append(f"{len(analysis.behavioral_changes)} behavioral change(s)")
        
        return ". ".join(parts) if parts else "No significant semantic changes detected."
    
    def get_stats(self) -> Dict[str, Any]:
        """Get semantic diff statistics"""
        return {
            "total_analyses": len(self.analysis_history),
            "has_llm": self.llm_call is not None,
        }
