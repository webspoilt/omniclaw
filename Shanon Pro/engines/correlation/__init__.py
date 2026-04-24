# Shannon Pro - Stage 3: Correlation Engine
# Bridges static analysis findings to dynamic exploitation queues
#
# Architecture: Postgres Ingestion -> Reachability Analysis -> Priority Scoring -> Exploit Queue

from .correlation_engine import CorrelationEngine, CorrelationConfig
from .reachability import ReachabilityAnalyzer, PathResult
from .priority_scorer import PriorityScorer, PriorityResult
from .exploit_queue import ExploitQueueManager, QueueItem, QueuePriority
from .postgres_client import PostgresClient

__all__ = [
    "CorrelationEngine",
    "CorrelationConfig",
    "ReachabilityAnalyzer",
    "PathResult",
    "PriorityScorer",
    "PriorityResult",
    "ExploitQueueManager",
    "QueueItem",
    "QueuePriority",
    "PostgresClient",
]
