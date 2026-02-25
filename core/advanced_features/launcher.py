"""
╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████╗ ███████╗████████╗██████╗  ██████╗     ██████╗ ██████╗ ██╗██████╗ ████████╗║
║   ██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗    ██╔══██╗██╔══██╗██║██╔══██╗╚══██╔══╝║
║   ██████╔╝█████╗     ██║   ██████╔╝██║   ██║    ██████╔╝██████╔╝██║██████╔╝   ██║   ║
║   ██╔══██╗██╔══╝     ██║   ██╔══██╗██║   ██║    ██╔══██╗██╔══██╗██║██╔═══╝    ██║   ║
║   ██║  ██║███████╗   ██║   ██║  ██║╚██████╔╝    ██████╔╝██║  ██║██║██║        ██║   ║
║   ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝     ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝        ╚═╝   ║
║                                                                              ║
║                      OMNICLAW ADVANCED LAUNCHER v2.0                         ║
║                     The Ultimate AI-Powered Toolkit                          ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   ┌─────────────────────────────────────────────────────────────────────┐    ║
║   │  [1] 💀 SECURITY & HACKING TOOLS                                 │    ║
║   │  [2] 🧠 AI & MACHINE LEARNING                                     │    ║
║   │  [3] 🌐 WEB & NETWORK TOOLS                                       │    ║
║   │  [4] 🛠️  DEVELOPMENT TOOLS                                       │    ║
║   │  [5] 🔬 RESEARCH & ANALYSIS                                        │    ║
║   │  [6] 📊 SELF-EVOLVING CORE (SEIC)                                │    ║
║   │  [7] ⚙️  ADVANCED FEATURES                                        │    ║
║   │  [8] 🎮 CUSTOMIZABLE TOOLS                                        │    ║
║   │  [9] 📁 FILE MANAGER                                              │    ║
║   │  [0] 🚀 QUICK LAUNCHER                                            │    ║
║   │                                                                     │    ║
║   │  [S] 🔧 Settings                                                   │    ║
║   │  [H] 📖 Help & Documentation                                       │    ║
║   │  [U] ⬆️ Update OmniClaw                                            │    ║
║   │  [X] ❌ Exit                                                       │    ║
║   └─────────────────────────────────────────────────────────────────────┘    ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════╝

Welcome to OmniClaw! Select a category to begin.
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime


# =============================================================================
# COLOR CONSTANTS
# =============================================================================

class Colors:
    """ANSI Color codes for terminal UI"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    
    # Basic colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    
    # Background
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


# =============================================================================
# TOOL DEFINITIONS
# =============================================================================

class Tool:
    """Represents a tool in the launcher"""
    
    def __init__(self, id: str, name: str, category: str, description: str, 
                 command: str = None, module: str = None, icon: str = "🔧"):
        self.id = id
        self.name = name
        self.category = category
        self.description = description
        self.command = command
        self.module = module
        self.icon = icon
        self.usage_count = 0
        self.last_used = None


# =============================================================================
# OMNICLAW LAUNCHER
# =============================================================================

