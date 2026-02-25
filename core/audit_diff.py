#!/usr/bin/env python3
"""
OmniClaw Audit Diff
Multi-file edit review system with unified diff view,
atomic apply, and rollback capability.
"""

import logging
import os
import shutil
import time
import difflib
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("OmniClaw.AuditDiff")


@dataclass
class FileChange:
    """Represents a proposed change to a single file"""
    file_path: str
    original: str
    modified: str
    intent: str  # Why this change is being made
    diff: str = ""
    change_type: str = "modify"  # "modify", "create", "delete"
    line_count_delta: int = 0
    
    def __post_init__(self):
        if not self.diff:
            self.diff = self._generate_diff()
        self.line_count_delta = (
            len(self.modified.splitlines()) - len(self.original.splitlines())
        )
    
    def _generate_diff(self) -> str:
        """Generate a unified diff"""
        original_lines = self.original.splitlines(keepends=True)
        modified_lines = self.modified.splitlines(keepends=True)
        return ''.join(difflib.unified_diff(
            original_lines, modified_lines,
            fromfile=f"a/{os.path.basename(self.file_path)}",
            tofile=f"b/{os.path.basename(self.file_path)}",
            lineterm='\n'
        ))


@dataclass
class EditSession:
    """A complete edit session with all proposed changes"""
    session_id: str
    intent: str
    changes: List[FileChange] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    applied_at: Optional[float] = None
    rolled_back_at: Optional[float] = None
    status: str = "pending"  # "pending", "applied", "rolled_back"
    backup_dir: Optional[str] = None


