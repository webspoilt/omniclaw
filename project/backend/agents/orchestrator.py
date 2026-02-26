from typing import Optional
from .architect import ArchitectAgent
from .coder import CoderAgent
from .reviewer import ReviewerAgent
from models import Message

class Orchestrator:
    def __init__(self):
        self.architect = ArchitectAgent()
        self.coder = CoderAgent()
        self.reviewer = ReviewerAgent()
        self.conversation_id: Optional[str] = None
    
    async def run_task(self, prompt: str, conversation_id: Optional[str] = None) -> str:
        # Initialize all agents with same conversation
        await self.architect.initialize_conversation(conversation_id)
        await self.coder.initialize_conversation(conversation_id)
        await self.reviewer.initialize_conversation(conversation_id)
        self.conversation_id = self.architect.conversation_id
        
        # Step 1: Architect creates design
        design = await self.architect.run(prompt)
        
        # Check for trigger phrase memory (example: "use previous pattern")
        if "use previous" in prompt.lower():
            remembered = self.architect.recall_trigger("design_pattern")
            if remembered:
                design += f"\n\nNote: Remembered pattern: {remembered}"
        
        # Step 2: Coder implements
        implementation = await self.coder.run(f"Implement this design:\n{design}")
        
        # Step 3: Reviewer checks
        review = await self.reviewer.run(f"Review this implementation:\n{implementation}")
        
        # Optional: store a trigger phrase
        if "pattern" in prompt.lower():
            self.architect.remember_trigger("design_pattern", design)
        
        # Combine final output (could be more sophisticated)
        final = f"## Design\n{design}\n\n## Implementation\n{implementation}\n\n## Review\n{review}"
        return final
