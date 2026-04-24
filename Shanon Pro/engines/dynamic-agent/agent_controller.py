"""
Agent Controller — Orchestrates dynamic pentesting agents with browser farm management.

Manages:
- Agent lifecycle (start, execute, stop)
- Browser farm scaling
- Task queue consumption
- Evidence collection and storage
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from .injection_agent import AgentConfig, InjectionAgent
from .models import ExploitResult, ExploitTask, ExploitStatus

logger = logging.getLogger(__name__)


@dataclass
class ControllerConfig:
    """Configuration for Agent Controller."""
    # Concurrency
    max_concurrent_agents: int = 5
    max_browsers_per_agent: int = 3
    
    # Queue
    queue_poll_interval_seconds: int = 5
    task_timeout_seconds: int = 300
    max_retries: int = 3
    
    # Evidence
    evidence_storage_path: str = "/tmp/shannon/evidence"
    
    # Health
    health_check_interval_seconds: int = 30
    browser_restart_after_tasks: int = 50  # Restart browser every N tasks


class AgentController:
    """
    Central controller for dynamic pentesting operations.
    
    Manages a pool of InjectionAgents, each with their own browser context.
    Consumes tasks from the Exploit Queue (Redis Streams) and distributes
    them to available agents.
    
    Usage:
        controller = AgentController(config)
        await controller.start()
        result = await controller.submit_task(task)
        await controller.stop()
    """
    
    def __init__(self, config: ControllerConfig):
        self.config = config
        
        # Agent pool
        self._agents: dict[str, InjectionAgent] = {}
        self._agent_tasks: dict[str, asyncio.Task] = {}
        self._agent_busy: dict[str, bool] = {}
        
        # Results
        self._results: dict[str, ExploitResult] = {}
        self._completed_count: int = 0
        self._failed_count: int = 0
        
        # State
        self._running: bool = False
        self._shutdown_event: Optional[asyncio.Event] = None
    
    async def start(self) -> None:
        """Start the controller and initialize agent pool."""
        self._running = True
        self._shutdown_event = asyncio.Event()
        
        # Pre-warm browser instances
        for i in range(self.config.max_concurrent_agents):
            agent_id = f"agent-{i}"
            agent_config = AgentConfig(
                headless=True,
                proxy_url=None,  # Would be mitmproxy for traffic capture
                record_video=True,
                capture_har=True,
            )
            
            agent = InjectionAgent(agent_config)
            await agent.start()
            
            self._agents[agent_id] = agent
            self._agent_busy[agent_id] = False
        
        logger.info(
            f"Agent Controller started with {len(self._agents)} agents"
        )
    
    async def stop(self) -> None:
        """Stop all agents and cleanup."""
        self._running = False
        
        # Cancel all running tasks
        for task in self._agent_tasks.values():
            if not task.done():
                task.cancel()
        
        # Wait for graceful shutdown
        await asyncio.sleep(2)
        
        # Stop all agents
        for agent in self._agents.values():
            await agent.stop()
        
        self._agents.clear()
        self._agent_tasks.clear()
        
        if self._shutdown_event:
            self._shutdown_event.set()
        
        logger.info("Agent Controller stopped")
    
    async def submit_task(self, task: ExploitTask) -> ExploitResult:
        """
        Submit a single task for execution.
        
        Args:
            task: Exploit task to execute
            
        Returns:
            ExploitResult with validation status
        """
        # Wait for available agent
        agent_id = await self._acquire_agent()
        
        try:
            self._agent_busy[agent_id] = True
            agent = self._agents[agent_id]
            
            logger.info(f"Task {task.task_id} assigned to {agent_id}")
            
            # Execute with timeout
            result = await asyncio.wait_for(
                agent.execute(task),
                timeout=self.config.task_timeout_seconds,
            )
            
            self._results[task.task_id] = result
            self._completed_count += 1
            
            if result.status == ExploitStatus.VALIDATED:
                logger.info(
                    f"Task {task.task_id}: VULNERABILITY CONFIRMED"
                )
            else:
                logger.info(
                    f"Task {task.task_id}: Not validated ({result.status.value})"
                )
            
            return result
            
        except asyncio.TimeoutError:
            logger.warning(f"Task {task.task_id} timed out")
            result = ExploitResult(
                task_id=task.task_id,
                finding_id=task.finding_id,
                status=ExploitStatus.TIMEOUT,
                summary="Task timed out",
            )
            self._failed_count += 1
            return result
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            result = ExploitResult(
                task_id=task.task_id,
                finding_id=task.finding_id,
                status=ExploitStatus.ERROR,
                summary=f"Error: {str(e)}",
            )
            self._failed_count += 1
            return result
            
        finally:
            self._agent_busy[agent_id] = False
    
    async def submit_tasks_batch(
        self,
        tasks: list[ExploitTask],
    ) -> list[ExploitResult]:
        """
        Submit multiple tasks with controlled concurrency.
        
        Args:
            tasks: List of exploit tasks
            
        Returns:
            List of ExploitResults in same order
        """
        semaphore = asyncio.Semaphore(self.config.max_concurrent_agents)
        
        async def execute_with_limit(task: ExploitTask) -> ExploitResult:
            async with semaphore:
                return await self.submit_task(task)
        
        results = await asyncio.gather(
            *[execute_with_limit(t) for t in tasks],
            return_exceptions=True,
        )
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ExploitResult(
                    task_id=tasks[i].task_id,
                    finding_id=tasks[i].finding_id,
                    status=ExploitStatus.ERROR,
                    summary=f"Batch execution error: {str(result)}",
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def _acquire_agent(self) -> str:
        """Wait for and return an available agent ID."""
        while True:
            for agent_id, busy in self._agent_busy.items():
                if not busy:
                    return agent_id
            
            # Wait and retry
            await asyncio.sleep(0.5)
    
    def get_metrics(self) -> dict[str, Any]:
        """Get controller performance metrics."""
        return {
            "agents_total": len(self._agents),
            "agents_busy": sum(1 for b in self._agent_busy.values() if b),
            "agents_available": sum(1 for b in self._agent_busy.values() if not b),
            "tasks_completed": self._completed_count,
            "tasks_failed": self._failed_count,
            "success_rate": (
                self._completed_count / (self._completed_count + self._failed_count)
                if (self._completed_count + self._failed_count) > 0 else 0
            ),
        }
    
    async def health_check(self) -> dict[str, Any]:
        """Health check all agents."""
        health = {
            "controller": "healthy" if self._running else "stopped",
            "agents": {},
        }
        
        for agent_id, agent in self._agents.items():
            try:
                # Check if browser is still responsive
                # This would need a ping method on InjectionAgent
                health["agents"][agent_id] = "healthy"
            except Exception as e:
                health["agents"][agent_id] = f"unhealthy: {e}"
        
        return health
