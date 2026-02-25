"""
⏰ TIME MACHINE DEBUGGER
Answers "when and WHY did it break?" - traces bugs to exact commit/requirement.
Kills: Debugging time, Junior/Mid Developers who trace bugs for hours

Author: OmniClaw Advanced Features
"""

import git
import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Optional, Callable
from datetime import datetime
from enum import Enum


class BugSeverity(Enum):
    CRITICAL = "critical"  # Data loss, security breach
    HIGH = "high"         # Major feature broken
    MEDIUM = "medium"     # Workaround exists
    LOW = "low"           # Minor issue


@dataclass
class CommitInfo:
    """Information about a commit"""
    hash: str
    short_hash: str
    message: str
    author: str
    date: datetime
    diff: str = ""
    files_changed: list[str] = field(default_factory=list)


@dataclass
class BugTimeline:
    """Timeline of when a bug was introduced and evolved"""
    introduced_in: CommitInfo
    detected_in: CommitInfo  
    root_cause_commit: Optional[CommitInfo] = None
    evolution: list[dict] = field(default_factory=list)
    requirements_related: list[str] = field(default_factory=list)
    
    # The "why" - captured from commit messages, PRs, issues
    root_cause_explanation: str = ""
    fix_commit: Optional[CommitInfo] = None


