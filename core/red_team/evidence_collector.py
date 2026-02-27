import base64
import json
import datetime
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class EvidenceCollector:
    """
    Captures and stores Proof‑of‑Concept data as Base64‑encoded files.
    """

    def __init__(self, storage_dir: str = "./poc_evidence"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    @staticmethod
    def _encode(obj) -> str:
        """Encode an object to Base64 (JSON or raw string)."""
        if isinstance(obj, (dict, list)):
            data = json.dumps(obj, indent=2)
        else:
            data = str(obj)
        return base64.b64encode(data.encode('utf-8')).decode('utf-8')

    def save_poc(self, vulnerability_type: str, request_data: Dict, response_data: Dict,
                 metadata: Optional[Dict] = None) -> str:
        """
        Save the PoC as a JSON file with Base64‑encoded fields.
        Returns the file path.
        """
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        poc_record = {
            "timestamp": timestamp,
            "vulnerability": vulnerability_type,
            "metadata": metadata or {},
            "request": {
                "method": request_data.get("method", "GET"),
                "url": request_data.get("url", ""),
                "headers": self._encode(request_data.get("headers", {})),
                "body": self._encode(request_data.get("body", ""))
            },
            "response": {
                "status": response_data.get("status", 0),
                "headers": self._encode(response_data.get("headers", {})),
                "body": self._encode(response_data.get("body", ""))
            }
        }

        filename = f"poc_{vulnerability_type}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.storage_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(poc_record, f, indent=2)

        logger.info(f"PoC saved: {filepath}")
        return filepath

    def save_llm_conversation(self, vulnerability_type: str, prompt: str, response: str,
                              metadata: Optional[Dict] = None) -> str:
        """
        Save an LLM conversation (prompt + response) as Base64.
        """
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        poc_record = {
            "timestamp": timestamp,
            "vulnerability": vulnerability_type,
            "metadata": metadata or {},
            "conversation": {
                "prompt": self._encode(prompt),
                "response": self._encode(response)
            }
        }

        filename = f"poc_{vulnerability_type}_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(self.storage_dir, filename)

        with open(filepath, 'w') as f:
            json.dump(poc_record, f, indent=2)

        logger.info(f"LLM PoC saved: {filepath}")
        return filepath
