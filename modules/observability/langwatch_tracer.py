"""
OmniClaw Observability

Provides LangWatch integration to trace LLM usage, inputs, outputs, 
and computing costs across all agents natively.
"""
import logging
import os
from contextlib import contextmanager

try:
    import langwatch
    LANGWATCH_AVAILABLE = True
except ImportError:
    LANGWATCH_AVAILABLE = False

logger = logging.getLogger(__name__)

def init_langwatch(api_key: str = None, endpoint: str = None):
    """Initialize the LangWatch sdk globally."""
    if not LANGWATCH_AVAILABLE:
        return
    
    # Prioritize provided keys, then environment variables
    key = api_key or os.environ.get("LANGWATCH_API_KEY")
    if key:
        langwatch.api_key = key
    
    ep = endpoint or os.environ.get("LANGWATCH_ENDPOINT")
    if ep:
        langwatch.endpoint = ep
        
    if key:
        logger.info("LangWatch observability enabled.")

@contextmanager
def omniclaw_trace(trace_name: str, user_id: str = None, metadata: dict = None):
    """
    Wraps an execution block in a LangWatch trace.
    Usage:
        with omniclaw_trace("agent_subtask", user_id="user123") as trace:
            # do LLM work...
            if trace: trace.update(output="Result")
    """
    if not LANGWATCH_AVAILABLE or not getattr(langwatch, "api_key", None):
        # Yield a dummy object if Langwatch isn't configured
        class DummyTrace:
            def update(self, *args, **kwargs): pass
            def log(self, *args, **kwargs): pass
        yield DummyTrace()
        return

    try:
        # Create a new trace context
        trace = langwatch.Trace(
            name=trace_name,
            user_id=user_id,
            metadata=metadata
        )
        yield trace
    except Exception as e:
        logger.error(f"Langwatch trace error: {e}")
        class DummyTrace:
            def update(self, *args, **kwargs): pass
            def log(self, *args, **kwargs): pass
        yield DummyTrace()
