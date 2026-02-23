#!/usr/bin/env python3
"""
OmniClaw Worker Agent
Executes sub-tasks with role-specific capabilities and self-correction
"""

import json
import logging
from typing import Dict, List, Optional, Any
import time
import asyncio

from .orchestrator import SubTask, TaskStatus, WorkerRole

logger = logging.getLogger("OmniClaw.Worker")


class WorkerAgent:
    """
    Worker Agent that executes sub-tasks
    - Specialized by role (researcher, executor, auditor, etc.)
    - Supports both chain-of-thought and specialized modes
    - Includes self-correction and peer review capabilities
    """
    
    def __init__(self, worker_id: str, role: WorkerRole, 
                 api_config: Dict[str, Any], memory=None, mode: str = "specialized"):
        self.worker_id = worker_id
        self.role = role
        self.api_config = api_config
        self.memory = memory
        self.mode = mode  # "chain_of_thought" or "specialized"
        
        # Execution state
        self.current_load = 0
        self.status = "idle"
        self.execution_history = []
        
        # Initialize API client
        self.api_client = self._initialize_api_client(api_config)
        
        # Role-specific tools
        self.tools = self._initialize_tools()
        
        logger.info(f"Worker {worker_id} initialized with role {role.value} in {mode} mode")
    
    def _initialize_api_client(self, api_config: Dict[str, Any]) -> Any:
        """Initialize the appropriate API client"""
        provider = api_config.get("provider", "openai").lower()
        
        if provider == "openai":
            from openai import AsyncOpenAI
            return AsyncOpenAI(api_key=api_config["key"])
        elif provider == "anthropic":
            from anthropic import AsyncAnthropic
            return AsyncAnthropic(api_key=api_config["key"])
        elif provider == "google":
            import google.generativeai as genai
            genai.configure(api_key=api_config["key"])
            return genai
        elif provider == "ollama":
            return {"base_url": api_config.get("base_url", "http://localhost:11434")}
        else:
            raise ValueError(f"Unsupported API provider: {provider}")
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """Initialize role-specific tools"""
        tools = {}
        
        if self.role == WorkerRole.RESEARCHER:
            tools["web_search"] = self._web_search
            tools["data_extraction"] = self._data_extraction
            
        elif self.role == WorkerRole.EXECUTOR:
            tools["shell_execute"] = self._shell_execute
            tools["file_operation"] = self._file_operation
            tools["browser_control"] = self._browser_control
            
        elif self.role == WorkerRole.AUDITOR:
            tools["code_review"] = self._code_review
            tools["security_scan"] = self._security_scan
            
        elif self.role == WorkerRole.CODER:
            tools["code_generate"] = self._code_generate
            tools["code_debug"] = self._code_debug
            tools["test_generate"] = self._test_generate
            
        elif self.role == WorkerRole.ANALYST:
            tools["data_analysis"] = self._data_analysis
            tools["report_generate"] = self._report_generate
            
        elif self.role == WorkerRole.CREATIVE:
            tools["content_generate"] = self._content_generate
            tools["design_concept"] = self._design_concept
        
        # All workers get these
        tools["memory_search"] = self._memory_search
        tools["memory_store"] = self._memory_store
        
        return tools
    
    async def execute_subtask(self, subtask: SubTask, context: Dict) -> Any:
        """
        Execute a sub-task
        
        Args:
            subtask: The sub-task to execute
            context: Task context
            
        Returns:
            Execution result
        """
        logger.info(f"Worker {self.worker_id} executing: {subtask.description}")
        
        self.status = "executing"
        self.current_load += 1
        start_time = time.time()
        
        try:
            if self.mode == "chain_of_thought":
                result = await self._execute_chain_of_thought(subtask, context)
            else:
                result = await self._execute_specialized(subtask, context)
            
            execution_time = time.time() - start_time
            
            # Record execution
            self.execution_history.append({
                "subtask_id": subtask.id,
                "description": subtask.description,
                "result": result,
                "execution_time": execution_time,
                "timestamp": time.time()
            })
            
            self.status = "idle"
            self.current_load -= 1
            
            return result
            
        except Exception as e:
            self.status = "error"
            self.current_load -= 1
            logger.error(f"Execution failed: {e}")
            raise
    
    async def _execute_chain_of_thought(self, subtask: SubTask, context: Dict) -> Any:
        """Execute using chain-of-thought reasoning"""
        cot_prompt = f"""You are an AI agent executing a task step by step.

Task: {subtask.description}

Context: {json.dumps(context, indent=2)}

Think through this task carefully:
1. Break down your approach into clear steps
2. Execute each step methodically
3. Verify your work at each stage
4. Provide the final result

Use this format:
THOUGHT: [Your reasoning about the task]
ACTION: [What you need to do]
OBSERVATION: [Result of the action]
...
FINAL_ANSWER: [Your complete final result]

Be thorough and check for errors."""
        
        response = await self._call_llm(cot_prompt)
        
        # Extract final answer
        if "FINAL_ANSWER:" in response:
            return response.split("FINAL_ANSWER:")[1].strip()
        return response
    
    async def _execute_specialized(self, subtask: SubTask, context: Dict) -> Any:
        """Execute using role-specific specialization"""
        # Build role-specific prompt
        role_prompt = self._build_role_prompt(subtask, context)
        
        # Execute with potential tool use
        response = await self._call_llm(role_prompt)
        
        # Check if tool use is needed
        if "TOOL:" in response:
            return await self._handle_tool_use(response, subtask, context)
        
        return response
    
    def _build_role_prompt(self, subtask: SubTask, context: Dict) -> str:
        """Build role-specific execution prompt"""
        base_prompt = f"""You are a {self.role.value.upper()} agent in the OmniClaw system.

Task: {subtask.description}

Context: {json.dumps(context, indent=2)}

"""
        
        role_instructions = {
            WorkerRole.RESEARCHER: """Your role is to research and gather information.
- Search for accurate, up-to-date information
- Analyze multiple sources
- Provide well-sourced, factual responses
- Use TOOL:web_search if you need to search the web""",
            
            WorkerRole.EXECUTOR: """Your role is to execute actions and perform tasks.
- You can execute shell commands, manage files, and control browsers
- Be careful and verify before making changes
- Report exactly what was done
- Use TOOL:shell_execute or TOOL:file_operation as needed""",
            
            WorkerRole.AUDITOR: """Your role is to review and validate work.
- Check for errors, bugs, and security issues
- Verify correctness and completeness
- Identify potential risks
- Provide constructive feedback""",
            
            WorkerRole.CODER: """Your role is to write and debug code.
- Write clean, well-documented code
- Follow best practices
- Include error handling
- Test your code when possible""",
            
            WorkerRole.ANALYST: """Your role is to analyze data and create reports.
- Find patterns and insights
- Present data clearly
- Support conclusions with evidence
- Create actionable recommendations""",
            
            WorkerRole.CREATIVE: """Your role is to generate creative content.
- Be original and innovative
- Consider user preferences
- Iterate based on feedback
- Deliver polished outputs""",
            
            WorkerRole.GENERAL: """Your role is to handle general tasks.
- Be adaptable and thorough
- Ask for clarification when needed
- Provide complete solutions"""
        }
        
        return base_prompt + role_instructions.get(self.role, "")
    
    async def _handle_tool_use(self, response: str, subtask: SubTask, context: Dict) -> Any:
        """Handle tool use requests from the LLM"""
        # Parse tool call
        lines = response.split("\n")
        tool_name = None
        tool_params = {}
        
        for line in lines:
            if line.startswith("TOOL:"):
                tool_name = line.replace("TOOL:", "").strip()
            elif line.startswith("PARAMS:"):
                try:
                    tool_params = json.loads(line.replace("PARAMS:", "").strip())
                except:
                    pass
        
        if tool_name and tool_name in self.tools:
            tool_result = await self.tools[tool_name](**tool_params)
            
            # Continue with tool result
            continuation_prompt = f"""You used tool {tool_name} and got:
{json.dumps(tool_result, indent=2)}

Continue with your task and provide the FINAL_ANSWER."""
            
            final_response = await self._call_llm(continuation_prompt)
            
            if "FINAL_ANSWER:" in final_response:
                return final_response.split("FINAL_ANSWER:")[1].strip()
            return final_response
        
        return response
    
    async def self_review(self, subtask: SubTask) -> Dict[str, Any]:
        """Perform self-review of completed work"""
        review_prompt = f"""Review your work on this task:

Task: {subtask.description}

Your Result: {json.dumps(subtask.result, indent=2)}

Evaluate:
1. Is the result complete and correct?
2. Are there any errors or issues?
3. Could the quality be improved?
4. Are there any edge cases not handled?

Respond in JSON:
{{
  "needs_correction": true/false,
  "issues": ["issue 1", "issue 2"],
  "suggestions": ["suggestion 1", "suggestion 2"]
}}"""
        
        try:
            response = await self._call_llm(review_prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Self-review failed: {e}")
            return {"needs_correction": False, "issues": [], "suggestions": []}
    
    async def review_subtask(self, subtask: SubTask, context: Dict) -> Dict[str, Any]:
        """Peer review another worker's sub-task"""
        review_prompt = f"""You are reviewing work done by another agent.

Original Task: {subtask.description}

Result: {json.dumps(subtask.result, indent=2)}

Worker Role: {subtask.role.value}

Provide a thorough review:
1. Accuracy: Is the result correct?
2. Completeness: Does it address all requirements?
3. Quality: Is the work well-done?
4. Issues: Any bugs, errors, or problems?
5. Improvements: Suggestions for better results?

Respond in JSON:
{{
  "needs_correction": true/false,
  "accuracy_score": 0-1,
  "completeness_score": 0-1,
  "quality_score": 0-1,
  "issues": ["issue 1"],
  "improvements": ["suggestion 1"],
  "confidence": 0-1
}}"""
        
        try:
            response = await self._call_llm(review_prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Peer review failed: {e}")
            return {"needs_correction": False, "confidence": 0.5}
    
    async def correct_subtask(self, subtask: SubTask, review: Any) -> Any:
        """Correct a sub-task based on review feedback"""
        correction_prompt = f"""Correct the following task based on review feedback:

Original Task: {subtask.description}

Current Result: {json.dumps(subtask.result, indent=2)}

Review Feedback: {json.dumps(review, indent=2)}

Provide the corrected result addressing all issues.

Respond with the complete corrected output."""
        
        try:
            response = await self._call_llm(correction_prompt)
            return response
        except Exception as e:
            logger.error(f"Correction failed: {e}")
            return subtask.result
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM API"""
        provider = self.api_config.get("provider", "openai").lower()
        model = self.api_config.get("model", "gpt-4")
        
        try:
            if provider == "openai":
                response = await self.api_client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": f"You are a {self.role.value} AI agent."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3
                )
                return response.choices[0].message.content
                
            elif provider == "anthropic":
                response = await self.api_client.messages.create(
                    model=model,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
            elif provider == "google":
                model = self.api_client.GenerativeModel(model)
                response = await model.generate_content_async(prompt)
                return response.text
                
            elif provider == "ollama":
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.api_client['base_url']}/api/generate",
                        json={
                            "model": model,
                            "prompt": prompt,
                            "stream": False
                        }
                    ) as resp:
                        data = await resp.json()
                        return data["response"]
                        
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    # Tool implementations
    async def _web_search(self, query: str, num_results: int = 5) -> Dict:
        """Search the web"""
        # Placeholder - integrate with search API
        return {"query": query, "results": [], "status": "placeholder"}
    
    async def _data_extraction(self, url: str) -> Dict:
        """Extract data from a URL"""
        return {"url": url, "data": {}, "status": "placeholder"}
    
    async def _shell_execute(self, command: str, timeout: int = 30) -> Dict:
        """Execute a shell command"""
        import subprocess
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            return {
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "Command timed out", "command": command}
        except Exception as e:
            return {"error": str(e), "command": command}
    
    async def _file_operation(self, operation: str, path: str, content: str = None) -> Dict:
        """Perform file operations"""
        try:
            if operation == "read":
                with open(path, 'r') as f:
                    return {"content": f.read(), "path": path}
            elif operation == "write":
                with open(path, 'w') as f:
                    f.write(content)
                return {"status": "written", "path": path}
            elif operation == "exists":
                import os
                return {"exists": os.path.exists(path), "path": path}
        except Exception as e:
            return {"error": str(e), "path": path}
    
    async def _browser_control(self, action: str, url: str = None) -> Dict:
        """Control browser instances"""
        return {"action": action, "url": url, "status": "placeholder"}
    
    async def _code_review(self, code: str, language: str = "python") -> Dict:
        """Review code"""
        return {"language": language, "issues": [], "suggestions": []}
    
    async def _security_scan(self, target: str) -> Dict:
        """Perform security scan"""
        return {"target": target, "vulnerabilities": [], "status": "placeholder"}
    
    async def _code_generate(self, requirements: str, language: str = "python") -> Dict:
        """Generate code"""
        return {"language": language, "code": "", "status": "placeholder"}
    
    async def _code_debug(self, code: str, error: str) -> Dict:
        """Debug code"""
        return {"fixed_code": "", "explanation": "", "status": "placeholder"}
    
    async def _test_generate(self, code: str, language: str = "python") -> Dict:
        """Generate tests"""
        return {"language": language, "tests": "", "status": "placeholder"}
    
    async def _data_analysis(self, data: Dict, analysis_type: str = "general") -> Dict:
        """Analyze data"""
        return {"analysis_type": analysis_type, "results": {}, "status": "placeholder"}
    
    async def _report_generate(self, data: Dict, format: str = "markdown") -> Dict:
        """Generate report"""
        return {"format": format, "report": "", "status": "placeholder"}
    
    async def _content_generate(self, prompt: str, content_type: str = "text") -> Dict:
        """Generate creative content"""
        return {"content_type": content_type, "content": "", "status": "placeholder"}
    
    async def _design_concept(self, requirements: str) -> Dict:
        """Generate design concept"""
        return {"concept": "", "elements": [], "status": "placeholder"}
    
    async def _memory_search(self, query: str, limit: int = 5) -> Dict:
        """Search memory"""
        if self.memory:
            results = await self.memory.search(query, limit)
            return {"results": results, "status": "success"}
        return {"results": [], "status": "no_memory"}
    
    async def _memory_store(self, key: str, value: Any) -> Dict:
        """Store in memory"""
        if self.memory:
            await self.memory.store(key, value)
            return {"status": "stored"}
        return {"status": "no_memory"}
