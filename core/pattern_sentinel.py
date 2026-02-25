#!/usr/bin/env python3
"""
OmniClaw Pattern Sentinel
Learns from past bugs in YOUR codebase and proactively warns
when similar patterns appear in new code or changes.
"""

import logging
import json
import time
import hashlib
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum

logger = logging.getLogger("OmniClaw.PatternSentinel")


class Severity(Enum):
    """Warning severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class BugPattern:
    """A recorded bug pattern"""
    pattern_id: str
    description: str                # What the bug was
    root_cause: str                 # Why it happened
    fix: str                        # How it was fixed
    files_affected: List[str] = field(default_factory=list)
    code_pattern: str = ""          # Code snippet that exhibits the bug
    detection_regex: str = ""       # Regex to detect similar patterns
    keywords: List[str] = field(default_factory=list)
    severity: str = "warning"
    language: str = "python"
    category: str = "general"       # "memory_leak", "race_condition", "null_ref", etc.
    occurrences: int = 1
    last_seen: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)


@dataclass
class PatternWarning:
    """A proactive warning about a potential bug pattern"""
    pattern_id: str
    severity: Severity
    message: str
    file_path: str
    line_number: Optional[int] = None
    code_context: str = ""
    suggestion: str = ""
    confidence: float = 0.5


class PatternSentinel:
    """
    Learns from past bugs and proactively warns about similar patterns.
    
    Records bug fixes, analyzes their root causes, and watches for
    the same patterns in new code — catching bugs before they happen.
    """
    
    def __init__(self, storage_dir: str = "./memory_db/patterns",
                 memory=None):
        """
        Args:
            storage_dir: Directory for storing bug patterns
            memory: Optional VectorMemory for semantic similarity
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.memory = memory
        
        # Pattern database
        self.patterns: Dict[str, BugPattern] = {}
        self._load_all()
        
        # Built-in patterns (language-agnostic gotchas)
        self._builtin_patterns = self._initialize_builtins()
        
        logger.info(f"PatternSentinel initialized: {len(self.patterns)} learned patterns, "
                    f"{len(self._builtin_patterns)} built-in patterns")
    
    def record_bug(self, description: str, root_cause: str, fix: str,
                    files_affected: List[str] = None,
                    code_pattern: str = "",
                    detection_regex: str = "",
                    keywords: List[str] = None,
                    severity: str = "warning",
                    language: str = "python",
                    category: str = "general") -> str:
        """
        Record a bug pattern for future detection.
        
        Args:
            description: What the bug was
            root_cause: Why it happened
            fix: How it was fixed
            files_affected: Files where the bug appeared
            code_pattern: Example code that exhibits the bug
            detection_regex: Regex pattern to detect similar bugs
            keywords: Keywords to help match this pattern
            severity: How severe this type of bug is
            language: Programming language
            category: Bug category
            
        Returns:
            Pattern ID
        """
        pattern_id = self._generate_id(description)
        
        # Auto-extract keywords if not provided
        if not keywords:
            keywords = self._extract_keywords(description, root_cause, fix)
        
        pattern = BugPattern(
            pattern_id=pattern_id,
            description=description,
            root_cause=root_cause,
            fix=fix,
            files_affected=files_affected or [],
            code_pattern=code_pattern,
            detection_regex=detection_regex,
            keywords=keywords,
            severity=severity,
            language=language,
            category=category,
        )
        
        self.patterns[pattern_id] = pattern
        self._save_pattern(pattern)
        
        # Store in vector memory
        if self.memory:
            try:
                import asyncio
                text = f"{description} | {root_cause} | {fix}"
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(
                        self.memory.store(pattern_id, text, "knowledge")
                    )
                else:
                    loop.run_until_complete(
                        self.memory.store(pattern_id, text, "knowledge")
                    )
            except Exception as e:
                logger.debug(f"Could not store pattern in vector memory: {e}")
        
        logger.info(f"Bug pattern recorded [{severity}]: {description}")
        return pattern_id
    
    def scan_for_patterns(self, code: str, language: str = "python",
                           file_path: str = "") -> List[PatternWarning]:
        """
        Scan code for known bug patterns.
        
        Args:
            code: Source code to analyze
            language: Programming language
            file_path: File path for context
            
        Returns:
            List of warnings for detected patterns
        """
        warnings = []
        
        # Check learned patterns
        for pid, pattern in self.patterns.items():
            if pattern.language != language and pattern.language != "any":
                continue
            
            matches = self._check_pattern(code, pattern, file_path)
            warnings.extend(matches)
        
        # Check built-in patterns
        for pattern in self._builtin_patterns:
            if pattern.language != language and pattern.language != "any":
                continue
            
            matches = self._check_pattern(code, pattern, file_path)
            warnings.extend(matches)
        
        # Sort by severity
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        warnings.sort(key=lambda w: severity_order.get(w.severity.value, 99))
        
        if warnings:
            logger.info(f"Found {len(warnings)} pattern warnings in {file_path or 'code'}")
        
        return warnings
    
    def get_warnings(self, file_path: str) -> List[PatternWarning]:
        """
        Get proactive warnings for a specific file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            List of warnings
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            # Detect language from extension
            ext = Path(file_path).suffix.lower()
            lang_map = {
                ".py": "python", ".js": "javascript", ".ts": "typescript",
                ".go": "go", ".rs": "rust", ".java": "java",
                ".c": "c", ".cpp": "cpp", ".rb": "ruby",
            }
            language = lang_map.get(ext, "unknown")
            
            return self.scan_for_patterns(code, language, file_path)
            
        except Exception as e:
            logger.error(f"Could not scan file {file_path}: {e}")
            return []
    
    def scan_diff(self, diff_text: str, language: str = "python") -> List[PatternWarning]:
        """
        Scan a diff for bug patterns (focuses on added lines).
        
        Args:
            diff_text: Unified diff text
            language: Programming language
            
        Returns:
            List of warnings
        """
        # Extract added lines from diff
        added_lines = []
        for line in diff_text.splitlines():
            if line.startswith('+') and not line.startswith('+++'):
                added_lines.append(line[1:])
        
        if not added_lines:
            return []
        
        added_code = '\n'.join(added_lines)
        return self.scan_for_patterns(added_code, language, "diff")
    
    # --- Private helpers ---
    
    def _check_pattern(self, code: str, pattern: BugPattern,
                        file_path: str) -> List[PatternWarning]:
        """Check if a specific pattern matches in the code"""
        warnings = []
        
        # Check via regex if available
        if pattern.detection_regex:
            try:
                for match in re.finditer(pattern.detection_regex, code):
                    line_num = code[:match.start()].count('\n') + 1
                    warnings.append(PatternWarning(
                        pattern_id=pattern.pattern_id,
                        severity=Severity(pattern.severity),
                        message=f"Potential bug: {pattern.description}",
                        file_path=file_path,
                        line_number=line_num,
                        code_context=match.group(0)[:200],
                        suggestion=f"Root cause: {pattern.root_cause}\nFix: {pattern.fix}",
                        confidence=0.8,
                    ))
            except re.error:
                pass
        
        # Check via keyword matching
        if pattern.keywords:
            code_lower = code.lower()
            keyword_hits = sum(1 for kw in pattern.keywords if kw.lower() in code_lower)
            keyword_ratio = keyword_hits / len(pattern.keywords) if pattern.keywords else 0
            
            if keyword_ratio >= 0.6:  # At least 60% keyword match
                warnings.append(PatternWarning(
                    pattern_id=pattern.pattern_id,
                    severity=Severity(pattern.severity),
                    message=f"Possible pattern match: {pattern.description}",
                    file_path=file_path,
                    suggestion=f"Root cause: {pattern.root_cause}\nFix: {pattern.fix}",
                    confidence=round(keyword_ratio * 0.7, 2),
                ))
        
        # Check via code pattern similarity
        if pattern.code_pattern and pattern.code_pattern in code:
            line_num = code[:code.index(pattern.code_pattern)].count('\n') + 1
            warnings.append(PatternWarning(
                pattern_id=pattern.pattern_id,
                severity=Severity(pattern.severity),
                message=f"Known bug pattern detected: {pattern.description}",
                file_path=file_path,
                line_number=line_num,
                code_context=pattern.code_pattern[:200],
                suggestion=f"Fix: {pattern.fix}",
                confidence=0.95,
            ))
        
        return warnings
    
    def _initialize_builtins(self) -> List[BugPattern]:
        """Initialize built-in common bug patterns"""
        return [
            BugPattern(
                pattern_id="builtin_mutable_default",
                description="Mutable default argument in function definition",
                root_cause="Default mutable arguments are shared across all calls",
                fix="Use None as default and initialize inside the function",
                detection_regex=r"def\s+\w+\(.*(?:=\s*\[\]|=\s*\{\}|=\s*set\(\)).*\)",
                keywords=["def", "default", "list", "dict", "mutable"],
                severity="warning",
                language="python",
                category="mutable_default",
            ),
            BugPattern(
                pattern_id="builtin_bare_except",
                description="Bare except clause catches all exceptions including SystemExit",
                root_cause="except: catches everything, masking real errors",
                fix="Use except Exception: or specific exception types",
                detection_regex=r"except\s*:",
                keywords=["except", "catch", "error"],
                severity="warning",
                language="python",
                category="error_handling",
            ),
            BugPattern(
                pattern_id="builtin_hardcoded_secret",
                description="Potential hardcoded secret or API key",
                root_cause="Secrets in source code can be leaked via version control",
                fix="Use environment variables or a secrets manager",
                detection_regex=r'(?:api_key|secret|password|token)\s*=\s*["\'][^"\']{8,}["\']',
                keywords=["api_key", "secret", "password", "token"],
                severity="critical",
                language="any",
                category="security",
            ),
            BugPattern(
                pattern_id="builtin_sql_injection",
                description="Potential SQL injection via string formatting",
                root_cause="User input directly interpolated into SQL query",
                fix="Use parameterized queries or an ORM",
                detection_regex=r'(?:execute|cursor\.execute)\s*\(\s*f["\']|(?:execute|cursor\.execute)\s*\(\s*["\'].*%\s',
                keywords=["execute", "sql", "query", "format", "cursor"],
                severity="critical",
                language="python",
                category="security",
            ),
            BugPattern(
                pattern_id="builtin_no_timeout",
                description="HTTP request without timeout",
                root_cause="Requests without timeout can hang indefinitely",
                fix="Always specify a timeout parameter",
                detection_regex=r'requests\.(?:get|post|put|delete|patch)\([^)]*(?<!\btimeout\b)[^)]*\)',
                keywords=["requests", "get", "post", "http"],
                severity="info",
                language="python",
                category="reliability",
            ),
        ]
    
    def _extract_keywords(self, *texts) -> List[str]:
        """Extract keywords from text"""
        stop_words = {"the", "a", "an", "is", "was", "were", "be", "been",
                      "being", "have", "has", "had", "do", "does", "did",
                      "will", "would", "could", "should", "may", "might",
                      "can", "shall", "to", "of", "in", "for", "on", "with",
                      "at", "by", "from", "and", "or", "but", "not", "this",
                      "that", "it", "its"}
        
        words = set()
        for text in texts:
            for word in re.findall(r'\b\w+\b', text.lower()):
                if word not in stop_words and len(word) > 2:
                    words.add(word)
        
        return list(words)[:20]
    
    def _generate_id(self, description: str) -> str:
        """Generate a unique pattern ID"""
        hash_val = hashlib.md5(f"{description}:{time.time()}".encode()).hexdigest()[:12]
        return f"pat_{hash_val}"
    
    def _save_pattern(self, pattern: BugPattern):
        """Save a pattern to disk"""
        path = self.storage_dir / f"{pattern.pattern_id}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(asdict(pattern), f, indent=2)
    
    def _load_all(self):
        """Load all patterns from disk"""
        for path in self.storage_dir.glob("pat_*.json"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                p = BugPattern(**data)
                self.patterns[p.pattern_id] = p
            except Exception as e:
                logger.warning(f"Could not load pattern {path}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pattern sentinel statistics"""
        patterns = list(self.patterns.values())
        return {
            "learned_patterns": len(patterns),
            "builtin_patterns": len(self._builtin_patterns),
            "by_severity": {
                s.value: sum(1 for p in patterns if p.severity == s.value)
                for s in Severity
            },
            "by_category": {},  # Could be expanded
            "storage_dir": str(self.storage_dir),
        }
