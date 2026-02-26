import litellm
from litellm import completion
from database import SessionLocal, CostEntry
from config import settings
import time

# Configure LiteLLM to use OpenRouter
litellm.openrouter_key = settings.openrouter_api_key
litellm.openrouter_base = settings.openrouter_base_url

async def tracked_completion(model: str, messages: list, agent_name: str, **kwargs):
    """Call LLM and record token usage/cost."""
    start = time.time()
    response = await completion(
        model=model,
        messages=messages,
        **kwargs
    )
    # Extract usage
    prompt_tokens = response.usage.prompt_tokens
    completion_tokens = response.usage.completion_tokens
    # Approximate cost (you can refine based on model pricing)
    cost = (prompt_tokens * 0.000003 + completion_tokens * 0.000015)  # example rate
    
    # Store in DB
    db = SessionLocal()
    cost_entry = CostEntry(
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        cost_usd=cost,
        agent=agent_name
    )
    db.add(cost_entry)
    db.commit()
    db.close()
    
    return response
