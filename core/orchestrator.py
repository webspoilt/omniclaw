#!/usr/bin/env python3
"""
OmniClaw Hybrid Hive Orchestrator
Implements the Manager-Worker loop for multi-API AI orchestration
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OmniClaw.Orchestrator")


class TaskStatus(Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    PEER_REVIEW = "peer_review"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRECTED = "corrected"


class WorkerRole(Enum):
    RESEARCHER = "researcher"
    EXECUTOR = "executor"
    AUDITOR = "auditor"
    CREATIVE = "creative"
    ANALYST = "analyst"
    CODER = "coder"
    GENERAL = "general"


@dataclass
class SubTask:
    """Represents a sub-task in the Hybrid Hive system"""
    id: str
    description: str
    role: WorkerRole
    status: TaskStatus = TaskStatus.PENDING
    assigned_worker: Optional[str] = None
    result: Any = None
    error: Optional[str] = None
    peer_reviews: List[Dict] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    iteration_count: int = 0
    max_iterations: int = 3


@dataclass
class Task:
    """Represents a complex task to be executed by the Hybrid Hive"""
    id: str
    goal: str
    subtasks: List[SubTask] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    final_result: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class HybridHiveOrchestrator:
    """
    Main orchestrator implementing the Manager-Worker architecture
    Supports both multi-API and single-API modes
    """
    
    def __init__(self, api_configs: List[Dict[str, Any]], memory_db=None):
        """
        Initialize the Hybrid Hive Orchestrator
        
        Args:
            api_configs: List of API configurations (provider, key, model, etc.)
            memory_db: Vector database instance for persistent memory
        """
        self.api_configs = api_configs
        self.memory = memory_db
        self.workers: Dict[str, 'WorkerAgent'] = {}
        self.manager: Optional['ManagerAgent'] = None
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.results: Dict[str, Task] = {}
        self.executor = ThreadPoolExecutor(max_workers=20)
        self.running = False
        self.peer_review_enabled = True
        self.self_correction_enabled = True
        
        # Initialize components
        self._initialize_hive()
        
        logger.info(f"Hybrid Hive initialized with {len(api_configs)} API(s)")
    
    def _initialize_hive(self):
        """Initialize the Manager and Worker agents"""
        from .manager import ManagerAgent
        from .worker import WorkerAgent
        
        # Create Manager (uses first API or best available)
        manager_api = self._select_best_api_for_role(WorkerRole.GENERAL)
        self.manager = ManagerAgent(
            api_config=manager_api,
            orchestrator=self,
            memory=self.memory
        )
        
        # Create Workers based on available APIs
        if len(self.api_configs) == 1:
            # Single-API mode: Create iterative chain-of-thought worker
            logger.info("Single-API mode: Initializing Chain-of-Thought processor")
            worker = WorkerAgent(
                worker_id="cot_worker_001",
                role=WorkerRole.GENERAL,
                api_config=self.api_configs[0],
                memory=self.memory,
                mode="chain_of_thought"
            )
            self.workers["cot_worker_001"] = worker
        else:
            # Multi-API mode: Create specialized workers
            logger.info("Multi-API mode: Initializing specialized worker pool")
            roles = [WorkerRole.RESEARCHER, WorkerRole.EXECUTOR, WorkerRole.AUDITOR, 
                     WorkerRole.CREATIVE, WorkerRole.ANALYST, WorkerRole.CODER]
            
            for i, api_config in enumerate(self.api_configs):
                role = roles[i % len(roles)]
                worker_id = f"{role.value}_{i:03d}"
                worker = WorkerAgent(
                    worker_id=worker_id,
                    role=role,
                    api_config=api_config,
                    memory=self.memory,
                    mode="specialized"
                )
                self.workers[worker_id] = worker
                logger.info(f"Created worker: {worker_id} with role {role.value}")
    
    def _select_best_api_for_role(self, role: WorkerRole) -> Dict[str, Any]:
        """Select the best API configuration for a given role"""
        if not self.api_configs:
            raise ValueError("No API configurations provided")
        
        # For now, return first API. Can be enhanced with capability matching
        return self.api_configs[0]
    
    def _generate_task_id(self, goal: str) -> str:
        """Generate a unique task ID"""
        hash_input = f"{goal}{time.time()}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]
    
    def _generate_subtask_id(self, task_id: str, index: int) -> str:
        """Generate a unique sub-task ID"""
        return f"{task_id}_sub_{index:03d}"
    
    async def execute_goal(self, goal: str, context: Optional[Dict] = None) -> Task:
        """
        Execute a complex goal using the Hybrid Hive architecture
        
        Args:
            goal: The high-level goal to achieve
            context: Additional context for the task
            
        Returns:
            Task object with results
        """
        task_id = self._generate_task_id(goal)
        task = Task(
            id=task_id,
            goal=goal,
            context=context or {}
        )
        
        logger.info(f"Starting task {task_id}: {goal}")
        
        # Phase 1: Manager decomposes goal into sub-tasks
        subtasks = await self.manager.decompose_goal(goal, context)
        task.subtasks = subtasks
        
        # Phase 2: Assign and execute sub-tasks
        if len(self.api_configs) == 1:
            # Single-API: Sequential chain-of-thought execution
            await self._execute_single_api_mode(task)
        else:
            # Multi-API: Parallel worker execution with dependencies
            await self._execute_multi_api_mode(task)
        
        # Phase 3: Compile final result
        task.final_result = await self.manager.compile_results(task)
        task.completed_at = time.time()
        self.results[task_id] = task
        
        # Store in memory
        if self.memory:
            await self.memory.store_task(task)
        
        logger.info(f"Task {task_id} completed in {task.completed_at - task.created_at:.2f}s")
        return task
    
    async def _execute_single_api_mode(self, task: Task):
        """Execute task in single-API chain-of-thought mode"""
        worker = list(self.workers.values())[0]
        
        for subtask in task.subtasks:
            logger.info(f"Executing sub-task {subtask.id}: {subtask.description}")
            
            # Execute with iterative refinement
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    result = await worker.execute_subtask(subtask, task.context)
                    subtask.result = result
                    subtask.status = TaskStatus.COMPLETED
                    subtask.completed_at = time.time()
                    
                    # Self-review
                    review = await worker.self_review(subtask)
                    if review.get("needs_correction", False):
                        logger.info(f"Self-correction needed for {subtask.id}")
                        subtask.status = TaskStatus.CORRECTED
                        correction = await worker.correct_subtask(subtask, review)
                        subtask.result = correction
                    
                    break
                except Exception as e:
                    logger.error(f"Attempt {attempt + 1} failed for {subtask.id}: {e}")
                    if attempt == max_attempts - 1:
                        subtask.status = TaskStatus.FAILED
                        subtask.error = str(e)
                    else:
                        await asyncio.sleep(1)
    
    async def _execute_multi_api_mode(self, task: Task):
        """Execute task in multi-API parallel mode"""
        # Build dependency graph
        dependency_graph = self._build_dependency_graph(task.subtasks)
        
        # Execute in waves based on dependencies
        completed_subtasks = set()
        pending_subtasks = set(st.id for st in task.subtasks)
        
        while pending_subtasks:
            # Find sub-tasks with satisfied dependencies
            ready_subtasks = [
                st for st in task.subtasks 
                if st.id in pending_subtasks and 
                all(dep in completed_subtasks for dep in st.dependencies)
            ]
            
            if not ready_subtasks:
                # Deadlock detection
                logger.error("Dependency deadlock detected!")
                break
            
            # Execute ready sub-tasks in parallel
            tasks = []
            for subtask in ready_subtasks:
                worker = self._select_worker_for_subtask(subtask)
                tasks.append(self._execute_with_peer_review(worker, subtask, task.context))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for subtask, result in zip(ready_subtasks, results):
                pending_subtasks.remove(subtask.id)
                if not isinstance(result, Exception):
                    completed_subtasks.add(subtask.id)
    
    def _build_dependency_graph(self, subtasks: List[SubTask]) -> Dict[str, List[str]]:
        """Build a dependency graph for sub-tasks"""
        graph = {}
        for st in subtasks:
            graph[st.id] = st.dependencies
        return graph
    
    def _select_worker_for_subtask(self, subtask: SubTask) -> 'WorkerAgent':
        """Select the best worker for a sub-task based on role matching"""
        # Find workers with matching role
        matching_workers = [
            w for w in self.workers.values() 
            if w.role == subtask.role
        ]
        
        if matching_workers:
            # Select least busy worker
            return min(matching_workers, key=lambda w: w.current_load)
        
        # Fallback to any available worker
        return min(self.workers.values(), key=lambda w: w.current_load)
    
    async def _execute_with_peer_review(self, worker: 'WorkerAgent', 
                                        subtask: SubTask, 
                                        context: Dict) -> Any:
        """Execute sub-task with peer review and self-correction"""
        logger.info(f"Worker {worker.worker_id} executing {subtask.id}")
        
        # Execute
        subtask.status = TaskStatus.IN_PROGRESS
        subtask.assigned_worker = worker.worker_id
        
        try:
            result = await worker.execute_subtask(subtask, context)
            subtask.result = result
            subtask.status = TaskStatus.PEER_REVIEW
            
            # Peer review phase
            if self.peer_review_enabled and len(self.workers) > 1:
                reviewers = self._select_peer_reviewers(worker.worker_id)
                reviews = await self._conduct_peer_review(subtask, reviewers, context)
                subtask.peer_reviews = reviews
                
                # Check if corrections needed
                if self._needs_correction(reviews):
                    logger.info(f"Peer review flagged corrections for {subtask.id}")
                    correction = await worker.correct_subtask(subtask, reviews)
                    subtask.result = correction
                    subtask.status = TaskStatus.CORRECTED
                else:
                    subtask.status = TaskStatus.COMPLETED
            else:
                subtask.status = TaskStatus.COMPLETED
            
            subtask.completed_at = time.time()
            return subtask.result
            
        except Exception as e:
            logger.error(f"Execution failed for {subtask.id}: {e}")
            subtask.status = TaskStatus.FAILED
            subtask.error = str(e)
            raise
    
    def _select_peer_reviewers(self, exclude_worker_id: str, count: int = 2) -> List['WorkerAgent']:
        """Select peer reviewers excluding the original worker"""
        other_workers = [
            w for w in self.workers.values() 
            if w.worker_id != exclude_worker_id
        ]
        return other_workers[:count]
    
    async def _conduct_peer_review(self, subtask: SubTask, 
                                   reviewers: List['WorkerAgent'], 
                                   context: Dict) -> List[Dict]:
        """Conduct peer review of a sub-task result"""
        reviews = []
        
        for reviewer in reviewers:
            review = await reviewer.review_subtask(subtask, context)
            reviews.append({
                "reviewer": reviewer.worker_id,
                "review": review,
                "timestamp": time.time()
            })
        
        return reviews
    
    def _needs_correction(self, reviews: List[Dict]) -> bool:
        """Determine if corrections are needed based on peer reviews"""
        if not reviews:
            return False
        
        # Majority vote on corrections needed
        correction_votes = sum(
            1 for r in reviews 
            if r["review"].get("needs_correction", False)
        )
        return correction_votes > len(reviews) / 2
    
    async def start(self):
        """Start the orchestrator's main loop"""
        self.running = True
        logger.info("Hybrid Hive orchestrator started")
        
        while self.running:
            try:
                # Process any queued tasks
                if not self.task_queue.empty():
                    task_data = await self.task_queue.get()
                    await self.execute_goal(**task_data)
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Orchestrator loop error: {e}")
    
    def stop(self):
        """Stop the orchestrator"""
        self.running = False
        self.executor.shutdown(wait=True)
        logger.info("Hybrid Hive orchestrator stopped")
    
    def get_task_status(self, task_id: str) -> Optional[Task]:
        """Get the status of a task"""
        return self.results.get(task_id)
    
    def get_all_workers(self) -> List[Dict]:
        """Get information about all workers"""
        return [
            {
                "id": w.worker_id,
                "role": w.role.value,
                "load": w.current_load,
                "status": w.status
            }
            for w in self.workers.values()
        ]
