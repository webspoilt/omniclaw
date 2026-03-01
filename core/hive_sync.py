#!/usr/bin/env python3
"""
hive_sync.py - P2P Synchronization Module for OmniClaw

Connects Mobile (Termux) and Desktop (Linux/WSL) nodes with AES-256-GCM encryption.
Handles:
  - Encrypted peer-to-peer messaging (ZeroMQ DEALER/ROUTER)
  - Vector DB query forwarding (shared context across nodes)
  - Load-based LLM task offloading (CPU threshold)
  - Heartbeat and online status tracking
  - Integration hooks for FAISS search and LLM inference callbacks
"""

import os
import sys
import json
import time
import threading
import queue
import logging
import base64
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum

try:
    import zmq
    HAS_ZMQ = True
except ImportError:
    HAS_ZMQ = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from Cryptodome.Cipher import AES
    from Cryptodome.Random import get_random_bytes
    HAS_CRYPTO = True
except ImportError:
    try:
        from Crypto.Cipher import AES
        from Crypto.Random import get_random_bytes
        HAS_CRYPTO = True
    except ImportError:
        HAS_CRYPTO = False

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# ------------------------------------------------------------------ #
#  Logging                                                            #
# ------------------------------------------------------------------ #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("HiveSync")

# ------------------------------------------------------------------ #
#  Configuration                                                      #
# ------------------------------------------------------------------ #
CONFIG_FILE = os.environ.get("HIVE_CONFIG", "hive_config.yaml")

_DEFAULT_CONFIG = {
    "node_id": "mobile",
    "listen_port": 5555,
    "peers": [],
    "aes_key": "",
    "cpu_threshold": 80.0,
    "memory_threshold": 90.0,
    "heartbeat_interval": 5,
    "peer_timeout": 15,
}


def load_config() -> dict:
    if HAS_YAML and os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return {**_DEFAULT_CONFIG, **yaml.safe_load(f)}
    # Also try env vars
    return {
        **_DEFAULT_CONFIG,
        "node_id": os.getenv("HIVE_NODE_ID", _DEFAULT_CONFIG["node_id"]),
        "listen_port": int(os.getenv("HIVE_PORT", str(_DEFAULT_CONFIG["listen_port"]))),
        "peers": (os.getenv("HIVE_PEERS", "").split(",")
                  if os.getenv("HIVE_PEERS") else []),
        "aes_key": os.getenv("HIVE_AES_KEY", ""),
        "cpu_threshold": float(os.getenv("HIVE_CPU_THRESHOLD",
                                          str(_DEFAULT_CONFIG["cpu_threshold"]))),
    }


# ------------------------------------------------------------------ #
#  Message Types                                                      #
# ------------------------------------------------------------------ #
class MsgType(Enum):
    HEARTBEAT = "heartbeat"
    QUERY     = "query"       # vector DB query
    OFFLOAD   = "offload"     # LLM offload request
    RESPONSE  = "response"
    ERROR     = "error"


@dataclass
class Message:
    type: MsgType
    id: str                   # correlation ID
    sender: str               # node_id
    payload: Any = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "id": self.id,
            "sender": self.sender,
            "payload": self.payload,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Message":
        return cls(
            type=MsgType(d["type"]),
            id=d["id"],
            sender=d["sender"],
            payload=d.get("payload"),
            timestamp=d.get("timestamp", time.time()),
        )


# ------------------------------------------------------------------ #
#  AES-256-GCM Encryption                                            #
# ------------------------------------------------------------------ #
class AESCipher:
    """Authenticated encryption: nonce(16) + ciphertext + tag(16)."""

    def __init__(self, key: bytes):
        if len(key) != 32:
            raise ValueError("AES key must be exactly 32 bytes")
        self.key = key

    def encrypt(self, data: bytes) -> bytes:
        cipher = AES.new(self.key, AES.MODE_GCM)
        ct, tag = cipher.encrypt_and_digest(data)
        return cipher.nonce + ct + tag

    def decrypt(self, enc: bytes) -> bytes:
        nonce, tag = enc[:16], enc[-16:]
        ct = enc[16:-16]
        cipher = AES.new(self.key, AES.MODE_GCM, nonce=nonce)
        return cipher.decrypt_and_verify(ct, tag)


