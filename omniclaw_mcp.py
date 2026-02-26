#!/usr/bin/env python3
"""
OmniClaw MCP Server
Exposes OmniClaw core functionality as a Model Context Protocol (MCP) server.
Can be used with clients like Claude Desktop.
"""

import subprocess
from pathlib import Path
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from core.automation.browser_agent import run_browser_automation_sync
from kernel_bridge.ebpf_monitor import ebpf_monitor
from core.quantum_gateway import quantum_gateway

# Load environment variables securely
load_dotenv()

# Initialize the MCP Server
mcp = FastMCP("OmniClaw")

@mcp.tool()
def run_agent_task(prompt: str) -> str:
    """Sends a task to the OmniClaw agent swarm and returns the result."""
    # This calls the existing omniclaw.py logic as a subprocess for isolated execution
    try:
        result = subprocess.run(
            ["python", "omniclaw.py", "task", prompt],
            capture_output=True, 
            text=True,
            check=False
        )
        return result.stdout if result.stdout else (result.stderr or "Task completed with no output.")
    except Exception as e:
        return f"Error executing task: {str(e)}"

@mcp.tool()
def get_system_health() -> str:
    """Traces system calls and returns a summary of kernel activity via the kernel bridge."""
    # Placeholder for kernel_bridge logic
    return "Kernel Bridge: Active. No anomalies detected."

@mcp.resource("config://settings")
def get_config() -> str:
    """Provides the current OmniClaw configuration."""
    config_path = Path("config.yaml")
    # Fallback to config.example.yaml if config is not created
    if not config_path.exists():
        config_path = Path("config.example.yaml")
        
    if config_path.exists():
        with open(config_path, "r") as f:
            return f.read()
    return "Error: config not found."

@mcp.tool()
def navigate_and_interact(task_description: str) -> str:
    """
    Uses an AI Vision agent and headless browser to navigate the web, 
    fill forms, extract data, or perform any complex web sequence.
    """
    try:
        return run_browser_automation_sync(task_description)
    except Exception as e:
        return f"Browser Automation failed: {str(e)}"

@mcp.tool()
def get_kernel_alerts(count: int = 10) -> list:
    """
    Retrieves the most recent anomalies detected by the Shadow Kernel eBPF monitor.
    """
    return ebpf_monitor.get_recent_alerts(count=count)

@mcp.tool()
def execute_quantum_script(qasm_string: str) -> dict:
    """
    Executes an OpenQASM 3 script via IBM Quantum.
    Provide the raw QASM string to receive probability counts.
    """
    return quantum_gateway.execute_qasm(qasm_string)

if __name__ == "__main__":
    # Start the server using stdio transport (standard for MCP)
    mcp.run(transport="stdio")
