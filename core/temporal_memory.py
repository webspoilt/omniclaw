#!/usr/bin/env python3
"""
OmniClaw Temporal Context Windows
Cross-session work snapshots that persist across restarts.
Resume exactly where you left off, even weeks later.
"""

import logging
import json
import time
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger("OmniClaw.TemporalMemory")


@dataclass
class WorkSnapshot:
    """A point-in-time snapshot of work state"""
    snapshot_id: str
    project: str
    task: str
    state: Dict[str, Any]
    files_modified: List[str] = field(default_factory=list)
    environment: Dict[str, Any] = field(default_factory=dict)
    partial_results: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    resumed_at: Optional[float] = None
    status: str = "interrupted"  # "interrupted", "completed", "resumed"


class TemporalContext:
    """
    Cross-session work snapshot system.
    
    Saves and restores complete work context, enabling seamless
    resumption of interrupted tasks — even weeks later.
    """
    
    def __init__(self, storage_dir: str = "./memory_db/snapshots",
                 memory=None):
        """
        Args:
            storage_dir: Directory for storing snapshots
            memory: Optional VectorMemory instance for semantic search
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.memory = memory
        self._snapshot_count = 0
        
        # Load existing snapshot index
        self.index: Dict[str, List[str]] = {}  # project -> [snapshot_ids]
        self._load_index()
        
        logger.info(f"TemporalContext initialized: {self.storage_dir}")
    
    def save_snapshot(self, project: str, task: str, state: Dict[str, Any],
                      files_modified: List[str] = None,
                      partial_results: Dict[str, Any] = None,
                      notes: str = "",
                      tags: List[str] = None) -> str:
        """
        Save a work snapshot with full context.
        
        Args:
            project: Project name/identifier
            task: Current task description
            state: Complete state dictionary
            files_modified: List of files that were modified
            partial_results: Any partial results to preserve
            notes: Free-text notes about current state
            tags: Tags for categorization
            
        Returns:
            Snapshot ID
        """
        self._snapshot_count += 1
        snapshot_id = f"snap_{project}_{self._snapshot_count}_{int(time.time())}"
        
        snapshot = WorkSnapshot(
            snapshot_id=snapshot_id,
            project=project,
            task=task,
            state=state,
            files_modified=files_modified or [],
            environment=self._capture_environment(),
            partial_results=partial_results or {},
            notes=notes,
            tags=tags or [],
        )
        
        # Save to disk
        snapshot_path = self.storage_dir / f"{snapshot_id}.json"
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(snapshot), f, indent=2, default=str)
        
        # Update index
        if project not in self.index:
            self.index[project] = []
        self.index[project].append(snapshot_id)
        self._save_index()
        
        # Store in vector memory for semantic search
        if self.memory:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(
                        self.memory.store(
                            snapshot_id,
                            {"task": task, "notes": notes, "project": project},
                            memory_type="task"
                        )
                    )
                else:
                    loop.run_until_complete(
                        self.memory.store(
                            snapshot_id,
                            {"task": task, "notes": notes, "project": project},
                            memory_type="task"
                        )
                    )
            except Exception as e:
                logger.debug(f"Could not store snapshot in vector memory: {e}")
        
        logger.info(f"Snapshot saved: {snapshot_id} — {task}")
        return snapshot_id
    
    def resume(self, project: str) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Resume the most recent interrupted work for a project.
        
        Args:
            project: Project name/identifier
            
        Returns:
            Tuple of (last_task_description, full_context) or (None, None) if no snapshots
        """
        if project not in self.index or not self.index[project]:
            logger.info(f"No snapshots found for project: {project}")
            return None, None
        
        # Get the most recent snapshot
        latest_id = self.index[project][-1]
        snapshot = self._load_snapshot(latest_id)
        
        if snapshot is None:
            return None, None
        
        # Mark as resumed
        snapshot["resumed_at"] = time.time()
        snapshot["status"] = "resumed"
        self._update_snapshot(latest_id, snapshot)
        
        context = {
            "task": snapshot["task"],
            "state": snapshot["state"],
            "files_modified": snapshot["files_modified"],
            "partial_results": snapshot["partial_results"],
            "notes": snapshot["notes"],
            "tags": snapshot["tags"],
            "snapshot_age": time.time() - snapshot["created_at"],
            "snapshot_age_human": self._human_time_delta(time.time() - snapshot["created_at"]),
            "environment_diff": self._diff_environment(snapshot.get("environment", {})),
        }
        
        logger.info(f"Resuming project '{project}': {snapshot['task']} "
                    f"(snapshot from {context['snapshot_age_human']} ago)")
        
        return snapshot["task"], context
    
    def get_timeline(self, project: str) -> List[Dict[str, Any]]:
        """
        Get chronological history of all work on a project.
        
        Args:
            project: Project name/identifier
            
        Returns:
            List of snapshot summaries, oldest first
        """
        if project not in self.index:
            return []
        
        timeline = []
        for snap_id in self.index[project]:
            snapshot = self._load_snapshot(snap_id)
            if snapshot:
                timeline.append({
                    "snapshot_id": snap_id,
                    "task": snapshot["task"],
                    "status": snapshot["status"],
                    "created_at": snapshot["created_at"],
                    "created_human": time.strftime(
                        '%Y-%m-%d %H:%M:%S',
                        time.localtime(snapshot["created_at"])
                    ),
                    "files_count": len(snapshot.get("files_modified", [])),
                    "notes": snapshot.get("notes", ""),
                    "tags": snapshot.get("tags", []),
                })
        
        return timeline
    
    async def find_related(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search snapshots by semantic similarity.
        
        Args:
            query: Search query
            limit: Max results
            
        Returns:
            List of matching snapshot summaries
        """
        if self.memory:
            results = await self.memory.search(query, limit=limit, memory_type="task")
            return results
        
        # Fallback: simple text search across all snapshots
        matches = []
        for project, snap_ids in self.index.items():
            for snap_id in snap_ids:
                snapshot = self._load_snapshot(snap_id)
                if snapshot:
                    text = f"{snapshot['task']} {snapshot.get('notes', '')}"
                    if query.lower() in text.lower():
                        matches.append({
                            "snapshot_id": snap_id,
                            "project": project,
                            "task": snapshot["task"],
                            "notes": snapshot.get("notes", ""),
                        })
        
        return matches[:limit]
    
    def mark_completed(self, project: str, snapshot_id: Optional[str] = None):
        """Mark a snapshot as completed"""
        if snapshot_id is None:
            if project in self.index and self.index[project]:
                snapshot_id = self.index[project][-1]
            else:
                return
        
        snapshot = self._load_snapshot(snapshot_id)
        if snapshot:
            snapshot["status"] = "completed"
            self._update_snapshot(snapshot_id, snapshot)
            logger.info(f"Marked snapshot as completed: {snapshot_id}")
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects with snapshot counts"""
        return [
            {
                "project": project,
                "snapshot_count": len(snap_ids),
                "latest_task": self._get_latest_task(snap_ids),
            }
            for project, snap_ids in self.index.items()
        ]
    
    # --- Private helpers ---
    
    def _capture_environment(self) -> Dict[str, Any]:
        """Capture current environment state"""
        return {
            "cwd": os.getcwd(),
            "python_version": os.sys.version,
            "platform": os.sys.platform,
            "timestamp": time.time(),
        }
    
    def _diff_environment(self, old_env: Dict) -> Dict[str, Any]:
        """Diff current environment against a snapshot's environment"""
        current = self._capture_environment()
        diff = {}
        for key in set(list(current.keys()) + list(old_env.keys())):
            if current.get(key) != old_env.get(key):
                diff[key] = {"was": old_env.get(key), "now": current.get(key)}
        return diff
    
    def _load_snapshot(self, snapshot_id: str) -> Optional[Dict]:
        """Load a snapshot from disk"""
        path = self.storage_dir / f"{snapshot_id}.json"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def _update_snapshot(self, snapshot_id: str, data: Dict):
        """Update a snapshot on disk"""
        path = self.storage_dir / f"{snapshot_id}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _load_index(self):
        """Load the snapshot index"""
        index_path = self.storage_dir / "_index.json"
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                self.index = json.load(f)
            # Count total snapshots
            self._snapshot_count = sum(len(v) for v in self.index.values())
    
    def _save_index(self):
        """Save the snapshot index"""
        index_path = self.storage_dir / "_index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2)
    
    def _get_latest_task(self, snap_ids: List[str]) -> str:
        """Get the task description from the most recent snapshot"""
        if snap_ids:
            snapshot = self._load_snapshot(snap_ids[-1])
            if snapshot:
                return snapshot.get("task", "Unknown")
        return "Unknown"
    
    @staticmethod
    def _human_time_delta(seconds: float) -> str:
        """Convert seconds to human-readable time delta"""
        if seconds < 60:
            return f"{int(seconds)} seconds"
        elif seconds < 3600:
            return f"{int(seconds / 60)} minutes"
        elif seconds < 86400:
            return f"{seconds / 3600:.1f} hours"
        elif seconds < 604800:
            return f"{seconds / 86400:.1f} days"
        else:
            return f"{seconds / 604800:.1f} weeks"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get temporal context statistics"""
        total = sum(len(v) for v in self.index.values())
        return {
            "projects": len(self.index),
            "total_snapshots": total,
            "storage_dir": str(self.storage_dir),
        }