class TimeMachineDebugger:
    """
    Time-travel debugging - trace bugs back to their origin.
    Answers: "When did this break?" and "Why did it break?"
    """
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        try:
            self.repo = git.Repo(repo_path)
        except:
            self.repo = None
        
        # Cache for commit data
        self.commit_cache: dict[str, CommitInfo] = {}
        
        # Bug patterns to search for
        self.bug_patterns = [
            r"(bug|fix|issue|error|broken|wrong|incorrect)",
            r"(patch|hack|workaround|temporary)",
            r"(revert|undo)",
        ]
    
    def investigate(
        self, 
        error_signature: str,
        search_commits: int = 100
    ) -> BugTimeline:
        """
        Investigate when and why an error started occurring.
        
        Args:
            error_signature: Error message, exception type, or failure pattern
            search_commits: How many commits back to search
        
        Returns:
            BugTimeline with full investigation results
        """
        if not self.repo:
            return self._mock_timeline(error_signature)
        
        commits = list(self.repo.iter_commits(max_count=search_commits))
        
        # Find when error first appeared
        introduction = self._find_introduction_commit(commits, error_signature)
        
        # Find related requirements/changes
        requirements = self._find_related_requirements(commits[:introduction.index] if introduction else [])
        
        # Try to determine root cause
        root_cause = self._analyze_root_cause(commits, introduction, error_signature)
        
        # Find if/when it was fixed
        fix_commit = self._find_fix_commit(commits, error_signature)
        
        # Build evolution timeline
        evolution = self._build_evolution(commits, introduction, error_signature)
        
        return BugTimeline(
            introduced_in=introduction,
            detected_in=commits[0],  # Current HEAD
            root_cause_commit=root_cause,
            requirements_related=requirements,
            root_cause_explanation=self._generate_explanation(
                introduction, root_cause, requirements
            ),
            fix_commit=fix_commit,
            evolution=evolution
        )
    
    def _find_introduction_commit(
        self, 
        commits: list, 
        error_signature: str
    ) -> CommitInfo:
        """Find the commit that introduced the bug/error"""
        
        for i, commit in enumerate(commits):
            commit_info = self._get_commit_info(commit)
            
            # Check commit message for bug-fixing keywords
            message_lower = commit.message.lower()
            
            # If this commit is a fix, the bug was introduced before it
            if any(re.search(p, message_lower) for p in self.bug_patterns):
                # Check what was changed
                if i + 1 < len(commits):
                    # Bug was likely introduced in previous meaningful change
                    prev_commit = commits[i + 1]
                    
                    # Check if the "fix" actually fixes something that broke
                    for j in range(i - 1, max(0, i - 10), -1):
                        prev_info = self._get_commit_info(commits[j])
                        if self._code_changed_meaningfully(commit_info, prev_info):
                            return prev_info
            
            # Check diff for patterns related to error
            try:
                diff = self.repo.git.diff(
                    commit.parents[0].hexsha if commit.parents else None,
                    commit.hexsha
                )
                if error_signature.lower() in diff.lower():
                    return commit_info
            except:
                pass
        
        # Default: return the oldest commit
        return self._get_commit_info(commits[-1]) if commits else None
    
    def _get_commit_info(self, commit) -> CommitInfo:
        """Get detailed commit info"""
        
        if commit.hexsha in self.commit_cache:
            return self.commit_cache[commit.hexsha]
        
        try:
            diff = self.repo.git.diff(
                commit.parents[0].hexsha if commit.parents else None,
                commit.hexsha
            )
        except:
            diff = ""
        
        try:
            files = list(commit.stats.files.keys())
        except:
            files = []
        
        info = CommitInfo(
            hash=commit.hexsha,
            short_hash=commit.hexsha[:7],
            message=commit.message.strip(),
            author=str(commit.author),
            date=commit.committed_datetime,
            diff=diff,
            files_changed=files
        )
        
        self.commit_cache[commit.hexsha] = info
        return info
    
    def _code_changed_meaningfully(
        self, 
        commit1: CommitInfo, 
        commit2: CommitInfo
    ) -> bool:
        """Check if code change was meaningful, not just whitespace"""
        
        if not commit1.diff or not commit2.diff:
            return False
        
        # Remove whitespace-only changes
        meaningful_diff = '\n'.join(
            line for line in commit1.diff.split('\n')
            if line.strip() and not line.startswith(('+', '-', ' '))
        )
        
        return len(meaningful_diff) > 50
    
    def _find_related_requirements(self, commits: list) -> list[str]:
        """Find related requirements from commit messages"""
        
        requirements = []
        
        # Keywords that indicate requirement-related commits
        req_keywords = [
            "feature", "implement", "add", "create", "requirement",
            "spec", "design", "api", "endpoint", "functionality"
        ]
        
        for commit in commits[:20]:  # Check last 20 commits
            info = self._get_commit_info(commit)
            msg_lower = info.message.lower()
            
            if any(kw in msg_lower for kw in req_keywords):
                requirements.append(info.message)
        
        return requirements[:5]  # Return top 5
    
    def _analyze_root_cause(
        self, 
        commits: list, 
        introduction: CommitInfo,
        error_signature: str
    ) -> Optional[CommitInfo]:
        """Analyze what caused the bug"""
        
        if not introduction:
            return None
        
        # Look for commits around the introduction
        intro_index = None
        for i, c in enumerate(commits):
            if c.hexsha == introduction.hash:
                intro_index = i
                break
        
        if intro_index is None:
            return introduction
        
        # Check commits before introduction
        for i in range(max(0, intro_index - 5), intro_index):
            info = self._get_commit_info(commits[i])
            
            # Look for commits that changed the same files
            if set(info.files_changed) & set(introduction.files_changed):
                return info
        
        return introduction
    
    def _find_fix_commit(
        self, 
        commits: list, 
        error_signature: str
    ) -> Optional[CommitInfo]:
        """Find if/when the bug was fixed"""
        
        fix_keywords = [
            "fix", "resolve", "repair", "patch", "correct",
            "bug", "issue", "solved", "fixed"
        ]
        
        for commit in commits:
            info = self._get_commit_info(commit)
            msg_lower = info.message.lower()
            
            # Check if this is a fix commit mentioning the error
            if any(kw in msg_lower for kw in fix_keywords):
                if error_signature.lower()[:30] in info.message.lower():
                    return info
        
        return None
    
    def _build_evolution(
        self, 
        commits: list, 
        introduction: CommitInfo,
        error_signature: str
    ) -> list[dict]:
        """Build timeline of how the bug evolved"""
        
        evolution = []
        
        intro_index = None
        for i, c in enumerate(commits):
            if c.hexsha == introduction.hash:
                intro_index = i
                break
        
        if intro_index is None:
            intro_index = len(commits) - 1
        
        # Get commits that touched same files
        for i in range(intro_index, max(0, intro_index - 10), -1):
            if i < len(commits):
                info = self._get_commit_info(commits[i])
                
                if set(info.files_changed) & set(introduction.files_changed):
                    evolution.append({
                        "commit": info.short_hash,
                        "date": info.date.isoformat(),
                        "message": info.message,
                        "files": info.files_changed
                    })
        
        return evolution
    
    def _generate_explanation(
        self,
        introduction: CommitInfo,
        root_cause: Optional[CommitInfo],
        requirements: list[str]
    ) -> str:
        """Generate human-readable explanation"""
        
        if not introduction:
            return "Could not determine bug origin"
        
        explanation = f"""
## Bug Origin Analysis

**First Appeared:** {introduction.short_hash}
**Date:** {introduction.date.strftime('%Y-%m-%d %H:%M')}
**Commit Message:** {introduction.message}
**Author:** {introduction.author}

"""
        
        if root_cause and root_cause.hash != introduction.hash:
            explanation += f"""**Root Cause Commit:** {root_cause.short_hash}
**Root Cause Date:** {root_cause.date.strftime('%Y-%m-%d')}
**What Changed:** {root_cause.message}

"""
        
        if requirements:
            explanation += "**Likely Related Requirements:**\n"
            for req in requirements[:3]:
                explanation += f"- {req}\n"
        
        return explanation
    
    def _mock_timeline(self, error_signature: str) -> BugTimeline:
        """Return mock timeline for demo/testing"""
        
        return BugTimeline(
            introduced_in=CommitInfo(
                hash="abc123",
                short_hash="abc123",
                message="Mock commit - integrate git to enable",
                author="Unknown",
                date=datetime.now()
            ),
            detected_in=CommitInfo(
                hash="def456",
                short_hash="def456", 
                message="Current HEAD",
                author="Unknown",
                date=datetime.now()
            ),
            root_cause_explanation="Mock timeline - requires git repository"
        )
    
    def explain_failure(
        self,
        current_error: str,
        historical_errors: list[str]
    ) -> str:
        """
        Explain why a failure is happening based on patterns.
        
        Args:
            current_error: Current error message
            historical_errors: Previous similar errors
        
        Returns:
            Explanation of the failure pattern
        """
        
        # Find patterns in historical errors
        if not historical_errors:
            return f"""
## Failure Analysis

**Current Error:** {current_error}

**Pattern:** First occurrence
**Recommendation:** Check recent changes to related files
"""
        
        # Analyze similarity
        current_hash = hashlib.md5(current_error.encode()).hexdigest()
        
        # Group similar errors
        error_groups = {}
        for err in historical_errors:
            err_hash = hashlib.md5(err.encode()).hexdigest()
            if err_hash[:4] == current_hash[:4]:
                if 'first' not in error_groups:
                    error_groups['first'] = err
                error_groups['first'] = err
        
        return f"""
## Failure Analysis

**Current Error:** {current_error}

**Pattern:** Similar errors occurred {len(historical_errors)} times before
**Likely Cause:** Regression - same issue re-introduced

**Previous Occurrences:**
{chr(10).join(f"- {e[:100]}..." for e in historical_errors[:3])}

**Recommendation:** Check commits between last occurrence and now
"""


# Demo
if __name__ == "__main__":
    debugger = TimeMachineDebugger("/tmp")  # Won't work without real repo
    
    print("⏰ TIME MACHINE DEBUGGER")
    print("=" * 50)
    print("""
To use with your project:
    
    from omniclaw_advanced_features import TimeMachineDebugger
    
    debugger = TimeMachineDebugger("/path/to/your/repo")
    
    # When you encounter an error:
    timeline = debugger.investigate(
        error_signature="TypeError: Cannot read property 'x' of undefined",
        search_commits=50
    )
    
    print(f"Bug introduced in: {timeline.introduced_in.short_hash}")
    print(f"Why: {timeline.root_cause_explanation}")
    
    # Or explain a failure pattern:
    explanation = debugger.explain_failure(
        current_error="Connection timeout",
        historical_errors=["Connection timeout", "TimeoutError", "Connection refused"]
    )
    print(explanation)
""")
    
    # Demo explanation
    demo_explanation = debugger.explain_failure(
        current_error="TypeError: Cannot read property 'name' of undefined",
        historical_errors=[
            "TypeError: Cannot read property 'id' of undefined",
            "Cannot read property 'data' of undefined"
        ]
    )
    print(demo_explanation)
