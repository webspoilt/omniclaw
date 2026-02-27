import asyncio
import signal
import logging
from typing import Optional

from agents.contextual_fuzzer import ContextualFuzzer
from agents.adversarial_refiner import AdversarialRefiner
from agents.poc_validator import PoCValidator
from agents.disclosure_engine import DisclosureEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OmniClawOrchestrator:
    def __init__(self, config: dict):
        self.config = config
        self.kill_switch = asyncio.Event()
        self.tasks = []
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        logger.warning("Received interrupt signal, activating kill-switch...")
        self.kill_switch.set()

    async def run_agent(self, agent_coro, name: str):
        """Wrap agent execution to watch kill-switch."""
        try:
            logger.info(f"Starting {name}")
            # Create a task that checks kill_switch periodically (handled inside agents)
            result = await agent_coro
            logger.info(f"{name} completed")
            return result
        except Exception as e:
            logger.error(f"{name} failed: {e}")
            return None
        finally:
            # If kill-switch is set, cancel all tasks
            if self.kill_switch.is_set():
                for task in self.tasks:
                    task.cancel()

    async def orchestrate(self):
        """Run the full pipeline with kill-switch monitoring."""
        # Instantiate agents
        fuzzer = ContextualFuzzer(
            target_url=self.config['target_url'],
            user_a_token=self.config['user_a_token'],
            user_b_token=self.config['user_b_token'],
            kill_switch=self.kill_switch
        )
        refiner = AdversarialRefiner(
            ollama_url=self.config.get('ollama_url', 'http://localhost:11434'),
            model=self.config.get('llama_model', 'llama2'),
            kill_switch=self.kill_switch
        )
        validator = PoCValidator(
            sandbox_url=self.config['sandbox_url'],
            kill_switch=self.kill_switch
        )
        disclosure = DisclosureEngine()

        # Step 1: Fuzz endpoints and find IDOR candidates
        idor_findings = await self.run_agent(fuzzer.run(), "ContextualFuzzer")
        if not idor_findings:
            idor_findings = []

        # Step 2: Use adversarial refinement to generate payloads for each finding
        refined_payloads = []
        for finding in idor_findings:
            if self.kill_switch.is_set():
                break
            # Example: create a prompt to generate XSS/SQLi payloads
            prompt = f"Generate a proof-of-concept payload to test for XSS at endpoint {finding['endpoint']} with parameters {finding['params']}. Provide only the payload."
            refined = await self.run_agent(refiner.refine(prompt), "AdversarialRefiner")
            if refined:
                # Parse refined response to extract payload (simplified)
                payload = {
                    'type': 'xss',  # assume; in practice detect from response
                    'method': finding.get('method', 'get'),
                    'endpoint': finding['endpoint'],
                    'parameters': finding.get('params', {}),
                    'payload_data': refined.strip()
                }
                refined_payloads.append(payload)

        # Step 3: Validate payloads in sandbox
        if refined_payloads:
            validated = await self.run_agent(validator.run(refined_payloads), "PoCValidator")
        else:
            validated = []

        # Step 4: Generate disclosure report
        if validated:
            report = disclosure.generate_report(validated, self.config['target_url'])
            disclosure.save_report(report, "omniclaw_report.md")
            logger.info("Disclosure report generated.")
        else:
            logger.info("No validated findings to report.")

        logger.info("Orchestration finished.")

async def main():
    config = {
        'target_url': 'http://localhost:3000',
        'sandbox_url': 'http://sandbox.local',
        'user_a_token': 'jwt_token_a',
        'user_b_token': 'jwt_token_b',
        'ollama_url': 'http://localhost:11434',
        'llama_model': 'llama2'
    }
    orchestrator = OmniClawOrchestrator(config)
    await orchestrator.orchestrate()

if __name__ == '__main__':
    asyncio.run(main())
