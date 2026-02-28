#!/usr/bin/env python3
"""
OmniClaw: The Hybrid Hive AI Agent System
Main entry point
"""

import asyncio
import argparse
import json
import logging
import sys
import os
import websockets
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add core to path
sys.path.insert(0, str(Path(__file__).parent))

from core.orchestrator import HybridHiveOrchestrator
from core.memory import VectorMemory
from core.api_pool import APIPool
from core.messaging_gateway import MessagingGateway

# New modules (ported from reference bots)
try:
    from core.security import SecurityLayer
    from core.skills.registry import ToolRegistry, get_tool_registry
    from core.skills.loader import SkillLoader
    from core.scheduler.cron import CronScheduler
    from core.scheduler.heartbeat import HeartbeatService
    from core.security.doctor import SecurityDoctor
except ImportError as e:
    print(f"⚠️ WARNING: Failed to load enhancement modules: {e}")

# System Pre-flight Checks
def preflight_checks():
    """Verify system requirements before loading heavy modules"""
    if sys.version_info < (3, 9):
        print("❌ CRITICAL ERROR: OmniClaw requires Python 3.9 or higher.")
        print(f"Current version: {sys.version.split(' ')[0]}")
        sys.exit(1)
        
    try:
        import requests
        import aiohttp
        import numpy
        import pydantic
    except ImportError as e:
        print(f"❌ CRITICAL ERROR: Missing core dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        sys.exit(1)

# Run preflight BEFORE loading advanced features
preflight_checks()

# Advanced Features (Loaded safely)
try:
    from core.reasoning_config import ReasoningLock, ReasoningConfig
    from core.context_mapper import ContextMapper
    from core.autonomous_fix import AutonomousFix
    from core.audit_diff import AuditDiff
    from core.temporal_memory import TemporalContext
    from core.decision_archaeology import DecisionArchaeologist
    from core.pattern_sentinel import PatternSentinel
    from core.echo_chambers import EchoChamber
    from core.living_docs import LivingDocumentation
    from core.semantic_diff import SemanticDiff
    from core.companion import CompanionLoop
except ImportError as e:
    print(f"⚠️ WARNING: Failed to load some advanced features: {e}")
    print("Some modules (like GUI or Local LLMs) may be disabled.")

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
        self.ws_clients = set()
        self.ws_server = None
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        
        # New subsystems (from reference bots)
        self.security: SecurityLayer = None
        self.tool_registry: ToolRegistry = None
        self.skill_loader: SkillLoader = None
        self.cron_scheduler: CronScheduler = None
        self.heartbeat: HeartbeatService = None
        
        # Advanced Features Init (Wrapped in try/catch for stability)
        try:
            # We check if classes exist because their imports might have failed
            if 'ReasoningLock' in globals(): self.reasoning_lock = ReasoningLock()
            if 'ContextMapper' in globals(): self.context_mapper = ContextMapper(Path.cwd())
            if 'AutonomousFix' in globals(): self.autonomous_fix = AutonomousFix(Path.cwd())
            if 'AuditDiff' in globals(): self.audit_diff = AuditDiff()
            if 'TemporalContext' in globals(): self.temporal_context = TemporalContext()
            if 'DecisionArchaeologist' in globals(): self.decision_archaeologist = DecisionArchaeologist()
            if 'PatternSentinel' in globals(): self.pattern_sentinel = PatternSentinel()
            if 'EchoChamber' in globals(): self.echo_chamber = EchoChamber()
            if 'LivingDocumentation' in globals(): self.living_docs = LivingDocumentation(str(Path.cwd()))
            if 'SemanticDiff' in globals(): self.semantic_diff = SemanticDiff()
            if 'CompanionLoop' in globals(): self.companion_loop = CompanionLoop()
        except Exception as e:
            logger.error(f"Failed to initialize one or more advanced features: {e}")
            logger.warning("Proceeding with core features only.")
    
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
            },
            "security": {
                "workspace_dir": "./workspace",
                "sandbox_enabled": True,
                "max_iterations": 15,
                "max_tokens_per_session": 50000,
                "session_timeout": 300
            },
            "skills": {
                "directory": "~/.omniclaw/skills",
                "auto_load": True
            },
            "scheduler": {
                "cron_enabled": True,
                "heartbeat_enabled": True,
                "heartbeat_interval": 1800
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
    
    async def websocket_handler(self, websocket, path=None):
        """Handle incoming WebSocket connections from the Tauri Mission Control GUI."""
        self.ws_clients.add(websocket)
        client_id = f"Client-{len(self.ws_clients)}"
        logger.info(f"GUI {client_id} connected via WebSocket")
        
        try:
            # Send initial swarm status
            status_update = json.dumps({
                "type": "swarm_status",
                "engines": [
                    {
                        "id": "omniclaw-core",
                        "name": "OmniClaw Core Engine",
                        "provider": "local",
                        "model": "Hybrid",
                        "status": "online",
                        "load": len(self.orchestrator.active_tasks) / 10 if hasattr(self.orchestrator, 'active_tasks') else 0.1,
                        "temperature": 0.0,
                        "lastPing": int(datetime.now().timestamp() * 1000),
                        "capabilities": ["control", "orchestration"]
                    }
                ],
                "activeWorkers": len([w for w in self.orchestrator.workers.values() if w.status == "busy"]) if hasattr(self.orchestrator, 'workers') else 0,
                "queueDepth": len(self.orchestrator.task_queue._queue) if hasattr(self.orchestrator, 'task_queue') else 0,
                "totalTokens": 0
            })
            await websocket.send(status_update)

            async for message in websocket:
                data = json.loads(message)
                msg_type = data.get("type")
                payload = data.get("payload", {})
                msg_id = data.get("id")

                if msg_type == "chat_message":
                    user_msg = payload.get("message", "")
                    tool_id = payload.get("toolId", "general")
                    
                    # Log message to terminal stream automatically
                    await self.broadcast_terminal("command", user_msg, tool_id)
                    
                    # Ensure orchestrator processes the task
                    task = await self.execute_task(user_msg)
                    result = task.final_result if task else "No result generated."
                    if isinstance(result, dict):
                         result = result.get("summary", "") or result.get("detailed_results", str(result))

                    # Broadcast the response back to chat stream
                    response_payload = {
                        "type": "chat_response",
                        "content": result,
                        "toolId": tool_id,
                        "metadata": {
                            "engine": task.assigned_engine if hasattr(task, 'assigned_engine') else "System"
                        }
                    }
                    await websocket.send(json.dumps(response_payload))

                elif msg_type == "activate_tool":
                    tool = payload.get("toolId")
                    logger.info(f"Tauri GUI requested activation of profile: {tool}")
                    await self.broadcast_terminal("system", f"Activating Profile: {tool}")

                elif msg_type == "deactivate_tool":
                    tool = payload.get("toolId")
                    logger.info(f"Tauri GUI requested deactivation of profile: {tool}")
                    await self.broadcast_terminal("system", f"Deactivating Profile: {tool}")

        except websockets.exceptions.ConnectionClosedOK:
            pass
        except Exception as e:
            logger.error(f"WebSocket Error: {e}")
        finally:
            self.ws_clients.remove(websocket)
            logger.info(f"GUI {client_id} disconnected")

    async def broadcast_terminal(self, msg_type: str, content: str, tool_id: str = None):
        """Broadcast terminal messages to all connected Tauri GUI clients"""
        if not self.ws_clients:
            return
            
        payload = {
            "type": "terminal_output",
            "message": {
                "id": f"msg-{int(datetime.now().timestamp()*1000)}",
                "timestamp": int(datetime.now().timestamp() * 1000),
                "type": msg_type,
                "content": content,
                "toolId": tool_id
            }
        }
        message_str = json.dumps(payload)
        for client in self.ws_clients:
            try:
                await client.send(message_str)
            except Exception:
                pass

    class OutputStreamAdapter:
        """Custom stream adapter to capture terminal output and send to websockets."""
        def __init__(self, original_stream, broadcast_func, msg_type):
            self.original_stream = original_stream
            self.broadcast_func = broadcast_func
            self.msg_type = msg_type

        def write(self, data):
            self.original_stream.write(data)
            if data and data.strip():
                # Strip ANSI escape codes if present
                clean_data = data.encode('ascii', 'ignore').decode('ascii').strip()
                if clean_data:
                    # Creating a fire-and-forget task for broadcasting
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(self.broadcast_func(self.msg_type, clean_data))
                    except RuntimeError:
                        pass # Loop might be closed

        def flush(self):
            self.original_stream.flush()

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
        for ep in api_configs:
            if "persona" in self.config:
                ep["persona"] = self.config["persona"]
        
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
        
        # --- Advanced Features ---
        adv_config = self.config.get("advanced", {})
        
        # Reasoning Lock
        reasoning_cfg = adv_config.get("reasoning", {})
        self.reasoning_lock = ReasoningLock(ReasoningConfig(
            min_tokens_per_response=reasoning_cfg.get("min_tokens", 500),
            enforce_chain_of_thought=reasoning_cfg.get("chain_of_thought", True),
            require_self_verification=reasoning_cfg.get("self_verification", True),
        ))
        
        # Context Mapper
        self.context_mapper = ContextMapper()
        
        # Autonomous Fix
        self.autonomous_fix = AutonomousFix(
            max_retries=adv_config.get("autofix", {}).get("max_retries", 3),
            sandbox_mode=adv_config.get("autofix", {}).get("sandbox", True),
        )
        
        # Audit Diff
        self.audit_diff = AuditDiff(
            backup_root=adv_config.get("audit_diff", {}).get("backup_root", "./.omniclaw_backups")
        )
        
        # Temporal Context
        self.temporal_context = TemporalContext(
            storage_dir=os.path.join(memory_config.get("db_path", "./memory_db"), "snapshots"),
            memory=self.memory,
        )
        
        # Decision Archaeology
        self.decision_archaeologist = DecisionArchaeologist(
            storage_dir=os.path.join(memory_config.get("db_path", "./memory_db"), "decisions"),
            memory=self.memory,
        )
        self.context_mapper.decision_store = self.decision_archaeologist
        
        # Pattern Sentinel
        self.pattern_sentinel = PatternSentinel(
            storage_dir=os.path.join(memory_config.get("db_path", "./memory_db"), "patterns"),
            memory=self.memory,
        )
        
        # Echo Chambers
        self.echo_chamber = EchoChamber(
            default_strategies=adv_config.get("echo_chambers", {}).get(
                "strategies", ["speed", "readability", "robust"]
            )
        )
        
        # Living Documentation
        self.living_docs = LivingDocumentation()
        
        # Semantic Diff
        self.semantic_diff = SemanticDiff()
        
        # Companion Loop
        self.companion_loop = CompanionLoop(
            config=self.config,
            orchestrator=self.orchestrator,
            messaging=self.messaging
        )
        
        logger.info("Advanced features initialized")
        
        # --- New Subsystems (ported from reference bots) ---
        try:
            # Security Layer
            sec_config = self.config.get("security", {})
            if 'SecurityLayer' in globals():
                self.security = SecurityLayer(
                    workspace_dir=sec_config.get("workspace_dir", "./workspace")
                )
                self.security.session_budget.max_iterations = sec_config.get("max_iterations", 15)
                self.security.session_budget.max_tokens_per_session = sec_config.get("max_tokens_per_session", 50000)
                self.security.session_budget.session_timeout = sec_config.get("session_timeout", 300)
                logger.info("🛡️  Security Layer initialized (5 layers active)")
            
            # Tool Registry
            if 'ToolRegistry' in globals():
                self.tool_registry = get_tool_registry()
                logger.info(f"🔧 Tool Registry initialized ({len(self.tool_registry.tools)} tools)")
            
            # Skill Loader
            skills_config = self.config.get("skills", {})
            if 'SkillLoader' in globals() and skills_config.get("auto_load", True):
                self.skill_loader = SkillLoader(skills_config.get("directory", "~/.omniclaw/skills"))
                loaded = self.skill_loader.load_all(self.tool_registry)
                if loaded > 0:
                    logger.info(f"📦 Loaded {loaded} custom skill(s)")
            
            # Cron Scheduler
            sched_config = self.config.get("scheduler", {})
            if 'CronScheduler' in globals() and sched_config.get("cron_enabled", True):
                self.cron_scheduler = CronScheduler(
                    db_path=os.path.join(memory_config.get("db_path", "./memory_db"), "omniclaw.db"),
                    on_execute=lambda msg: self.orchestrator.execute_goal(msg) if self.orchestrator else None,
                )
                logger.info("⏰ Cron Scheduler initialized")
            
            # Heartbeat Service
            if 'HeartbeatService' in globals() and sched_config.get("heartbeat_enabled", True):
                self.heartbeat = HeartbeatService(
                    workspace=sec_config.get("workspace_dir", "./workspace"),
                    on_execute=lambda msg: self.orchestrator.execute_goal(msg) if self.orchestrator else None,
                    interval_s=sched_config.get("heartbeat_interval", 1800),
                )
                logger.info(f"🫀 Heartbeat Service initialized (every {sched_config.get('heartbeat_interval', 1800)}s)")
        except Exception as e:
            logger.error(f"Failed to initialize new subsystems: {e}")
            logger.warning("Proceeding with core + advanced features only.")
        
        # Register default commands
        self._register_commands()
        
        logger.info("OmniClaw v4.0.0 initialization complete")
    
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
        
        # --- Advanced Feature Commands ---
        
        @self.messaging.register_command("context")
        async def cmd_context(command):
            root = command.kwargs.get("dir", ".")
            doc = self.context_mapper.generate_project_doc(root)
            return f"📋 Project Context Generated\n\n{doc[:3000]}..."
        
        @self.messaging.register_command("snapshot")
        async def cmd_snapshot(command):
            if not command.args:
                # Resume mode
                projects = self.temporal_context.list_projects()
                if not projects:
                    return "📸 No snapshots found. Use: /snapshot <project> <task>"
                result = "📸 Available Projects:\n\n"
                for p in projects:
                    result += f"  • {p['project']} ({p['snapshot_count']} snapshots)\n"
                    result += f"    Last: {p['latest_task']}\n"
                return result
            
            project = command.args[0]
            task_desc = " ".join(command.args[1:]) if len(command.args) > 1 else "Manual snapshot"
            snap_id = self.temporal_context.save_snapshot(
                project=project, task=task_desc, state={"source": "messaging"}
            )
            return f"📸 Snapshot saved: {snap_id}"
        
        @self.messaging.register_command("decisions")
        async def cmd_decisions(command):
            if command.args:
                query = " ".join(command.args)
                results = await self.decision_archaeologist.query_decisions(query)
                if not results:
                    return "🏛️ No matching decisions found."
                result = f"🏛️ Decisions matching '{query}':\n\n"
                for d in results[:5]:
                    result += f"  [{d['impact'].upper()}] {d['decision']}\n"
                    result += f"  └─ {d['reasoning'][:100]}\n\n"
                return result
            
            recent = self.decision_archaeologist.get_recent(limit=5)
            if not recent:
                return "🏛️ No decisions recorded yet."
            result = "🏛️ Recent Decisions:\n\n"
            for d in recent:
                result += f"  [{d['impact'].upper()}] {d['decision']}\n"
            return result
        
        @self.messaging.register_command("patterns")
        async def cmd_patterns(command):
            stats = self.pattern_sentinel.get_stats()
            return (f"🛡️ Pattern Sentinel\n\n"
                    f"Learned patterns: {stats['learned_patterns']}\n"
                    f"Built-in patterns: {stats['builtin_patterns']}")
        
        @self.messaging.register_command("explore")
        async def cmd_explore(command):
            if not command.args:
                return "🔮 Usage: /explore <task description>"
            task = " ".join(command.args)
            return f"🔮 Spawning shadow agents for: {task[:100]}...\n(Use programmatic API for full results)"
        
        @self.messaging.register_command("docs")
        async def cmd_docs(command):
            root = command.kwargs.get("dir", ".")
            generated = self.living_docs.update_docs(root)
            return f"📚 Documentation updated: {len(generated)} diagrams generated"
        
        @self.messaging.register_command("diff")
        async def cmd_diff(command):
            stats = self.semantic_diff.get_stats()
            return (f"🔬 Semantic Diff\n\n"
                    f"Analyses performed: {stats['total_analyses']}\n"
                    f"LLM available: {stats['has_llm']}")
        
        # --- New Subsystem Commands ---
        
        @self.messaging.register_command("security")
        async def cmd_security(command):
            if not self.security:
                return "❌ Security layer not initialized"
            if command.args and command.args[0] == "audit":
                doctor = SecurityDoctor(
                    workspace_dir=self.config.get("security", {}).get("workspace_dir", "./workspace")
                )
                report = doctor.run_audit()
                return f"🛡️ Security Audit\n\n{report['summary']}"
            status = self.security.get_status()
            return (f"🛡️ Security Status\n\n"
                    f"Layers active: {status['layers_active']}\n"
                    f"Workspace: {status['workspace']}\n"
                    f"Active sessions: {status['active_sessions']}\n"
                    f"Blocked patterns: {status['blocked_patterns']}\n"
                    f"Injection patterns: {status['injection_patterns']}")
        
        @self.messaging.register_command("cron")
        async def cmd_cron(command):
            if not self.cron_scheduler:
                return "❌ Cron scheduler not initialized"
            if not command.args:
                jobs = await self.cron_scheduler.list_jobs()
                if not jobs:
                    return "⏰ No cron jobs. Use: /cron add <name> <message> [interval_seconds]"
                result = "⏰ Cron Jobs\n\n"
                for j in jobs:
                    enabled = "✅" if j['enabled'] else "❌"
                    result += f"{enabled} #{j['id']} {j['name']}\n"
                    result += f"   {j['message'][:80]}\n"
                    if j.get('cron_expr'):
                        result += f"   Cron: {j['cron_expr']}\n"
                    elif j.get('interval_seconds'):
                        result += f"   Every: {j['interval_seconds']}s\n"
                    result += "\n"
                return result
            action = command.args[0]
            if action == "add" and len(command.args) >= 3:
                name = command.args[1]
                message = " ".join(command.args[2:])
                interval = int(command.kwargs.get("interval", 3600))
                job_id = await self.cron_scheduler.add_job(name, message, interval_seconds=interval)
                return f"⏰ Added cron job #{job_id}: {name}"
            elif action == "remove" and len(command.args) >= 2:
                job_id = int(command.args[1])
                await self.cron_scheduler.remove_job(job_id)
                return f"⏰ Removed cron job #{job_id}"
            return "⏰ Usage: /cron [add <name> <message>|remove <id>]"
        
        @self.messaging.register_command("skills")
        async def cmd_skills(command):
            if not self.tool_registry:
                return "❌ Tool registry not initialized"
            status = self.tool_registry.get_status()
            result = f"📦 Skills & Tools ({status['total_tools']} registered)\n\n"
            for name in status['tool_names']:
                confirm = " [⚠️ needs confirm]" if name in status['confirmation_required'] else ""
                result += f"  • {name}{confirm}\n"
            if self.skill_loader:
                loader_status = self.skill_loader.get_status()
                result += f"\nSkills dir: {loader_status['skills_dir']}\n"
                result += f"Loaded: {len(loader_status['loaded'])} | Failed: {len(loader_status['failed'])}"
            return result
        
        @self.messaging.register_command("heartbeat")
        async def cmd_heartbeat(command):
            if not self.heartbeat:
                return "❌ Heartbeat service not initialized"
            if command.args and command.args[0] == "trigger":
                result = await self.heartbeat.trigger_now()
                return f"🫀 Heartbeat triggered\n\n{result or 'No tasks found.'}" 
            status = self.heartbeat.get_status()
            return (f"🫀 Heartbeat Service\n\n"
                    f"Enabled: {status['enabled']}\n"
                    f"Running: {status['running']}\n"
                    f"Interval: {status['interval_s']}s\n"
                    f"Ticks: {status['tick_count']}\n"
                    f"Last action: {status['last_action']}\n"
                    f"File: {status['heartbeat_file']}\n"
                    f"File exists: {status['heartbeat_file_exists']}")
    
    async def start(self):
        """Start all services"""
        logger.info("Starting OmniClaw services...")
        self.running = True

        # Start WebSocket server for Tauri GUI on port 8765
        try:
            self.ws_server = await websockets.serve(self.websocket_handler, "localhost", 8765)
            logger.info("WebSocket Server listening on ws://localhost:8765 for Tauri GUI.")
            
            # Intercept stdout/stderr for GUI telemetry
            sys.stdout = self.OutputStreamAdapter(self.original_stdout, self.broadcast_terminal, "stdout")
            sys.stderr = self.OutputStreamAdapter(self.original_stderr, self.broadcast_terminal, "stderr")
        except Exception as e:
            logger.error(f"Failed to start WebSocket server on 8765: {e}")
        
        # Start messaging gateway
        if self.messaging:
            await self.messaging.start()
        
        # Start orchestrator
        if self.orchestrator:
            asyncio.create_task(self.orchestrator.start())
            
        # Start Companion
        if self.companion_loop:
            asyncio.create_task(self.companion_loop.start())
        
        # Start Cron Scheduler
        if self.cron_scheduler:
            await self.cron_scheduler.start()
        
        # Start Heartbeat
        if self.heartbeat:
            await self.heartbeat.start()
        
        logger.info("OmniClaw services started")
    
    async def stop(self):
        """Stop all services"""
        logger.info("Stopping OmniClaw services...")
        self.running = False
        
        # Restore original streams
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
        if self.ws_server:
            self.ws_server.close()
            await self.ws_server.wait_closed()
        
        if self.messaging:
            await self.messaging.stop()
        
        if self.orchestrator:
            self.orchestrator.stop()
            
        if self.companion_loop:
            self.companion_loop.stop()
        
        # Stop new subsystems
        if self.cron_scheduler:
            await self.cron_scheduler.stop()
        
        if self.heartbeat:
            self.heartbeat.stop()
        
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
    
    # GUI command
    subparsers.add_parser("gui", help="Launch the Mission Control Web GUI")
    
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
        # Interactive Setup
        import yaml
        if not app.config.get("persona") or not app.config.get("persona", {}).get("user_name"):
            print("\n👋 Welcome to OmniClaw v3.2.0!")
            print("Let's set up your AI Companion persona.")
            user_name = input("What is your name? ").strip()
            ai_name = input("What would you like to call me? ").strip()
            ai_role = input("What role should I act as? (e.g. AI companion, gf, bf, friend, agent): ").strip()
            
            app.config["persona"] = {
                "ai_name": ai_name or "OmniClaw",
                "user_name": user_name or "User",
                "ai_role": ai_role or "AI orchestration manager",
                "proactive_messaging": True,
                "schedule_awareness": True
            }
            
            config_path = args.config or "config.yaml"
            try:
                with open(config_path, "w") as f:
                    yaml.dump(app.config, f)
                print(f"✅ Persona saved to {config_path}!\n")
            except Exception as e:
                print(f"⚠️ Could not save to {config_path}: {e}\n")
                
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
        
    elif args.command == "gui":
        print("\n🚀 Launching OmniClaw Mission Control GUI...\n")
        asyncio.run(app.initialize())
        
        try:
            from core.dashboard import MissionControl
            from nicegui import ui, app as nicegui_app
            
            dashboard = MissionControl(app)
            
            # Hook shutting down OmniClaw into NiceGUI's shutdown event
            nicegui_app.on_shutdown(app.stop)
            
            show_gui = True
            if os.name == 'posix' and not os.environ.get('DISPLAY') and not os.environ.get('WAYLAND_DISPLAY'):
                print("⚠️ Headless environment detected. Running NiceGUI in headless mode (no auto-open).")
                show_gui = False
            
            ui.run(title="OmniClaw Mission Control", port=8080, dark=True, reload=False, show=show_gui)
        except ImportError:
            print("❌ NiceGUI is not installed. Please run: pip install nicegui")
            sys.exit(1)
    
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
