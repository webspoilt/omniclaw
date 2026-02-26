from fastapi import APIRouter, HTTPException
from models import ToolExecutionRequest, ToolExecutionResponse
from tools.ebpf_monitor import EbpfMonitorTool

router = APIRouter(prefix="/api/tools", tags=["tools"])

# Tool registry
_tools = {
    "ebpf_monitor": EbpfMonitorTool()
}

@router.post("/execute", response_model=ToolExecutionResponse)
async def execute_tool(request: ToolExecutionRequest):
    tool = _tools.get(request.tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    try:
        result = await tool.execute(request.parameters)
        return ToolExecutionResponse(result=result)
    except Exception as e:
        return ToolExecutionResponse(result="", error=str(e))
