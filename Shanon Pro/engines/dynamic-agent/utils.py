import logging
import subprocess
import re
import time
import os
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("DynamicAgent.AutonomousFix")

@dataclass
class ParsedError:
    error_type: str
    message: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    stack_trace: str = ""
    language: str = "python"
    raw_stderr: str = ""

@dataclass
class FixAttempt:
    error: ParsedError
    fix_description: str
    patch_command: Optional[str] = None
    success: bool = False
    timestamp: float = field(default_factory=time.time)

class ErrorParser:
    """Parses Python error output."""
    TRACEBACK_PATTERN = re.compile(
        r'File "(.+?)", line (\d+)(?:, in .+)?\n\s+(.+)\n(\w+Error): (.+)',
        re.MULTILINE
    )
    
    @classmethod
    def parse(cls, stderr: str) -> ParsedError:
        match = cls.TRACEBACK_PATTERN.search(stderr)
        if match:
            return ParsedError(
                error_type=match.group(4),
                message=match.group(5),
                file_path=match.group(1),
                line_number=int(match.group(2)),
                stack_trace=stderr,
                raw_stderr=stderr
            )
        return ParsedError(error_type="UnknownError", message=stderr[:500], raw_stderr=stderr)

class AutonomousFix:
    """
    Autonomous error fixing for Dynamic Agent.
    Bridges LLM capabilities to fix execution errors in real-time.
    """
    def __init__(self, llm_provider: Optional[Callable] = None, max_retries: int = 2):
        self.llm = llm_provider
        self.max_retries = max_retries
        self.fix_history: List[FixAttempt] = []

    async def wrap_execution(self, func: Callable, *args, **kwargs) -> Any:
        """Wrap an async function with auto-fix logic."""
        attempt = 0
        while attempt <= self.max_retries:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                attempt += 1
                if attempt > self.max_retries or not self.llm:
                    raise e
                
                logger.warning(f"Execution failed (attempt {attempt}/{self.max_retries+1}): {e}")
                error = ErrorParser.parse(str(e))
                
                # Ask LLM for a fix strategy
                fix_suggestion = await self._get_fix_suggestion(error)
                if not fix_suggestion:
                    raise e
                
                # In a real implementation, we might apply a patch or change parameters
                # For now, we'll log the fix and retry
                logger.info(f"LLM suggested fix: {fix_suggestion}")
                # (Actual fixing logic would go here)
        
    async def _get_fix_suggestion(self, error: ParsedError) -> Optional[str]:
        if not self.llm: return None
        
        prompt = f"""An exploit script failed with the following error:
Error: {error.error_type}
Message: {error.message}
Stack Trace: {error.stack_trace}

Suggest a one-line fix for this error to make the exploitation successful."""
        
        try:
            return await self.llm(prompt)
        except:
            return None
