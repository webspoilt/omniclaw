# Shannon Pro - Stage 3: Correlation Engine
# Bridges static analysis findings to dynamic exploitation queues
#
# Architecture: Postgres Ingestion -> Reachability Analysis -> Priority Scoring -> Exploit Queue

from .correlation_engine import CorrelationConfig, CorrelationEngine
from .exploit_queue import ExploitQueueManager, QueueItem, QueuePriority
from .postgres_client import PostgresClient
from .priority_scorer import PriorityResult, PriorityScorer
from .reachability import PathResult, ReachabilityAnalyzer

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
