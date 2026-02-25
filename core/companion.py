import asyncio
import logging
from datetime import datetime
from core.orchestrator import HybridHiveOrchestrator
from core.messaging_gateway import MessagingGateway

logger = logging.getLogger("CompanionLoop")

class CompanionLoop:
    def __init__(self, config: dict, orchestrator: HybridHiveOrchestrator, messaging: MessagingGateway = None):
        self.config = config
        self.orchestrator = orchestrator
        self.messaging = messaging
        self.persona = config.get("persona", {})
        self.proactive = self.persona.get("proactive_messaging", True)
        self.running = False
        
        # Keep track of when we last sent a message
        self.last_check_in = None
        
    async def start(self):
        if not self.proactive or not self.persona.get("user_name"):
            return
            
        self.running = True
        logger.info(f"AI Companion Loop started as {self.persona.get('ai_name', 'OmniClaw')}.")
        asyncio.create_task(self._run_loop())
        
    def stop(self):
        self.running = False
        logger.info("AI Companion Loop stopped.")
        
    async def _run_loop(self):
        while self.running:
            try:
                await asyncio.sleep(60) # Check every minute
                
                now = datetime.now()
                hour = now.hour
                
                # Simple schedule awareness
                schedule_event = None
                if hour == 9 and (self.last_check_in is None or self.last_check_in.hour != 9):
                    schedule_event = "morning_greeting"
                elif hour == 13 and (self.last_check_in is None or self.last_check_in.hour != 13):
                    schedule_event = "lunch_check"
                elif hour == 19 and (self.last_check_in is None or self.last_check_in.hour != 19):
                    schedule_event = "dinner_check"
                elif hour == 23 and (self.last_check_in is None or self.last_check_in.hour != 23):
                    schedule_event = "sleep_check"
                
                if schedule_event:
                    self.last_check_in = now
                    await self._send_proactive_message(schedule_event)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in companion loop: {e}")
                
    async def _send_proactive_message(self, event: str):
        prompt = f"The current schedule event is {event}. Generate a very short, natural and caring proactive message acting as {self.persona.get('ai_name', 'your AI')} ({self.persona.get('ai_role', 'companion')}) to check on {self.persona.get('user_name', 'the user')}. Do not include quotes or meta text. Act natural."
        
        try:
            task = await self.orchestrator.execute_goal(prompt)
            msg = task.final_result
            
            if isinstance(msg, dict):
                msg = msg.get("summary", "") or msg.get("detailed_results", str(msg))
                
            if msg:
                print(f"\n[Companion {self.persona.get('ai_name', 'OmniClaw')}]: {msg}\nYou: ", end="", flush=True)
                
        except Exception as e:
            logger.error(f"Failed to send proactive message: {e}")
