#!/usr/bin/env python3
"""
OmniClaw Manager Agent
Responsible for goal decomposition, task assignment, and result compilation
"""

import json
import logging
from typing import Dict, List, Optional, Any
import time
import hashlib

from .orchestrator import SubTask, Task, TaskStatus, WorkerRole

logger = logging.getLogger("OmniClaw.Manager")


class ManagerAgent:
    """
    Manager Agent that orchestrates the Hybrid Hive
    - Decomposes complex goals into sub-tasks
    - Assigns tasks to appropriate workers
    - Compiles and validates final results
    """
    
    def __init__(self, api_config: Dict[str, Any], orchestrator, memory=None):
        self.api_config = api_config
        self.orchestrator = orchestrator
        self.memory = memory
        self.decomposition_history = []
        
        # Initialize API client based on provider - Replaced by Arbitrator
        self.api_client = None
        
        logger.info("Manager Agent initialized")
    
    def _initialize_api_client(self, api_config: Dict[str, Any]) -> Any:
        """Initialize the appropriate API client (Deprecated in favor of Arbitrator)"""
        return None
    
    async def decompose_goal(self, goal: str, context: Optional[Dict] = None) -> List[SubTask]:
        """
        Decompose a complex goal into sub-tasks
        
        Args:
            goal: The high-level goal
            context: Additional context
            
        Returns:
            List of SubTask objects
        """
        logger.info(f"Decomposing goal: {goal}")
        
        # Check memory for similar decompositions
        if self.memory:
            similar = await self.memory.find_similar_decompositions(goal)
            if similar:
                logger.info("Found similar decomposition in memory")
                return self._adapt_decomposition(similar, goal, context)
        
        # Use LLM to decompose the goal
        decomposition_prompt = self._build_decomposition_prompt(goal, context)
        
        try:
            decomposition = await self._call_llm(decomposition_prompt)
            subtasks_data = json.loads(decomposition)
            
            # Create SubTask objects
            subtasks = []
            for i, st_data in enumerate(subtasks_data.get("subtasks", [])):
                subtask_id = f"{hashlib.md5(goal.encode()).hexdigest()[:12]}_sub_{i:03d}"
                
                # Map string role to enum
                role_str = st_data.get("role", "general").lower()
                role = self._parse_role(role_str)
                
                subtask = SubTask(
                    id=subtask_id,
                    description=st_data["description"],
                    role=role,
                    dependencies=st_data.get("dependencies", []),
                    max_iterations=st_data.get("max_iterations", 3)
                )
                subtasks.append(subtask)
            
            # Store decomposition in history
            self.decomposition_history.append({
                "goal": goal,
                "subtasks": subtasks,
                "timestamp": time.time()
            })
            
            logger.info(f"Goal decomposed into {len(subtasks)} sub-tasks")
            return subtasks
            
        except Exception as e:
            logger.error(f"Decomposition failed: {e}")
            # Fallback to single sub-task
            return [SubTask(
                id=f"{hashlib.md5(goal.encode()).hexdigest()[:12]}_sub_000",
                description=goal,
                role=WorkerRole.GENERAL
            )]
    
    def _build_decomposition_prompt(self, goal: str, context: Optional[Dict]) -> str:
        """Build the prompt for goal decomposition"""
        context_str = json.dumps(context, indent=2) if context else "No additional context"
        
        return f"""You are the Manager Agent of OmniClaw, an AI orchestration system.
Your task is to decompose a complex goal into smaller, actionable sub-tasks.

Goal: {goal}

Context: {context_str}

Available Worker Roles:
- researcher: Gathers information, searches, analyzes data
- executor: Performs actions, executes code, makes changes
- auditor: Reviews, validates, checks for errors and risks
- creative: Generates content, designs, creative solutions
- analyst: Analyzes data, creates reports, finds patterns
- coder: Writes, reviews, and debugs code
- general: Handles general tasks

Decompose the goal into sub-tasks. For each sub-task, specify:
1. description: Clear, actionable description
2. role: The most appropriate worker role
3. dependencies: IDs of sub-tasks that must complete first (use indices 0, 1, 2...)
4. max_iterations: Maximum self-correction attempts (1-5)

Respond in JSON format:
{{
  "subtasks": [
    {{
      "description": "...",
      "role": "researcher",
      "dependencies": [],
      "max_iterations": 3
    }}
  ],
  "reasoning": "Brief explanation of decomposition strategy"
}}

Ensure sub-tasks are:
- Independent where possible (for parallel execution)
- Clearly defined with specific outcomes
- Ordered correctly with dependencies
- Appropriately sized (not too granular, not too large)"""
    
    def _parse_role(self, role_str: str) -> WorkerRole:
        """Parse role string to WorkerRole enum"""
        role_map = {
            "researcher": WorkerRole.RESEARCHER,
            "executor": WorkerRole.EXECUTOR,
            "auditor": WorkerRole.AUDITOR,
            "creative": WorkerRole.CREATIVE,
            "analyst": WorkerRole.ANALYST,
            "coder": WorkerRole.CODER,
            "general": WorkerRole.GENERAL
        }
        return role_map.get(role_str, WorkerRole.GENERAL)
    
    def _adapt_decomposition(self, similar: Dict, goal: str, context: Optional[Dict]) -> List[SubTask]:
        """Adapt a similar decomposition for the current goal"""
        # For now, return the similar decomposition
        # Can be enhanced with actual adaptation logic
        return similar.get("subtasks", [])
    
    async def compile_results(self, task: Task) -> Dict[str, Any]:
        """
        Compile sub-task results into final output
        
        Args:
            task: The completed task with sub-task results
            
        Returns:
            Compiled final result
        """
        logger.info(f"Compiling results for task {task.id}")
        
        # Build compilation prompt
        compilation_prompt = self._build_compilation_prompt(task)
        
        try:
            compilation = await self._call_llm(compilation_prompt)
            result = json.loads(compilation)
            return result
        except Exception as e:
            logger.error(f"Compilation failed: {e}")
            # Fallback to simple aggregation
            return {
                "goal": task.goal,
                "subtask_results": [
                    {"description": st.description, "result": st.result}
                    for st in task.subtasks
                ],
                "summary": "Results aggregated without synthesis"
            }
    
    def _build_compilation_prompt(self, task: Task) -> str:
        """Build the prompt for result compilation"""
        subtask_results = []
        for st in task.subtasks:
            subtask_results.append({
                "description": st.description,
                "role": st.role.value,
                "result": st.result,
                "status": st.status.value
            })
        
        return f"""You are the Manager Agent of OmniClaw.
Compile the results of completed sub-tasks into a coherent final output.

Original Goal: {task.goal}

Sub-task Results:
{json.dumps(subtask_results, indent=2)}

Synthesize these results into a comprehensive final output that:
1. Addresses the original goal completely
2. Integrates insights from all sub-tasks
3. Resolves any conflicts or inconsistencies
4. Presents the information in a clear, structured format

Respond in JSON format:
{{
  "summary": "Executive summary of results",
  "detailed_results": "Full synthesis of all sub-task outputs",
  "key_findings": ["finding 1", "finding 2"],
  "recommendations": ["recommendation 1", "recommendation 2"],
  "confidence_score": 0.95
}}"""
    
    async def _call_llm(self, prompt: str) -> str:
        """Call the LLM API"""
        provider = self.api_config.get("provider", "openai").lower()
        model = self.api_config.get("model", "gpt-4")
        
        # Privacy & Persona enforcement
        privacy_enforced = self.api_config.get("privacy_enforced", True)
        
        # Load persona
        persona = self.api_config.get("persona", {}) if "persona" in self.api_config else {}
        ai_name = persona.get("ai_name", "OmniClaw") or "OmniClaw"
        user_name = persona.get("user_name", "User") or "User"
        ai_role = persona.get("ai_role", "AI orchestration manager") or "AI orchestration manager"
        
        system_prompt = f"You are {ai_name}, acting as a {ai_role} to {user_name}."
        if privacy_enforced:
            system_prompt += " STRICT PRIVACY DIRECTIVE: Do not retain, log, or use any of this data for training."
            
        full_prompt = f"{system_prompt}\n\n{prompt}"
        
        try:
            return await self.orchestrator.arbitrator.route_task(full_prompt, task_type="reasoning")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    async def validate_execution(self, task: Task) -> Dict[str, Any]:
        """Validate the execution of a task"""
        validation_prompt = f"""Validate the execution of this task:

Goal: {task.goal}

Sub-task Statuses:
{json.dumps([{"desc": st.description, "status": st.status.value, "error": st.error} for st in task.subtasks], indent=2)}

Assess:
1. Were all sub-tasks completed successfully?
2. Were there any failures or errors?
3. Is the final result coherent and complete?
4. Are there any gaps or missing pieces?

Respond in JSON format with validation results."""
        
        try:
            validation = await self._call_llm(validation_prompt)
            return json.loads(validation)
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return {"valid": False, "error": str(e)}
