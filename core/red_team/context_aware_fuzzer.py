import requests
import json
import concurrent.futures
from typing import List, Dict, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IDORFuzzer:
    """
    Compares responses between two user sessions to find IDOR vulnerabilities.
    """

    def __init__(self, base_url: str, session_a_headers: Dict, session_b_headers: Dict,
                 endpoints: List[str], num_threads: int = 5):
        self.base_url = base_url.rstrip('/')
        self.session_a_headers = session_a_headers
        self.session_b_headers = session_b_headers
        self.endpoints = endpoints  # e.g., ["/api/user/{}", "/api/order/{}"]
        self.num_threads = num_threads
        self.session = requests.Session()

    @staticmethod
    def discover_endpoints(openapi_spec: str = None, crawl_url: str = None) -> List[str]:
        """
        Stub: In production, parse OpenAPI or crawl to generate endpoint list.
        """
        # Example: return ["/api/users/{}", "/api/posts/{}"]
        return []

    def _fetch(self, url: str, headers: Dict) -> Tuple[int, str, Dict]:
        try:
            resp = self.session.get(url, headers=headers, timeout=5)
            return resp.status_code, resp.text, dict(resp.headers)
        except Exception as e:
            return 0, str(e), {}

    def _compare_responses(self, url_a: str, url_b: str) -> Dict:
        """Fetch and compare responses from both sessions."""
        status_a, body_a, headers_a = self._fetch(url_a, self.session_a_headers)
        status_b, body_b, headers_b = self._fetch(url_b, self.session_b_headers)

        # Heuristic: treat as potential IDOR if:
        # - Both return 200 OK
        # - Both return 403/401 (but one returns 200?) – need careful analysis
        # - Content lengths differ significantly (indicating different data)
        result = {
            "url": url_a,
            "status_a": status_a,
            "status_b": status_b,
            "len_a": len(body_a),
            "len_b": len(body_b),
            "potential": False,
            "reason": ""
        }

        if status_a == 200 and status_b == 200:
            if abs(len(body_a) - len(body_b)) > 100:  # threshold
                result["potential"] = True
                result["reason"] = "Both 200 OK but content length differs significantly"
        elif status_a == 200 and status_b in (403, 401):
            # Session B cannot access, Session A can -> normal (A is privileged)
            pass
        elif status_a in (403, 401) and status_b == 200:
            # Session B (unprivileged) can access what A (privileged) cannot? Unlikely, but flag.
            result["potential"] = True
            result["reason"] = "Unprivileged session accessed resource that privileged cannot"
        return result

    def run(self) -> List[Dict]:
        """Test all endpoints with object ID range."""
        all_findings = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = []
            for endpoint in self.endpoints:
                for obj_id in range(1, 20):  # configurable range
                    url = f"{self.base_url}{endpoint.format(obj_id)}"
                    futures.append(executor.submit(self._compare_responses, url, url))

            for future in concurrent.futures.as_completed(futures):
                res = future.result()
                if res["potential"]:
                    logger.warning(f"Potential IDOR: {res}")
                    all_findings.append(res)
        return all_findings

# Example usage
if __name__ == "__main__":
    fuzzer = IDORFuzzer(
        base_url="https://api.example.com",
        session_a_headers={"Authorization": "Bearer tokenA"},
        session_b_headers={"Authorization": "Bearer tokenB"},
        endpoints=["/api/user/{}", "/api/order/{}"]
    )
    findings = fuzzer.run()
    print(json.dumps(findings, indent=2))
