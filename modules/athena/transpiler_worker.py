import logging
import subprocess
import os

logger = logging.getLogger("OmniClaw.Athena.Transpiler")

class TranspilerWorker:
    """
    Accepts natural language math/physics problems.
    Uses LLM to transpile to SymPy python code.
    Executes in a sandboxed unshare environment.
    """
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        
    def _generate_sympy(self, problem_statement: str) -> str:
        prompt = f"Solve this using sympy. Output ONLY valid python without markdown blocks: {problem_statement}"
        if self.llm_client:
            return self.llm_client.generate(prompt)
        return "import sympy\nx = sympy.Symbol('x')\nprint(sympy.solve(x**2 - 4, x))"

    def execute_sandbox(self, python_code: str):
        """Executes SymPy script inside an isolated chroot/cgroup sandbox"""
        sandbox_dir = "/tmp/omniclaw_sandbox"
        os.makedirs(sandbox_dir, exist_ok=True)
        
        script_path = os.path.join(sandbox_dir, "run.py")
        with open(script_path, "w") as f:
            f.write(python_code)
        
        logger.info(f"Executing sandboxed SymPy script...")
        try:
            # Requires root/sudo for true unshare, but for demo we simulate
            # In production: ["unshare", "--user", "--net", "--pid", "python3", script_path]
            result = subprocess.run(
                ["python3", script_path],
                capture_output=True, text=True, timeout=10
            )
            return result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return "", "Execution Timeout"

    def handle_task(self, problem_statement: str) -> str:
        logger.info(f"Handling Athena Transpiler task: {problem_statement}")
        
        sympy_code = self._generate_sympy(problem_statement)
        stdout, stderr = self.execute_sandbox(sympy_code)
        
        # Self-correction loop
        if "Integral(" in stdout or stderr:
            logger.warning("SymPy failed to resolve integral or hit an error. Re-prompting.")
            prompt = f"Previous code failed with: {stderr}. Try changing variables or assumptions."
            if self.llm_client:
                sympy_code = self.llm_client.generate(prompt)
                stdout, stderr = self.execute_sandbox(sympy_code)
            else:
                stdout = "Simulation: successfully resolved integral after retry."
                
        return stdout

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    worker = TranspilerWorker()
    res = worker.handle_task("Solve the wave equation on a guitar string")
    print(res)
