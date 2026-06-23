import logging
import os
import subprocess

import pexpect

logger = logging.getLogger("OmniClaw.Athena.Lean")

class LeanWorker:
    """
    Interfaces with a headless Lean 4 theorem prover.
    Capable of checking proofs and extracting tactic states.
    """
    def __init__(self):
        # We assume lean is installed and available in PATH
        self.temp_dir = "/tmp/omniclaw_lean"
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.info("Initialized Athena Lean 4 Worker")

    def check_proof(self, lean_code: str) -> dict:
        """
        Writes Lean code to a temp file and runs the compiler/checker.
        """
        proof_path = os.path.join(self.temp_dir, "proof.lean")
        with open(proof_path, "w") as f:
            f.write(lean_code)

        logger.info("Checking Lean proof...")
        try:
            res = subprocess.run(["lean", proof_path], capture_output=True, text=True, timeout=15)

            if "error:" in res.stderr or "error:" in res.stdout:
                logger.warning("Lean check failed with errors.")
                return {"status": "failed", "tactic_state": res.stderr + res.stdout}

            return {"status": "success", "output": res.stdout}

        except subprocess.TimeoutExpired:
            logger.error("Lean verification timed out.")
            return {"status": "timeout"}
        except FileNotFoundError:
            logger.error("Lean 4 executable not found in PATH.")
            return {"status": "failed", "tactic_state": "Lean not installed"}

    def run_repl(self):
        """
        Example stub for long-running REPL interaction.
        """
        try:
            self.lean = pexpect.spawn("lean --run", encoding="utf-8")
            logger.info("Spawned Lean REPL process.")
        except Exception as e:
            logger.error(f"Failed to spawn Lean REPL: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    worker = LeanWorker()
    code = "def f (x : Nat) : Nat := x + 1\n#check f"
    print(worker.check_proof(code))
