from abc import ABC, abstractmethod
from typing import Dict, Any

class MCPTool(ABC):
    """Base class for MCP-compliant tools."""
    
    @abstractmethod
    async def execute(self, parameters: Dict[str, Any]) -> str:
        """Execute the tool with given parameters and return result as string."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    def get_schema(self) -> dict:
        """Return tool schema for LLM function calling."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters_schema()
        }
    
    def parameters_schema(self) -> dict:
        """Override to define JSON schema for parameters."""
        return {"type": "object", "properties": {}}
