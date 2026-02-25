#!/usr/bin/env python3
"""
OmniClaw Autonomous Fix
Wraps command execution with automatic error parsing, LLM-driven
fix analysis, and retry logic. No human intervention required.
"""

import logging
import subprocess
import re
import time
import os
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("OmniClaw.AutonomousFix")


@dataclass
class ParsedError:
    """Structured representation of a parsed error"""
    error_type: str          # e.g. "SyntaxError", "ModuleNotFoundError"
    message: str             # The error message
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    column: Optional[int] = None
    stack_trace: str = ""
    language: str = "unknown"
    raw_stderr: str = ""


@dataclass
class FixAttempt:
    """Record of a fix attempt"""
    error: ParsedError
    fix_description: str
    patch_command: Optional[str] = None
    file_changes: Dict[str, str] = field(default_factory=dict)
    success: bool = False
    timestamp: float = field(default_factory=time.time)


@dataclass
class ExecutionResult:
    """Result of a command execution"""
    command: str
    returncode: int
    stdout: str
    stderr: str
    fix_attempts: List[FixAttempt] = field(default_factory=list)
    total_attempts: int = 1
    auto_fixed: bool = False


class ErrorParser:
    """Parses error output from various languages and tools"""
    
    # Python error patterns
    PYTHON_PATTERNS = {
        "traceback": re.compile(
            r'File "(.+?)", line (\d+)(?:, in .+)?\n\s+(.+)\n(\w+Error): (.+)',
            re.MULTILINE
        ),
        "syntax_error": re.compile(
            r'File "(.+?)", line (\d+)\n\s+(.+)\n\s+\^+\nSyntaxError: (.+)',
            re.MULTILINE
        ),
        "module_not_found": re.compile(
            r"ModuleNotFoundError: No module named '(.+?)'"
        ),
        "import_error": re.compile(
            r"ImportError: cannot import name '(.+?)' from '(.+?)'"
        ),
    }
    
    # Node.js error patterns
    NODE_PATTERNS = {
        "error": re.compile(
            r'(.+?):(\d+)\n.+\n\s+(.+)\n\n(\w+Error): (.+)',
            re.MULTILINE
        ),
        "module_not_found": re.compile(
            r"Error: Cannot find module '(.+?)'"
        ),
    }
    
    # Generic patterns
    GENERIC_PATTERNS = {
        "permission_denied": re.compile(r"[Pp]ermission denied"),
        "file_not_found": re.compile(r"No such file or directory: '?(.+?)'?$", re.MULTILINE),
        "command_not_found": re.compile(r"command not found: (.+)"),
    }
    
    @classmethod
    def parse(cls, stderr: str, stdout: str = "") -> ParsedError:
        """
        Parse error output and return a structured error.
        
        Args:
            stderr: Standard error output
            stdout: Standard output (sometimes has errors too)
            
        Returns:
            ParsedError with extracted information
        """
        combined = f"{stderr}\n{stdout}"
        
        # Try Python patterns first
        error = cls._try_python_patterns(stderr)
        if error:
            return error
        
        # Try Node.js patterns
        error = cls._try_node_patterns(stderr)
        if error:
            return error
        
        # Try generic patterns
        error = cls._try_generic_patterns(combined)
        if error:
            return error
        
        # Fallback: return raw error
        return ParsedError(
            error_type="UnknownError",
            message=stderr[:500] if stderr else stdout[:500],
            raw_stderr=stderr,
            language="unknown"
        )
    
    @classmethod
    def _try_python_patterns(cls, stderr: str) -> Optional[ParsedError]:
        """Try to parse Python-specific errors"""
        # Module not found
        match = cls.PYTHON_PATTERNS["module_not_found"].search(stderr)
        if match:
            return ParsedError(
                error_type="ModuleNotFoundError",
                message=f"No module named '{match.group(1)}'",
                language="python",
                raw_stderr=stderr
            )
        
        # Import error
        match = cls.PYTHON_PATTERNS["import_error"].search(stderr)
        if match:
            return ParsedError(
                error_type="ImportError",
                message=f"Cannot import '{match.group(1)}' from '{match.group(2)}'",
                language="python",
                raw_stderr=stderr
            )
        
        # Syntax error
        match = cls.PYTHON_PATTERNS["syntax_error"].search(stderr)
        if match:
            return ParsedError(
                error_type="SyntaxError",
                message=match.group(4),
                file_path=match.group(1),
                line_number=int(match.group(2)),
                language="python",
                stack_trace=stderr,
                raw_stderr=stderr
            )
        
        # General traceback
        match = cls.PYTHON_PATTERNS["traceback"].search(stderr)
        if match:
            return ParsedError(
                error_type=match.group(4),
                message=match.group(5),
                file_path=match.group(1),
                line_number=int(match.group(2)),
                language="python",
                stack_trace=stderr,
                raw_stderr=stderr
            )
        
        return None
    
    @classmethod
    def _try_node_patterns(cls, stderr: str) -> Optional[ParsedError]:
        """Try to parse Node.js-specific errors"""
        match = cls.NODE_PATTERNS["module_not_found"].search(stderr)
        if match:
            return ParsedError(
                error_type="ModuleNotFoundError",
                message=f"Cannot find module '{match.group(1)}'",
                language="javascript",
                raw_stderr=stderr
            )
        
        match = cls.NODE_PATTERNS["error"].search(stderr)
        if match:
            return ParsedError(
                error_type=match.group(4),
                message=match.group(5),
                file_path=match.group(1),
                line_number=int(match.group(2)),
                language="javascript",
                stack_trace=stderr,
                raw_stderr=stderr
            )
        
        return None
    
    @classmethod
    def _try_generic_patterns(cls, output: str) -> Optional[ParsedError]:
        """Try generic error patterns"""
        if cls.GENERIC_PATTERNS["permission_denied"].search(output):
            return ParsedError(
                error_type="PermissionError",
                message="Permission denied",
                raw_stderr=output
            )
        
        match = cls.GENERIC_PATTERNS["file_not_found"].search(output)
        if match:
            return ParsedError(
                error_type="FileNotFoundError",
                message=f"No such file or directory: {match.group(1)}",
                file_path=match.group(1),
                raw_stderr=output
            )
        
        match = cls.GENERIC_PATTERNS["command_not_found"].search(output)
        if match:
            return ParsedError(
                error_type="CommandNotFoundError",
                message=f"Command not found: {match.group(1)}",
                raw_stderr=output
            )
        
        return None


