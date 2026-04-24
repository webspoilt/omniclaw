#!/usr/bin/env python3
"""
OmniClaw Manager Agent
Orchestrates user input, triggers MiroFish simulations, and invokes the Auditor.
"""

import asyncio
import logging
from pathlib import Path

from .swarm_engine import SwarmSimulator
from .auditor import Auditor
from .knowledge import KnowledgeGraph
from .config import settings
from .models import SimulationRequest, SimulationResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Manager:
    def __init__(self):
        self.knowledge = KnowledgeGraph(persist_directory=settings.CHROMA_DB_PATH)
        self.auditor = Auditor()
        self.simulator = SwarmSimulator(
            model=settings.OLLAMA_MODEL,
            num_agents=settings.NUM_AGENTS,
            base_url=settings.OLLAMA_BASE_URL,
        )

    async def run_simulation(self, request: SimulationRequest) -> SimulationResult | None:
        """Execute a simulation with the given context."""
        logger.info(f"Starting simulation: {request.context}")

        # Retrieve similar past simulations from knowledge graph
        similar = self.knowledge.query_similar(request.context, top_k=3)
        if similar:
            logger.info(f"Found {len(similar)} similar memories")

        # Run the swarm
        raw_output = await self.simulator.run(request.context, similar_memories=similar)

        # Audit the output
        audit_result = self.auditor.audit(raw_output, request.context)
        if not audit_result.passed:
            logger.error(f"Audit failed: {audit_result.reason}")
            return None

        # Store the successful simulation
        result = SimulationResult(
            context=request.context,
            output=raw_output,
            audit=audit_result,
        )
        self.knowledge.store(result)
        logger.info("Simulation stored in knowledge graph")
        return result

    async def interactive_loop(self):
        """Simple REPL for user input."""
        print("OmniClaw Manager (type 'exit' to quit)")
        while True:
            user_input = input("\nEnter simulation context: ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if not user_input:
                continue
            req = SimulationRequest(context=user_input)
            result = await self.run_simulation(req)
            if result:
                print(f"\n✅ Simulation result:\n{result.output['aggregated']}\n")
            else:
                print("\n❌ Simulation failed audit.\n")


async def main():
    manager = Manager()
    await manager.interactive_loop()


if __name__ == "__main__":
    asyncio.run(main())
