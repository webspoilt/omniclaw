#!/usr/bin/env python3
"""
OmniClaw: The Hybrid Hive AI Agent System
Main entry point
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.orchestrator import HybridHiveOrchestrator
from core.memory import VectorMemory
from core.api_pool import APIPool
from core.messaging_gateway import MessagingGateway

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OmniClaw")


class OmniClaw:
    """Main OmniClaw application class"""
    
    def __init__(self, config_path: str = None):
        self.config = self._load_config(config_path)
        self.orchestrator: HybridHiveOrchestrator = None
        self.memory: VectorMemory = None
        self.api_pool: APIPool = None
        self.messaging: MessagingGateway = None
        self.running = False
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        defaults = {
            "apis": [],
            "memory": {
                "db_path": "./memory_db",
                "embedding_provider": "ollama"
            },
            "messaging": {
                "telegram": {"enabled": False},
                "whatsapp": {"enabled": False}
            },
            "kernel_bridge": {
                "enabled": True,
                "monitor_syscalls": True,
                "monitor_files": False,
                "monitor_network": False
            }
        }
        
        if config_path and Path(config_path).exists():
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
                # Merge with defaults
                for key, value in defaults.items():
                    if key not in config:
                        config[key] = value
                return config
        
        return defaults
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("Initializing OmniClaw...")
        
        # Initialize memory
        memory_config = self.config.get("memory", {})
        self.memory = VectorMemory(
            db_path=memory_config.get("db_path", "./memory_db"),
            embedding_provider=memory_config.get("embedding_provider", "ollama")
        )
        logger.info("Vector memory initialized")
        
        # Initialize API pool
        self.api_pool = APIPool()
        for i, api_config in enumerate(self.config.get("apis", [])):
            if api_config.get("key"):
                self.api_pool.add_endpoint(f"api_{i}", api_config)
        
        api_count = len(self.api_pool.endpoints)
        logger.info(f"API pool initialized with {api_count} endpoint(s)")
        
        # Initialize orchestrator
        api_configs = [ep for ep in self.config.get("apis", []) if ep.get("key")]
        
        # Fallback to Ollama if no APIs configured
        if not api_configs:
            logger.info("No API keys found, using Ollama fallback")
            api_configs = [{
                "provider": "ollama",
                "key": "ollama",
                "model": "llama2",
                "base_url": "http://localhost:11434"
            }]
        
        self.orchestrator = HybridHiveOrchestrator(
            api_configs=api_configs,
            memory_db=self.memory
        )
        logger.info("Hybrid Hive orchestrator initialized")
        
        # Initialize messaging gateway
        messaging_config = self.config.get("messaging", {})
        self.messaging = MessagingGateway()
        
        telegram_config = messaging_config.get("telegram", {})
        if telegram_config.get("enabled") and telegram_config.get("token"):
            self.messaging.setup_telegram(
                token=telegram_config["token"],
                allowed_users=telegram_config.get("allowed_users", [])
            )
        
        whatsapp_config = messaging_config.get("whatsapp", {})
        if whatsapp_config.get("enabled"):
            self.messaging.setup_whatsapp(
                allowed_numbers=whatsapp_config.get("allowed_numbers", [])
            )
        
        self.messaging.set_orchestrator(self.orchestrator)
        logger.info("Messaging gateway initialized")
        
        # Register default commands
        self._register_commands()
        
        logger.info("OmniClaw initialization complete")
    
    def _register_commands(self):
        """Register default messaging commands"""
        
        @self.messaging.register_command("status")
        async def cmd_status(command):
            return f"""🤖 OmniClaw Status

Orchestrator: {'Running' if self.orchestrator else 'Not initialized'}
APIs: {len(self.api_pool.endpoints) if self.api_pool else 0} connected
Memory: {self.memory.get_stats() if self.memory else 'Not initialized'}
Messaging: {self.messaging.get_status() if self.messaging else 'Not initialized'}
"""
        
        @self.messaging.register_command("task")
        async def cmd_task(command):
            if not command.args:
                return "❌ Please provide a task description"
            
            goal = " ".join(command.args)
            task = await self.orchestrator.execute_goal(goal)
            return f"✅ Task started: {task.id}\nGoal: {goal[:100]}..."
        
        @self.messaging.register_command("memory")
        async def cmd_memory(command):
            if not self.memory:
                return "❌ Memory not initialized"
            
            stats = self.memory.get_stats()
            return f"""🧠 Memory Stats

