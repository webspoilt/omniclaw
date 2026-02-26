import asyncio
import litellm
import logging
from typing import List

logger = logging.getLogger("OmniClaw.Council")

class LLMCouncil:
    """
    LLM Council
    Runs multiple models in parallel and aggregates their answers to reduce hallucination.
    """
    def __init__(self, council_members: List[str] = None, judge_model: str = "gpt-4o"):
        self.council_members = council_members or ["gpt-4o", "claude-3-5-sonnet-20241022", "gemini-1.5-pro"]
        self.judge_model = judge_model

    async def debate(self, prompt: str) -> str:
        """
        Runs the prompt against all council members and uses the judge model to pick the best answer.
        """
        logger.info(f"Starting council debate with {len(self.council_members)} members")
        
        # Parallel Fan-Out
        tasks = []
        for model in self.council_members:
            tasks.append(self._safely_call_model(model, prompt))
            
        responses_raw = await asyncio.gather(*tasks)
        
        # Filter out failed responses
        responses = [r for r in responses_raw if r is not None]
        
        if not responses:
            return "Council Debate Failed: All models returned errors."
        
        if len(responses) == 1:
            logger.warning("Only one model succeeded in the council debate.")
            return responses[0]

        # Chairman Synthesis / Simple Voting
        logger.info(f"Collecting votes from {self.judge_model}...")
        judge_prompt = f"Given the user query: '{prompt}', which of the following answers is most accurate, logical, and helpful?\n"
        for i, r in enumerate(responses):
            judge_prompt += f"\n--- Answer {i+1} ---\n{r}\n"
        judge_prompt += "\nRespond ONLY with the single digit number of the best answer (e.g., '1' or '2')."
        
        try:
            verdict_response = await litellm.acompletion(
                model=self.judge_model,
                messages=[{"role": "user", "content": judge_prompt}]
            )
            verdict_text = verdict_response.choices[0].message.content.strip()
            
            # Extract the first digit found in the verdict text
            best_idx = 0
            for char in verdict_text:
                if char.isdigit():
                    best_idx = int(char) - 1
                    break
                    
            if 0 <= best_idx < len(responses):
                logger.info(f"Council selected Answer {best_idx+1}")
                return responses[best_idx]
            else:
                logger.warning(f"Judge returned invalid index '{verdict_text}', returning first answer.")
                return responses[0]
                
        except Exception as e:
            logger.error(f"Judge model failed: {e}")
            return responses[0]

    async def _safely_call_model(self, model: str, prompt: str) -> str:
        try:
            response = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Council member '{model}' failed: {e}")
            return None
