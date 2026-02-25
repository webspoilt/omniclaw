import asyncio
from nicegui import ui, app as nicegui_app
import logging
import sys

logger = logging.getLogger("MissionControl")

class MissionControl:
    def __init__(self, omniclaw_app):
        self.app = omniclaw_app
        self.log_lines = []
        self._setup_ui()
        
    def _setup_ui(self):
        ui.colors(primary='#4facfe', secondary='#00f2fe', accent='#8a2be2', dark='#121212', positive='#00f2fe')
        ui.add_head_html('<style>body { background-color: #121212; color: white; }</style>')
        
        # Header
        with ui.header(elevated=True).classes('items-center justify-between bg-[#1e1e1e] border-b border-[#333] px-4 py-2'):
            with ui.row().classes('items-center gap-4'):
                ui.icon('rocket_launch', size='sm').classes('text-secondary')
                ui.label('OmniClaw Mission Control').classes('text-xl font-bold tracking-wider text-white')
            
            with ui.row().classes('items-center gap-2'):
                ui.label('Engine Status:').classes('text-gray-400')
                self.status_label = ui.label('OFFLINE').classes('text-red-500 font-bold')
                
        # Main Layout
        with ui.row().classes('w-full h-[calc(100vh-80px)] p-6 gap-6 flex-nowrap'):
            # Left pane: Controls & Swarm
            with ui.column().classes('w-1/3 h-full gap-6 flex-shrink-0'):
                self._build_control_panel()
                self._build_swarm_panel()
                self._build_tools_panel()
                
            # Right pane: Chat & Console
            with ui.column().classes('w-2/3 h-full gap-6 flex-grow'):
                self._build_chat_panel()
                self._build_console_panel()
                
    def _build_control_panel(self):
        with ui.card().classes('w-full bg-[#1e1e1e] border border-[#333] shadow-lg'):
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.icon('power_settings_new', size='sm').classes('text-gray-300')
                ui.label('Core Engine Controls').classes('text-lg font-bold text-white')
                
            with ui.row().classes('w-full justify-between gap-4'):
                ui.button('Ignite Swarm', icon='play_arrow', on_click=self.start_app, color='positive').classes('flex-grow')
                ui.button('Halt Engine', icon='stop', on_click=self.stop_app, color='red-500').classes('flex-grow')
            
    def _build_swarm_panel(self):
        with ui.card().classes('w-full flex-grow bg-[#1e1e1e] border border-[#333] shadow-lg overflow-hidden flex flex-col'):
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.icon('hub', size='sm').classes('text-gray-300')
                ui.label('Agent Swarm Status').classes('text-lg font-bold text-white')
                
            self.agent_grid = ui.column().classes('w-full flex-grow flex-nowrap overflow-y-auto pr-2 gap-4')
            ui.timer(2.0, self._update_agent_grid)
            
    def _build_tools_panel(self):
        with ui.card().classes('w-full bg-[#1e1e1e] border border-[#333] shadow-lg'):
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.icon('build', size='sm').classes('text-gray-300')
                ui.label('Quick Workflows').classes('text-lg font-bold text-white')
                
            ui.button('Run Deep Network Recon', icon='radar', on_click=lambda: self._execute_tool_task('Perform a full nmap and subfinder recon on localhost.'), color='primary').classes('w-full mb-3')
            ui.button('Audit Security Posture', icon='security', on_click=lambda: self._execute_tool_task('Perform a basic security audit of my open network ports and report vulnerabilities.'), color='primary').classes('w-full mb-3')
            ui.button('Check System Health', icon='health_and_safety', on_click=lambda: self._execute_tool_task('Check the current system RAM, CPU, and disk usage and assess health.'), color='primary').classes('w-full')

    def _build_chat_panel(self):
        with ui.card().classes('w-full h-[60%] bg-[#1e1e1e] border border-[#333] shadow-lg flex flex-col'):
            with ui.row().classes('items-center justify-between w-full mb-2'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('chat', size='sm').classes('text-gray-300')
                    ui.label('OmniClaw Mission Interface').classes('text-lg font-bold text-white')
                
            self.chat_messages = ui.column().classes('w-full flex-grow overflow-y-auto bg-[#121212] p-4 rounded-lg border border-[#333]')
            
            with ui.row().classes('w-full mt-4 items-center gap-3'):
                self.chat_input = ui.input(placeholder='Ask OmniClaw or assign a mission...').classes('flex-grow').on('keydown.enter', self.send_message)
                ui.button(icon='send', on_click=self.send_message, color='secondary').classes('rounded-full')
                
    def _build_console_panel(self):
        with ui.card().classes('w-full h-[35%] bg-[#1e1e1e] border border-[#333] shadow-lg flex flex-col'):
            with ui.row().classes('items-center gap-2 mb-2'):
                ui.icon('terminal', size='sm').classes('text-gray-300')
                ui.label('Live Telemetry & Logs').classes('text-lg font-bold text-white')
                
            self.console_log = ui.log().classes('w-full flex-grow bg-black text-[#00f2fe] font-mono text-sm p-3 rounded-lg border border-[#333]')
            
            # Hook into normal print
            self.original_stdout = sys.stdout
            sys.stdout.write = self._log_to_console
            sys.stderr.write = self._log_to_console
            
    def _log_to_console(self, msg):
        if msg.strip() and msg != '\n':
            if hasattr(self, 'console_log'):
                self.console_log.push(msg.strip())
        self.original_stdout.write(msg)
        
    async def start_app(self):
        if not self.app.running:
            self.status_label.set_text('INITIALIZING...')
            self.status_label.classes(replace='text-yellow-500 font-bold')
            await self.app.start()
            self.status_label.set_text('ONLINE')
            self.status_label.classes(replace='text-green-500 font-bold')
            if hasattr(self, 'console_log'):
                self.console_log.push("[✅] OmniClaw Swarm Initialized and Online.")
            
    async def stop_app(self):
        if self.app.running:
            await self.app.stop()
            self.status_label.set_text('OFFLINE')
            self.status_label.classes(replace='text-red-500 font-bold')
            if hasattr(self, 'console_log'):
                self.console_log.push("[🛑] OmniClaw Swarm Terminated.")
            
    def _update_agent_grid(self):
        self.agent_grid.clear()
        if not self.app.running:
            with self.agent_grid:
                with ui.row().classes('items-center gap-2 p-2'):
                    ui.icon('power_off', size='sm').classes('text-gray-500')
                    ui.label('Swarm offline. Click Ignite Swarm.').classes('text-gray-500 italic')
            return
            
        with self.agent_grid:
            with ui.row().classes('w-full bg-[#121212] p-3 rounded border border-[#333] items-center justify-between'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('psychology', size='sm').classes('text-secondary')
                    ui.label('Manager Node').classes('text-white font-semibold')
                
                if self.app.orchestrator:
                    task_count = len(self.app.orchestrator.active_tasks) if hasattr(self.app.orchestrator, 'active_tasks') else 0
                    ui.label(f'Active Maps: {task_count}').classes('text-gray-400 text-xs')
                
            ui.label('Worker Nodes').classes('text-gray-400 text-sm font-bold mt-2 uppercase tracking-wide')
            
            for name, ep in self.app.api_pool.endpoints.items():
                with ui.row().classes('w-full bg-[#121212] p-3 rounded border border-[#333] items-center justify-between'):
                    with ui.column().classes('gap-0'):
                        ui.label(f"{ep.get('provider', 'Unknown')}").classes('text-white font-semibold')
                        ui.label(f"{ep.get('model', 'Model')}").classes('text-gray-400 text-xs')
                    
                    status = ep.get('status', 'offline')
                    status_col = 'text-green-400' if status == 'healthy' else 'text-red-400'
                    ui.label(status.upper()).classes(f'{status_col} text-xs font-bold px-2 py-1 bg-black rounded')
                    
    async def send_message(self):
        msg = self.chat_input.value
        if not msg.strip(): return
        
        self.chat_input.value = ''
        with self.chat_messages:
            ui.chat_message(msg, name='Commander', sent=True, avatar='https://api.dicebear.com/7.x/bottts/svg?seed=user').classes('text-white')
            
        if not self.app.running:
            with self.chat_messages:
                ui.chat_message("OmniClaw is offline. Please ignite swarm first.", name='System', avatar='https://api.dicebear.com/7.x/bottts/svg?seed=system').classes('text-red-400')
            return
            
        try:
            with self.chat_messages:
                thinking = ui.chat_message('Analyzing vectors...', name='OmniClaw', avatar='https://api.dicebear.com/7.x/bottts/svg?seed=omni')
                
            # Await the orchestrator task
            task = await self.app.execute_task(msg)
            result_str = task.final_result
            if isinstance(result_str, dict):
                result_str = result_str.get("summary", "") or result_str.get("detailed_results", str(result_str))
                
            thinking.delete()
            with self.chat_messages:
                ui.chat_message(result_str, name='OmniClaw', avatar='https://api.dicebear.com/7.x/bottts/svg?seed=omni')
        except Exception as e:
            logger.error(f"Chat error: {e}")
            with self.chat_messages:
                ui.chat_message(f"Critical Subsystem Fault: {str(e)}", name='System Error', avatar='https://api.dicebear.com/7.x/bottts/svg?seed=error').classes('text-red-400')
                
    def _execute_tool_task(self, prompt: str):
        self.chat_input.value = prompt
        # We can't await directly in a lambda, so we schedule the coroutine via nicegui's background task wrapper or asyncio.create_task
        asyncio.create_task(self.send_message())
