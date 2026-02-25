"""
🛡️ OMNICLAW SECURITY RESEARCH SUITE
====================================
Advanced security research and bug hunting toolkit.

Capabilities:
- Vulnerability Detection & Analysis
- CVE Research & Tracking
- Security Auditing
- Penetration Testing Assistance (Authorized)
- Responsible Disclosure Reports
- Attack Surface Analysis
- Exploit Verification (Defensive)
- Security Posture Assessment

For authorized security research and bug bounty only.
Use responsibly and ethically.

Author: OmniClaw Advanced Features - Security Research Module
"""

import ast
import json
import os
import re
import sqlite3
import hashlib
import uuid
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Callable


# =============================================================================
# ENUMS & DATA STRUCTURES
# =============================================================================

class VulnerabilitySeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    RCE = "rce"
    PATH_TRAVERSAL = "path_traversal"
    IDOR = "idor"
    AUTH_BYPASS = "auth_bypass"
    XXE = "xxe"
    DESERIALIZATION = "deserialization"
    SSRF = "ssrf"
    INSECURE_DESIGN = "insecure_design"
    HARDCODE_SECRETS = "hardcoded_secrets"
    WEAK_CRYPTO = "weak_crypto"
    MEMORY_LEAK = "memory_leak"
    RACE_CONDITION = "race_condition"


@dataclass
class Vulnerability:
    """Represents a found vulnerability"""
    id: str
    type: VulnerabilityType
    severity: VulnerabilitySeverity
    title: str
    description: str
    
    # Location
    file_path: str
    line_number: int
    code_snippet: str
    
    # Details
    cwe_id: str = ""
    cvss_score: float = 0.0
    impact: str = ""
    remediation: str = ""
    
    # Metadata
    confidence: str = "high"  # high, medium, low
    verified: bool = False
    false_positive: bool = False


@dataclass
class SecurityReport:
    """Security audit report"""
    id: str
    project_name: str
    scan_date: datetime
    vulnerabilities: list[Vulnerability]
    
    # Summary
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    
    # Recommendations
    overall_severity: str = ""
    risk_rating: str = ""
    recommendations: list[str] = field(default_factory=list)


@dataclass
class CVEDetails:
    """CVE information"""
    id: str
    description: str
    severity: str
    cvss_score: float
    published_date: str
    affected_products: list[str]
    references: list[str]
    exploitation: str
    mitigation: str


# =============================================================================
# VULNERABILITY SCANNER
# =============================================================================

