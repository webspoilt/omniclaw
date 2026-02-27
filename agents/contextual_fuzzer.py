import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import logging
from typing import Set, Dict, List, Optional

logger = logging.getLogger(__name__)

class ContextualFuzzer:
    def __init__(self, target_url: str, user_a_token: str, user_b_token: str, 
                 kill_switch: asyncio.Event, max_concurrent=10):
        self.target_url = target_url.rstrip('/')
        self.user_a_token = user_a_token
        self.user_b_token = user_b_token
        self.kill_switch = kill_switch
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.endpoints: Set[str] = set()
        self.idor_candidates: List[Dict] = []

    async def discover_endpoints(self, session: aiohttp.ClientSession):
        """Crawl the target to find all links and forms."""
        if self.kill_switch.is_set():
            return
        try:
            async with session.get(self.target_url) as resp:
                html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')
            # Extract all href links
            for a in soup.find_all('a', href=True):
                href = a['href']
                full_url = urljoin(self.target_url, href)
                if full_url.startswith(self.target_url):
                    self.endpoints.add(full_url)
            # Extract forms
            for form in soup.find_all('form'):
                action = form.get('action', '')
                full_url = urljoin(self.target_url, action)
                self.endpoints.add(full_url)
                # Record parameters
                method = form.get('method', 'get').lower()
                inputs = form.find_all('input')
                params = {inp.get('name'): inp.get('value', '') 
                          for inp in inputs if inp.get('name')}
                self.endpoints.add((full_url, method, params))  # store tuple for later
            logger.info(f"Discovered {len(self.endpoints)} endpoints")
        except Exception as e:
            logger.error(f"Discovery error: {e}")

    async def test_idor(self, session: aiohttp.ClientSession, endpoint: str, 
                        params: Dict, method: str = 'get'):
        """Attempt to access endpoint with swapped tokens."""
        if self.kill_switch.is_set():
            return
        async with self.semaphore:
            # Request with User A token
            headers_a = {'Authorization': f'Bearer {self.user_a_token}'}
            func = session.get if method == 'get' else session.post
            try:
                async with func(endpoint, headers=headers_a, params=params) as resp_a:
                    if resp_a.status != 200:
                        return
                    text_a = await resp_a.text()
            except Exception as e:
                logger.debug(f"Request failed: {e}")
                return

            # Request with User B token (IDOR test)
            headers_b = {'Authorization': f'Bearer {self.user_b_token}'}
            try:
                async with func(endpoint, headers=headers_b, params=params) as resp_b:
                    if resp_b.status == 200:
                        text_b = await resp_b.text()
                        # If both succeed and are similar, possible IDOR
                        if text_a == text_b:  # naive check, could use hash comparison
                            self.idor_candidates.append({
                                'endpoint': endpoint,
                                'method': method,
                                'params': params,
                                'evidence': 'Both users accessed same resource'
                            })
                            logger.warning(f"Potential IDOR at {endpoint}")
            except Exception as e:
                logger.debug(f"IDOR test error: {e}")

    async def run(self):
        """Main entry point."""
        async with aiohttp.ClientSession() as session:
            await self.discover_endpoints(session)
            # For each endpoint that had parameters, test IDOR
            tasks = []
            for item in self.endpoints:
                if isinstance(item, tuple):
                    url, method, params = item
                    tasks.append(self.test_idor(session, url, params, method))
                # Also test discovered simple links? Could be resource IDs in path.
                # For simplicity, we skip; a real implementation would parse path parameters.
            await asyncio.gather(*tasks)
        return self.idor_candidates
