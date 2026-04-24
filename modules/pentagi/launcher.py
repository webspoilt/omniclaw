"""
PentAGI Subsystem Launcher

Manages the cloning, Docker Compose execution, and configuration bridging 
between OmniClaw's environment and PentAGI's `.env` requirements.
"""

import os
import subprocess
import logging
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)

class PentagiLauncher:
    def __init__(self, omniclaw_workspace: str = "."):
        self.workspace = Path(omniclaw_workspace).resolve()
        self.pentagi_dir = self.workspace / "modules" / "pentagi" / "vxcontrol_pentagi"
        self.repo_url = "https://github.com/vxcontrol/pentagi"
        self.omniclaw_config = self.workspace / "config.yaml"
        
    def _clone_repo(self):
        """Clone the repository if it does not exist."""
        if not self.pentagi_dir.exists():
            logger.info(f"Cloning PentAGI from {self.repo_url} into {self.pentagi_dir}...")
            # Ensure parent exists
            self.pentagi_dir.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["git", "clone", self.repo_url, str(self.pentagi_dir)],
                check=True
            )
        else:
            logger.info("PentAGI repository already cloned locally.")

    def _sync_env_configuration(self):
        """
        Bridges API keys from OmniClaw's `config.yaml` to PentAGI's `.env` file automatically.
        """
        env_file_path = self.pentagi_dir / ".env"
        example_env_path = self.pentagi_dir / ".env.example"
        
        # Read PentAGI .env.example
        if not env_file_path.exists() and example_env_path.exists():
            env_content = example_env_path.read_text()
            env_file_path.write_text(env_content)
        elif not env_file_path.exists():
            logger.error("Neither .env nor .env.example found in PentAGI repo.")
            return

        # Attempt to inject known keys from OmniClaw config
        if not self.omniclaw_config.exists():
            return
            
        try:
            with open(self.omniclaw_config, 'r') as f:
                omni_cfg = yaml.safe_load(f)
                
            apis = omni_cfg.get("apis", [])
            env_lines = env_file_path.read_text().splitlines()
            new_lines = []
            
            openai_key = next((api["key"] for api in apis if api["provider"] == "openai"), None)
            anthropic_key = next((api["key"] for api in apis if api["provider"] == "anthropic"), None)
            
            for line in env_lines:
                if line.startswith("OPEN_AI_KEY=") and openai_key:
                    new_lines.append(f"OPEN_AI_KEY={openai_key}")
                elif line.startswith("ANTHROPIC_API_KEY=") and anthropic_key:
                    new_lines.append(f"ANTHROPIC_API_KEY={anthropic_key}")
                else:
                    new_lines.append(line)
                    
            env_file_path.write_text("\n".join(new_lines) + "\n")
            logger.info("Successfully synced API keys from OmniClaw config to PentAGI .env")
            
        except Exception as e:
            logger.warning(f"Could not sync OmniClaw configs to PentAGI .env: {e}")

    def boot(self):
        """
        Clone, sync, and launch PentAGI via docker-compose.
        Warning: this binds massive infrastructure.
        """
        self._clone_repo()
        self._sync_env_configuration()
        
        logger.info("Starting PentAGI docker-compose stack...")
        try:
            # Standard Pentagi requires the main file and graphs/db
            subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=str(self.pentagi_dir),
                check=True
            )
            # Boot secondary files usually requested for Graphiti and observability
            subprocess.run(
                ["docker", "compose", "-f", "docker-compose-graphiti.yml", "up", "-d"],
                cwd=str(self.pentagi_dir)
            )
            subprocess.run(
                ["docker", "compose", "-f", "docker-compose-langfuse.yml", "up", "-d"],
                cwd=str(self.pentagi_dir)
            )
            logger.info("PentAGI stack booted successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to boot PentAGI stack: {e}")
            raise

    def stop(self):
        """Tear down the PentAGI stack."""
        if self.pentagi_dir.exists():
            logger.info("Stopping PentAGI docker-compose stack...")
            subprocess.run(
                ["docker", "compose", "down"],
                cwd=str(self.pentagi_dir)
            )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    launcher = PentagiLauncher(omniclaw_workspace=os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    print("Launcher initialized. Use boot() to start the stack.")