class VulnerabilityScanner:
    """
    Advanced vulnerability detection engine.
    Scans code for security vulnerabilities and weaknesses.
    """
    
    def __init__(self):
        self.vulnerabilities: list[Vulnerability] = []
        self.db_path = "./vulnerabilities.db"
        self._init_database()
        
        # Load vulnerability patterns
        self.patterns = self._load_patterns()
    
    def _init_database(self):
        """Initialize vulnerability database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS vulnerabilities (
                id TEXT PRIMARY KEY,
                type TEXT,
                severity TEXT,
                title TEXT,
                file_path TEXT,
                line_number INTEGER,
                code_snippet TEXT,
                cwe_id TEXT,
                cvss_score REAL,
                verified INTEGER DEFAULT 0
            )
        """)
        self.conn.commit()
    
    def _load_patterns(self) -> dict:
        """Load vulnerability detection patterns"""
        
        return {
            # SQL Injection
            VulnerabilityType.SQL_INJECTION: {
                "patterns": [
                    r'(?:execute|query|fetch|select|insert|update|delete).*?f["\'].*?\{',
                    r'["\'].*?%s.*?".*?(?:execute|query)',
                    r'cursor\.execute\([^,]+\+',
                    r'\$\{.*?(?:sql|query)',
                ],
                "severity": VulnerabilitySeverity.CRITICAL,
                "cwe_id": "CWE-89",
                "cvss": 9.8,
                "title": "SQL Injection",
                "description": "User input directly concatenated into SQL query",
                "remediation": "Use parameterized queries or ORM"
            },
            
            # Cross-Site Scripting (XSS)
            VulnerabilityType.XSS: {
                "patterns": [
                    r'innerHTML\s*=\s*[^;]+(?<!sanitize)',
                    r'dangerouslySetInnerHTML',
                    r'eval\s*\([^)]*(?:request|params|input)',
                    r'document\.write\(',
                    r'\<\%\=.*?\%\>',
                ],
                "severity": VulnerabilitySeverity.HIGH,
                "cwe_id": "CWE-79",
                "cvss": 7.3,
                "title": "Cross-Site Scripting (XSS)",
                "description": "Untrusted data included in web page without validation",
                "remediation": "Use context-aware output encoding and Content Security Policy"
            },
            
            # Remote Code Execution
            VulnerabilityType.RCE: {
                "patterns": [
                    r'eval\s*\(',
                    r'exec\s*\(',
                    r'system\s*\(',
                    r'shell_exec\s*\(',
                    r'__import__\s*\(\s*["\']os["\']',
                    r'child_process\.exec\(',
                    r'Runtime\.getRuntime\(\)\.exec',
                ],
                "severity": VulnerabilitySeverity.CRITICAL,
                "cwe_id": "CWE-94",
                "cvss": 10.0,
                "title": "Remote Code Execution (RCE)",
                "description": "Application executes arbitrary code from untrusted source",
                "remediation": "Avoid dynamic code execution, use sandboxing"
            },
            
            # Path Traversal
            VulnerabilityType.PATH_TRAVERSAL: {
                "patterns": [
                    r'open\s*\([^)]*\+[^)]*\+',
                    r'file\s*=\s*request\.[^;]+\+',
                    r'File\s*\([^)]*\+[^)]*\)',
                    r'\.\.\/.*?(?:file|path|read)',
                    r'PathTraversal',
                ],
                "severity": VulnerabilitySeverity.HIGH,
                "cwe_id": "CWE-22",
                "cvss": 8.6,
                "title": "Path Traversal",
                "description": "Application uses insufficient validation to access files",
                "remediation": "Validate and sanitize file paths, use allowlists"
            },
            
            # Hardcoded Secrets
            VulnerabilityType.HARDCODE_SECRETS: {
                "patterns": [
                    r'(?:api[_-]?key|secret|password|token|auth)[_-]?\w*\s*=\s*["\'][a-zA-Z0-9]{8,}["\']',
                    r'sk-[a-zA-Z0-9]{20,}',
                    r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----',
                    r'ghp_[a-zA-Z0-9]{36}',
                    r'AKIA[0-9A-Z]{16}',
                    r'["\'][0-9a-f]{32}["\']',
                ],
                "severity": VulnerabilitySeverity.CRITICAL,
                "cwe_id": "CWE-798",
                "cvss": 9.8,
                "title": "Hardcoded Secrets",
                "description": "Sensitive data hardcoded in source code",
                "remediation": "Use environment variables or secrets manager"
            },
            
            # Insecure Deserialization
            VulnerabilityType.DESERIALIZATION: {
                "patterns": [
                    r'pickle\.loads\(',
                    r'yaml\.load\([^,)]+\)',
                    r'json\.pickle',
                    r'unserialize\s*\(',
                    r'ObjectInputStream',
                    r'XMLDecoder',
                ],
                "severity": VulnerabilitySeverity.CRITICAL,
                "cwe_id": "CWE-502",
                "cvss": 9.8,
                "title": "Insecure Deserialization",
                "description": "Untrusted data deserialized without validation",
                "remediation": "Use safe deserialization, validate input"
            },
            
            # XXE
            VulnerabilityType.XXE: {
                "patterns": [
                    r'DocumentBuilderFactory',
                    r'SAXParser',
                    r'XMLReader',
                    r'<!DOCTYPE.*?ENTITY',
                    r'System\.identityHashCode',
                ],
                "severity": VulnerabilitySeverity.HIGH,
                "cwe_id": "CWE-611",
                "cvss": 8.2,
                "title": "XML External Entity (XXE)",
                "description": "XML parser processes external entity references",
                "remediation": "Disable external entities and DTD processing"
            },
            
            # SSRF
            VulnerabilityType.SSRF: {
                "patterns": [
                    r'requests\.(?:get|post)\([^)]*input',
                    r'urlopen\([^)]*(?:url|link)',
                    r'file_get_contents\([^)]*http',
                    r'curl_exec\(',
                ],
                "severity": VulnerabilitySeverity.HIGH,
                "cwe_id": "CWE-918",
                "cvss": 8.6,
                "title": "Server-Side Request Forgery (SSRF)",
                "description": "Application fetches untrusted URL without validation",
                "remediation": "Validate URLs against allowlists"
            },
            
            # Weak Crypto
            VulnerabilityType.WEAK_CRYPTO: {
                "patterns": [
                    r'md5\s*\(',
                    r'sha1\s*\(',
                    r'DES\.',
                    r'RC4',
                    r'ssl_context\s*=\s*SSL\.',
                    r'verify\s*=\s*False',
                ],
                "severity": VulnerabilitySeverity.MEDIUM,
                "cwe_id": "CWE-327",
                "cvss": 5.9,
                "title": "Use of Weak Cryptographic Algorithm",
                "description": "Application uses broken or weak cryptographic algorithm",
                "remediation": "Use modern algorithms (AES-256, SHA-256+)"
            },
            
            # Command Injection
            VulnerabilityType.RCE: {
                "patterns": [
                    r'subprocess\.(?:call|run|Popen)\([^)]*shell\s*=\s*True',
                    r'os\.system\(',
                    r'os\.popen\(',
                    r'Command\(',
                    r'ProcessBuilder',
                ],
                "severity": VulnerabilitySeverity.CRITICAL,
                "cwe_id": "CWE-78",
                "cvss": 9.8,
                "title": "OS Command Injection",
                "description": "Application constructs OS commands from untrusted input",
                "remediation": "Avoid shell commands, use API instead"
            }
        }
    
    def scan_file(self, file_path: str) -> list[Vulnerability]:
        """Scan a single file for vulnerabilities"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return []
        
        vulnerabilities = []
        
        # Check each vulnerability type
        for vuln_type, pattern_data in self.patterns.items():
            patterns = pattern_data["patterns"]
            
            for i, line in enumerate(content.split('\n'), 1):
                # Skip comments
                if line.strip().startswith(('#', '//', '/*', '*', '<!--')):
                    continue
                
                for pattern in patterns:
                    try:
                        if re.search(pattern, line, re.IGNORECASE):
                            vuln = Vulnerability(
                                id=str(uuid.uuid4()),
                                type=vuln_type,
                                severity=pattern_data["severity"],
                                title=pattern_data["title"],
                                description=pattern_data["description"],
                                file_path=file_path,
                                line_number=i,
                                code_snippet=line.strip()[:100],
                                cwe_id=pattern_data["cwe_id"],
                                cvss_score=pattern_data["cvss"],
                                remediation=pattern_data["remediation"]
                            )
                            vulnerabilities.append(vuln)
                            break
                    except re.error:
                        pass
        
        # Also run AST-based analysis
        if file_path.endswith('.py'):
            vulnerabilities.extend(self._scan_python_ast(file_path, content))
        
        return vulnerabilities
    
    def _scan_python_ast(self, file_path: str, content: str) -> list[Vulnerability]:
        """Advanced AST-based Python vulnerability scanning"""
        
        vulnerabilities = []
        
        try:
            tree = ast.parse(content)
        except:
            return vulnerabilities
        
        # Check for dangerous imports
        dangerous_imports = {
            'pickle': VulnerabilityType.DESERIALIZATION,
            'marshal': VulnerabilityType.DESERIALIZATION,
            'eval': VulnerabilityType.RCE,
            'exec': VulnerabilityType.RCE,
            'subprocess': VulnerabilityType.RCE,
        }
        
        for node in ast.walk(tree):
            # Check dangerous function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in dangerous_imports:
                        vuln = Vulnerability(
                            id=str(uuid.uuid4()),
                            type=dangerous_imports[node.func.id],
                            severity=VulnerabilitySeverity.CRITICAL,
                            title=f"Dangerous function: {node.func.id}",
                            description=f"Use of dangerous function {node.func.id}",
                            file_path=file_path,
                            line_number=node.lineno,
                            code_snippet=f"{node.func.id}(...)",
                            cwe_id="CWE-94",
                            cvss_score=9.8
                        )
                        vulnerabilities.append(vuln)
            
            # Check for SQL queries
            if isinstance(node, ast.Call):
                if hasattr(node.func, 'attr'):
                    if node.func.attr in ['execute', 'cursor']:
                        # Check if using f-string or concatenation
                        for arg in node.args:
                            if isinstance(arg, (ast.JoinedStr, ast.BinOp)):
                                vuln = Vulnerability(
                                    id=str(uuid.uuid4()),
                                    type=VulnerabilityType.SQL_INJECTION,
                                    severity=VulnerabilitySeverity.CRITICAL,
                                    title="Potential SQL Injection",
                                    description="SQL query built with string concatenation",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    code_snippet="query with string concat",
                                    cwe_id="CWE-89",
                                    cvss_score=9.8
                                )
                                vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def scan_project(self, project_path: str) -> SecurityReport:
        """Scan entire project for vulnerabilities"""
        
        vulnerabilities = []
        
        # File extensions to scan
        extensions = {'.py', '.js', '.ts', '.java', '.go', '.rb', '.php', '.cs'}
        
        for root, dirs, files in os.walk(project_path):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in [
                '__pycache__', 'node_modules', '.git', 'venv', 'dist', 'build'
            ]]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    vulns = self.scan_file(file_path)
                    vulnerabilities.extend(vulns)
        
        # Generate report
        return self._generate_report(project_path, vulnerabilities)
    
    def _generate_report(self, project_name: str, vulnerabilities: list[Vulnerability]) -> SecurityReport:
        """Generate security report"""
        
        report = SecurityReport(
            id=str(uuid.uuid4()),
            project_name=project_name,
            scan_date=datetime.now(),
            vulnerabilities=vulnerabilities
        )
        
        # Count by severity
        for vuln in vulnerabilities:
            if vuln.severity == VulnerabilitySeverity.CRITICAL:
                report.critical_count += 1
            elif vuln.severity == VulnerabilitySeverity.HIGH:
                report.high_count += 1
            elif vuln.severity == VulnerabilitySeverity.MEDIUM:
                report.medium_count += 1
            elif vuln.severity == VulnerabilitySeverity.LOW:
                report.low_count += 1
            else:
                report.info_count += 1
        
        # Calculate risk rating
        if report.critical_count > 0:
            report.risk_rating = "CRITICAL"
        elif report.high_count > 0:
            report.risk_rating = "HIGH"
        elif report.medium_count > 0:
            report.risk_rating = "MEDIUM"
        elif report.low_count > 0:
            report.risk_rating = "LOW"
        else:
            report.risk_rating = "MINIMAL"
        
        # Generate recommendations
        report.recommendations = self._generate_recommendations(vulnerabilities)
        
        return report
    
    def _generate_recommendations(self, vulnerabilities: list[Vulnerability]) -> list[str]:
        """Generate security recommendations"""
        
        recommendations = []
        
        types_found = set(v.type for v in vulnerabilities)
        
        if VulnerabilityType.SQL_INJECTION in types_found:
            recommendations.append("Use parameterized queries or ORM for all database operations")
        
        if VulnerabilityType.XSS in types_found:
            recommendations.append("Implement Content Security Policy and output encoding")
        
        if VulnerabilityType.RCE in types_found:
            recommendations.append("Avoid eval/exec, use sandboxing for untrusted code")
        
        if VulnerabilityType.HARDCODE_SECRETS in types_found:
            recommendations.append("Move secrets to environment variables or secrets manager")
        
        if VulnerabilityType.DESERIALIZATION in types_found:
            recommendations.append("Use safe serialization formats, validate all input")
        
        if VulnerabilityType.WEAK_CRYPTO in types_found:
            recommendations.append("Upgrade to modern cryptographic algorithms")
        
        return recommendations
    
    def save_report(self, report: SecurityReport, output_path: str = "security_report.md"):
        """Save report to file"""
        
        md = f"""# Security Audit Report
