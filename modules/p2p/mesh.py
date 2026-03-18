#!/usr/bin/env python3
"""
mesh.py — ZeroMQ Neural Mesh Node

ROUTER/DEALER P2P mesh with AES-256-GCM encryption.
Supports task offloading, knowledge queries, sync, and heartbeat
with capability advertisement (CPU, memory, available models).
"""

import os
import json
import time
import queue
import threading
import logging
from typing import Any, Dict, Optional, Callable, List
from pathlib import Path

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

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from modules.p2p.protocol import Message, MsgType

try:
    from p2p.crypto import AESCipher
except ImportError:
    from core.hive_sync import AESCipher  # fallback

try:
    from core.kill_switch import check_kill_switch
    from core.resource_utils import resource_check
except ImportError:
    def check_kill_switch(): pass
    def resource_check(**kw): return True

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("NeuralMesh")


class NeuralMeshNode:
    """
    ZeroMQ ROUTER/DEALER P2P mesh node with AES-256-GCM encryption.

    Usage:
        node = NeuralMeshNode("desktop", 5555, ["100.64.1.2:5555"], aes_key)
        node.task_handler = my_task_fn
        node.knowledge_handler = my_knowledge_fn
        node.start()
    """

    def __init__(self, node_id: str, listen_port: int,
                 peers: List[str], aes_key: bytes):
        """
        Initialize NeuralMeshNode.

        Args:
            node_id: Unique identifier for this node
            listen_port: TCP port to bind the ROUTER socket
            peers: List of "host:port" peer addresses to connect as DEALERs
            aes_key: 32-byte AES-256-GCM key for wire encryption

        .. warning:: **Issue #20 — Static AES key limitation.**
            The current implementation uses a single pre-shared AES-256-GCM
            key for all peer connections.  This means key compromise affects
            the entire mesh.  A proper Diffie-Hellman ECDH key exchange is
            planned for v4.3.  In the meantime, rotate the key via the
            ``AES_KEY`` environment variable and never commit it to source
            control.
        """
        if not HAS_ZMQ:
            raise ImportError("pyzmq required: pip install pyzmq")

        # Warn if using the hardcoded demo key from __main__
        _DEMO_KEY_B64 = "dGhpc2lzMzJieXRla2V5Zm9yYWVzMjU2Z2NtISE="
        try:
            import base64
            if aes_key == base64.b64decode(_DEMO_KEY_B64):
                import warnings
                warnings.warn(
                    "NeuralMeshNode: using the default demo AES key — "
                    "set AES_KEY env var to a real 32-byte key before "
                    "deploying! (Issue #20)",
                    DeprecationWarning,
                    stacklevel=2,
                )
                logger.warning(
                    "SECURITY: NeuralMesh is using the default demo AES key. "
                    "Set AES_KEY to a real 32-byte base64-encoded secret."
                )
        except Exception:
            pass

        self.node_id = node_id
        self.listen_port = listen_port
        self.cipher = AESCipher(aes_key)
        self.ctx = zmq.Context()

        self.router = self.ctx.socket(zmq.ROUTER)
        self.router.bind(f"tcp://*:{listen_port}")

        self.dealers: Dict[str, zmq.Socket] = {}
        self.peer_info: Dict[str, dict] = {}
        self.pending: Dict[str, queue.Queue] = {}
        self.lock = threading.Lock()
        self.running = False

        # Callbacks
        self.task_handler: Optional[Callable] = None
        self.knowledge_handler: Optional[Callable] = None

        for addr in peers:
            if addr.strip():
                self._connect_peer(addr.strip())

        logger.info(f"NeuralMeshNode '{node_id}' bound on :{listen_port}")

    def _connect_peer(self, address: str):
        dealer = self.ctx.socket(zmq.DEALER)
        dealer.setsockopt_string(zmq.IDENTITY, self.node_id)
        dealer.connect(f"tcp://{address}")
        pid = f"peer_{address}"
        self.dealers[pid] = dealer
        self.peer_info[pid] = {"address": address, "last_seen": 0,
                                "capabilities": {}}

    # ---- Lifecycle ----
    def start(self):
        self.running = True
        for fn in (self._recv_loop, self._hb_loop):
            t = threading.Thread(target=fn, daemon=True)
            t.start()
        logger.info("Mesh node online")

    def stop(self):
        self.running = False
        for d in self.dealers.values():
            d.close()
        self.router.close()
        self.ctx.term()
        logger.info("Mesh node stopped")

    # ---- Send ----
    def _send(self, peer_id: str, msg: Message) -> bool:
        if peer_id not in self.dealers:
            return False
        try:
            encrypted = self.cipher.encrypt(msg.to_json())
            self.dealers[peer_id].send(encrypted)
            return True
        except Exception as e:
            logger.error(f"Send to {peer_id}: {e}")
            return False

    # ---- Receive ----
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
                    msg = Message.from_json(self.cipher.decrypt(encrypted))
                except Exception:
                    continue
                sender = identity.decode()
                if sender not in self.peer_info:
                    self.peer_info[sender] = {"address": "unknown",
                                               "last_seen": time.time()}
                self.peer_info[sender]["last_seen"] = time.time()
                self._handle(msg, sender)
            except Exception as e:
                logger.error(f"Recv: {e}")

    def _handle(self, msg: Message, sender: str):
        if msg.type == MsgType.HEARTBEAT:
            if msg.payload:
                self.peer_info[sender]["capabilities"] = msg.payload

        elif msg.type == MsgType.TASK_REQUEST:
            result = (self.task_handler(msg.payload)
                      if self.task_handler else {"error": "no handler"})
            self._send(sender, Message(MsgType.TASK_RESPONSE, msg.id,
                                        self.node_id, payload={"result": result}))

        elif msg.type == MsgType.KNOWLEDGE_QUERY:
            result = (self.knowledge_handler(msg.payload)
                      if self.knowledge_handler else {})
            self._send(sender, Message(MsgType.KNOWLEDGE_RESPONSE, msg.id,
                                        self.node_id, payload=result))

        elif msg.type in (MsgType.TASK_RESPONSE, MsgType.KNOWLEDGE_RESPONSE,
                          MsgType.ERROR):
            with self.lock:
                q = self.pending.pop(msg.id, None)
            if q:
                q.put(msg.payload)

    # ---- Heartbeat ----
    def _hb_loop(self):
        while self.running:
            caps = {
                "cpu": psutil.cpu_percent() if HAS_PSUTIL else 0,
                "memory": psutil.virtual_memory().percent if HAS_PSUTIL else 0,
            }
            hb = Message(MsgType.HEARTBEAT, "", self.node_id, payload=caps)
            for pid in list(self.dealers):
                self._send(pid, hb)
            time.sleep(5)

    # ---- Public API ----
    def request_task(self, peer_id: str, task: dict,
                     timeout: float = 30) -> Optional[Any]:
        rid = Message.make_id(self.node_id)
        q: queue.Queue = queue.Queue()
        with self.lock:
            self.pending[rid] = q
        msg = Message(MsgType.TASK_REQUEST, rid, self.node_id, payload=task)
        if not self._send(peer_id, msg):
            with self.lock:
                self.pending.pop(rid, None)
            return None
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None
        finally:
            with self.lock:
                self.pending.pop(rid, None)

    def query_knowledge(self, peer_id: str, query: dict,
                        timeout: float = 10) -> Optional[Any]:
        rid = Message.make_id(self.node_id)
        q: queue.Queue = queue.Queue()
        with self.lock:
            self.pending[rid] = q
        msg = Message(MsgType.KNOWLEDGE_QUERY, rid, self.node_id, payload=query)
        if not self._send(peer_id, msg):
            with self.lock:
                self.pending.pop(rid, None)
            return None
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None
        finally:
            with self.lock:
                self.pending.pop(rid, None)

    def get_online_peers(self) -> List[str]:
        now = time.time()
        return [p for p, info in self.peer_info.items()
                if now - info.get("last_seen", 0) < 15]

    def should_offload(self) -> bool:
        if not HAS_PSUTIL:
            return False
        return psutil.cpu_percent(0.1) > 70


if __name__ == "__main__":
    import base64
    key = base64.b64decode(os.getenv("AES_KEY", "dGhpc2lzMzJieXRla2V5Zm9yYWVzMjU2Z2NtISE="))
    node = NeuralMeshNode(
        os.getenv("NODE_ID", "desktop"), 5555,
        os.getenv("PEERS", "").split(","), key,
    )
    node.task_handler = lambda t: f"Processed: {t}"
    node.knowledge_handler = lambda q: {"results": []}
    node.start()
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        node.stop()
