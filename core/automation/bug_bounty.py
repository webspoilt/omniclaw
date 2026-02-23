#!/usr/bin/env python3
"""
OmniClaw Bug Bounty Hunter
Automated security research and vulnerability detection
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import time
import json
import re
from urllib.parse import urljoin, urlparse

logger = logging.getLogger("OmniClaw.BugBounty")


class VulnerabilitySeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Vulnerability:
    """Represents a discovered vulnerability"""
    name: str
    severity: VulnerabilitySeverity
    target: str
    description: str
    evidence: str
    remediation: str
    cwe_id: Optional[str] = None
    cvss_score: Optional[float] = None
    discovered_at: float = field(default_factory=time.time)
    verified: bool = False
    reported: bool = False


@dataclass
class Target:
    """Represents a bug bounty target"""
    domain: str
    scope: List[str]
    out_of_scope: List[str]
    program_name: str
    platform: str  # HackerOne, Bugcrowd, etc.
    max_bounty: Optional[int] = None
    notes: str = ""


class BugBountyHunter:
    """
    Automated bug bounty hunting system
    Performs reconnaissance, scanning, and vulnerability detection
    """
    
    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.targets: List[Target] = []
        self.vulnerabilities: List[Vulnerability] = []
        self.discovered_subdomains: Set[str] = set()
        self.discovered_endpoints: Set[str] = set()
        self.running = False
        self.scan_tasks = []
        
        # Scan modules
        self.scanners = {
            'recon': self._recon_scan,
            'port': self._port_scan,
            'web': self._web_scan,
            'api': self._api_scan,
            'secrets': self._secrets_scan,
        }
        
        logger.info("Bug Bounty Hunter initialized")
    
    def add_target(self, target: Target):
        """Add a bug bounty target"""
        self.targets.append(target)
        logger.info(f"Added target: {target.domain}")
    
    async def start_monitoring(self):
        """Start continuous monitoring of targets"""
        self.running = True
        
        for target in self.targets:
            task = asyncio.create_task(self._monitor_target(target))
            self.scan_tasks.append(task)
        
        logger.info("Bug bounty monitoring started")
    
    async def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        
        for task in self.scan_tasks:
            task.cancel()
        
        logger.info("Bug bounty monitoring stopped")
    
    async def _monitor_target(self, target: Target):
        """Monitor a single target continuously"""
        while self.running:
            try:
                # Run all scan types
                for scan_type, scanner in self.scanners.items():
                    logger.info(f"Running {scan_type} scan on {target.domain}")
                    await scanner(target)
                
                # Wait before next scan cycle
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Monitoring error for {target.domain}: {e}")
                await asyncio.sleep(300)
    
    async def _recon_scan(self, target: Target):
        """Reconnaissance - subdomain enumeration"""
        try:
            # Use subfinder, amass, or similar
            subdomains = await self._enumerate_subdomains(target.domain)
            
            for subdomain in subdomains:
                if subdomain not in self.discovered_subdomains:
                    self.discovered_subdomains.add(subdomain)
                    logger.info(f"New subdomain discovered: {subdomain}")
                    
                    # Check if subdomain is in scope
                    if self._is_in_scope(subdomain, target):
                        # Trigger deeper scan
                        asyncio.create_task(self._deep_scan(subdomain, target))
                        
        except Exception as e:
            logger.error(f"Recon scan error: {e}")
    
    async def _enumerate_subdomains(self, domain: str) -> Set[str]:
        """Enumerate subdomains using multiple techniques"""
        subdomains = set()
        
        # DNS brute force
        common_prefixes = [
            'www', 'mail', 'ftp', 'admin', 'api', 'app', 'blog',
            'dev', 'staging', 'test', 'demo', 'portal', 'secure',
            'vpn', 'remote', 'webmail', 'support', 'help',
            'cdn', 'static', 'assets', 'media', 'img', 'images',
            'js', 'css', 'docs', 'wiki', 'git', 'jenkins',
            'grafana', 'prometheus', 'kibana', 'elastic',
        ]
        
        for prefix in common_prefixes:
            subdomain = f"{prefix}.{domain}"
            if await self._dns_resolve(subdomain):
                subdomains.add(subdomain)
        
        # Certificate transparency logs
        ct_subdomains = await self._query_ct_logs(domain)
        subdomains.update(ct_subdomains)
        
        return subdomains
    
    async def _dns_resolve(self, hostname: str) -> bool:
        """Check if hostname resolves"""
        try:
            import socket
            socket.gethostbyname(hostname)
            return True
        except:
            return False
    
    async def _query_ct_logs(self, domain: str) -> Set[str]:
        """Query certificate transparency logs"""
        subdomains = set()
        
        try:
            import aiohttp
            
            # Use crt.sh
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for entry in data:
                            name = entry.get('name_value', '')
                            if name and '*' not in name:
                                subdomains.add(name)
                                
        except Exception as e:
            logger.error(f"CT log query error: {e}")
        
        return subdomains
    
    async def _port_scan(self, target: Target):
        """Port scanning for exposed services"""
        # Common web ports
        ports = [80, 443, 8080, 8443, 3000, 5000, 8000, 9000]
        
        for subdomain in list(self.discovered_subdomains)[:10]:  # Limit to first 10
            for port in ports:
                try:
                    import aiohttp
                    
                    protocol = 'https' if port in [443, 8443] else 'http'
                    url = f"{protocol}://{subdomain}:{port}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=5) as resp:
                            if resp.status < 500:
                                logger.info(f"Open port found: {url}")
                                
                                # Check for common misconfigurations
                                await self._check_misconfigurations(url)
                                
                except Exception:
                    pass
    
    async def _web_scan(self, target: Target):
        """Web application security scanning"""
        for subdomain in list(self.discovered_subdomains)[:5]:
            url = f"https://{subdomain}"
            
            try:
                # Check for common vulnerabilities
                await self._check_xss(url)
                await self._check_sqli(url)
                await self._check_ssrf(url)
                await self._check_idor(url)
                await self._check_cors(url)
                await self._check_security_headers(url)
                
            except Exception as e:
                logger.error(f"Web scan error: {e}")
    
    async def _check_xss(self, url: str):
        """Check for XSS vulnerabilities"""
        payloads = [
            '<script>alert(1)</script>',
            '"><script>alert(1)</script>',
            "'><script>alert(1)</script>",
        ]
        
        # Test query parameters
        test_url = f"{url}?q={payloads[0]}"
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(test_url) as resp:
                    text = await resp.text()
                    
                    if payloads[0] in text:
                        vuln = Vulnerability(
                            name="Reflected XSS",
                            severity=VulnerabilitySeverity.HIGH,
                            target=url,
                            description="Reflected XSS vulnerability found in query parameter",
                            evidence=f"Payload reflected: {payloads[0]}",
                            remediation="Implement proper input sanitization and output encoding",
                            cwe_id="CWE-79"
                        )
                        self.vulnerabilities.append(vuln)
                        logger.warning(f"XSS vulnerability found: {url}")
                        
        except Exception as e:
            logger.debug(f"XSS check error: {e}")
    
    async def _check_sqli(self, url: str):
        """Check for SQL Injection vulnerabilities"""
        error_patterns = [
            'sql syntax',
            'mysql_fetch',
            'pg_query',
            'sqlite_query',
            'ORA-',
            'SQL Server',
        ]
        
        payloads = ["'", "''", "' OR '1'='1", "'; DROP TABLE users; --"]
        
        for payload in payloads:
            test_url = f"{url}?id={payload}"
            
            try:
                import aiohttp
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(test_url) as resp:
                        text = await resp.text().lower()
                        
                        for pattern in error_patterns:
                            if pattern.lower() in text:
                                vuln = Vulnerability(
                                    name="SQL Injection",
                                    severity=VulnerabilitySeverity.CRITICAL,
                                    target=url,
                                    description="SQL Injection vulnerability detected",
                                    evidence=f"Error message: {pattern}",
                                    remediation="Use parameterized queries and prepared statements",
                                    cwe_id="CWE-89"
                                )
                                self.vulnerabilities.append(vuln)
                                logger.warning(f"SQLi vulnerability found: {url}")
                                return
                                
            except Exception as e:
                logger.debug(f"SQLi check error: {e}")
    
    async def _check_ssrf(self, url: str):
        """Check for Server-Side Request Forgery"""
        # Placeholder for SSRF detection
        pass
    
    async def _check_idor(self, url: str):
        """Check for Insecure Direct Object Reference"""
        # Placeholder for IDOR detection
        pass
    
    async def _check_cors(self, url: str):
        """Check for CORS misconfigurations"""
        try:
            import aiohttp
            
            headers = {'Origin': 'https://evil.com'}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as resp:
                    acao = resp.headers.get('Access-Control-Allow-Origin')
                    acac = resp.headers.get('Access-Control-Allow-Credentials')
                    
                    if acao == '*' and acac == 'true':
                        vuln = Vulnerability(
                            name="CORS Misconfiguration",
                            severity=VulnerabilitySeverity.MEDIUM,
                            target=url,
                            description="Dangerous CORS configuration allowing any origin with credentials",
                            evidence="Access-Control-Allow-Origin: * with credentials",
                            remediation="Restrict Access-Control-Allow-Origin to specific domains",
                            cwe_id="CWE-942"
                        )
                        self.vulnerabilities.append(vuln)
                        
        except Exception as e:
            logger.debug(f"CORS check error: {e}")
    
    async def _check_security_headers(self, url: str):
        """Check for missing security headers"""
        important_headers = [
            'Strict-Transport-Security',
            'Content-Security-Policy',
            'X-Frame-Options',
            'X-Content-Type-Options',
            'Referrer-Policy',
            'Permissions-Policy',
        ]
        
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    missing = []
                    
                    for header in important_headers:
                        if header not in resp.headers:
                            missing.append(header)
                    
                    if len(missing) >= 3:
                        vuln = Vulnerability(
                            name="Missing Security Headers",
                            severity=VulnerabilitySeverity.LOW,
                            target=url,
                            description=f"Multiple security headers missing: {', '.join(missing)}",
                            evidence=f"Missing: {', '.join(missing)}",
                            remediation="Implement recommended security headers",
                            cwe_id="CWE-693"
                        )
                        self.vulnerabilities.append(vuln)
                        
        except Exception as e:
            logger.debug(f"Security headers check error: {e}")
    
    async def _api_scan(self, target: Target):
        """API security scanning"""
        # Look for API endpoints
        common_api_paths = [
            '/api', '/api/v1', '/api/v2', '/rest', '/graphql',
            '/swagger.json', '/api-docs', '/openapi.json',
        ]
        
        for subdomain in list(self.discovered_subdomains)[:5]:
            for path in common_api_paths:
                url = f"https://{subdomain}{path}"
                
                try:
                    import aiohttp
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=5) as resp:
                            if resp.status == 200:
                                logger.info(f"API endpoint found: {url}")
                                
                                # Check for API documentation exposure
                                if 'swagger' in path or 'api-docs' in path:
                                    vuln = Vulnerability(
                                        name="Exposed API Documentation",
                                        severity=VulnerabilitySeverity.MEDIUM,
                                        target=url,
                                        description="API documentation is publicly accessible",
                                        evidence=f"Documentation found at {url}",
                                        remediation="Restrict access to API documentation"
                                    )
                                    self.vulnerabilities.append(vuln)
                                    
                except Exception:
                    pass
    
    async def _secrets_scan(self, target: Target):
        """Scan for exposed secrets"""
        # GitHub/GitLab scanning
        await self._scan_repos(target.domain)
    
    async def _scan_repos(self, domain: str):
        """Scan public repositories for secrets"""
        # Use GitHub API to search for code
        patterns = [
            (r'[a-zA-Z0-9]{40}', 'Possible API key'),
            (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API key'),
            (r'AKIA[0-9A-Z]{16}', 'AWS Access Key'),
            (r'ghp_[a-zA-Z0-9]{36}', 'GitHub Personal Token'),
        ]
        
        # Placeholder for repo scanning
        pass
    
    async def _deep_scan(self, subdomain: str, target: Target):
        """Perform deep scan on discovered subdomain"""
        logger.info(f"Starting deep scan of {subdomain}")
        
        # Crawl for endpoints
        endpoints = await self._crawl_endpoints(subdomain)
        
        # Test each endpoint
        for endpoint in endpoints:
            await self._test_endpoint(endpoint, target)
    
    async def _crawl_endpoints(self, subdomain: str) -> Set[str]:
        """Crawl website for endpoints"""
        endpoints = set()
        
        try:
            import aiohttp
            from bs4 import BeautifulSoup
            
            url = f"https://{subdomain}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    html = await resp.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract links
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('/'):
                            endpoints.add(urljoin(url, href))
                            
        except Exception as e:
            logger.debug(f"Crawl error: {e}")
        
        return endpoints
    
    async def _test_endpoint(self, endpoint: str, target: Target):
        """Test a specific endpoint for vulnerabilities"""
        # Placeholder for endpoint testing
        pass
    
    async def _check_misconfigurations(self, url: str):
        """Check for common misconfigurations"""
        # Check for directory listing
        # Check for default credentials
        # Check for exposed admin panels
        pass
    
    def _is_in_scope(self, subdomain: str, target: Target) -> bool:
        """Check if subdomain is in scope"""
        # Check out of scope first
        for oos in target.out_of_scope:
            if oos in subdomain:
                return False
        
        # Check in scope
        if not target.scope:
            return True
        
        for scope in target.scope:
            if scope in subdomain:
                return True
        
        return False
    
    def get_vulnerabilities(self, severity: VulnerabilitySeverity = None) -> List[Vulnerability]:
        """Get discovered vulnerabilities"""
        if severity:
            return [v for v in self.vulnerabilities if v.severity == severity]
        return self.vulnerabilities
    
    def generate_report(self, target: Target = None) -> Dict[str, Any]:
        """Generate vulnerability report"""
        vulns = self.vulnerabilities
        if target:
            vulns = [v for v in vulns if v.target.endswith(target.domain)]
        
        by_severity = {
            'critical': len([v for v in vulns if v.severity == VulnerabilitySeverity.CRITICAL]),
            'high': len([v for v in vulns if v.severity == VulnerabilitySeverity.HIGH]),
            'medium': len([v for v in vulns if v.severity == VulnerabilitySeverity.MEDIUM]),
            'low': len([v for v in vulns if v.severity == VulnerabilitySeverity.LOW]),
            'info': len([v for v in vulns if v.severity == VulnerabilitySeverity.INFO]),
        }
        
        return {
            'summary': {
                'total': len(vulns),
                'by_severity': by_severity,
                'targets_scanned': len(self.targets),
                'subdomains_discovered': len(self.discovered_subdomains),
            },
            'vulnerabilities': [
                {
                    'name': v.name,
                    'severity': v.severity.value,
                    'target': v.target,
                    'description': v.description,
                    'evidence': v.evidence,
                    'remediation': v.remediation,
                    'cwe_id': v.cwe_id,
                    'discovered_at': v.discovered_at,
                }
                for v in vulns
            ]
        }
