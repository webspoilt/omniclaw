import asyncio
import logging
import time
import uuid
from typing import Any

import msgpack
import zmq
import zmq.asyncio

logger = logging.getLogger("OmniClaw.ZMQOrchestrator")

class MessageType:
    TASK_DISPATCH = "TASK_DISPATCH"
    TASK_RESULT = "TASK_RESULT"
    CONTEXT_HANDOFF_REQUEST = "CONTEXT_HANDOFF_REQUEST"
    CONTEXT_HANDOFF_RESULT = "CONTEXT_HANDOFF_RESULT"
    ANOMALY_ALERT = "ANOMALY_ALERT"
    REGISTER = "REGISTER"
    SYNC_VECTORS = "SYNC_VECTORS"


class ZMQOrchestrator:
    """
    Manager Node using ZeroMQ ROUTER socket for Agent-to-Agent communication.
    Handles message dispatch, worker registration, and vector sync routing.
    """
    def __init__(self, bind_address: str = "tcp://0.0.0.0:5555"):
        self.ctx = zmq.asyncio.Context()
        self.router = self.ctx.socket(zmq.ROUTER)
        self.router.bind(bind_address)

        self.registry: dict[str, dict[str, Any]] = {}  # worker_id -> capabilities
        self.running = False

    def create_envelope(self, msg_type: str, routing_id: str, payload: dict, priority: int = 1) -> bytes:
        """Create a standard MessagePack envelope"""
        envelope = {
            "header": {
                "msg_id": str(uuid.uuid4()),
                "type": msg_type,
                "timestamp": time.time(),
                "routing_id": routing_id,
                "priority": priority
            },
            "payload": payload
        }
        return msgpack.packb(envelope)

    async def start(self):
        self.running = True
        logger.info("ZMQ Orchestrator starting on ROUTER socket.")
        while self.running:
            try:
                # recv_multipart returns: [identity, empty, payload]
                frames = await self.router.recv_multipart()
                if len(frames) < 3:
                    logger.warning("Received malformed multipart message")
                    continue

                sender_id = frames[0]
                packed_msg = frames[2]

                msg = msgpack.unpackb(packed_msg)
                header = msg.get("header", {})
                payload = msg.get("payload", {})
                msg_type = header.get("type")

                await self.route_message(sender_id, msg_type, payload)

            except Exception as e:
                logger.error(f"Error in ZMQ loop: {e}")

    async def route_message(self, sender_id: bytes, msg_type: str, payload: dict):
        if msg_type == MessageType.REGISTER:
            capabilities = payload.get("capabilities", [])
            node_type = payload.get("node_type", "unknown")
            self.registry[sender_id.decode('utf-8')] = {
                "capabilities": capabilities,
                "node_type": node_type,
                "last_seen": time.time()
            }
            logger.info(f"Registered worker {sender_id.decode('utf-8')} with capabilities: {capabilities}")

        elif msg_type == MessageType.ANOMALY_ALERT:
            logger.warning(f"ANOMALY ALERT from {sender_id.decode('utf-8')}: {payload}")
            # Dispatch to security mitigation handlers

        elif msg_type == MessageType.TASK_RESULT:
            logger.info(f"Received task result from {sender_id.decode('utf-8')}: {payload.get('task_id')}")
            # Handle task completion

        elif msg_type == MessageType.CONTEXT_HANDOFF_REQUEST:
            logger.info(f"Context handoff requested by {sender_id.decode('utf-8')}")
            await self.handle_context_handoff(sender_id, payload)

        elif msg_type == MessageType.SYNC_VECTORS:
            logger.info(f"Vector sync requested by {sender_id.decode('utf-8')}")
            await self.handle_vector_sync(sender_id, payload)

        else:
            logger.warning(f"Unknown message type {msg_type} from {sender_id.decode('utf-8')}")

    async def send_to_worker(self, target_id: str, msg_type: str, payload: dict, priority: int = 1):
        """Send a message to a specific registered worker"""
        envelope = self.create_envelope(msg_type, "manager", payload, priority)
        await self.router.send_multipart([target_id.encode('utf-8'), b"", envelope])

    async def handle_context_handoff(self, sender_id: bytes, payload: dict):
        """
        Handle offloaded search query from Edge Node.
        The Edge Node (SQLite-vec) didn't find high-confidence results,
        so we search the Compute Core (LanceDB).
        """
        payload.get("query")
        # Pseudo-code for LanceDB search
        # results = lancedb_search(query)
        mock_results = [{"doc": "Simulated LanceDB result for handoff", "score": 0.95}]

        await self.send_to_worker(
            target_id=sender_id.decode('utf-8'),
            msg_type=MessageType.CONTEXT_HANDOFF_RESULT,
            payload={"results": mock_results}
        )

    async def handle_vector_sync(self, sender_id: bytes, payload: dict):
        """
        Handle vector hash exchange.
        Edge node sends hash of its sqlite-vec state.
        Manager compares and sends missing vectors.
        """
        payload.get("hash")
        # Compare hashes, extract diff...
        diff = [] # mock

        await self.send_to_worker(
            target_id=sender_id.decode('utf-8'),
            msg_type=MessageType.SYNC_VECTORS,
            payload={"action": "update", "vectors": diff}
        )

    def stop(self):
        self.running = False
        self.router.close()
        self.ctx.term()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    orchestrator = ZMQOrchestrator()
    asyncio.run(orchestrator.start())