class AutonomousFix:
    """
    Autonomous command execution with auto-fix capability.
    
    Runs commands, parses failures, asks the LLM for fixes,
    applies them, and retries — all without human intervention.
    """
    
    def __init__(self, llm_call: Optional[Callable] = None, max_retries: int = 3,
                 sandbox_mode: bool = True):
        """
        Args:
            llm_call: Async function that takes a prompt string and returns LLM response
            max_retries: Maximum number of auto-fix retries
            sandbox_mode: If True, restrict dangerous operations
        """
        self.llm_call = llm_call
        self.max_retries = max_retries
        self.sandbox_mode = sandbox_mode
        self.fix_history: List[FixAttempt] = []
        self._error_signatures_seen: set = set()  # Prevent infinite loops
        
        logger.info(f"AutonomousFix initialized: max_retries={max_retries}, sandbox={sandbox_mode}")
    
    async def execute_with_autofix(self, command: str, cwd: str = ".",
                                    timeout: int = 60) -> ExecutionResult:
        """
        Execute a command with automatic error fixing and retry.
        
        Args:
            command: Shell command to execute
            cwd: Working directory
            timeout: Command timeout in seconds
            
        Returns:
            ExecutionResult with details of execution and any fix attempts
        """
        logger.info(f"Executing with autofix: {command}")
        
        result = self._run_command(command, cwd, timeout)
        execution = ExecutionResult(
            command=command,
            returncode=result["returncode"],
            stdout=result["stdout"],
            stderr=result["stderr"]
        )
        
        attempt = 0
        while result["returncode"] != 0 and attempt < self.max_retries:
            attempt += 1
            logger.info(f"Command failed (attempt {attempt}/{self.max_retries}), analyzing error...")
            
            # Parse the error
            error = ErrorParser.parse(result["stderr"], result["stdout"])
            
            # Check for infinite loop (same error signature)
            error_sig = f"{error.error_type}:{error.message}"
            if error_sig in self._error_signatures_seen:
                logger.warning(f"Same error seen again, stopping auto-fix to avoid loop: {error_sig}")
                break
            self._error_signatures_seen.add(error_sig)
            
            # Ask LLM for a fix
            fix = await self._analyze_and_fix(error, command, cwd)
            
            if fix is None:
                logger.warning("LLM could not suggest a fix")
                break
            
            # Apply the fix
            applied = await self._apply_fix(fix, cwd)
            if not applied:
                logger.warning("Could not apply the suggested fix")
                break
            
            execution.fix_attempts.append(fix)
            self.fix_history.append(fix)
            
            # Retry the original command
            result = self._run_command(command, cwd, timeout)
            execution.returncode = result["returncode"]
            execution.stdout = result["stdout"]
            execution.stderr = result["stderr"]
            execution.total_attempts = attempt + 1
            
            if result["returncode"] == 0:
                execution.auto_fixed = True
                fix.success = True
                logger.info(f"Auto-fix successful after {attempt} attempt(s)!")
        
        # Clear error signatures for next execution
        self._error_signatures_seen.clear()
        
        return execution
    
    def _run_command(self, command: str, cwd: str, timeout: int) -> Dict[str, Any]:
        """Run a shell command and capture output"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s"
            }
        except Exception as e:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    async def _analyze_and_fix(self, error: ParsedError, command: str,
                                cwd: str) -> Optional[FixAttempt]:
        """Ask the LLM to analyze the error and suggest a fix"""
        if not self.llm_call:
            logger.warning("No LLM configured for autonomous fix")
            return None
        
        # Read the relevant file if we know which file errored
        file_context = ""
        if error.file_path and os.path.exists(error.file_path):
            try:
                with open(error.file_path, 'r') as f:
                    lines = f.readlines()
                # Show context around the error line
                if error.line_number:
                    start = max(0, error.line_number - 10)
                    end = min(len(lines), error.line_number + 10)
                    file_context = f"\nFile: {error.file_path}\n"
                    for i in range(start, end):
                        marker = " >> " if i + 1 == error.line_number else "    "
                        file_context += f"{marker}{i + 1}: {lines[i]}"
            except Exception:
                pass
        
        prompt = f"""You are an autonomous debugging agent. A command failed and you must fix it.