## Project: {report.project_name}
## Date: {report.scan_date.strftime('%Y-%m-%d %H:%M')}

---

## Executive Summary

| Severity | Count |
|----------|-------|
| Critical | {report.critical_count} |
| High | {report.high_count} |
| Medium | {report.medium_count} |
| Low | {report.low_count} |
| Info | {report.info_count} |

**Risk Rating:** {report.risk_rating}

---

## Vulnerabilities Found

"""
        
        # Group by severity
        severity_order = [
            VulnerabilitySeverity.CRITICAL,
            VulnerabilitySeverity.HIGH,
            VulnerabilitySeverity.MEDIUM,
            VulnerabilitySeverity.LOW,
            VulnerabilitySeverity.INFO
        ]
        
        for severity in severity_order:
            vulns = [v for v in report.vulnerabilities if v.severity == severity]
            if vulns:
                md += f"### {severity.value.upper()} Severity\n\n"
                
                for vuln in vulns:
                    md += f"""**{vuln.title}**

- **File:** `{vuln.file_path}:{vuln.line_number}`
- **CWE:** {vuln.cwe_id}
- **CVSS:** {vuln.cvss_score}
- **Description:** {vuln.description}
- **Code:** 
```
{vuln.code_snippet}
```
- **Remediation:** {vuln.remediation}

