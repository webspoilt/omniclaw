import concurrent.futures
import requests
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class IDORFuzzer:
    """
    Multi‑threaded fuzzer for IDOR vulnerabilities.
    Compares responses from privileged and unprivileged tokens.
    """

    def __init__(self, base_url: str, privileged_headers: Dict, unprivileged_headers: Dict,
                 endpoints: List[str], num_threads: int = 5):
        self.base_url = base_url.rstrip('/')
        self.privileged_headers = privileged_headers
        self.unprivileged_headers = unprivileged_headers
        self.endpoints = endpoints  # list of paths like "/api/user/{}"
        self.num_threads = num_threads
        self.session = requests.Session()

    def _fetch(self, url: str, headers: Dict) -> Tuple[int, str, Dict]:
        """Perform GET request and return status, text, headers."""
        try:
            resp = self.session.get(url, headers=headers, timeout=5)
            return resp.status_code, resp.text, dict(resp.headers)
        except Exception as e:
            return 0, str(e), {}

    def _test_single_endpoint(self, endpoint: str) -> Dict:
        """Test an endpoint (may contain {} for object ID substitution)."""
        # Example: endpoint = "/api/user/{}", we test a range of IDs
        results = []
        for obj_id in range(1, 10):  # configurable range
            url = f"{self.base_url}{endpoint.format(obj_id)}"
            logger.debug(f"Testing {url}")

            # Fetch with privileged and unprivileged tokens
            status_priv, body_priv, headers_priv = self._fetch(url, self.privileged_headers)
            status_unpriv, body_unpriv, headers_unpriv = self._fetch(url, self.unprivileged_headers)

            # Compare: success with unprivileged but not with privileged? Actually IDOR is when unprivileged can access privileged data.
            # We consider a potential issue if unprivileged gets a 200 OK and the response contains sensitive data (or differs significantly).
            # Simplified heuristic: unprivileged 200 vs privileged 200, but content may differ.
            # Here we flag if unpriv 200 and priv 200 but content lengths differ significantly (indicating different data).
            # In real tests, you'd need more sophisticated analysis (e.g., JSON comparison).
            if status_unpriv == 200 and status_priv == 200:
                # Compare content length as a simple metric
                len_diff = abs(len(body_priv) - len(body_unpriv))
                if len_diff > 100:  # arbitrary threshold
                    results.append({
                        "url": url,
                        "object_id": obj_id,
                        "status_priv": status_priv,
                        "status_unpriv": status_unpriv,
                        "content_length_priv": len(body_priv),
                        "content_length_unpriv": len(body_unpriv),
                        "potential_idor": True
                    })
            elif status_unpriv == 200 and status_priv != 200:
                # Unpriv can access something that priv cannot? Unlikely, but maybe priv token expired.
                results.append({
                    "url": url,
                    "object_id": obj_id,
                    "status_priv": status_priv,
                    "status_unpriv": status_unpriv,
                    "potential_idor": True
                })
        return {"endpoint": endpoint, "results": results}

    def run(self) -> List[Dict]:
        """Run tests on all endpoints using thread pool."""
        all_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            future_to_endpoint = {executor.submit(self._test_single_endpoint, ep): ep for ep in self.endpoints}
            for future in concurrent.futures.as_completed(future_to_endpoint):
                ep = future_to_endpoint[future]
                try:
                    result = future.result()
                    all_results.append(result)
                    if result["results"]:
                        logger.warning(f"Potential IDOR in {ep}: {result['results']}")
                except Exception as e:
                    logger.error(f"Error testing {ep}: {e}")
        return all_results
