from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from models import Message
from cost_tracker import tracked_completion
from database import SessionLocal, ConversationMemory
from config import settings
import uuid

class BaseAgent(ABC):
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.conversation_id: Optional[str] = None
        self.messages: List[Message] = []
    
    async def initialize_conversation(self, conversation_id: Optional[str] = None):
        if conversation_id:
            self.conversation_id = conversation_id
            # Load previous messages from memory? (optional)
        else:
            self.conversation_id = str(uuid.uuid4())
        self.messages = [Message(role="system", content=self.system_prompt)]
    
    async def add_user_message(self, content: str):
        self.messages.append(Message(role="user", content=content))
    
    async def call_llm(self, tools: Optional[List[Dict]] = None) -> str:
        """Call LLM with current messages and optional tools."""
        response = await tracked_completion(
            model=settings.model,
            messages=[m.dict() for m in self.messages],
            agent_name=self.name,
            tools=tools
        )
        assistant_message = response.choices[0].message
        content = assistant_message.content or ""
        self.messages.append(Message(role="assistant", content=content))
        return content
    
    async def run(self, user_input: str, tools: Optional[List[Dict]] = None) -> str:
        """Main entry point for agent."""
        await self.add_user_message(user_input)
        return await self.call_llm(tools)
    
    def remember_trigger(self, trigger_phrase: str, response: str):
        """Store trigger phrase for future use."""
        db = SessionLocal()
        mem = ConversationMemory(
            conversation_id=self.conversation_id,
            trigger_phrase=trigger_phrase,
            response=response
        )
        db.add(mem)
        db.commit()
        db.close()
    
    def recall_trigger(self, trigger_phrase: str) -> Optional[str]:
        """Retrieve memory for a trigger phrase."""
        db = SessionLocal()
        mem = db.query(ConversationMemory).filter(
            ConversationMemory.conversation_id == self.conversation_id,
            ConversationMemory.trigger_phrase == trigger_phrase
        ).first()
        db.close()
        return mem.response if mem else None