---
"""
        
        md += """
## Recommendations

"""
        for rec in report.recommendations:
            md += f"- {rec}\n"
        
        md += f"""
---

## Report Details

- **Report ID:** {report.id}
- **Generated by:** OmniClaw Security Research Suite
- **Scan Type:** Static Analysis + Pattern Matching

---
*This report is for authorized security testing only.*
"""
        
        with open(output_path, 'w') as f:
            f.write(md)
        
        return output_path


# =============================================================================
# CVE RESEARCH AGENT
# =============================================================================

class CVEResearchAgent:
    """
    Research and track CVEs.
    """
    
    def __init__(self, llm_provider=None):
        self.llm = llm_provider
        self.cve_cache: dict[str, CVEDetails] = {}
    
    async def research_cve(self, cve_id: str) -> CVEDetails:
        """Research a specific CVE"""
        
        # Would fetch from NVD API
        # This is a placeholder
        
        return CVEDetails(
            id=cve_id,
            description="CVE description from NVD",
            severity="HIGH",
            cvss_score=9.8,
            published_date="2024-01-01",
            affected_products=["Product A", "Product B"],
            references=[f"https://nvd.nist.gov/vuln/detail/{cve_id}"],
            exploitation="Proof of concept available",
            mitigation="Apply vendor patch"
        )
    
    async def search_vulnerabilities(self, keyword: str) -> list[dict]:
        """Search for vulnerabilities by keyword"""
        
        # Would search CVE database
        return [
            {
                "id": "CVE-2024-0001",
                "description": f"Vulnerability related to {keyword}",
                "severity": "HIGH",
                "cvss": 8.5
            }
        ]
    
    def get_latest_cves(self, limit: int = 10) -> list[dict]:
        """Get latest CVEs"""
        
        # Would fetch from NVD
        return [
            {
                "id": "CVE-2024-XXXX",
                "description": "Recent vulnerability",
                "severity": "CRITICAL",
                "cvss": 9.8
            }
        ][:limit]


# =============================================================================
# ATTACK SURFACE ANALYZER
# =============================================================================

class AttackSurfaceAnalyzer:
    """
    Analyze application attack surface.
    """
    
    def __init__(self):
        self.endpoints: list[dict] = []
        self.inputs: list[dict] = []
        self.auth_points: list[dict] = []
    
    def analyze_file(self, file_path: str) -> dict:
        """Analyze a file for attack surface"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except:
            return {}
        
        analysis = {
            "endpoints": [],
            "inputs": [],
            "auth_points": [],
            "file_upload": False,
            "external_calls": []
        }
        
        # Find endpoints
        endpoint_patterns = [
            r'@app\.(?:get|post|put|delete|patch)\([\'""]\/([^\'""/]+)',
            r'@router\.(?:get|post|put|delete|patch)\([\'""]\/([^\'""/]+)',
            r'app\.(?:get|post|put|delete|patch)\([\'""]\/([^\'""/]+)',
            r'def\s+(?:handle_|process_|do_)?(\w+)\s*\(',
        ]
        
        for pattern in endpoint_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                analysis["endpoints"].append(match.group(1))
        
        # Find inputs
        input_patterns = [
            r'request\.(?:args|form|json|values)\[[\'""](\w+)[\'""]\]',
            r'Request\.(?:Query|Form|Body)\([\'""](\w+)[\'""]',
            r'@RequestParam\([\'""](\w+)[\'""]\)',
        ]
        
        for pattern in input_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                analysis["inputs"].append(match.group(1))
        
        # Find authentication
        auth_patterns = [
            r'@require',
            r'.*auth@login_required',
            r'is_authenticated',
            r'check_password',
            r'verify_token',
            r'jwt\.decode',
        ]
        
        for pattern in auth_patterns:
            if re.search(pattern, content):
                analysis["auth_points"].append(pattern)
        
        # Find file uploads
        if re.search(r'(?:file|multipart)', content, re.IGNORECASE):
            analysis["file_upload"] = True
        
        # Find external calls
        external_patterns = [
            r'requests\.(?:get|post)',
            r'fetch\(',
            r'axios\.',
            r'http\.',
        ]
        
        for pattern in external_patterns:
            if re.search(pattern, content):
                analysis["external_calls"].append(pattern)
        
        return analysis
    
    def analyze_project(self, project_path: str) -> dict:
        """Analyze entire project attack surface"""
        
        total_analysis = {
            "total_endpoints": 0,
            "total_inputs": 0,
            "auth_coverage": 0,
            "high_risk_features": [],
            "recommendations": []
        }
        
        extensions = {'.py', '.js', '.ts', '.java'}
        
        for root, dirs, files in os.walk(project_path):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', 'node_modules', '.git']]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    analysis = self.analyze_file(file_path)
                    
                    total_analysis["total_endpoints"] += len(analysis.get("endpoints", []))
                    total_analysis["total_inputs"] += len(analysis.get("inputs", []))
        
        # Generate recommendations
        if total_analysis["total_endpoints"] > 0:
            if total_analysis["total_inputs"] / total_analysis["total_endpoints"] < 2:
                total_analysis["recommendations"].append(
                    "Low input validation coverage - review all endpoints"
                )
        
        return total_analysis


