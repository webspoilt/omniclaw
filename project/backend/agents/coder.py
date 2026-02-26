from .base import BaseAgent

class CoderAgent(BaseAgent):
    def __init__(self):
        system_prompt = """You are the Coder agent. You implement the specifications provided by the Architect.
Write clean, efficient, and well-documented code. Respond with code blocks and explanations.
If you need clarification, ask."""
        super().__init__("Coder", system_prompt)
