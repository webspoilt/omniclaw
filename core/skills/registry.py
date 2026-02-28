"""
ToolRegistry — Decorator-based tool registration with OpenAI-format schema generation.

Ported from NanoClaw's tools/registry.py.
Provides `@tool` decorator for registering functions as agent tools,
and `ToolRegistry` class for managing and executing them.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
import logging
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger("OmniClaw.Skills.Registry")


@dataclass
class ToolInfo:
    """Information about a registered tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable
    needs_confirmation: bool = False
    required_params: list[str] = field(default_factory=list)


# Global tool registry
_registry: dict[str, ToolInfo] = {}
_tool_registry_instance: Optional["ToolRegistry"] = None


def tool(
    name: str,
    description: str,
    parameters: dict[str, Any],
    needs_confirmation: bool = False,
    required: Optional[list[str]] = None,
) -> Callable:
    """
    Decorator to register a function as an agent tool.

    Usage:
        @tool(
            name="web_search",
            description="Search the internet",
            parameters={"query": {"type": "string", "description": "Search query"}}
        )
        async def web_search(query: str) -> str:
            ...

    Args:
        name: Tool name (used in LLM tool_calls)
        description: Human-readable description for LLM
        parameters: JSON Schema for parameters
        needs_confirmation: If True, always asks user before executing
        required: List of required parameter names (defaults to all)
    """

    def decorator(func: Callable) -> Callable:
        req_params = required if required is not None else list(parameters.keys())
        info = ToolInfo(
            name=name,
            description=description,
            parameters=parameters,
            handler=func,
            needs_confirmation=needs_confirmation,
            required_params=req_params,
        )
        _registry[name] = info

        # If registry instance exists, update it too
        if _tool_registry_instance is not None:
            _tool_registry_instance.tools[name] = info

        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            return await func(*args, **kwargs)

        return wrapper

    return decorator


class ToolRegistry:
    """Registry for managing and executing tools."""

    def __init__(self) -> None:
        """Initialize with copy of global registry."""
        global _tool_registry_instance
        self.tools: dict[str, ToolInfo] = dict(_registry)
        _tool_registry_instance = self

    def get_schemas(self) -> list[dict[str, Any]]:
        """
        Generate OpenAI-compatible tool schemas for LLM.

        Returns:
            List of tool schemas in OpenAI function-calling format
        """
        schemas = []
        for name, info in self.tools.items():
            schemas.append({
                "type": "function",
                "function": {
                    "name": info.name,
                    "description": info.description,
                    "parameters": {
                        "type": "object",
                        "properties": info.parameters,
                        "required": info.required_params,
                    },
                },
            })
        return schemas

    def get_tool_names(self) -> list[str]:
        """Get list of registered tool names."""
        return list(self.tools.keys())

    async def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        confirm_callback: Optional[Callable] = None,
    ) -> str:
        """
        Execute a tool by name with given arguments.

        Args:
            name: Tool name
            arguments: Tool arguments
            confirm_callback: Optional async callback for user confirmation

        Returns:
            Tool result as string
        """
        if name not in self.tools:
            return f"Unknown tool: {name}"

        tool_info = self.tools[name]

        # Tools that always need confirmation
        if tool_info.needs_confirmation and confirm_callback:
            import json
            approved = await confirm_callback(
                f"Tool `{name}` wants to run with:\n"
                f"```\n{json.dumps(arguments, indent=2)}\n```\n\nAllow?"
            )
            if not approved:
                return "User denied this action."

        try:
            # Handle malformed LLM output: {'parameters': {'query': '...'}}
            if "parameters" in arguments and len(arguments) == 1:
                logger.warning(f"Tool {name}: unwrapping nested 'parameters' from LLM")
                arguments = arguments["parameters"]

            result = await tool_info.handler(**arguments)
            return str(result)
        except TypeError as e:
            return f"Invalid arguments for {name}: {e}"
        except Exception as e:
            return f"Tool {name} failed: {e}"

    def register(self, tool_info: ToolInfo) -> None:
        """Manually register a tool."""
        self.tools[tool_info.name] = tool_info
        _registry[tool_info.name] = tool_info

    def unregister(self, name: str) -> bool:
        """Unregister a tool by name. Returns True if found."""
        removed = name in self.tools
        self.tools.pop(name, None)
        _registry.pop(name, None)
        return removed

    def get_status(self) -> dict:
        """Get registry status."""
        return {
            "total_tools": len(self.tools),
            "tool_names": self.get_tool_names(),
            "confirmation_required": [
                n for n, t in self.tools.items() if t.needs_confirmation
            ],
        }


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _tool_registry_instance
    if _tool_registry_instance is None:
        _tool_registry_instance = ToolRegistry()
    else:
        _tool_registry_instance.tools.update(_registry)
    return _tool_registry_instance


def reset_registry() -> None:
    """Reset the global registry (useful for testing)."""
    global _tool_registry_instance, _registry
    _registry.clear()
    _tool_registry_instance = None
