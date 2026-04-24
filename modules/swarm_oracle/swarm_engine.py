"""
MiroFish Swarm Simulation Engine
Spawns 50+ agents with distinct personas using Ollama.
"""

import asyncio
import logging
import random
from typing import List, Dict, Any, Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential

from .personas import PERSONAS, Persona
from .config import settings

logger = logging.getLogger(__name__)


class Agent:
    def __init__(self, agent_id: int, persona: Persona):
        self.id = agent_id
        self.persona = persona


class SwarmSimulator:
    def __init__(self, model: str, num_agents: int, base_url: str = "http://localhost:11434"):
        self.model = model
        self.num_agents = num_agents
        self.base_url = base_url
        self.agents = self._create_agents()

    def _create_agents(self) -> List[Agent]:
        """Create agents by cycling through available personas."""
        agents = []
        for i in range(self.num_agents):
            persona = PERSONAS[i % len(PERSONAS)]
            agents.append(Agent(agent_id=i, persona=persona))
        return agents

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _query_ollama(self, prompt: str, agent: Agent) -> str:
        """Send a prompt to Ollama and return the response."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7 + random.uniform(-0.2, 0.2),  # slight personality variation
            },
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response", "")
                else:
                    text = await resp.text()
                    raise Exception(f"Ollama error {resp.status}: {text}")

    async def _agent_task(self, agent: Agent, context: str, similar_memories: List[str]) -> str:
        """Task for a single agent: generate a response based on persona."""
        persona_desc = agent.persona.description
        memories_text = ""
        if similar_memories:
            memories_text = "Relevant past simulations:\n" + "\n".join(similar_memories[:2]) + "\n"

        prompt = f"""You are a {persona_desc}. Simulate market sentiment for: {context}.

{memories_text}Provide your analysis in character, focusing on your typical concerns. Keep it concise (max 100 words)."""

        response = await self._query_ollama(prompt, agent)
        return f"Agent {agent.id} ({agent.persona.name}): {response}"

    async def run(self, context: str, similar_memories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run all agents concurrently and aggregate results."""
        if similar_memories is None:
            similar_memories = []

        tasks = [self._agent_task(agent, context, similar_memories) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        outputs = []
        for r in results:
            if isinstance(r, Exception):
                logger.error(f"Agent failed: {r}")
            else:
                outputs.append(r)

        aggregated = "\n".join(outputs)
        return {
            "aggregated": aggregated,
            "individual": outputs,
            "num_agents": len(self.agents),
            "successful": len(outputs),
        }
