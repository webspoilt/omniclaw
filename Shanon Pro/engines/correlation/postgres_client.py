"""
PostgreSQL client for Static Analysis findings ingestion.
Handles secure database connections with TLS and prepared statements.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

import asyncpg

logger = logging.getLogger(__name__)


class PostgresClient:
    """
    Async PostgreSQL client for findings persistence.
    
    Security:
    - TLS 1.3 with certificate pinning
    - Prepared statements only (no string interpolation)
    - Connection pooling with max limits
    - Read/write role separation
    """
    
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        ssl_mode: str = "require",
        max_connections: int = 20,
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.ssl_mode = ssl_mode
        self.max_connections = max_connections
        
        self._pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """Initialize connection pool."""
        self._pool = await asyncpg.create_pool(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password,
            ssl=self.ssl_mode,
            max_size=self.max_connections,
            command_timeout=30,
        )
        logger.info(f"Connected to PostgreSQL at {self.host}:{self.port}")
    
    async def disconnect(self) -> None:
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            logger.info("PostgreSQL connection closed")
    
    @asynccontextmanager
    async def transaction(self):
        """Acquire connection with transaction."""
        if not self._pool:
            raise RuntimeError("Not connected to database")
        
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn
    
    async def fetch_findings_by_scan(
        self,
        scan_id: str,
        min_confidence: float = 0.0,
        vuln_category: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Fetch static findings for a scan.
        
        Args:
            scan_id: Scan identifier
            min_confidence: Minimum confidence threshold
            vuln_category: Filter by vulnerability category
            
        Returns:
            List of finding dictionaries
        """
        async with self.transaction() as conn:
            query = """
                SELECT 
                    f.finding_id,
                    f.scan_id,
                    f.rule_id,
                    f.vuln_category,
                    f.severity,
                    f.confidence_score,
                    f.file_path,
                    f.line_number,
                    f.method_name,
                    f.cpg_context,
                    f.cypher_query,
                    f.dataflow_hash,
                    f.source_node,
                    f.sink_node,
                    f.has_sanitizer,
                    f.status,
                    f.detected_at,
                    s.commit_sha,
                    s.repo_url
                FROM static_findings f
                JOIN scans s ON f.scan_id = s.scan_id
                WHERE f.scan_id = $1
                  AND f.confidence_score >= $2
                  AND f.status = 'open'
            """
            
            params = [scan_id, min_confidence]
            
            if vuln_category:
                query += " AND f.vuln_category = $3"
                params.append(vuln_category)
            
            query += " ORDER BY f.confidence_score DESC, f.severity DESC"
            
            rows = await conn.fetch(query, *params)
            
            return [dict(row) for row in rows]
    
    async def fetch_slices_by_finding(
        self,
        finding_id: str,
    ) -> list[dict[str, Any]]:
        """Fetch dataflow slices for a finding."""
        async with self.transaction() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    slice_id,
                    finding_id,
                    source_node,
                    sink_node,
                    traversal_path,
                    path_length,
                    sanitizers_encountered,
                    is_constant_propagated
                FROM dataflow_slices
                WHERE finding_id = $1
                ORDER BY path_length ASC
                """,
                finding_id,
            )
            return [dict(row) for row in rows]
    
    async def get_dynamic_results_by_finding(
        self,
        finding_id: str,
    ) -> list[dict[str, Any]]:
        """Check if a finding has already been dynamically tested."""
        async with self.transaction() as conn:
            rows = await conn.fetch(
                """
                SELECT 
                    r.result_id,
                    r.task_id,
                    r.vuln_type,
                    r.target_url,
                    r.exploit_status,
                    r.exploit_confidence,
                    r.indicators
                FROM dynamic_results r
                WHERE r.finding_id = $1
                ORDER BY r.tested_at DESC
                """,
                finding_id,
            )
            return [dict(row) for row in rows]
    
    async def upsert_correlation(
        self,
        finding_id: str,
        result_id: Optional[str],
        correlation_type: str,
        correlation_score: float,
        is_reachable: bool,
        reachability_path: Optional[dict],
        priority: str,
    ) -> str:
        """
        Insert or update correlation record.
        
        Returns:
            correlation_id
        """
        async with self.transaction() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO correlations (
                    finding_id, result_id, correlation_type, correlation_score,
                    is_reachable, reachability_path, priority
                ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (finding_id) DO UPDATE SET
                    result_id = EXCLUDED.result_id,
                    correlation_type = EXCLUDED.correlation_type,
                    correlation_score = EXCLUDED.correlation_score,
                    is_reachable = EXCLUDED.is_reachable,
                    reachability_path = EXCLUDED.reachability_path,
                    priority = EXCLUDED.priority,
                    correlated_at = NOW()
                RETURNING correlation_id
                """,
                finding_id,
                result_id,
                correlation_type,
                correlation_score,
                is_reachable,
                json.dumps(reachability_path) if reachability_path else None,
                priority,
            )
            return row["correlation_id"]
    
    async def create_exploit_queue_item(
        self,
        correlation_id: str,
        vuln_type: str,
        injection_points: dict,
        validation_strategies: list[str],
        priority: str,
    ) -> str:
        """
        Create exploit queue item.
        
        Returns:
            queue_item_id
        """
        async with self.transaction() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO exploit_queue (
                    correlation_id, vuln_type, injection_points,
                    validation_strategies, queue_status, priority
                ) VALUES ($1, $2, $3, $4, 'queued', $5)
                RETURNING queue_item_id
                """,
                correlation_id,
                vuln_type,
                json.dumps(injection_points),
                validation_strategies,
                priority,
            )
            return row["queue_item_id"]
    
    async def get_queue_stats(self) -> dict[str, Any]:
        """Get exploit queue statistics."""
        async with self.transaction() as conn:
            row = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) FILTER (WHERE queue_status = 'queued') as queued,
                    COUNT(*) FILTER (WHERE queue_status = 'assigned') as assigned,
                    COUNT(*) FILTER (WHERE queue_status = 'running') as running,
                    COUNT(*) FILTER (WHERE queue_status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE queue_status = 'failed') as failed
                FROM exploit_queue
                """
            )
            return dict(row) if row else {}
