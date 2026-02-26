import asyncio
import logging
from typing import Dict, Any, Optional

try:
    from browser_use import Agent, Controller
    from langchain_openai import ChatOpenAI
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False

logger = logging.getLogger("OmniClaw.BrowserAgent")

# Optional controller for custom actions (e.g. CAPTCHA solving, injecting credentials)
controller = Controller()

class BrowserAutomationAgent:
    """
    Agent for driving headless/headful browsers to achieve dynamic goals on the web.
    """
    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        self.llm = None
        if BROWSER_USE_AVAILABLE:
            try:
                # LLM should be vision-capable (e.g. gpt-4o or claude-3-5-sonnet)
                self.llm = ChatOpenAI(model=self.model_name)
            except Exception as e:
                logger.warning(f"Failed to initialize LLM for Browser Automation: {e}")

    async def execute_task(self, task: str) -> str:
        """
        Executes a browser automation task based on natural language.
        """
        if not BROWSER_USE_AVAILABLE:
            return "Error: browser-use or langchain_openai is not installed."
            
        if not self.llm:
            return "Error: LLM could not be initialized. Please check your AI API keys."
            
        logger.info(f"Starting browser automation for task: {task}")
        
        try:
            agent = Agent(
                task=task,
                llm=self.llm,
                controller=controller
            )
            result = await agent.run()
            return f"Browser Automation Result:\n{str(result)}"
        except Exception as e:
            logger.error(f"Browser automation failed: {e}")
            return f"Error during browser automation: {str(e)}"

# Synchronous helper to cleanly expose to tools / MCP
def run_browser_automation_sync(task: str, model_name: str = "gpt-4o") -> str:
    agent = BrowserAutomationAgent(model_name=model_name)
    return asyncio.run(agent.execute_task(task))
