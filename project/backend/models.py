from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class Message(BaseModel):
    role: str
    content: str

class AgentTaskRequest(BaseModel):
    prompt: str
    conversation_id: Optional[str] = None

class AgentTaskResponse(BaseModel):
    conversation_id: str
    messages: List[Message]
    final_output: Optional[str] = None

class CostRecord(BaseModel):
    id: int
    timestamp: datetime
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    agent: str

class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]

class ToolExecutionResponse(BaseModel):
    result: str
    error: Optional[str] = None
