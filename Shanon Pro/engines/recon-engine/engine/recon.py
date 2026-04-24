import asyncio
import logging
import time
import socket
import aiohttp
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger("ReconEngine")

@dataclass
class ReconFinding:
    type: str
    target: str
    description: str
    severity: str = "info"
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

class ReconEngine:
    """
    Recon Engine — Outside-in security discovery.
    Based on OmniClaw's BugBountyHunter.
    """
    
    def __init__(self):
        self.findings: List[ReconFinding] = []
        self.subdomains: Set[str] = set()
        self.endpoints: Set[str] = set()
        
    async def run_discovery(self, domain: str) -> Dict[str, Any]:
        """Run full discovery on a domain."""
        logger.info(f"Starting discovery for {domain}")
        
        # 1. Subdomain Enumeration
        await self._enumerate_subdomains(domain)
        
        # 2. Port Scanning & Service Discovery
        await self._scan_services()
        
        # 3. Web & API Discovery
        await self._discover_endpoints()
        
        return {
            "subdomains": list(self.subdomains),
            "endpoints": list(self.endpoints),
            "findings": [f.__dict__ for f in self.findings]
        }

    async def _enumerate_subdomains(self, domain: str):
        """Enumerate subdomains using DNS and CT logs."""
        # Certificate Transparency logs
        try:
            url = f"https://crt.sh/?q=%.{domain}&output=json"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for entry in data:
                            name = entry.get('name_value', '')
                            if name and '*' not in name:
                                for sub in name.split('\n'):
                                    self.subdomains.add(sub.strip())
        except Exception as e:
            logger.error(f"CT log query failed: {e}")

        # Basic DNS Brute Force
        common = ['www', 'api', 'dev', 'staging', 'test', 'admin', 'git', 'app']
        for prefix in common:
            sub = f"{prefix}.{domain}"
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, socket.gethostbyname, sub)
                self.subdomains.add(sub)
            except:
                pass

    async def _scan_services(self):
        """Scan discovered subdomains for open ports."""
        ports = [80, 443, 8080, 8443, 3000, 5000, 8000]
        for sub in list(self.subdomains)[:10]:
            for port in ports:
                try:
                    conn = asyncio.open_connection(sub, port)
                    _, writer = await asyncio.wait_for(conn, timeout=1.0)
                    writer.close()
                    await writer.wait_closed()
                    
                    self.findings.append(ReconFinding(
                        type="open_port",
                        target=f"{sub}:{port}",
                        description=f"Open port {port} found on {sub}",
                        metadata={"subdomain": sub, "port": port}
                    ))
                except:
                    pass

    async def _discover_endpoints(self):
        """Crawl subdomains for web and API endpoints."""
        for sub in list(self.subdomains)[:5]:
            url = f"https://{sub}"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=5) as resp:
                        if resp.status == 200:
                            html = await resp.text()
                            soup = BeautifulSoup(html, 'html.parser')
                            for link in soup.find_all('a', href=True):
                                href = link['href']
                                if href.startswith('/'):
                                    full_url = urljoin(url, href)
                                    self.endpoints.add(full_url)
                                elif urlparse(href).netloc == sub:
                                    self.endpoints.add(href)
            except:
                pass

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        engine = ReconEngine()
        results = asyncio.run(engine.run_discovery(sys.argv[1]))
        import json
        print(json.dumps(results, indent=2))
