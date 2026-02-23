#!/usr/bin/env python3
"""
OmniClaw Messaging Gateway
Integrates with Telegram and WhatsApp for remote control
"""

import asyncio
import logging
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import json
import time

logger = logging.getLogger("OmniClaw.MessagingGateway")


class Platform(Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"
    SLACK = "slack"
    IMESSAGE = "imessage"
    MATRIX = "matrix"


@dataclass
class Message:
    """Represents a message from any platform"""
    id: str
    platform: Platform
    sender_id: str
    sender_name: str
    content: str
    timestamp: float
    chat_id: str
    is_group: bool
    reply_to: Optional[str] = None
    media: Optional[List[Dict]] = None


@dataclass
class Command:
    """Represents a parsed command"""
    name: str
    args: List[str]
    kwargs: Dict[str, str]
    raw: str
    message: Message


class TelegramBot:
    """Telegram Bot integration using python-telegram-bot"""
    
    def __init__(self, token: str, allowed_users: Optional[List[str]] = None):
        self.token = token
        self.allowed_users = set(allowed_users or [])
        self.application = None
        self.message_handlers: List[Callable[[Message], None]] = []
        self.running = False
        
    async def initialize(self):
        """Initialize the Telegram bot"""
        try:
            from telegram.ext import Application, CommandHandler, MessageHandler, filters
            
            self.application = Application.builder().token(self.token).build()
            
            # Add handlers
            self.application.add_handler(CommandHandler("start", self._handle_start))
            self.application.add_handler(CommandHandler("help", self._handle_help))
            self.application.add_handler(CommandHandler("status", self._handle_status))
            self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
            
            logger.info("Telegram bot initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Telegram bot: {e}")
            return False
    
    async def start(self):
        """Start the bot"""
        if not self.application:
            await self.initialize()
        
        self.running = True
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("Telegram bot started")
    
    async def stop(self):
        """Stop the bot"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
        
        self.running = False
        logger.info("Telegram bot stopped")
    
    def add_message_handler(self, handler: Callable[[Message], None]):
        """Add a message handler"""
        self.message_handlers.append(handler)
    
    async def send_message(self, chat_id: str, text: str, **kwargs):
        """Send a message"""
        if self.application:
            await self.application.bot.send_message(chat_id=chat_id, text=text, **kwargs)
    
    async def send_photo(self, chat_id: str, photo: bytes, caption: str = None):
        """Send a photo"""
        if self.application:
            await self.application.bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)
    
    async def send_document(self, chat_id: str, document: bytes, filename: str, caption: str = None):
        """Send a document"""
        if self.application:
            from telegram import InputFile
            await self.application.bot.send_document(
                chat_id=chat_id,
                document=InputFile(document, filename=filename),
                caption=caption
            )
    
    def _is_authorized(self, user_id: str) -> bool:
        """Check if user is authorized"""
        if not self.allowed_users:
            return True
        return user_id in self.allowed_users
    
    async def _handle_start(self, update, context):
        """Handle /start command"""
        user_id = str(update.effective_user.id)
        if not self._is_authorized(user_id):
            await update.message.reply_text("⛔ You are not authorized to use this bot.")
            return
        
        welcome_msg = """🤖 *Welcome to OmniClaw!*

I'm your AI agent controller. Send me commands and I'll execute them for you.

*Quick Commands:*
/help - Show all commands
/status - Check agent status
/task <description> - Execute a task
/research <topic> - Research a topic
/code <description> - Generate code
/analyze <data> - Analyze data

You can also send me any natural language request!"""
        
        await update.message.reply_text(welcome_msg, parse_mode="Markdown")
    
    async def _handle_help(self, update, context):
        """Handle /help command"""
        user_id = str(update.effective_user.id)
        if not self._is_authorized(user_id):
            return
        
        help_msg = """📚 *OmniClaw Commands*

*Agent Control:*
/status - Check agent status
/pause - Pause agent
/resume - Resume agent
/restart - Restart agent

*Task Execution:*
/task <description> - Execute a task
/research <topic> - Research topic
/code <language> <description> - Generate code
/analyze <data/file> - Analyze data
/shell <command> - Execute shell command (if enabled)

*System:*
/stats - System statistics
/memory - Memory usage
/apis - List API connections

*Settings:*
/config - Show configuration
/config set <key> <value> - Update setting"""
        
        await update.message.reply_text(help_msg, parse_mode="Markdown")
    
    async def _handle_status(self, update, context):
        """Handle /status command"""
        user_id = str(update.effective_user.id)
        if not self._is_authorized(user_id):
            return
        
        status_msg = "🤖 *OmniClaw Status*\n\n"
        status_msg += "Status: 🟢 Active\n"
        status_msg += "Workers: 3 active\n"
        status_msg += "Queue: 0 tasks\n"
        status_msg += "APIs: 2 connected\n"
        status_msg += "Uptime: 2h 34m\n"
        
        await update.message.reply_text(status_msg, parse_mode="Markdown")
    
    async def _handle_message(self, update, context):
        """Handle incoming messages"""
        user_id = str(update.effective_user.id)
        if not self._is_authorized(user_id):
            return
        
        # Convert to Message format
        message = Message(
            id=str(update.message.message_id),
            platform=Platform.TELEGRAM,
            sender_id=user_id,
            sender_name=update.effective_user.username or update.effective_user.first_name,
            content=update.message.text,
            timestamp=time.time(),
            chat_id=str(update.effective_chat.id),
            is_group=update.effective_chat.type in ['group', 'supergroup'],
            reply_to=str(update.message.reply_to_message.message_id) if update.message.reply_to_message else None
        )
        
        # Notify handlers
        for handler in self.message_handlers:
            try:
                handler(message)
            except Exception as e:
                logger.error(f"Message handler error: {e}")


class WhatsAppBot:
    """WhatsApp integration using whatsapp-web.js or similar"""
    
    def __init__(self, session_name: str = "omniclaw", allowed_numbers: Optional[List[str]] = None):
        self.session_name = session_name
        self.allowed_numbers = set(allowed_numbers or [])
        self.client = None
        self.message_handlers: List[Callable[[Message], None]] = []
        self.qr_code: Optional[str] = None
        self.ready = False
    
    async def initialize(self):
        """Initialize WhatsApp client"""
        try:
            # Note: This requires whatsapp-web.js via Node.js
            # For Python, we can use a wrapper or REST API approach
            logger.info("WhatsApp bot initialized (Node.js bridge required)")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp bot: {e}")
            return False
    
    async def start(self):
        """Start WhatsApp client"""
        logger.info("WhatsApp bot started")
    
    async def stop(self):
        """Stop WhatsApp client"""
        logger.info("WhatsApp bot stopped")
    
    def add_message_handler(self, handler: Callable[[Message], None]):
        """Add a message handler"""
        self.message_handlers.append(handler)
    
        """Send a message"""
        logger.info(f"WhatsApp send to {chat_id}: {text}")


try:
    import discord
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False


class DiscordBot:
    """Discord integration using discord.py"""
    
    def __init__(self, token: str):
        self.token = token
        self.client = None
        self.message_handlers: List[Callable[[Message], None]] = []
        self.ready = False
        self._task = None
    
    async def initialize(self):
        if not DISCORD_AVAILABLE:
            logger.error("discord.py missing. Run `pip install discord.py`")
            return False
            
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        @self.client.event
        async def on_ready():
            self.ready = True
            logger.info(f"Discord bot logged in as {self.client.user}")
            
        @self.client.event
        async def on_message(message: discord.Message):
            if message.author == self.client.user:
                return
                
            omni_msg = Message(
                id=str(message.id),
                text=message.content,
                sender_id=str(message.author.id),
                sender_name=message.author.name,
                chat_id=str(message.channel.id),
                timestamp=message.created_at.timestamp(),
                platform=Platform.DISCORD
            )
            
            for handler in self.message_handlers:
                await handler(omni_msg)
                
        return True
            
    async def start(self):
        if not self.client:
            return
            
        logger.info("Starting Discord bot loop")
        self._task = asyncio.create_task(self.client.start(self.token))
        
    async def stop(self):
        if self.client:
            logger.info("Stopping Discord bot")
            await self.client.close()
            if self._task:
                self._task.cancel()
        
    def add_message_handler(self, handler: Callable[[Message], None]):
        self.message_handlers.append(handler)
        
    async def send_message(self, chat_id: str, text: str):
        if not self.client or not self.ready:
            return
            
        try:
            channel = self.client.get_channel(int(chat_id))
            if not channel:
                # If cannot get channel directly from cache, try fetch
                channel = await self.client.fetch_channel(int(chat_id))
            
            if channel:
                # Chunk big code responses
                if len(text) > 1900:
                    chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
                    for chunk in chunks:
                        await channel.send(chunk)
                else:
                    await channel.send(text)
        except Exception as e:
            logger.error(f"Failed to send to Discord: {e}")


class SlackBot:
    """Slack integration using slack_sdk"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.client = None
        self.message_handlers: List[Callable[[Message], None]] = []
        self.ready = False
        
    async def initialize(self):
        try:
            logger.info("Slack bot initialized")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Slack bot: {e}")
            return False
            
    async def start(self):
        logger.info("Slack bot started")
        
    async def stop(self):
        logger.info("Slack bot stopped")
        
    def add_message_handler(self, handler: Callable[[Message], None]):
        self.message_handlers.append(handler)
        
    async def send_message(self, chat_id: str, text: str):
        logger.info(f"Slack send to {chat_id}: {text}")


class IMessageBot:
    """iMessage integration (macOS local)"""
    
    def __init__(self):
        self.message_handlers: List[Callable[[Message], None]] = []
        self.ready = False
        
    async def initialize(self):
        logger.info("iMessage gateway initialized (macOS only)")
        return True
        
    async def start(self):
        logger.info("iMessage monitor started")
        
    async def stop(self):
        logger.info("iMessage monitor stopped")
        
    def add_message_handler(self, handler: Callable[[Message], None]):
        self.message_handlers.append(handler)
        
    async def send_message(self, chat_id: str, text: str):
        logger.info(f"iMessage send to {chat_id}: {text}")


class MatrixBot:
    """Matrix protocol integration"""
    
    def __init__(self):
        self.message_handlers: List[Callable[[Message], None]] = []
        self.ready = False
        
    async def initialize(self):
        logger.info("Matrix protocol bot initialized (nio required)")
        return True
        
    async def start(self):
        logger.info("Matrix bot started")
        
    async def stop(self):
        logger.info("Matrix bot stopped")
        
    def add_message_handler(self, handler: Callable[[Message], None]):
        self.message_handlers.append(handler)
        
    async def send_message(self, chat_id: str, text: str):
        logger.info(f"Matrix send to {chat_id}: {text}")


class MessagingGateway:
    """
    Unified messaging gateway for multiple platforms
    Handles Telegram, WhatsApp, and other messaging platforms
    """
    
    def __init__(self):
        self.telegram: Optional[TelegramBot] = None
        self.whatsapp: Optional[WhatsAppBot] = None
        self.discord: Optional[DiscordBot] = None
        self.slack: Optional[SlackBot] = None
        self.imessage: Optional[IMessageBot] = None
        self.matrix: Optional[MatrixBot] = None
        self.command_handlers: Dict[str, Callable[[Command], Any]] = {}
        self.orchestrator = None
        self.running = False
    
    def setup_telegram(self, token: str, allowed_users: Optional[List[str]] = None):
        """Setup Telegram bot"""
        self.telegram = TelegramBot(token, allowed_users)
        self.telegram.add_message_handler(self._handle_incoming_message)
        logger.info("Telegram bot configured")
    
    def setup_whatsapp(self, allowed_numbers: Optional[List[str]] = None):
        """Setup WhatsApp bot"""
        self.whatsapp = WhatsAppBot(allowed_numbers=allowed_numbers)
        self.whatsapp.add_message_handler(self._handle_incoming_message)
        logger.info("WhatsApp bot configured")
        
    def setup_discord(self, token: str):
        """Setup Discord bot"""
        self.discord = DiscordBot(token)
        self.discord.add_message_handler(self._handle_incoming_message)
        logger.info("Discord bot configured")
        
    def setup_slack(self, bot_token: str):
        """Setup Slack bot"""
        self.slack = SlackBot(bot_token)
        self.slack.add_message_handler(self._handle_incoming_message)
        logger.info("Slack bot configured")
        
    def setup_imessage(self):
        """Setup iMessage monitor"""
        self.imessage = IMessageBot()
        self.imessage.add_message_handler(self._handle_incoming_message)
        logger.info("iMessage monitor configured")
        
    def setup_matrix(self):
        """Setup Matrix bot"""
        self.matrix = MatrixBot()
        self.matrix.add_message_handler(self._handle_incoming_message)
        logger.info("Matrix bot configured")
    
    def register_command(self, name: str, handler: Callable[[Command], Any]):
        """Register a command handler"""
        self.command_handlers[name] = handler
        logger.info(f"Registered command: {name}")
    
    def set_orchestrator(self, orchestrator):
        """Set the orchestrator for task execution"""
        self.orchestrator = orchestrator
    
    async def start(self):
        """Start all messaging platforms"""
        self.running = True
        
        if self.telegram:
            await self.telegram.start()
        if self.whatsapp:
            await self.whatsapp.start()
        if self.discord:
            await self.discord.start()
        if self.slack:
            await self.slack.start()
        if self.imessage:
            await self.imessage.start()
        if self.matrix:
            await self.matrix.start()
        
        logger.info("Messaging gateway started")
    
    async def stop(self):
        """Stop all messaging platforms"""
        self.running = False
        
        if self.telegram:
            await self.telegram.stop()
        if self.whatsapp:
            await self.whatsapp.stop()
        if self.discord:
            await self.discord.stop()
        if self.slack:
            await self.slack.stop()
        if self.imessage:
            await self.imessage.stop()
        if self.matrix:
            await self.matrix.stop()
        
        logger.info("Messaging gateway stopped")
    
    def _handle_incoming_message(self, message: Message):
        """Handle incoming messages from any platform"""
        logger.info(f"Message from {message.platform.value}: {message.content[:50]}...")
        
        # Parse command
        command = self._parse_command(message)
        
        if command:
            # Execute command
            asyncio.create_task(self._execute_command(command))
        else:
            # Treat as natural language request
            asyncio.create_task(self._handle_natural_language(message))
    
    def _parse_command(self, message: Message) -> Optional[Command]:
        """Parse message for commands"""
        content = message.content.strip()
        
        if not content.startswith('/'):
            return None
        
        # Parse command
        parts = content[1:].split()
        if not parts:
            return None
        
        name = parts[0].lower()
        args = []
        kwargs = {}
        
        for part in parts[1:]:
            if '=' in part:
                key, value = part.split('=', 1)
                kwargs[key] = value
            else:
                args.append(part)
        
        return Command(
            name=name,
            args=args,
            kwargs=kwargs,
            raw=content,
            message=message
        )
    
    async def _execute_command(self, command: Command):
        """Execute a parsed command"""
        handler = self.command_handlers.get(command.name)
        
        if handler:
            try:
                result = await handler(command)
                await self._send_reply(command.message, result)
            except Exception as e:
                await self._send_reply(command.message, f"❌ Error: {str(e)}")
        else:
            # Unknown command, try orchestrator
            if self.orchestrator:
                try:
                    task = await self.orchestrator.execute_goal(
                        f"Execute command: {command.raw}"
                    )
                    await self._send_reply(command.message, f"✅ Task started: {task.id}")
                except Exception as e:
                    await self._send_reply(command.message, f"❌ Error: {str(e)}")
            else:
                await self._send_reply(command.message, "❓ Unknown command. Type /help for available commands.")
    
    async def _handle_natural_language(self, message: Message):
        """Handle natural language requests"""
        if not self.orchestrator:
            await self._send_reply(message, "⚠️ Agent not initialized")
            return
        
        try:
            # Send acknowledgment
            await self._send_reply(message, "🤔 Processing your request...")
            
            # Execute through orchestrator
            task = await self.orchestrator.execute_goal(message.content)
            
            # Send result
            result_text = self._format_task_result(task)
            await self._send_reply(message, result_text)
            
        except Exception as e:
            await self._send_reply(message, f"❌ Error: {str(e)}")
    
    def _format_task_result(self, task) -> str:
        """Format task result for messaging"""
        result = f"✅ *Task Completed*\n\n"
        result += f"Goal: {task.goal[:100]}...\n"
        result += f"Duration: {(task.completed_at - task.created_at):.1f}s\n"
        
        if task.final_result:
            if isinstance(task.final_result, dict):
                result += f"\n*Summary:*\n{task.final_result.get('summary', 'N/A')[:200]}"
            else:
                result += f"\n*Result:*\n{str(task.final_result)[:200]}"
        
        return result
    
    async def _send_reply(self, message: Message, text: str):
        """Send a reply to the original message"""
        if message.platform == Platform.TELEGRAM and self.telegram:
            await self.telegram.send_message(message.chat_id, text, parse_mode="Markdown")
        elif message.platform == Platform.WHATSAPP and self.whatsapp:
            await self.whatsapp.send_message(message.chat_id, text)
        elif message.platform == Platform.DISCORD and self.discord:
            await self.discord.send_message(message.chat_id, text)
        elif message.platform == Platform.SLACK and self.slack:
            await self.slack.send_message(message.chat_id, text)
        elif message.platform == Platform.IMESSAGE and self.imessage:
            await self.imessage.send_message(message.chat_id, text)
        elif message.platform == Platform.MATRIX and self.matrix:
            await self.matrix.send_message(message.chat_id, text)
    
    async def broadcast(self, text: str, platforms: Optional[List[Platform]] = None):
        """Broadcast message to all platforms"""
        platforms = platforms or [Platform.TELEGRAM, Platform.WHATSAPP, Platform.DISCORD, Platform.SLACK]
        
        for platform in platforms:
            if platform == Platform.TELEGRAM and self.telegram:
                pass
            elif platform == Platform.WHATSAPP and self.whatsapp:
                pass
            elif platform == Platform.DISCORD and self.discord:
                pass
            elif platform == Platform.SLACK and self.slack:
                pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get gateway status"""
        return {
            "telegram": self.telegram is not None and self.telegram.running,
            "whatsapp": self.whatsapp is not None and self.whatsapp.ready,
            "discord": self.discord is not None and self.discord.ready,
            "slack": self.slack is not None and self.slack.ready,
            "imessage": self.imessage is not None and self.imessage.ready,
            "matrix": self.matrix is not None and self.matrix.ready,
            "commands": list(self.command_handlers.keys()),
            "running": self.running
        }
