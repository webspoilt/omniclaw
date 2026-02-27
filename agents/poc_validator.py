import asyncio
import aiohttp
import hashlib
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class PoCValidator:
    def __init__(self, sandbox_url: str, kill_switch: asyncio.Event):
        self.sandbox_url = sandbox_url.rstrip('/')
        self.kill_switch = kill_switch
        self.evidence_chain = []  # list of dicts with hash, payload, response snippet

    async def execute_payload(self, session: aiohttp.ClientSession, 
                              payload: Dict[str, Any]) -> Optional[Dict]:
        """
        payload: {
            'type': 'xss' | 'sqli' | 'injection',
            'method': 'get' | 'post',
            'endpoint': '/test',
            'parameters': {'param': 'value'},
            'payload_data': '...'
        }
        """
        if self.kill_switch.is_set():
            return None
        # Merge payload into parameters
        params = payload.get('parameters', {}).copy()
        # For simplicity, we replace a placeholder or append to a parameter.
        # In real life, you'd have more sophisticated injection.
        # Here we just set a known parameter to the payload.
        if 'param' in params:
            params['param'] = payload['payload_data']
        else:
            # If no param, add one
            params['input'] = payload['payload_data']

        func = session.get if payload['method'] == 'get' else session.post
        url = self.sandbox_url + payload['endpoint']
        try:
            async with func(url, params=params if payload['method']=='get' else None,
                            data=params if payload['method']=='post' else None) as resp:
                response_text = await resp.text()
                status = resp.status
        except Exception as e:
            logger.error(f"Payload execution failed: {e}")
            return None

        # Check for source code leakage (e.g., PHP tags, stack traces)
        leaked = False
        leakage_patterns = ['<?php', 'Exception', 'Stack trace', 'function', 'class ']
        for pattern in leakage_patterns:
            if pattern in response_text:
                leaked = True
                break

        # Generate evidence hash
        evidence_str = f"{payload}{response_text[:500]}"  # combine payload and response snippet
        evidence_hash = hashlib.sha256(evidence_str.encode()).hexdigest()

        record = {
            'hash': evidence_hash,
            'payload': payload,
            'status': status,
            'response_snippet': response_text[:200],
            'leaked_source': leaked,
            'timestamp': asyncio.get_event_loop().time()
        }
        self.evidence_chain.append(record)
        return record

    async def run(self, payloads: list) -> list:
        """Execute a list of payloads and return validated ones."""
        async with aiohttp.ClientSession() as session:
            tasks = [self.execute_payload(session, p) for p in payloads]
            results = await asyncio.gather(*tasks)
        # Filter successful ones (status 200 and maybe leaked)
        validated = [r for r in results if r and r['status'] == 200 and r['leaked_source']]
        return validated