COMMAND: {command}
WORKING DIR: {cwd}

ERROR TYPE: {error.error_type}
ERROR MESSAGE: {error.message}
LANGUAGE: {error.language}

FULL STDERR:
{error.raw_stderr[:3000]}
{file_context}

Analyze this error and provide a fix. Respond in this exact format:

FIX_DESCRIPTION: <one-line description of the fix>
FIX_TYPE: <"command" or "file_edit">
FIX_COMMAND: <shell command to run, if fix_type is "command">
FIX_FILE: <file path to edit, if fix_type is "file_edit">
FIX_FIND: <exact text to find in the file>
FIX_REPLACE: <replacement text>

If the error is a missing package, use FIX_TYPE: command with the install command.
If the error is a code bug, use FIX_TYPE: file_edit with the exact fix.
Only suggest ONE fix at a time."""
        
        try:
            response = await self.llm_call(prompt)
            return self._parse_fix_response(response, error)
        except Exception as e:
            logger.error(f"LLM fix analysis failed: {e}")
            return None
    
    def _parse_fix_response(self, response: str, error: ParsedError) -> Optional[FixAttempt]:
        """Parse the LLM's fix suggestion"""
        fix = FixAttempt(error=error, fix_description="")
        
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith("FIX_DESCRIPTION:"):
                fix.fix_description = line.split(":", 1)[1].strip()
            elif line.startswith("FIX_COMMAND:"):
                fix.patch_command = line.split(":", 1)[1].strip()
            elif line.startswith("FIX_FILE:"):
                current_file = line.split(":", 1)[1].strip()
                fix.file_changes[current_file] = ""
            elif line.startswith("FIX_FIND:"):
                fix.file_changes["__find__"] = line.split(":", 1)[1].strip()
            elif line.startswith("FIX_REPLACE:"):
                fix.file_changes["__replace__"] = line.split(":", 1)[1].strip()
        
        if fix.fix_description:
            return fix
        return None
    
    async def _apply_fix(self, fix: FixAttempt, cwd: str) -> bool:
        """Apply a fix attempt"""
        try:
            if fix.patch_command:
                # Safety check in sandbox mode
                if self.sandbox_mode and self._is_dangerous(fix.patch_command):
                    logger.warning(f"Blocked dangerous command in sandbox: {fix.patch_command}")
                    return False
                
                logger.info(f"Applying fix command: {fix.patch_command}")
                result = self._run_command(fix.patch_command, cwd, timeout=30)
                return result["returncode"] == 0
            
            elif "__find__" in fix.file_changes and "__replace__" in fix.file_changes:
                # File edit fix
                find_text = fix.file_changes["__find__"]
                replace_text = fix.file_changes["__replace__"]
                
                # Find the target file
                target_file = None
                for key in fix.file_changes:
                    if key not in ("__find__", "__replace__"):
                        target_file = key
                        break
                
                if target_file and os.path.exists(target_file):
                    with open(target_file, 'r') as f:
                        content = f.read()
                    
                    if find_text in content:
                        new_content = content.replace(find_text, replace_text, 1)
                        with open(target_file, 'w') as f:
                            f.write(new_content)
                        logger.info(f"Applied file edit to: {target_file}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            return False
    
    def _is_dangerous(self, command: str) -> bool:
        """Check if a command is potentially dangerous"""
        dangerous_patterns = [
            "rm -rf /", "rm -rf ~", "mkfs", "dd if=",
            ":(){", "chmod -R 777 /", "format", "> /dev/sda",
        ]
        cmd_lower = command.lower()
        return any(p in cmd_lower for p in dangerous_patterns)
    
    def get_fix_history(self) -> List[Dict[str, Any]]:
        """Get history of all fix attempts"""
        return [
            {
                "error_type": f.error.error_type,
                "error_message": f.error.message,
                "fix": f.fix_description,
                "success": f.success,
                "timestamp": f.timestamp
            }
            for f in self.fix_history
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get auto-fix statistics"""
        total = len(self.fix_history)
        successful = sum(1 for f in self.fix_history if f.success)
        return {
            "total_fix_attempts": total,
            "successful_fixes": successful,
            "success_rate": round(successful / total, 3) if total > 0 else 0,
            "max_retries": self.max_retries,
            "sandbox_mode": self.sandbox_mode,
        }
