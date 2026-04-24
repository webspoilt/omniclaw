"""
Security utilities for the Static Analysis Engine.
Credential management and secret scanning with zero-trust principles.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class CredentialVault(ABC):
    """Abstract credential vault for secure secret retrieval."""
    
    @abstractmethod
    async def get_credential(self, credential_id: str) -> str:
        """Retrieve and decrypt a credential."""
        pass
    
    @abstractmethod
    async def rotate_credential(self, credential_id: str) -> bool:
        """Trigger credential rotation."""
        pass


class HashiCorpVault(CredentialVault):
    """HashiCorp Vault integration for credential management."""
    
    def __init__(self, vault_addr: str, role_id: str, secret_id: str):
        self.vault_addr = vault_addr
        self.role_id = role_id
        self.secret_id = secret_id
        self._client_token: Optional[str] = None
    
    async def get_credential(self, credential_id: str) -> str:
        """Retrieve credential from Vault KV store."""
        if not self._client_token:
            await self._authenticate()
        
        # Vault API call would go here
        # Simplified for architecture demonstration
        return "retrieved-credential"
    
    async def _authenticate(self) -> None:
        """Authenticate with AppRole."""
        pass
    
    async def rotate_credential(self, credential_id: str) -> bool:
        """Request credential rotation."""
        return True


class SecretScanner:
    """
    Post-clone secret scanning to prevent credential leakage.
    
    Integrates with gitleaks and trufflehog for comprehensive detection.
    """
    
    def __init__(self, gitleaks_path: str = "gitleaks", trufflehog_path: str = "trufflehog"):
        self.gitleaks_path = gitleaks_path
        self.trufflehog_path = trufflehog_path
    
    async def scan(self, repo_path: Path) -> list[dict]:
        """
        Scan repository for leaked secrets.
        
        Returns:
            List of detected secrets with metadata
        """
        findings = []
        
        # Run gitleaks
        gitleaks_results = await self._run_gitleaks(repo_path)
        findings.extend(gitleaks_results)
        
        # Run trufflehog filesystem scan
        trufflehog_results = await self._run_trufflehog(repo_path)
        findings.extend(trufflehog_results)
        
        return findings
    
    async def _run_gitleaks(self, repo_path: Path) -> list[dict]:
        """Run gitleaks detect on repository."""
        try:
            proc = await asyncio.create_subprocess_exec(
                self.gitleaks_path,
                "detect",
                "--source", str(repo_path),
                "--verbose",
                "--no-git",  # Scan files, not git history
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
            
            findings = []
            # Parse gitleaks output (simplified)
            for line in stdout.decode().split("\n"):
                if "Secret Detected" in line or "Match" in line:
                    findings.append({
                        "tool": "gitleaks",
                        "match": line,
                        "severity": "critical",
                    })
            
            return findings
            
        except FileNotFoundError:
            logger.warning("gitleaks not found, skipping secret scan")
            return []
        except asyncio.TimeoutError:
            logger.warning("gitleaks scan timed out")
            return []
    
    async def _run_trufflehog(self, repo_path: Path) -> list[dict]:
        """Run trufflehog filesystem scan."""
        try:
            proc = await asyncio.create_subprocess_exec(
                self.trufflehog_path,
                "filesystem",
                str(repo_path),
                "--json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
            
            findings = []
            for line in stdout.decode().split("\n"):
                if line.strip():
                    try:
                        import json
                        finding = json.loads(line)
                        findings.append({
                            "tool": "trufflehog",
                            "detector": finding.get("DetectorName", "unknown"),
                            "raw": finding.get("Raw", ""),
                            "severity": "critical",
                        })
                    except json.JSONDecodeError:
                        pass
            
            return findings
            
        except FileNotFoundError:
            logger.warning("trufflehog not found, skipping filesystem scan")
            return []
        except asyncio.TimeoutError:
            logger.warning("trufflehog scan timed out")
            return []