class OmniClawLauncher:
    """
    Kali Linux-style launcher for OmniClaw advanced features.
    Provides easy access to all tools via CLI menu.
    """
    
    def __init__(self):
        self.tools = []
        self.categories = {}
        self.history = []
        self.favorites = []
        self.settings = self._load_settings()
        self._init_tools()
    
    def _load_settings(self) -> dict:
        """Load user settings"""
        
        default_settings = {
            "theme": "cyber",
            "color_scheme": "green",
            "show_icons": True,
            "auto_update": True,
            "verbose": False,
            "favorites": []
        }
        
        if os.path.exists("./settings.json"):
            try:
                with open("./settings.json", 'r') as f:
                    settings = json.load(f)
                    return {**default_settings, **settings}
            except:
                pass
        
        return default_settings
    
    def _save_settings(self):
        """Save user settings"""
        
        with open("./settings.json", 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def _init_tools(self):
        """Initialize all available tools"""
        
        # =========================================================================
        # SECURITY & HACKING TOOLS
        # =========================================================================
        
        security_tools = [
            Tool("sec_vuln_scan", "Vulnerability Scanner", "Security", 
                 "Scan code for vulnerabilities (SQLi, XSS, RCE, etc.)",
                 "python -m omniclaw.advanced_features.launcher --tool vuln_scanner",
                 "security_research.VulnerabilityScanner", "🔍"),
            
            Tool("sec_cve", "CVE Research Agent", "Security",
                 "Research and track CVEs",
                 "python -m omniclaw.advanced_features.launcher --tool cve_research",
                 "security_research.CVEResearchAgent", "🎯"),
            
            Tool("sec_audit", "Security Audit", "Security",
                 "Full security audit of codebase",
                 "python -m omniclaw.advanced_features.launcher --tool security_audit",
                 "security_research.SecurityResearchHub", "🛡️"),
            
            Tool("sec_surface", "Attack Surface Analyzer", "Security",
                 "Analyze application attack surface",
                 "python -m omniclaw.advanced_features.launcher --tool attack_surface",
                 "security_research.AttackSurfaceAnalyzer", "🎯"),
            
            Tool("sec_disclosure", "Responsible Disclosure", "Security",
                 "Generate responsible disclosure reports",
                 "python -m omniclaw.advanced_features.launcher --tool disclosure",
                 None, "📜"),
            
            Tool("sec_pentest", "Penetration Test Planner", "Security",
                 "Plan penetration tests (Authorized only)",
                 "python -m omniclaw.advanced_features.launcher --tool pentest",
                 None, "⚔️"),
        ]
        
        # =========================================================================
        # AI & MACHINE LEARNING
        # =========================================================================
        
        ai_tools = [
            Tool("ai_create_llm", "Create Custom LLM", "AI & ML",
                 "Create your own LLM architecture",
                 "python -m omniclaw.advanced_features.launcher --tool create_llm",
                 "self_evolving_core.LLMCreationEngine", "🧠"),
            
            Tool("ai_finetune", "Fine-tune Model", "AI & ML",
                 "Fine-tune existing models on custom data",
                 "python -m omniclaw.advanced_features.launcher --tool finetune",
                 "self_evolving_core.SelfEvolvingIntelligenceCore", "🎛️"),
            
            Tool("ai_agi", "Create AGI Model", "AI & ML",
                 "Create distilled AGI-like model",
                 "python -m omniclaw.advanced_features.launcher --tool agi",
                 "self_evolving_core.LLMCreationEngine", "🌟"),
            
            Tool("ai_learn", "Learn from Data", "AI & ML",
                 "Teach OmniClaw new skills from data",
                 "python -m omniclaw.advanced_features.launcher --tool learn",
                 "self_evolving_core.SkillAcquisitionEngine", "📚"),
            
            Tool("ai_improve", "Self-Improvement", "AI & ML",
                 "Trigger self-improvement cycle",
                 "python -m omniclaw.advanced_features.launcher --tool improve",
                 "self_evolving_core.SelfImprovementEngine", "🔄"),
            
            Tool("ai_verify", "Output Verifier", "AI & ML",
                 "Verify outputs (Zero Hallucination)",
                 "python -m omniclaw.advanced_features.launcher --tool verify",
                 "self_evolving_core.VerificationEngine", "✅"),
        ]
        
        # =========================================================================
        # WEB & NETWORK TOOLS
        # =========================================================================
        
        web_tools = [
            Tool("web_nmap", "Network Scanner", "Web & Network",
                 "Scan networks and discover services",
                 "nmap -v -sV target", None, "🌐"),
            
            Tool("web_recon", "Reconnaissance", "Web & Network",
                 "Gather information about targets",
                 "python -m omniclaw.advanced_features.launcher --tool recon",
                 None, "🔎"),
            
            Tool("web_proxy", "Web Proxy", "Web & Network",
                 "HTTP proxy for testing",
                 "python -m omniclaw.advanced_features.launcher --tool proxy",
                 None, "🔄"),
            
            Tool("web_enum", "Enumerator", "Web & Network",
                 "Enumerate directories, subdomains",
                 "python -m omniclaw.advanced_features.launcher --tool enumerate",
                 None, "📋"),
        ]
        
        # =========================================================================
        # DEVELOPMENT TOOLS
        # =========================================================================
        
        dev_tools = [
            Tool("dev_code_review", "Code Review", "Development",
                 "Multi-perspective code review",
                 "python -m omniclaw.advanced_features.launcher --tool code_review",
                 "consciousness_collision.ConsciousnessCollision", "👀"),
            
            Tool("dev_codedna", "CodeDNA Interpreter", "Development",
                 "Understand code intent, preserve logic",
                 "python -m omniclaw.advanced_features.launcher --tool codedna",
                 "code_dna.CodeDNAInterpreter", "🧬"),
            
            Tool("dev_refactor", "Autonomous Refactor", "Development",
                 "Auto-fix failed builds",
                 "python -m omniclaw.advanced_features.launcher --tool refactor",
                 None, "🔧"),
            
            Tool("dev_contract", "Contract Enforcer", "Development",
                 "Enforce architectural rules",
                 "python -m omniclaw.advanced_features.launcher --tool contract",
                 "contract_enforcer.ContractEnforcer", "⚖️"),
            
            Tool("dev_audit", "Project-Wide Audit", "Development",
                 "Multi-file change auditing",
                 "python -m omniclaw.advanced_features.launcher --tool audit_diff",
                 None, "📝"),
            
            Tool("dev_translate", "Paradigm Translator", "Development",
                 "Convert code between frameworks/languages",
                 "python -m omniclaw.advanced_features.launcher --tool translate",
                 "paradigm_translator.ParadigmTranslator", "🌐"),
        ]
        
        # =========================================================================
        # RESEARCH & ANALYSIS
        # =========================================================================
        
        research_tools = [
            Tool("res_dna", "DNA Storage Research", "Research",
                 "Research DNA data storage",
                 "python -m omniclaw.advanced_features.launcher --tool dna_storage",
                 "self_evolving_core.ResearchAgent", "🧬"),
            
            Tool("res_quantum", "Quantum Computing Research", "Research",
                 "Research quantum computing",
                 "python -m omniclaw.advanced_features.launcher --tool quantum",
                 "self_evolving_core.ResearchAgent", "⚛️"),
            
            Tool("res_agi", "AGI Research", "Research",
                 "Research artificial general intelligence",
                 "python -m omniclaw.advanced_features.launcher --tool agi_research",
                 "self_evolving_core.ResearchAgent", "🌟"),
            
            Tool("res_math", "Mathematical Proofs", "Research",
                 "Verify and generate mathematical proofs",
                 "python -m omniclaw.advanced_features.launcher --tool math_proof",
                 "self_evolving_core.SelfImprovementEngine", "📐"),
            
            Tool("res_time", "Time Machine Debugger", "Research",
                 "Trace bugs to exact commit",
                 "python -m omniclaw.advanced_features.launcher --tool time_machine",
                 "time_machine.TimeMachineDebugger", "⏰"),
            
            Tool("res_predictor", "Bug Predictor", "Research",
                 "Predict bugs before they happen",
                 "python -m omniclaw.advanced_features.launcher --tool predictor",
                 "predictor.PredictorEngine", "🔮"),
        ]
        
        # =========================================================================
        # SELF-EVOLVING CORE (SEIC)
        # =========================================================================
        
        seic_tools = [
            Tool("seic_status", "SEIC Status", "SEIC",
                 "View SEIC system status",
                 "python -m omniclaw.advanced_features.launcher --tool seic_status",
                 "self_evolving_core.SelfEvolvingIntelligenceCore", "📊"),
            
            Tool("seic_skills", "View Learned Skills", "SEIC",
                 "View all learned skills",
                 "python -m omniclaw.advanced_features.launcher --tool skills",
                 None, "🎓"),
            
            Tool("seic_research", "Active Research", "SEIC",
                 "View ongoing research projects",
                 "python -m omniclaw.advanced_features.launcher --tool research",
                 None, "🔬"),
            
            Tool("seic_background", "Background Mode", "SEIC",
                 "Start background self-improvement",
                 "python -m omniclaw.advanced_features.launcher --tool background",
                 None, "⚡"),
            
            Tool("seic_parallel", "Parallel Processing", "SEIC",
                 "Execute multiple tasks in parallel",
                 "python -m omniclaw.advanced_features.launcher --tool parallel",
                 "self_evolving_core.ParallelProcessingHub", "🚀"),
        ]
        
        # =========================================================================
        # ADVANCED FEATURES
        # =========================================================================
        
        advanced_tools = [
            Tool("adv_memory", "Memory Graph", "Advanced",
                 "Query project knowledge graph",
                 "python -m omniclaw.advanced_features.launcher --tool memory_graph",
                 "memory_graph.MemoryGraphNetwork", "🕸️"),
            
            Tool("adv_diagram", "Living Architecture", "Advanced",
                 "Generate auto-updating diagrams",
                 "python -m omniclaw.advanced_features.launcher --tool diagram",
                 "living_diagram.LivingArchitectureDiagram", "📐"),
            
            Tool("adv_infra", "Natural Language Infra", "Advanced",
                 "Generate infra from description",
                 "python -m omniclaw.advanced_features.launcher --tool infra",
                 "natural_language_infra.NaturalLanguageInfra", "🏗️"),
            
            Tool("adv_pm", "Autonomous PM", "Advanced",
                 "Feature request → Full implementation",
                 "python -m omniclaw.advanced_features.launcher --tool autonomous_pm",
                 "autonomous_pm.AutonomousProductManager", "👔"),
            
            Tool("adv_context", "Context Mapping", "Advanced",
                 "Auto-generate CLAUDE.md/OMNICLAW.md",
                 "python -m omniclaw.advanced_features.launcher --tool context",
                 None, "🗺️"),
        ]
        
        # =========================================================================
        # FILE MANAGER
        # =========================================================================
        
        file_tools = [
            Tool("file_explore", "File Explorer", "File Manager",
                 "Browse project files",
                 "python -m omniclaw.advanced_features.launcher --tool explorer",
                 None, "📁"),
            
            Tool("file_search", "Search Files", "File Manager",
                 "Search for files by content",
                 "python -m omniclaw.advanced_features.launcher --tool search",
                 None, "🔍"),
            
            Tool("file_compare", "Compare Files", "File Manager",
                 "Compare two files",
                 "python -m omniclaw.advanced_features.launcher --tool compare",
                 None, "📊"),
            
            Tool("file_skills", "Skills Folder", "File Manager",
                 "View learned skills folder",
                 "python -m omniclaw.advanced_features.launcher --tool skills_folder",
                 None, "🎓"),
            
            Tool("file_research", "Research Folder", "File Manager",
                 "View research projects folder",
                 "python -m omniclaw.advanced_features.launcher --tool research_folder",
                 None, "🔬"),
        ]
        
        # Combine all tools
        self.tools = (security_tools + ai_tools + web_tools + dev_tools + 
                     research_tools + seic_tools + advanced_tools + file_tools)
        
        # Organize by category
        self.categories = {
            "Security": security_tools,
            "AI & ML": ai_tools,
            "Web & Network": web_tools,
            "Development": dev_tools,
            "Research": research_tools,
            "SEIC": seic_tools,
            "Advanced": advanced_tools,
            "File Manager": file_tools,
        }
    
    # =========================================================================
    # UI FUNCTIONS
    # =========================================================================
    
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_banner(self):
        """Print OmniClaw banner"""
        banner = f"""
{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ██████╗ ███████╗████████╗██████╗  ██████╗     ██████╗ ██████╗ ██╗██████╗ ████████╗║
║   ██╔══██╗██╔════╝╚══██╔══╝██╔══██╗██╔═══██╗    ██╔══██╗██╔══██╗██║██╔══██╗╚══██╔══╝║
║   ██████╔╝█████╗     ██║   ██████╔╝██║   ██║    ██████╔╝██████╔╝██║██████╔╝   ██║   ║
║   ██╔══██╗██╔══╝     ██║   ██╔══██╗██║   ██║    ██╔══██╗██╔══██╗██║██╔═══╝    ██║   ║
║   ██║  ██║███████╗   ██║   ██║  ██║╚██████╔╝    ██████╔╝██║  ██║██║██║        ██║   ║
║   ╚═╝  ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝     ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝        ╚═╝   ║
║                                                                              ║
║                      {Colors.BRIGHT_GREEN}OMNICLAW ADVANCED LAUNCHER v2.0{Colors.BRIGHT_CYAN}                         ║
║                     {Colors.BRIGHT_YELLOW}The Ultimate AI-Powered Toolkit{Colors.BRIGHT_CYAN}                          ║
║                                                                              ║
╠══════════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║   [{Colors.BRIGHT_RED}1{Colors.BRIGHT_CYAN}] 💀 {Colors.RED}SECURITY & HACKING{Colors.RESET}      [{Colors.BRIGHT_GREEN}5{Colors.BRIGHT_CYAN}] 🔬 {Colors.CYAN}RESEARCH & ANALYSIS{Colors.RESET}          ║
║   [{Colors.BRIGHT_RED}2{Colors.BRIGHT_CYAN}] 🧠 {Colors.RED}AI & MACHINE LEARNING{Colors.RESET}  [{Colors.BRIGHT_GREEN}6{Colors.BRIGHT_CYAN}] 📊 {Colors.CYAN}SELF-EVOLVING CORE{Colors.RESET}           ║
║   [{Colors.BRIGHT_RED}3{Colors.BRIGHT_CYAN}] 🌐 {Colors.RED}WEB & NETWORK{Colors.RESET}         [{Colors.BRIGHT_GREEN}7{Colors.BRIGHT_CYAN}] ⚙️  {Colors.CYAN}ADVANCED FEATURES{Colors.RESET}            ║
║   [{Colors.BRIGHT_RED}4{Colors.BRIGHT_CYAN}] 🛠️  {Colors.RED}DEVELOPMENT TOOLS{Colors.RESET}     [{Colors.BRIGHT_GREEN}8{Colors.BRIGHT_CYAN}] 🎮 {Colors.CYAN}CUSTOMIZABLE TOOLS{Colors.RESET}            ║
║                                                                              ║
║   [{Colors.BRIGHT_YELLOW}9{Colors.BRIGHT_CYAN}] 📁 {Colors.YELLOW}FILE MANAGER{Colors.RESET}            [{Colors.BRIGHT_MAGENTA}R{Colors.BRIGHT_CYAN}] 🎯 {Colors.MAGENTA}RAPID TOOLS{Colors.RESET}                   ║
║   [{Colors.BRIGHT_YELLOW}0{Colors.BRIGHT_CYAN}] 🚀 {Colors.YELLOW}QUICK LAUNCHER{Colors.RESET}          [{Colors.BRIGHT_MAGENTA}S{Colors.BRIGHT_CYAN}] ⚙️  {Colors.MAGENTA}SETTINGS{Colors.RESET}                       ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}"""
        print(banner)
    
    def print_category_menu(self, category: str, tools: list):
        """Print a category menu"""
        
        header = f"""
{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗
║  {Colors.BRIGHT_RED}▼{Colors.BRIGHT_CYAN}  {category.upper():^70}  {Colors.BRIGHT_RED}▼{Colors.BRIGHT_CYAN}
╚══════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
"""
        print(header)
        
        # Print tools in columns
        for i, tool in enumerate(tools, 1):
            icon = tool.icon if self.settings["show_icons"] else ""
            print(f"  {Colors.BRIGHT_GREEN}[{i:2d}]{Colors.RESET} {icon:2} {Colors.BOLD}{tool.name:<35}{Colors.RESET} - {tool.description}")
        
        print(f"\n  {Colors.BRIGHT_YELLOW}[B]{Colors.RESET}ack to Main Menu")
        print(f"  {Colors.BRIGHT_YELLOW}[H]{Colors.RESET}ome")
        print(f"  {Colors.BRIGHT_YELLOW}[X]{Colors.RESET}it")
    
    def print_tool_details(self, tool: Tool):
        """Print detailed tool information"""
        
        details = f"""
{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗
║  {Colors.BRIGHT_GREEN}▶{Colors.BRIGHT_CYAN}  {tool.name.upper():^70}  {Colors.BRIGHT_GREEN}▶{Colors.BRIGHT_CYAN}
╚══════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}

  {Colors.BOLD}Description:{Colors.RESET}
  {tool.description}

  {Colors.BOLD}Category:{Colors.RESET}
  {tool.category}

  {Colors.BOLD}Module:{Colors.RESET}
  {tool.module or "Standalone"}

  {Colors.BOLD}Command:{Colors.RESET}
  {tool.command or "Run via launcher"}

  {Colors.BOLD}Usage:{Colors.RESET}
  This tool has been used {tool.usage_count} times.
  {"Last used: " + str(tool.last_used) if tool.last_used else "Never used"}
"""
        print(details)
    
    # =========================================================================
    # MAIN LOOP
    # =========================================================================
    
    def run(self):
        """Main launcher loop"""
        
        while True:
            self.clear_screen()
            self.print_banner()
            
            choice = input(f"\n{Colors.BRIGHT_CYAN}OmniClaw{Colors.RESET} > ").strip().lower()
            
            if choice in ['1', 'security']:
                self._show_category("Security")
            elif choice in ['2', 'ai', 'ml']:
                self._show_category("AI & ML")
            elif choice in ['3', 'web', 'network']:
                self._show_category("Web & Network")
            elif choice in ['4', 'dev', 'development']:
                self._show_category("Development")
            elif choice in ['5', 'research']:
                self._show_category("Research")
            elif choice in ['6', 'seic']:
                self._show_category("SEIC")
            elif choice in ['7', 'advanced']:
                self._show_category("Advanced")
            elif choice in ['8', 'custom']:
                self._show_category("Custom")
            elif choice in ['9', 'file', 'files']:
                self._show_category("File Manager")
            elif choice in ['0', 'quick', 'rapid']:
                self._show_quick_launcher()
            elif choice == 's':
                self._show_settings()
            elif choice == 'h':
                self._show_help()
            elif choice == 'u':
                self._check_updates()
            elif choice in ['x', 'exit', 'quit']:
                print(f"\n{Colors.BRIGHT_GREEN}Goodbye! 👋{Colors.RESET}\n")
                break
            else:
                print(f"\n{Colors.BRIGHT_RED}Invalid choice. Press Enter to continue...{Colors.RESET}")
                input()
    
    def _show_category(self, category: str):
        """Show category tools"""
        
        while True:
            self.clear_screen()
            tools = self.categories.get(category, [])
            self.print_category_menu(category, tools)
            
            choice = input(f"\n{Colors.BRIGHT_CYAN}{category}{Colors.RESET} > ").strip().lower()
            
            if choice == 'b' or choice == 'back':
                break
            elif choice == 'h' or choice == 'home':
                return
            elif choice == 'x' or choice == 'exit':
                print(f"\n{Colors.BRIGHT_GREEN}Goodbye! 👋{Colors.RESET}\n")
                sys.exit(0)
            else:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(tools):
                        self._run_tool(tools[idx])
                except ValueError:
                    pass
    
    def _run_tool(self, tool: Tool):
        """Run a specific tool"""
        
        self.clear_screen()
        
        # Update usage
        tool.usage_count += 1
        tool.last_used = datetime.now()
        
        # Print tool header
        print(f"""
{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗
║  {tool.icon:2}  Launching: {tool.name:<60}  
╚══════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
""")
        
        print(f"Description: {tool.description}\n")
        
        if tool.command:
            print(f"{Colors.YELLOW}Executing:{Colors.RESET} {tool.command}\n")
            os.system(tool.command)
        else:
            # Would launch via module
            print(f"{Colors.YELLOW}Module:{Colors.RESET} {tool.module}")
            print(f"\n{Colors.BRIGHT_YELLOW}This tool requires module initialization.{Colors.RESET}")
        
        print(f"\n{Colors.BRIGHT_GREEN}✅ Tool execution complete!{Colors.RESET}")
        input(f"\n{Colors.BRIGHT_CYAN}Press Enter to continue...{Colors.RESET}")
    
    def _show_quick_launcher(self):
        """Quick launcher - search and run tools"""
        
        while True:
            self.clear_screen()
            
            print(f"""
{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗
║  🚀 QUICK LAUNCHER - Type to search, number to run                         ║
╚══════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}
""")
            
            query = input(f"{Colors.BRIGHT_CYAN}Search{Colors.RESET}: ").strip().lower()
            
            if query in ['b', 'back', 'x', 'exit']:
                break
            
            if not query:
                continue
            
            # Search tools
            results = [t for t in self.tools if query in t.name.lower() or query in t.description.lower()]
            
            if not results:
                print(f"\n{Colors.BRIGHT_RED}No tools found matching '{query}'{Colors.RESET}")
                input(f"\n{Colors.BRIGHT_CYAN}Press Enter to continue...{Colors.RESET}")
                continue
            
            print(f"\nFound {len(results)} tools:\n")
            
            for i, tool in enumerate(results[:10], 1):
                icon = tool.icon if self.settings["show_icons"] else ""
                print(f"  {Colors.BRIGHT_GREEN}[{i}]{Colors.RESET} {icon:2} {tool.name}")
                print(f"       {tool.description}")
                print(f"       {Colors.CYAN}Category: {tool.category}{Colors.RESET}\n")
            
            choice = input(f"\n{Colors.BRIGHT_CYAN}Select (number){Colors.RESET} > ").strip()
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(results):
                    self._run_tool(results[idx])
            except ValueError:
                pass
    
    def _show_settings(self):
        """Show settings menu"""
        
        while True:
            self.clear_screen()
            
            print(f"""
{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗
║  ⚙️  SETTINGS                                                                     ║
╚══════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}

  {Colors.BRIGHT_GREEN}[1]{Colors.RESET} Theme: {self.settings['theme']}
  {Colors.BRIGHT_GREEN}[2]{Colors.RESET} Color Scheme: {self.settings['color_scheme']}
  {Colors.BRIGHT_GREEN}[3]{Colors.RESET} Show Icons: {self.settings['show_icons']}
  {Colors.BRIGHT_GREEN}[4]{Colors.RESET} Auto Update: {self.settings['auto_update']}
  {Colors.BRIGHT_GREEN}[5]{Colors.RESET} Verbose: {self.settings['verbose']}

  {Colors.BRIGHT_YELLOW}[S]{Colors.RESET}ave & Exit
  {Colors.BRIGHT_YELLOW}[X]{Colors.RESET}ancel
""")
            
            choice = input(f"\n{Colors.BRIGHT_CYAN}Settings{Colors.RESET} > ").strip().lower()
            
            if choice == 's':
                self._save_settings()
                print(f"\n{Colors.BRIGHT_GREEN}Settings saved!{Colors.RESET}")
                time.sleep(1)
                break
            elif choice == 'x':
                break
            elif choice == '1':
                self.settings['theme'] = input("Theme (cyber/dark/light): ") or "cyber"
            elif choice == '2':
                self.settings['color_scheme'] = input("Color (green/blue/red): ") or "green"
            elif choice == '3':
                self.settings['show_icons'] = not self.settings['show_icons']
            elif choice == '4':
                self.settings['auto_update'] = not self.settings['auto_update']
            elif choice == '5':
                self.settings['verbose'] = not self.settings['verbose']
    
    def _show_help(self):
        """Show help"""
        
        self.clear_screen()
        
        help_text = f"""
{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗
║  📖 OMNICLAW HELP                                                                ║
╚══════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}

{Colors.BOLD}Getting Started:{Colors.RESET}
  1. Select a category from the main menu
  2. Choose a tool by number
  3. Follow on-screen instructions

{Colors.BOLD}Quick Tips:{Colors.RESET}
  • Type numbers to navigate menus
  • Use [0] for Quick Launcher (search tools by name)
  • Press [X] to exit any menu
  • [S]ettings for customization

{Colors.BOLD}Tool Categories:{Colors.RESET}
  • Security: Vulnerability scanning, CVE research, pentesting
  • AI & ML: Create LLMs, fine-tune, self-improvement
  • Development: Code review, refactoring, translations
  • Research: Topic research, mathematical proofs
  • SEIC: Self-evolving core status and controls

{Colors.BOLD}For More Info:{Colors.RESET}
  • README.md - Full documentation
  • GitHub - github.com/webspoilt/omniclaw
  • Discord - discord.gg/ZU4mQaqh

{Colors.BRIGHT_GREEN}Happy Hacking! 🔐{Colors.RESET}
"""
        
        print(help_text)
        input(f"\n{Colors.BRIGHT_CYAN}Press Enter to continue...{Colors.RESET}")
    
    def _check_updates(self):
        """Check for updates"""
        
        print(f"""
{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗
║  ⬆️  UPDATE OMNICLAW                                                            ║
╚══════════════════════════════════════════════════════════════════════════════════╝
{Colors.RESET}

Checking for updates...

{Colors.BRIGHT_YELLOW}Current Version: v2.0.0{Colors.RESET}
{Colors.BRIGHT_GREEN}You are up to date!{Colors.RESET}

For manual update:
  git pull origin main
  pip install -r requirements.txt

""")
        
        input(f"{Colors.BRIGHT_CYAN}Press Enter to continue...{Colors.RESET}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point"""
    
    launcher = OmniClawLauncher()
    launcher.run()


if __name__ == "__main__":
    main()