Conversations: {stats['conversations']}
Tasks: {stats['tasks']}
Knowledge: {stats['knowledge_items']}
Total Embeddings: {stats['total_embeddings']}
FAISS Enabled: {stats['faiss_enabled']}
"""
        
        @self.messaging.register_command("apis")
        async def cmd_apis(command):
            if not self.api_pool:
                return "❌ API pool not initialized"
            
            stats = self.api_pool.get_stats()
            result = "🔗 API Status\n\n"
            
            for ep_id, ep_stats in stats.get("endpoints", {}).items():
                status_emoji = "🟢" if ep_stats["status"] == "healthy" else "🔴"
                result += f"{status_emoji} {ep_stats['provider']}/{ep_stats['model']}\n"
                result += f"   Requests: {ep_stats['requests']}, Errors: {ep_stats['errors']}\n\n"
            
            return result
    
    async def start(self):
        """Start all services"""
        logger.info("Starting OmniClaw services...")
        self.running = True
        
        # Start messaging gateway
        if self.messaging:
            await self.messaging.start()
        
        # Start orchestrator
        if self.orchestrator:
            asyncio.create_task(self.orchestrator.start())
        
        logger.info("OmniClaw services started")
    
    async def stop(self):
        """Stop all services"""
        logger.info("Stopping OmniClaw services...")
        self.running = False
        
        if self.messaging:
            await self.messaging.stop()
        
        if self.orchestrator:
            self.orchestrator.stop()
        
        logger.info("OmniClaw services stopped")
    
    async def execute_task(self, goal: str, context: Dict = None) -> Any:
        """Execute a task through the orchestrator"""
        if not self.orchestrator:
            raise RuntimeError("Orchestrator not initialized")
        
        return await self.orchestrator.execute_goal(goal, context)
    
    async def interactive_chat(self):
        """Run interactive chat session"""
        print("\n🤖 OmniClaw Interactive Chat")
        print("Type 'exit' or 'quit' to end the session\n")
        
        while self.running:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    break
                
                if not user_input:
                    continue
                
                print("🤖 Thinking...")
                
                task = await self.execute_task(user_input)
                
                if task.final_result:
                    if isinstance(task.final_result, dict):
                        print(f"\n🤖 {task.final_result.get('summary', str(task.final_result))}\n")
                    else:
                        print(f"\n🤖 {task.final_result}\n")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
        
        print("\nGoodbye! 👋")


def main():
    parser = argparse.ArgumentParser(
        description="OmniClaw: The Hybrid Hive AI Agent System"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file",
        default=os.environ.get("OMNICLAW_CONFIG")
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Status command
    subparsers.add_parser("status", help="Show system status")
    
    # Task command
    task_parser = subparsers.add_parser("task", help="Execute a task")
    task_parser.add_argument("goal", nargs="+", help="Task goal/description")
    task_parser.add_argument("--context", "-ctx", help="JSON context data")
    
    # Chat command
    subparsers.add_parser("chat", help="Start interactive chat")
    
    # Daemon command
    subparsers.add_parser("daemon", help="Run as daemon")
    
    # API management
    api_parser = subparsers.add_parser("api", help="API management")
    api_subparsers = api_parser.add_subparsers(dest="api_command")
    api_subparsers.add_parser("list", help="List configured APIs")
    api_subparsers.add_parser("add", help="Add API")
    api_subparsers.add_parser("remove", help="Remove API")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize OmniClaw
    app = OmniClaw(config_path=args.config)
    
    # Run command
    if args.command == "daemon":
        # Run as daemon
        asyncio.run(app.initialize())
        asyncio.run(app.start())
        
        # Keep running
        try:
            while app.running:
                asyncio.sleep(1)
        except KeyboardInterrupt:
            asyncio.run(app.stop())
    
    elif args.command == "chat":
        asyncio.run(app.initialize())
        asyncio.run(app.start())
        asyncio.run(app.interactive_chat())
        asyncio.run(app.stop())
    
    elif args.command == "task":
        goal = " ".join(args.goal)
        context = json.loads(args.context) if args.context else {}
        
        asyncio.run(app.initialize())
        
        async def run_task():
            task = await app.execute_task(goal, context)
            print(json.dumps({
                "task_id": task.id,
                "goal": task.goal,
                "status": "completed" if task.completed_at else "failed",
                "duration": task.completed_at - task.created_at if task.completed_at else None,
                "result": task.final_result
            }, indent=2))
        
        asyncio.run(run_task())
    
    elif args.command == "status":
        asyncio.run(app.initialize())
        
        async def show_status():
            print("\n🤖 OmniClaw Status\n")
            print(f"Config: {args.config or 'default'}")
            print(f"Memory DB: {app.config.get('memory', {}).get('db_path')}")
            print(f"APIs: {len(app.config.get('apis', []))} configured")
            
            if app.memory:
                stats = app.memory.get_stats()
                print(f"\nMemory Stats:")
                print(f"  Conversations: {stats['conversations']}")
                print(f"  Tasks: {stats['tasks']}")
                print(f"  Knowledge: {stats['knowledge_items']}")
            
            print()
        
        asyncio.run(show_status())
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
