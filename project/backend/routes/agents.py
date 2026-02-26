from fastapi import APIRouter, HTTPException
from models import AgentTaskRequest, AgentTaskResponse, Message
from agents.orchestrator import Orchestrator
import logging

router = APIRouter(prefix="/api/agents", tags=["agents"])
logger = logging.getLogger(__name__)

@router.post("/task", response_model=AgentTaskResponse)
async def run_agent_task(request: AgentTaskRequest):
    try:
        orchestrator = Orchestrator()
        final_output = await orchestrator.run_task(
            prompt=request.prompt,
            conversation_id=request.conversation_id
        )
        # For simplicity, return final output as one assistant message
        messages = [Message(role="assistant", content=final_output)]
        return AgentTaskResponse(
            conversation_id=orchestrator.conversation_id,
            messages=messages,
            final_output=final_output
        )
    except Exception as e:
        logger.exception("Agent task failed")
        raise HTTPException(status_code=500, detail=str(e))
