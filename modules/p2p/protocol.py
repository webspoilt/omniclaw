"""
protocol.py — P2P Neural Mesh message types and serialization.

All mesh communication follows this schema. Messages are JSON-serialized,
then AES-256-GCM encrypted before transmission over ZeroMQ.
"""

import time
import json
import os
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Dict


class MsgType(Enum):
    HEARTBEAT          = "heartbeat"
    TASK_REQUEST       = "task_request"
    TASK_RESPONSE      = "task_response"
    TASK_OFFER         = "task_offer"
    KNOWLEDGE_QUERY    = "knowledge_query"
    KNOWLEDGE_RESPONSE = "knowledge_response"
    SYNC_REQUEST       = "sync_request"
    SYNC_DATA          = "sync_data"
    ERROR              = "error"


@dataclass
class Message:
    type: MsgType
    id: str
    sender: str
    recipient: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_json(self) -> bytes:
        d = asdict(self)
        d["type"] = self.type.value
        return json.dumps(d).encode("utf-8")

    @classmethod
    def from_json(cls, data: bytes) -> "Message":
        d = json.loads(data)
        d["type"] = MsgType(d["type"])
        return cls(**d)

    @staticmethod
    def make_id(node_id: str) -> str:
        return f"{node_id}_{time.time()}_{os.urandom(4).hex()}"
