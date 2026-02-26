import litellm
import logging

from .hardware_monitor import hardware_monitor

logger = logging.getLogger("OmniClaw.Arbitrator")

class Arbitrator:
    """
    Model-Agnostic Arbitrator
    Routes tasks to the most appropriate LLM based on task complexity.
    """
    def __init__(self, local_model="ollama/llama2", default_cloud_model="gpt-4o"):
        self.local_model = local_model
        self.default_cloud_model = default_cloud_model

    async def route_task(self, prompt: str, task_type: str = "simple") -> str:
        """
        Routes the task to a model based on complexity.
        task_type can be "simple", "complex", or "reasoning"
        """
        health = hardware_monitor.get_system_health()
        
        if task_type == "simple" and not health.get("is_overloaded", False):
            model = self.local_model
        elif task_type == "reasoning":
            model = "claude-3-5-sonnet-20241022"
        else:
            # This triggers if complex, or if simple but system is overloaded
            model = self.default_cloud_model
            if task_type == "simple":
                logger.warning(f"System overloaded (CPU: {health.get('cpu_percent')}%, RAM: {health.get('ram_percent')}%). Routing simple task to cloud: {model}")
            
        logger.info(f"Routing '{task_type}' task to model: {model}")
        
        try:
            response = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LiteLLM routing failed for {model}: {e}")
            # Fallback
            return f"Error from Arbitrator: {str(e)}"
