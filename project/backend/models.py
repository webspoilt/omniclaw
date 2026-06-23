from datetime import datetime
from typing import Any

from pydantic import BaseModel


class Message(BaseModel):
    role: str
    content: str

class AgentTaskRequest(BaseModel):
    prompt: str
    conversation_id: str | None = None

class AgentTaskResponse(BaseModel):
    conversation_id: str
    messages: list[Message]
    final_output: str | None = None

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
    parameters: dict[str, Any]

class ToolExecutionResponse(BaseModel):
    result: str
    error: str | None = None