# ------------------------------------------------------------------ #
#  Peer Tracking                                                      #
# ------------------------------------------------------------------ #
@dataclass
class Peer:
    node_id: str
    address: str
    last_seen: float = 0.0
    cpu_load: float = 0.0
    online: bool = False


# ------------------------------------------------------------------ #
#  HiveNode                                                           #
# ------------------------------------------------------------------ #
class HiveNode:
    """
    ZeroMQ-based P2P mesh node.

    Usage:
        node = HiveNode(config)
        node.register_query_handler(my_faiss_search)
        node.register_offload_handler(my_llm_inference)
        node.start()
    """

    def __init__(self, config: dict):
        if not HAS_ZMQ:
            raise ImportError("pyzmq is required: pip install pyzmq")
        if not HAS_CRYPTO:
            raise ImportError("pycryptodome is required: pip install pycryptodome")

        self.node_id = config["node_id"]
        self.listen_port = config["listen_port"]
        self.peer_addresses = [a.strip() for a in config.get("peers", []) if a.strip()]
        self.cpu_threshold = config.get("cpu_threshold", 80.0)
        self.hb_interval = config.get("heartbeat_interval", 5)
        self.peer_timeout = config.get("peer_timeout", 15)

        # Decode AES key
        raw_key = config.get("aes_key", "")
        if isinstance(raw_key, str):
            raw_key = base64.b64decode(raw_key) if raw_key else b""
        if len(raw_key) != 32:
            raise ValueError("AES key must be 32 bytes (base64-encoded in config)")

        self.cipher = AESCipher(raw_key)
        self.ctx = zmq.Context()

        # ROUTER for inbound
        self.router = self.ctx.socket(zmq.ROUTER)
        self.router.bind(f"tcp://*:{self.listen_port}")
        logger.info(f"ROUTER bound on :{self.listen_port}")

        # DEALER per peer
        self.dealers: Dict[str, zmq.Socket] = {}
        self.peers: Dict[str, Peer] = {}

        self.pending: Dict[str, queue.Queue] = {}
        self.pending_lock = threading.Lock()

        # Callbacks
        self.on_query: Optional[Callable] = None
        self.on_offload: Optional[Callable] = None

        self.running = False

        for addr in self.peer_addresses:
            self._add_peer(addr)

    # ---- peer management ----
    def _add_peer(self, address: str):
        dealer = self.ctx.socket(zmq.DEALER)
        dealer.setsockopt_string(zmq.IDENTITY, self.node_id)
        dealer.connect(f"tcp://{address}")
        pid = f"peer_{address}"
        self.dealers[pid] = dealer
        self.peers[pid] = Peer(node_id="unknown", address=address)
        logger.info(f"→ peer {address}")

    # ---- lifecycle ----
    def start(self):
        self.running = True
        threading.Thread(target=self._recv_loop, daemon=True, name="HiveRecv").start()
        threading.Thread(target=self._hb_loop, daemon=True, name="HiveHB").start()
        logger.info(f"HiveNode '{self.node_id}' online")

    def stop(self):
        self.running = False
        for d in self.dealers.values():
            d.close()
        self.router.close()
        self.ctx.term()
        logger.info("HiveNode stopped")

    # ---- comms ----
    def _send(self, peer_id: str, msg: Message) -> bool:
        if peer_id not in self.dealers:
            return False
        try:
            data = json.dumps(msg.to_dict()).encode()
            self.dealers[peer_id].send(self.cipher.encrypt(data))
            return True
        except Exception as e:
            logger.error(f"Send to {peer_id}: {e}")
            return False

    def _recv_loop(self):
        poller = zmq.Poller()
        poller.register(self.router, zmq.POLLIN)
        while self.running:
            try:
                socks = dict(poller.poll(1000))
                if self.router not in socks:
                    continue
                identity, encrypted = self.router.recv_multipart()
                try:
                    data = json.loads(self.cipher.decrypt(encrypted))
                    msg = Message.from_dict(data)
                except Exception as e:
                    logger.warning(f"Decrypt/parse fail: {e}")
                    continue

                sender = identity.decode()
                if sender not in self.peers:
                    self.peers[sender] = Peer(node_id=sender, address="unknown")
                self._handle(msg, sender)
            except Exception as e:
                logger.error(f"Recv error: {e}")

    def _handle(self, msg: Message, sender: str):
        if msg.type == MsgType.HEARTBEAT:
            p = self.peers.get(sender)
            if p:
                p.last_seen = time.time()
                p.online = True
                if msg.payload and "cpu" in msg.payload:
                    p.cpu_load = msg.payload["cpu"]

        elif msg.type == MsgType.QUERY:
            cb = self.on_query
            try:
                result = cb(msg.payload) if cb else "No query handler"
                rtype = MsgType.RESPONSE
            except Exception as e:
                result, rtype = str(e), MsgType.ERROR
            self._send(sender, Message(rtype, msg.id, self.node_id, result))

        elif msg.type == MsgType.OFFLOAD:
            cb = self.on_offload
            try:
                result = cb(msg.payload) if cb else "No offload handler"
                rtype = MsgType.RESPONSE
            except Exception as e:
                result, rtype = str(e), MsgType.ERROR
            self._send(sender, Message(rtype, msg.id, self.node_id, result))

        elif msg.type in (MsgType.RESPONSE, MsgType.ERROR):
            with self.pending_lock:
                q = self.pending.pop(msg.id, None)
            if q:
                q.put(msg.payload if msg.type == MsgType.RESPONSE else msg)

    # ---- heartbeat ----
    def _hb_loop(self):
        while self.running:
            cpu = psutil.cpu_percent(0.1) if HAS_PSUTIL else 0.0
            mem = psutil.virtual_memory().percent if HAS_PSUTIL else 0.0
            hb = Message(MsgType.HEARTBEAT, "", self.node_id,
                         {"cpu": cpu, "memory": mem})
            for pid in self.dealers:
                self._send(pid, hb)
            time.sleep(self.hb_interval)

    # ---- public API ----
    def register_query_handler(self, fn: Callable):
        """fn(query_str) -> results"""
        self.on_query = fn

    def register_offload_handler(self, fn: Callable):
        """fn(task_dict) -> llm_output"""
        self.on_offload = fn

    def query_peer(self, peer_id: str, query: str,
                   timeout: float = 10.0) -> Optional[Any]:
        rid = f"{self.node_id}_{time.time()}_{os.urandom(4).hex()}"
        q: queue.Queue = queue.Queue()
        with self.pending_lock:
            self.pending[rid] = q
        if not self._send(peer_id, Message(MsgType.QUERY, rid,
                                           self.node_id, query)):
            with self.pending_lock:
                self.pending.pop(rid, None)
            return None
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None
        finally:
            with self.pending_lock:
                self.pending.pop(rid, None)

    def offload_task(self, peer_id: str, task: Any,
                     timeout: float = 60.0) -> Optional[Any]:
        rid = f"{self.node_id}_{time.time()}_{os.urandom(4).hex()}"
        q: queue.Queue = queue.Queue()
        with self.pending_lock:
            self.pending[rid] = q
        if not self._send(peer_id, Message(MsgType.OFFLOAD, rid,
                                           self.node_id, task)):
            with self.pending_lock:
                self.pending.pop(rid, None)
            return None
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None
        finally:
            with self.pending_lock:
                self.pending.pop(rid, None)

    def get_online_peers(self) -> List[str]:
        now = time.time()
        return [pid for pid, p in self.peers.items()
                if now - p.last_seen < self.peer_timeout]

    def should_offload(self) -> bool:
        if not HAS_PSUTIL:
            return False
        return psutil.cpu_percent(0.1) > self.cpu_threshold


# ------------------------------------------------------------------ #
#  Standalone demo                                                    #
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    cfg = load_config()
    node = HiveNode(cfg)
    node.register_query_handler(lambda q: [f"result for '{q}'"])
    node.register_offload_handler(lambda t: f"LLM output for {t}")
    node.start()

    try:
        while True:
            time.sleep(10)
            online = node.get_online_peers()
            logger.info(f"Online peers: {online}")
            if node.should_offload() and online:
                r = node.offload_task(online[0], {"prompt": "test"})
                logger.info(f"Offload result: {r}")
    except KeyboardInterrupt:
        node.stop()
