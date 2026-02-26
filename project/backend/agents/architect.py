from .base import BaseAgent

class ArchitectAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are the Architect agent. Your role is to:
1. Understand the user's high-level request.
2. Break it down into components and create a design specification.
3. Pass clear, structured tasks to the Coder agent.
Be concise but thorough. Use markdown for structure."""
        super().__init__("Architect", system_prompt)