class AuditDiff:
    """
    Multi-file edit review system.
    
    Collects proposed changes across multiple files, generates
    a unified audit view, and applies/rolls back atomically.
    """
    
    def __init__(self, backup_root: str = "./.omniclaw_backups"):
        """
        Args:
            backup_root: Directory for storing backups before applying changes
        """
        self.backup_root = Path(backup_root)
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        self.sessions: Dict[str, EditSession] = {}
        self._session_counter = 0
        
        logger.info(f"AuditDiff initialized: backup_root={backup_root}")
    
    def create_session(self, intent: str) -> str:
        """
        Create a new edit session.
        
        Args:
            intent: High-level description of what these edits accomplish
            
        Returns:
            Session ID
        """
        self._session_counter += 1
        session_id = f"edit_{self._session_counter}_{int(time.time())}"
        
        session = EditSession(
            session_id=session_id,
            intent=intent
        )
        self.sessions[session_id] = session
        
        logger.info(f"Created edit session: {session_id} — {intent}")
        return session_id
    
    def add_change(self, session_id: str, file_path: str, 
                   original: str, modified: str, intent: str,
                   change_type: str = "modify") -> FileChange:
        """
        Add a proposed file change to a session.
        
        Args:
            session_id: The edit session ID
            file_path: Path to the file being changed
            original: Original file content
            modified: Modified file content
            intent: Why this specific change is being made
            change_type: "modify", "create", or "delete"
            
        Returns:
            The created FileChange
        """
        if session_id not in self.sessions:
            raise ValueError(f"Unknown session: {session_id}")
        
        change = FileChange(
            file_path=os.path.abspath(file_path),
            original=original,
            modified=modified,
            intent=intent,
            change_type=change_type
        )
        
        self.sessions[session_id].changes.append(change)
        logger.info(f"Added change to session {session_id}: {file_path} ({change_type})")
        
        return change
    
    def propose_change(self, session_id: str, file_path: str,
                       modified: str, intent: str) -> FileChange:
        """
        Propose a change to an existing file (reads original automatically).
        
        Args:
            session_id: The edit session ID
            file_path: Path to the file
            modified: New content for the file
            intent: Why this change is being made
            
        Returns:
            The created FileChange
        """
        abs_path = os.path.abspath(file_path)
        
        if os.path.exists(abs_path):
            with open(abs_path, 'r', encoding='utf-8') as f:
                original = f.read()
            change_type = "modify"
        else:
            original = ""
            change_type = "create"
        
        return self.add_change(session_id, abs_path, original, modified, 
                              intent, change_type)
    
    def generate_unified_view(self, session_id: str) -> str:
        """
        Generate a human-readable audit view of all changes in a session.
        
        Args:
            session_id: The edit session ID
            
        Returns:
            Formatted string showing all changes
        """
        if session_id not in self.sessions:
            raise ValueError(f"Unknown session: {session_id}")
        
        session = self.sessions[session_id]
        lines = []
        
        lines.append("=" * 72)
        lines.append(f"AUDIT DIFF — {session.intent}")
        lines.append(f"Session: {session_id}")
        lines.append(f"Created: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(session.created_at))}")
        lines.append(f"Files affected: {len(session.changes)}")
        lines.append("=" * 72)
        
        total_additions = 0
        total_deletions = 0
        
        for i, change in enumerate(session.changes, 1):
            lines.append("")
            lines.append(f"--- Change {i}/{len(session.changes)} ---")
            lines.append(f"File: {change.file_path}")
            lines.append(f"Type: {change.change_type.upper()}")
            lines.append(f"Intent: {change.intent}")
            
            if change.change_type == "delete":
                lines.append(f"[ENTIRE FILE WILL BE DELETED]")
                total_deletions += len(change.original.splitlines())
            else:
                lines.append("")
                lines.append(change.diff if change.diff else "[No changes detected]")
                
                # Count additions/deletions
                for line in change.diff.splitlines():
                    if line.startswith('+') and not line.startswith('+++'):
                        total_additions += 1
                    elif line.startswith('-') and not line.startswith('---'):
                        total_deletions += 1
        
        lines.append("")
        lines.append("-" * 72)
        lines.append(f"SUMMARY: +{total_additions} additions, -{total_deletions} deletions")
        lines.append(f"Status: {session.status.upper()}")
        lines.append("-" * 72)
        
        return "\n".join(lines)
    
    def apply_changes(self, session_id: str) -> Dict[str, Any]:
        """
        Apply all changes in a session atomically with backup.
        
        Args:
            session_id: The edit session ID
            
        Returns:
            Result dict with success status and details
        """
        if session_id not in self.sessions:
            raise ValueError(f"Unknown session: {session_id}")
        
        session = self.sessions[session_id]
        
        if session.status != "pending":
            return {"success": False, "reason": f"Session already {session.status}"}
        
        # Create backup directory
        backup_dir = self.backup_root / session_id
        backup_dir.mkdir(parents=True, exist_ok=True)
        session.backup_dir = str(backup_dir)
        
        applied_files = []
        
        try:
            # Phase 1: Backup all originals
            for change in session.changes:
                if os.path.exists(change.file_path):
                    backup_path = backup_dir / self._safe_filename(change.file_path)
                    shutil.copy2(change.file_path, backup_path)
                    logger.debug(f"Backed up: {change.file_path}")
            
            # Phase 2: Apply all changes
            for change in session.changes:
                if change.change_type == "delete":
                    if os.path.exists(change.file_path):
                        os.remove(change.file_path)
                        applied_files.append(change.file_path)
                else:
                    # Create parent directories if needed
                    os.makedirs(os.path.dirname(change.file_path), exist_ok=True)
                    with open(change.file_path, 'w', encoding='utf-8') as f:
                        f.write(change.modified)
                    applied_files.append(change.file_path)
                
                logger.info(f"Applied: {change.change_type} {change.file_path}")
            
            session.status = "applied"
            session.applied_at = time.time()
            
            return {
                "success": True,
                "files_changed": len(applied_files),
                "files": applied_files,
                "backup_dir": str(backup_dir)
            }
            
        except Exception as e:
            # Rollback on failure
            logger.error(f"Error applying changes, rolling back: {e}")
            self._rollback_from_backup(session, backup_dir)
            return {
                "success": False,
                "reason": str(e),
                "rolled_back": True
            }
    
    def rollback(self, session_id: str) -> Dict[str, Any]:
        """
        Rollback a previously applied session.
        
        Args:
            session_id: The edit session ID
            
        Returns:
            Result dict
        """
        if session_id not in self.sessions:
            raise ValueError(f"Unknown session: {session_id}")
        
        session = self.sessions[session_id]
        
        if session.status != "applied":
            return {"success": False, "reason": f"Session not applied (status: {session.status})"}
        
        backup_dir = Path(session.backup_dir) if session.backup_dir else None
        if not backup_dir or not backup_dir.exists():
            return {"success": False, "reason": "No backup found"}
        
        return self._rollback_from_backup(session, backup_dir)
    
    def _rollback_from_backup(self, session: EditSession, 
                               backup_dir: Path) -> Dict[str, Any]:
        """Restore files from backup"""
        restored = []
        
        try:
            for change in session.changes:
                backup_path = backup_dir / self._safe_filename(change.file_path)
                
                if change.change_type == "create":
                    # Remove the newly created file
                    if os.path.exists(change.file_path):
                        os.remove(change.file_path)
                        restored.append(change.file_path)
                elif backup_path.exists():
                    shutil.copy2(backup_path, change.file_path)
                    restored.append(change.file_path)
            
            session.status = "rolled_back"
            session.rolled_back_at = time.time()
            
            logger.info(f"Rolled back session {session.session_id}: {len(restored)} files restored")
            
            return {
                "success": True,
                "files_restored": len(restored),
                "files": restored
            }
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return {"success": False, "reason": str(e)}
    
    @staticmethod
    def _safe_filename(file_path: str) -> str:
        """Convert a file path to a safe backup filename"""
        return file_path.replace(os.sep, "__").replace(":", "_").replace(" ", "_")
    
    def get_session(self, session_id: str) -> Optional[EditSession]:
        """Get a session by ID"""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all edit sessions"""
        return [
            {
                "session_id": s.session_id,
                "intent": s.intent,
                "file_count": len(s.changes),
                "status": s.status,
                "created_at": s.created_at,
            }
            for s in self.sessions.values()
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get audit diff statistics"""
        return {
            "total_sessions": len(self.sessions),
            "pending": sum(1 for s in self.sessions.values() if s.status == "pending"),
            "applied": sum(1 for s in self.sessions.values() if s.status == "applied"),
            "rolled_back": sum(1 for s in self.sessions.values() if s.status == "rolled_back"),
            "backup_root": str(self.backup_root),
        }