# =============================================================================
# SECURITY RESEARCH HUB - MAIN CLASS
# =============================================================================

class SecurityResearchHub:
    """
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║              🛡️ OMNICLAW SECURITY RESEARCH HUB 🛡️                     ║
    ╠══════════════════════════════════════════════════════════════════════════╣
    ║                                                                          ║
    ║  Advanced Security Research & Bug Hunting Suite                         ║
    ║                                                                          ║
    ║  Capabilities:                                                          ║
    ║  ✓ Vulnerability Scanning & Detection                                    ║
    ║  ✓ CVE Research & Tracking                                               ║
    ║  ✓ Security Auditing                                                     ║
    ║  ✓ Attack Surface Analysis                                              ║
    ║  ✓ Penetration Test Planning (Authorized)                              ║
    ║  ✓ Responsible Disclosure Reports                                       ║
    ║  ✓ Code Review Assistance                                                ║
    ║  ✓ Security Best Practices Validation                                    ║
    ║                                                                          ║
    ║  For authorized security research and bug bounty only.                  ║
    ║  Use responsibly and ethically.                                          ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """
    
    def __init__(self, llm_provider=None):
        self.llm = llm_provider
        
        # Initialize modules
        self.scanner = VulnerabilityScanner()
        self.cve_agent = CVEResearchAgent(llm_provider)
        self.surface_analyzer = AttackSurfaceAnalyzer()
    
    # =========================================================================
    # MAIN SCANNING FUNCTIONS
    # =========================================================================
    
    async def scan_for_vulnerabilities(
        self,
        project_path: str,
        scan_type: str = "full"
    ) -> SecurityReport:
        """
        Scan project for vulnerabilities.
        
        Args:
            project_path: Path to project
            scan_type: full, quick, extended
        
        Returns:
            SecurityReport with all findings
        """
        
        print(f"🔍 Starting {scan_type} vulnerability scan...")
        
        # Run vulnerability scan
        report = self.scanner.scan_project(project_path)
        
        print(f"✅ Scan complete!")
        print(f"   Critical: {report.critical_count}")
        print(f"   High: {report.high_count}")
        print(f"   Medium: {report.medium_count}")
        print(f"   Low: {report.low_count}")
        
        return report
    
    async def scan_file(self, file_path: str) -> list[Vulnerability]:
        """Scan a single file for vulnerabilities"""
        
        return self.scanner.scan_file(file_path)
    
    async def analyze_attack_surface(self, project_path: str) -> dict:
        """Analyze project attack surface"""
        
        return self.surface_analyzer.analyze_project(project_path)
    
    async def research_cve(self, cve_id: str) -> CVEDetails:
        """Research a specific CVE"""
        
        return await self.cve_agent.research_cve(cve_id)
    
    async def search_vulnerabilities(self, keyword: str) -> list[dict]:
        """Search for vulnerabilities"""
        
        return await self.cve_agent.search_vulnerabilities(keyword)
    
    # =========================================================================
    # REPORTING
    # =========================================================================
    
    def generate_report(self, report: SecurityReport, output_path: str = "security_report.md") -> str:
        """Generate security report"""
        
        return self.scanner.save_report(report, output_path)
    
    def generate_responsible_disclosure(
        self,
        vulnerability: Vulnerability,
        project_name: str
    ) -> str:
        """Generate responsible disclosure report"""
        
        report = f"""# Responsible Disclosure Report

## Vulnerability Details

**Type:** {vulnerability.type.value}
**Severity:** {vulnerability.severity.value.upper()}
**CVSS Score:** {vulnerability.cvss_score}
**CWE ID:** {vulnerability.cwe_id}

## Location

**File:** {vulnerability.file_path}
**Line:** {vulnerability.line_number}

```code
{vulnerability.code_snippet}
```

## Description

{vulnerability.description}

## Impact

{vulnerability.impact or "Potential security impact on the application."}

## Remediation

{vulnerability.remediation}

## Timeline

- **Discovered:** {datetime.now().strftime('%Y-%m-%d')}
- **Reported:** [Date]
- **Acknowledged:** [Date]
- **Fixed:** [Date]

## Credits

Reported by OmniClaw Security Research

---
*For authorized security testing only.*
"""
        
        return report
    
    # =========================================================================
    # PENETRATION TEST ASSISTANCE (AUTHORIZED)
    # =========================================================================
    
    async def plan_penetration_test(
        self,
        target: str,
        scope: list[str]
    ) -> dict:
        """
        Plan a penetration test (for authorized testing only).
        
        Args:
            target: Target application/system
            scope: In-scope targets
        
        Returns:
            Penetration test plan
        """
        
        return {
            "target": target,
            "scope": scope,
            "phases": [
                {
                    "name": "Reconnaissance",
                    "tasks": [
                        "Passive reconnaissance",
                        "OSINT gathering",
                        "Technology fingerprinting"
                    ]
                },
                {
                    "name": "Scanning",
                    "tasks": [
                        "Port scanning",
                        "Service enumeration",
                        "Vulnerability scanning"
                    ]
                },
                {
                    "name": "Enumeration",
                    "tasks": [
                        "Directory enumeration",
                        "Parameter discovery",
                        "User enumeration"
                    ]
                },
                {
                    "name": "Exploitation",
                    "tasks": [
                        "Attempt exploits",
                        "Privilege escalation",
                        "Persistence establishment"
                    ]
                },
                {
                    "name": "Reporting",
                    "tasks": [
                        "Document findings",
                        "Risk rating",
                        "Recommendations"
                    ]
                }
            ],
            "rules_of_engagement": [
                "Only test in-scope targets",
                "Do not exceed authorized access",
                "Document all findings",
                "Report immediately if critical vulnerability found"
            ]
        }
    
    async def suggest_attack_vectors(
        self,
        target_type: str
    ) -> list[dict]:
        """
        Suggest common attack vectors for testing.
        (For authorized testing only)
        """
        
        vectors = {
            "web_application": [
                {"vector": "SQL Injection", "testing": "Try ' OR '1'='1 in all inputs"},
                {"vector": "XSS", "testing": "Try <script>alert(1)</script> in inputs"},
                {"vector": "IDOR", "testing": "Change IDs in requests to access other users"},
                {"vector": "CSRF", "testing": "Check if anti-CSRF tokens are missing"},
                {"vector": "SSRF", "testing": "Try internal URLs (localhost, 169.254.169.254)"},
            ],
            "api": [
                {"vector": "Broken Authentication", "testing": "Test JWT alg confusion, weak secrets"},
                {"vector": "Mass Assignment", "testing": "Add unexpected parameters"},
                {"vector": "Rate Limiting", "testing": "Check for missing rate limits"},
            ],
            "mobile": [
                {"vector": "Insecure Storage", "testing": "Check local storage for sensitive data"},
                {"vector": "Insecure Communication", "testing": "Check for TLS/SSL pinning"},
            ]
        }
        
        return vectors.get(target_type, [])


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    
    print("""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║              🛡️ OMNICLAW SECURITY RESEARCH SUITE 🛡️                     ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    
    Usage:
    
    from omniclaw_advanced_features import SecurityResearchHub
    
    # Initialize
    security = SecurityResearchHub()
    
    # 1. SCAN FOR VULNERABILITIES
    report = await security.scan_for_vulnerabilities("/path/to/project")
    
    # 2. GENERATE REPORT
    security.generate_report(report, "security_report.md")
    
    # 3. ANALYZE ATTACK SURFACE
    surface = await security.analyze_attack_surface("/path/to/project")
    
    # 4. RESEARCH CVE
    cve = await security.research_cve("CVE-2024-0001")
    
    # 5. PLAN PENETRATION TEST (Authorized)
    plan = await security.plan_penetration_test("target.com", ["api.target.com"])
    
    # 6. SUGGEST ATTACK VECTORS (Authorized)
    vectors = await security.suggest_attack_vectors("web_application")
    
    # 7. RESPONSIBLE DISCLOSURE
    disclosure = security.generate_responsible_disclosure(vuln, "MyProject")
    
    """)
    
    # Quick demo
    import asyncio
    
    async def demo():
        security = SecurityResearchHub()
        
        # Demo scan (won't find real vulns in empty dir)
        print("\n🔍 Running demo scan...")
        
        # Create test file
        test_code = '''
import sqlite3
import pickle

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return sqlite3.execute(query)

def execute_command(cmd):
    eval(cmd)
'''
        
        os.makedirs("/tmp/test_vuln", exist_ok=True)
        with open("/tmp/test_vuln/vuln_demo.py", 'w') as f:
            f.write(test_code)
        
        # Scan
        vulns = await security.scan_file("/tmp/test_vuln/vuln_demo.py")
        
        print(f"\n✅ Found {len(vulns)} vulnerabilities:")
        
        for v in vulns:
            print(f"\n[{v.severity.value.upper()}] {v.title}")
            print(f"  File: {v.file_path}:{v.line_number}")
            print(f"  CWE: {v.cwe_id}")
            print(f"  CVSS: {v.cvss_score}")
    
    asyncio.run(demo())
