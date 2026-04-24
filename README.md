<p align="center">
  <img src="https://raw.githubusercontent.com/webspoilt/omniclaw/main/public/logo.svg" width="180" height="180" alt="OmniClaw Logo">
</p>

<h1 align="center" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 3em; color: #4A90E2; margin-bottom: 0;">OmniClaw</h1>
<h3 align="center" style="font-weight: 300; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #666; margin-top: 5px;">The Hybrid Hive AI Agent System</h3>

<p align="center">
  <a href="https://github.com/webspoilt/omniclaw/releases">
    <img src="https://img.shields.io/badge/version-v4.4.0-blue.svg?style=for-the-badge&logo=appveyor" alt="Version">
  </a>
  <img src="https://img.shields.io/badge/status-active-brightgreen.svg?style=for-the-badge" alt="Status">
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge&logo=open-source-initiative" alt="License">
  </a>
  <a href="https://python.org">
    <img src="https://img.shields.io/badge/python-3.9%2B-yellow.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  </a>
  <a href="https://buymeacoffee.com/webspoilt">
    <img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black" alt="Buy Me a Coffee">
  </a>
  <br><br>
  <em>A fully deployable, open-source AI agent system that scales across Mobile (Termux/Android), Laptop, and High-End PC using a "Hybrid Hive" architecture where multiple AI models collaborate autonomously.</em>
</p>

> **🤖 Built with AI Assistance**: Please note that parts of OmniClaw's architecture and features were developed alongside AI coding assistants. While powerful, this means there may be unexpected bugs or edge cases in certain modules. Contributions and issue reports are highly welcome!

---

> [!WARNING]
> **🚨 EXPERIMENTAL & BETA SOFTWARE**
> 
> This system is currently in **Beta** and is highly experimental. 
> - **Security:** Do **NOT** share private keys, passwords, or personal things with the agent.
> - **Environment:** Kindly use this *only* inside a Virtual Machine (VM).
> - **Kernel Level:** For eBPF/Kernel level access, please use Linux inside **VMware** or **VirtualBox**.
> - **Liability:** Use at your own risk!
> 
> **🛑 STRICT LEGAL WARNING:** Using OmniClaw for automated hacking, unauthorized network penetration, or malicious exploitation is **strictly illegal and punishable by law**. We do not encourage, endorse, or support malicious activities. You assume all risk and liability for how you deploy this autonomous tool.

## 🌟 Features

### 1. Hybrid Hive Architecture
- **Multi-API Orchestrator**: Manager-Worker loop handling 10+ AI API keys simultaneously
- **Task Division**: Automatic decomposition of complex goals into sub-tasks
- **Self-Correction**: Peer-review system where workers check each other's work
- **Single-API Mode**: Chain-of-Thought processing for bug-free results with one API
- **Local Agentic AI**: Natively supports strictly offline, privacy-first Local LLMs (via Ollama) executing autonomously as full agents.

### 2. System & Kernel Integration
- **Kernel Bridge (C++/eBPF)**: Real-time Linux/Android system call and network monitoring
- **Vibe-Coded Execution**: Agent writes, compiles, and installs tools on-demand
- **Deep System Access**: Shell commands, file management, browser control
- **Linux Native Tool Execution**: Natively integrates and executes Linux system tools for powerful automation.

### 3. Mobile "Super-App" & Interfaces
- **"Allow Everything" Permissions**: React Native UI with Accessibility and Background Service
- **Human Proxy Mode**: Read screens and click buttons autonomously
- **Termux WiFi Host**: OmniClaw can run flawlessly on an Android phone connected to WiFi using Termux to host the core AI node 24/7.
- **Multi-Channel Inbox**: Out-of-the-box support for Telegram, WhatsApp, Discord, Slack, Matrix, and iMessage.
- **Voice Wake & Audio**: Global hot-word activation (like Siri) for macOS desktop and mobile continuous conversation.

### 4. Automation & Earning
- **Financial Automation**: Trading platform hooks and earning workflows
- **Persistent Memory**: Local Vector Database for context retention
- **Bug Bounty Hunting**: Automated research and vulnerability detection

### 5. Absolute Data Privacy 🛡️
- **No Training Guarantee**: All core API integrations (OpenAI, Anthropic, Gemini, etc.) programmatically opt-out of data retention and engine training, strictly enforcing data isolation.

### 6. OmniClaw Mission Control (Tauri Native GUI) 🖥️
- **Cross-Platform Dashboard**: A performant React/Tauri desktop application built to monitor Swarm operations, view live Xterm.js terminal streams, and manually activate agent tools (like Bug Bounty or Algo Trader) seamlessly.
- **WebSocket Telemetry**: OmniClaw streams reasoning logs and stdout intercepts directly to the UI dynamically without any clunky polling. 

### 7. AI Companion & Custom Personas 💖
- **Interactive Roleplay**: Set your Agent to act as a friend, partner, or specialized assistant.
- **Proactive Engagement**: The `CompanionLoop` background thread monitors the time and spontaneously checks on you (e.g., asking if you've eaten lunch), forging a true companion connection.

### 8. Future Tech Research Module 🔮
- **Advanced Domains**: Simulates deep research into Quantum computing, DNA computing, 1nm lithography-free chips, and GPU manufacturing without human intervention.

### 9. Advanced AI Features (v2.0) 🆕

#### Core System Enhancements
- **🧠 Reasoning Lock**: Forces deep chain-of-thought reasoning on every LLM call with configurable depth levels
- **📋 Context Mapper**: Auto-generates `OMNICLAW.md` project documentation by scanning code, rules, and dependencies
- **🔧 Autonomous Fix**: Auto-parses errors → asks LLM for fix → applies → retries (no human intervention)
- **📝 Audit Diff**: Multi-file edit review with unified diff view, atomic apply, and full rollback
- **📸 Temporal Context**: Cross-session work snapshots — resume exactly where you left off, even weeks later
- **🏛️ Decision Archaeology**: Logs the reasoning behind decisions, queryable forever with semantic search
- **🛡️ Pattern Sentinel**: Learns from past bugs in YOUR codebase and warns proactively (5 built-in detectors)
- **🔮 Echo Chambers**: Spawns 7 shadow agents (speed, readability, security, etc.) to explore alternatives in parallel
- **📐 Living Docs**: AST-based Mermaid diagrams that auto-update as code changes
- **🔬 Semantic Diff**: Understands the MEANING of code changes (behavioral, API contract, SOLID violations)

#### Revolutionary Features
- **🔮 Consciousness Collision**: 5-agent multi-perspective code review (Skeptic, Security Expert, Architect, etc.)
- **🧬 CodeDNA Interpreter**: Understands WHY code was written, preserves business logic during refactoring
- **⏰ Time Machine Debugger**: Traces bugs to the exact git commit and requirement that introduced them
- **🕸️ Memory Graph Network**: Full knowledge graph — "What breaks if I change X?" with dependency chains
- **🔮 Predictor Engine**: Learns from YOUR codebase's bug history, warns before you repeat mistakes
- **⚖️ Contract Enforcer**: Blocks code that violates architectural rules (no direct DB calls, no hardcoded secrets)
- **🌐 Paradigm Translator**: Converts between frameworks/languages semantically (React→Vue, Python→JS)
- **🏗️ Natural Language Infra**: "Set up production k8s" → Full Terraform + Helm + CI/CD
- **👔 Autonomous PM**: Single sentence → SPEC + Architecture + Code + Tests + Docs
- **🔒 Security Research Hub**: Autonomous vulnerability scanning and security assessment
- [x] **Self-Evolving Core**: System that improves itself over time based on usage patterns

### 10. Advanced AI Features (v3.0) - The God-Tier Expansion 🚀

#### Architectural Paradigms
- **🕰️ Temporal Memory (Entropy Decay)**: FAISS indices that automatically prune old, unused context vectors to prevent hallucination loops.
- **📈 Hardware-Aware Orchestration**: Dynamic routing via psutil — automatically offloads standard LLM requests to Cloud APIs if local CPU/RAM is spiking.
- **🧠 The Shadow Kernel**: Direct eBPF Linux Syscall hooks using `bcc`. The AI can now physically monitor `execve` anomalies and network reads in ring-0.
- **⚛️ Quantum Gateway**: Seamlessly routes OpenQASM 3 circuits to IBM Quantum hardware/simulators right from a chat prompt.
- **🎯 DIEN Recommendation Engine**: A 3-layer architecture (Candidate Gen -> DIN Attention -> DIEN Evolution) that tracks your intent over time to predict the perfect `browser-use` or `kernel_alerts` tool to load before you even ask.
- **👻 The Immortal Kernel (Experimental)**: eBPF Segfault tracers that dump failed memory segments to the LLM, prompting it to auto-generate a C++ hot-patch. 
- **🧬 Biometric Vibe Lock**: Only unlocks "Ghost Mode" tools if the user's keystroke dynamics or voiceprint match the baseline trust score. 

- **🧬 Biometric Vibe Lock**: Only unlocks "Ghost Mode" tools if the user's keystroke dynamics or voiceprint match the baseline trust score. 

### 11. Sovereign Sentinel (v3.2.0) - Security & Stability Update 🛡️

#### Security Reinforcement
- **⚖️ Contract Enforcer (Fixed)**: Architectural rules are now strictly enforced with zero syntax overhead. Blocks illegal DB calls and hardcoded secrets before they hit your git history.
- **🛡️ Secure Token Scrubbing**: Automatically detects and replaces leaked API keys in log outputs using the AST-aware sentinel logic.
- **🔒 Kernel Perimeter**: Hardened eBPF syscall monitoring with real-time anomaly detection for unauthorized `execve` calls.

#### Performance & Sync
- **⚡ Git-Aware Sync (Optimized)**: Intelligence integration in `.gitignore` — no more tracking 10,000+ `node_modules`. Blazing fast `git status` even in huge monorepos.
- **💾 Compressed Temporal FAISS**: FAISS indices are now serialized with Brotli compression, saving 60% disk space while retaining 99% recall.
- **🔄 Atomic Multi-State Push**: Seamless one-click push for all agent states (code, docs, and memory) to GitHub simultaneously.

### 12. Red Team Automation & Exploitation (v3.3.0) 🛑
- **Automated Adversarial Logic Engine**: Context-Aware fuzzing, IDOR detection, and Prompt Injection using recursive model payloads via `PromptInjectorMutator`.
- **TorHive Stealth Orchestrator**: Direct routing of all worker HTTP traffic through dynamically rotated Tor circuits for ultimate anonymity.
- **Responsible Disclosure Pipeline**: Encrypted evidence capture (Fernet), automated Markdown/PDF report generation with CVSS severity scoring.
- **Auto-Disclosure Agent**: SMTP dispatch system for securely emailing vulnerability reports to vendors.

### 13. Mission Control & Strategic Architecture (v3.3.0)
- **OpenRouter/LiteLLM Agnosticism**: Seamlessly switch between Claude, GPT, and custom models with automated sub-cent cost tracking.
- **Financial Observability**: FastAPI + React dashboard that tracks token usage and task success rates, ensuring the agent doesn't overspend API credits.
- **Peer-Reviewed Multi-Agent Workflows**: LangGraph-inspired pipelines where Architect, Coder, and Reviewer agents debate code changes autonomously.
- **MCP (Model Context Protocol) Tools**: Agents access system functions through standardized MCP endpoints (e.g., the root eBPF monitor).
- **Persistent Trigger Memory**: Agents save and recall important states via specific "trigger phrases".

### 14. Security Sandbox & Defense Layer (v4.0.0) 🛡️

#### Multi-Layer Security Architecture
- **🔒 FileGuard**: Workspace-scoped file access control — blocks path traversal attacks, symlink escapes, and access to sensitive files (`.env`, `.ssh`, private keys, credentials).
- **🛡️ ShellSandbox**: Three-tier shell command filtering pipeline:
  - **Tier 1 (BLOCKED):** Instant reject — `rm -rf /`, `mkfs`, `dd if=`, `curl|sh`, process tracing, env dumps (~40 patterns)
  - **Tier 2 (CONFIRM):** User approval required — `rm`, `pip install`, `sudo`, `docker`, `git push` (~17 patterns)
  - **Tier 3 (ALLOW):** Safe commands in sandboxed workspace with stripped environment
- **🧬 PromptGuard**: Prompt injection defense with 27 detection patterns, Unicode NFKC normalization against homoglyph attacks, and tool output trust-boundary wrapping.
- **💰 SessionBudget**: Prevents runaway loops and API cost overruns — max iterations, token budgets, tool call rate limits, shell command limits, and session timeouts.
- **🩺 SecurityDoctor**: Installation diagnostics — audits workspace permissions, config file safety, exposed API keys, and skill directory security.

### 15. Custom Skill System (v4.0.0) 📦
- **🔧 Tool Registry**: Decorator-based `@tool` registration with OpenAI-compatible function-calling schema generation. Register custom tools with a single decorator.
- **📂 Skill Auto-Loader**: Drop `.py` files into `~/.omniclaw/skills/` and they're automatically discovered and loaded at startup with file ownership validation.
- **✅ Confirmation Support**: Mark destructive tools as `needs_confirmation=True` for user approval before execution.

### 16. Scheduled Tasks & Heartbeat (v4.0.0) ⏰
- **⏰ Cron Scheduler**: Persistent SQLite-backed job scheduling that survives restarts. Supports cron expressions and interval-based scheduling with prompt injection screening.
- **🫀 Heartbeat Service**: Periodic agent wake-up driven by `HEARTBEAT.md`. Uses LLM tool-calls for intelligent decision-making (skip vs. run) — only executes tasks when needed.
- **🔄 Background Automation**: Schedule recurring prompts like daily reports, health checks, or automated research tasks.

### 17. Autonomous IPS — Intrusion Prevention System (v4.1.0) 🛡️🔥
- **🔍 eBPF Network Monitor**: Kernel-level `tcp_v4_connect` and `inet_csk_accept` tracing via a dedicated `monitor.bpf.c` CO-RE program — detects SSH brute-force attacks in real-time.
- **🧠 LLM Threat Classifier**: Worker-agent AI analyzes alerts and classifies threats as `brute_force`, `credential_stuffing`, `forgotten_password`, or `benign` — preventing false positives.
- **🚫 Autonomous IP Blocking**: Executes `iptables` or `nftables` rules to block malicious IPs without human intervention.
- **🔒 Dry-Run Safety**: Enabled by default — logs block commands without executing them. Admin IP whitelist prevents self-lockout.
- **📋 JSON Action Log**: Every IPS action is logged to `ips_actions.jsonl` for the Manager agent to review and audit.
- **📱 Termux/Mobile Fallback**: Gracefully degrades to `/var/log/auth.log` parsing or mock simulation when eBPF is unavailable.

### 18. Self-Evolving Code Janitor (v4.1.0) 🧬
- **📡 Log Monitoring**: Watchdog-based real-time monitoring of `./logs/` for `ERROR` and `CRITICAL` tracebacks.
- **🔍 Traceback Parsing**: Extracts the faulty source file and line number from Python tracebacks.
- **🧠 LLM Fix Proposal**: Sends error context + source code to an LLM (Ollama or OpenAI) and retrieves a corrected code block.
- **🧪 Isolated Testing**: Creates a temporary copy, applies the fix, and runs an LLM-generated test to verify correctness.
- **🌿 Git Integration**: Creates a `fix/<error-type>` branch and commits the change if tests pass.
- **🔔 Notifications**: JSON payloads sent to Telegram/Discord webhooks.
- **✋ Manual Approval**: Optional diff review before committing.
- **💾 Safe I/O**: Atomic writes (`.tmp` → rename) with `.bak` backups. Duplicate prevention via hash store.

### 19. P2P Hive Sync (v4.1.0) 🕸️
- **🔗 ZeroMQ Mesh**: DEALER/ROUTER sockets for asynchronous peer-to-peer messaging between Mobile (Termux) and Desktop nodes.
- **🔐 AES-256-GCM**: All payloads encrypted with a pre-shared key before transmission. Authenticated encryption prevents tampering.
- **💗 Heartbeat**: Each node broadcasts CPU/memory load periodically. Peers detected as online/offline via configurable timeout.
- **📦 Query Forwarding**: Forward FAISS vector DB searches to peers when local results are insufficient.
- **⚡ LLM Offloading**: Automatically offload heavy LLM tasks to desktop when mobile CPU exceeds threshold.
- **🔌 Integration Hooks**: Register callbacks for `on_query` and `on_offload` to plug in your own FAISS and LLM functions.

### 20. Scout Agent — Security Recon (v4.1.0) 🕵️
- **🎯 Target Validation**: Hard-coded blocklist (IPs, domains, CIDRs) prevents scanning unauthorized targets.
- **🔧 Modular Tools**: Subfinder, Nmap, Nuclei integrated with a standard `SecurityTool` base class — easily extensible (e.g., ffuf, whatweb).
- **🧠 LLM Analysis**: Tool outputs sent to LLM to identify "low-hanging fruit" vulnerabilities with severity classification.
- **📄 Markdown Reports**: Timestamped `vulnerability_report_*.md` with summary, findings, and raw tool outputs.
- **🚨 Instant Alerts**: Telegram/Discord notifications for any HIGH or CRITICAL findings.
- **🛡️ Safety First**: Exits immediately if target matches blocklist. No automatic exploitation — advisory only.

### 21. Neural Mesh Protocol (v4.3.0) 🧠
- **🕸️ ZeroMQ Mesh**: ROUTER/DEALER P2P with capability-based heartbeat (CPU, memory, available models).
- **📡 Task Offloading**: Route LLM inference or heavy compute to the least-loaded peer.
- **📚 Knowledge Queries**: Cross-node vector/graph search via unified protocol.
- **🔐 AES-256-GCM**: All messages encrypted with pre-shared key.
- **📄 Typed Protocol**: `protocol.py` with dataclass messages and enum types (HEARTBEAT, TASK_REQUEST, KNOWLEDGE_QUERY, SYNC).

### 22. Vision Module (v4.3.0) 👁️
- **📱 Computer Use**: Cross-platform screen capture (X11/Wayland/macOS/Windows/Termux) with multimodal LLM analysis.
- **📷 Termux Camera**: Capture via `termux-camera-photo` with base64 encoding and LLM analysis.
- **🌱 Plant Health**: Leaf disease detection, pest identification, and care recommendations from plant images.

### 23. Memory Module (v4.3.0) 🧠
- **💾 Vector Store**: LanceDB wrapper for embedding storage and similarity search with in-memory fallback.
- **📊 Graph Store**: NetworkX directed graph with JSON persistence for entity relationships.
- **🔗 Knowledge Graph**: Unified layer combining vector similarity + relationship traversal.

### 24. Orchestrator Daemon (v4.3.0) 🏛️
- **🚀 Unified Startup**: `core/main.py` daemon that boots all workers based on node type (desktop vs mobile).
- **🛡️ Kill Switch**: Global halt for all autonomous shell execution — toggleable via MCP.
- **📈 Resource Gating**: Battery/CPU/memory checks before every heavy operation on mobile.
- **🧬 Genesis**: Self-evolution agent that collects telemetry and suggests refactoring.

### 25. Secure Enclave & Hardware Locks (v4.3.0) 🔒
- **🔑 Hardware Authentication**: `YubiKeyManager` derives AES-256-GCM encryption keys via HMAC-SHA1 challenge-response.
- **🛡️ Encrypted Configurations**: Sensitive modules load configs from `.yaml.aes` using the `SecureConfigLoader` bound to physical hardware.
- **💻 Hardware-Locked Execution**: Evolution and code-refactor agents (Genesis, Janitor) strictly check `platform.node()` to ensure execution remains locally isolated on authorized hardware.
- **📦 Private Submodules**: Sensitive operational capabilities seamlessly mount via Git submodules (`kernel_bridge/`, `offensive/`).

### 26. OmniClaw Swarm Oracle (v4.3.0) 🐋
- **🧠 50+ Agent Multi-Persona Swarm**: Spawns concurrent agents (Whale, Retailer, Skeptic, etc.) using Ollama to simulate complex market sentiment and cyber-security scenarios.
- **🛡️ Predictive Auditor**: Built-in validation heuristic layer that intercepts Agent hallucinations and automatically rejects contradictory logic before execution.
- **🕸️ ChromaDB Memory Graph**: Vector-based semantic persistence of past swarm simulations, allowing OmniClaw to reference previous state-changes and predictive outcomes.
- **⚙️ Rust eBPF Sentinel Skeleton**: Lightweight Rust bridge (`libbpf-rs`) engineered for deep-kernel Windows ETW / Linux `execve` telemetry gathering during swarm activity.

### 27. Advanced Anti-Bot & Decensoring (v4.3.0) 🦇
- **🕵️ Stealth Scraper**: Native integration of the `Scrapling` framework to bypass Cloudflare Turnstile, Kasada, and Incapsula natively using Playwright.
- **🔓 Local Model Decensoring**: Agentic integration with `Heretic-LLM`, allowing OmniClaw to automatically download and directionally ablate HuggingFace models to remove censorship alignments locally.

### 28. CashClaw Business Orchestrator (v4.3.0) 💰
- **💼 Freelance Automation**: Fully integrated the CashClaw engine natively into OmniClaw. 12 powerful AI business skills (`cashclaw-seo-auditor`, `cashclaw-invoicer`, `cashclaw-content-writer`, etc.) are now available in the `skills` directory.
- **💳 Stripe & HYRVEai**: OmniClaw agents can now accept gig marketplace requests, execute them using CashClaw capabilities, and generate Stripe invoices autonomously.

### 29. Sovereign Sentinel (v4.4.0) — The 2026 Fusion 🛡️🚀
- **Unified pnpm Monorepo**: Clean, enterprise-grade architecture fusing OmniClaw and Shannon Pro into a single workspace (`apps/`, `engines/`, `packages/`).
- **CVE-to-PoC Factory**: Autonomous pipeline that monitors NVD/GitHub, performs reachability-aware static analysis (CPG), and synthesizes functional Python exploits via specialized workers.
- **eBPF Sentinel (Rust)**: High-performance `libbpf-rs` module for Ring-0 stealth, hooking `sys_execve` to detect security tools (EDR) and triggering automatic IP rotation/migration.
- **Durable Worker (TS)**: TypeScript-based durable orchestrator (Inspired by Temporal.io) for long-running security missions that resume after failure.
- **P2P Knowledge Mesh**: ZeroMQ + AES-256-GCM communication layer for offloading heavy analysis from mobile (Termux) to high-end PC nodes with unified vector memory (LanceDB).

### 30. LangWatch Observability (v4.3.0) 📊
- **📈 Global AI Tracing**: The entire orchestrator loop is natively wrapped in `LangWatch` context closures, tracking metrics on token costs, latency, and autonomous agent responses to your observability dashboard.

## 🌐 Real-World Use Cases
Wondering what you can actually build with an autonomous agent swarm? 
Check out our **[Real-World Use Cases](USE_CASES.md)** document to see how engineers are using OmniClaw for:
- 🎯 Autonomous Bug Bounty Hunting
- 🩺 24/7 Server Health & Incident Response
- 🎙️ Hands-Free Smart Home Automation

## 🚀 Quick Start

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/webspoilt/omniclaw/blob/main/OmniClaw_Colab_Sandbox.ipynb)

> **🍼 NEW TO ALL THIS?** Read our **[Very Simple: 24/7 Deployment Guide](DEPLOYMENT_GUIDE.md)** for a complete step-by-step walkthrough on how to set up Telegram, rent a Cloud Computer, and install OmniClaw easily using the `setup.sh` Blueprint.

### One-Click Installer Blueprint (Local)

Simply run our included blueprint script to automatically detect your OS, verify your RAM, pill the correct size AI model via Ollama, and launch the defensive bridge:
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/webspoilt/omniclaw.git
cd omniclaw

# Install dependencies
pip install -r requirements.txt

# Configure
cp config.example.yaml config.yaml
nano config.yaml  # Add your API keys

# Run
python omniclaw.py chat
```

## 📱 Platform Support & Comprehensive Guides

We believe you shouldn't have to watch a YouTube tutorial to set this up. Everything is documented here.

| Platform | Features | Setup Guide |
|----------|----------|-------------|
| **Linux (Desktop/VPS)** | Full (eBPF root access, Terminal tools) | [View the 24/7 Deployment Guide](DEPLOYMENT_GUIDE.md) |
| **Android (Termux)** | Full (Mobile Super-App, 24/7 cheap hosting) | [The Ultimate Termux/SSH Zero-to-Hero Guide](DEPLOYMENT_GUIDE.md#choice-c-an-android-phone-using-termux---the-complete-guide) |
| **macOS** | Partial (Voice Wake, CLI access) | Clone and run `./setup.sh` |
| **Windows (WSL)** | Experimental | Install WSL2 Ubuntu, then run `./setup.sh` |

### 🛠️ Deep Dive: How The Features Actually Work

**Termux WiFi Host (The 2 Watt AI Server)**
Why leave a 500W PC running when an old Android phone uses 2 Watts? By installing F-Droid, downloading Termux, executing `termux-setup-storage`, and installing OpenSSH (`pkg install openssh`), you can cast your phone's terminal instantly to your Windows/Mac PC over WiFi (`ssh -p 8022`). From there, OmniClaw runs flawlessly 24/7 as a background agent. [Read the step-by-step Termux guide here](DEPLOYMENT_GUIDE.md#choice-c-an-android-phone-using-termux---the-complete-guide).

**eBPF Kernel Bridge (Linux Only)**
If you are running on a true Linux kernel (Ubuntu VPS, Debian, etc.) with root access, OmniClaw is not restricted to standard chat-bot APIs. It compiles a C/Rust binary that attaches directly to the operating system kernel. It intercepts packet traffic and traces system calls in real time. *Note: Doing this inside Termux without a rooted Android is restricted.*

**Multi-Channel Gateway (Telegram & Discord)**
You command the hive using standard chat apps. You simply message `@BotFather` on Telegram, create a token, get your ID from `@userinfobot`, and place them in the `config.yaml`. The agent will now securely reply only to you.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID HIVE                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  Manager    │◄──►│   Worker 1  │◄──►│   Worker 2  │      │
│  │  (GPT-5)    │    │ (Claude-4.6)│    │(Gemini-3.1) │      │
│  └──────┬──────┘    └─────────────┘    └─────────────┘      │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │   Worker 3  │◄──►│   Worker 4  │◄──►│   Worker N  │      │
│  │  (Ollama)   │    │  (Custom)   │    │   (API X)   │      │
│  └─────────────┘    └─────────────┘    └─────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  SYSTEM INTEGRATION                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │eBPF Monitor │  │ Vector DB   │  │  Messaging  │          │
│  │  (Kernel)   │  │  (FAISS)    │  │(TG/WhatsApp)│          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## 🔧 Configuration

### API Configuration

```yaml
# config.yaml
privacy_enforced: true

apis:
  - provider: openai
    key: "sk-..."
    model: gpt-5
    priority: 1
    
  - provider: anthropic
    key: "sk-ant-..."
    model: claude-4.6-opus
    priority: 2
    
  - provider: google
    key: "..."
    model: gemini-3.1
    priority: 3
    
  - provider: ollama
    key: "ollama"
    model: llama2:13b
    base_url: http://localhost:11434
    priority: 4
```

### Memory Configuration

```yaml
memory:
  db_path: "./memory_db"
  embedding_provider: "ollama"  # or "openai"
  max_history: 1000
```

### Messaging & Voice Gateway

```yaml
messaging:
  discord:
    enabled: true
    token: "YOUR_DISCORD_BOT_TOKEN"
  slack:
    enabled: true
    bot_token: "xoxb-..."
  telegram:
    enabled: true
    token: "YOUR_BOT_TOKEN"
    allowed_users: ["your_telegram_id"]
    
  whatsapp:
    enabled: true
    allowed_numbers: ["+1234567890"]
    
  imessage:
    enabled: true
  matrix:
    enabled: true

voice:
  macos_hotword: "Hey Omni"
  elevenlabs_api_key: "sk-..."
```

### Security & Sandbox (v4.0)

```yaml
security:
  workspace_dir: "./workspace"     # All file/shell ops sandboxed here
  sandbox_enabled: true
  max_iterations: 15               # Max LLM loops per message
  max_tokens_per_session: 50000    # Token budget per session
  session_timeout: 300             # Session timeout in seconds

  # IPS — Autonomous Intrusion Prevention (v4.1)
  ips:
    enabled: true
    dry_run: true                  # SAFETY: always start with true
    admin_whitelist:
      - "127.0.0.1"
      - "YOUR_ADMIN_IP"
    fail_threshold: 5
    block_tool: "iptables"         # or "nftables"
    llm_analysis: true

skills:
  directory: "~/.omniclaw/skills"  # Drop .py files here
  auto_load: true                  # Auto-discover at startup

scheduler:
  cron_enabled: true
  heartbeat_enabled: true
  heartbeat_interval: 1800         # 30 minutes
```

## 💬 Usage

### Interactive Chat

```bash
omniclaw chat
```

### Execute Single Task

```bash
omniclaw task "Research the latest AI developments and create a summary report"
```

### Run as Daemon

```bash
omniclaw daemon
systemctl --user start omniclaw  # With systemd
```

### Omni-Channel Control (OpenClaw / Moltbot Interface)

You can run OmniClaw as your own personal **Moltbot / OpenClaw Assistant** directly from Discord, Slack, Telegram, WhatsApp, iMessage, or Matrix. By connecting the messaging gateway in `config.yaml`, the agent will listen and respond to chats securely:

1. Use [@BotFather](https://t.me/BotFather) on Telegram to create a bot and get a Token.
2. Put the Token in `config.yaml` > `messaging` > `telegram`.
3. Put your own Telegram User ID in `allowed_users` so nobody else can control your machine.
4. Send commands to your bot to trigger agentic behaviors:

```
/task Research quantum computing advances
/status Check agent status
/memory Show memory statistics
/security View security layer status
/security audit Run full security diagnostic
/cron List scheduled jobs
/cron add daily-report "Create a daily summary" --interval=86400
/skills List all registered tools
/heartbeat View heartbeat status
/heartbeat trigger Manually trigger heartbeat check
```

## 🛠️ Development

### Project Structure

```
omniclaw/
├── core/                           # Core Python modules
│   ├── orchestrator.py             # Hybrid Hive orchestrator
│   ├── manager.py                  # Manager agent
│   ├── worker.py                   # Worker agents
│   ├── memory.py                   # Vector memory system
│   ├── api_pool.py                 # API management
│   ├── messaging_gateway.py        # Telegram/WhatsApp integration
│   ├── reasoning_config.py         # 🧠 Reasoning Lock
│   ├── context_mapper.py           # 📋 Context Mapper
│   ├── autonomous_fix.py           # 🔧 Autonomous Fix
│   ├── audit_diff.py               # 📝 Audit Diff
│   ├── temporal_memory.py          # 📸 Temporal Context
│   ├── decision_archaeology.py     # 🏛️ Decision Archaeology
│   ├── pattern_sentinel.py         # 🛡️ Pattern Sentinel
│   ├── echo_chambers.py            # 🔮 Echo Chambers
│   ├── living_docs.py              # 📐 Living Documentation
│   ├── semantic_diff.py            # 🔬 Semantic Diff
│   ├── security/                   # 🔒 Security Sandbox (v4.0+)
│   │   ├── __init__.py             #   Unified SecurityLayer class (6 layers)
│   │   ├── file_guard.py           #   Workspace file access control
│   │   ├── shell_sandbox.py        #   3-tier command filtering
│   │   ├── prompt_guard.py         #   Prompt injection defense
│   │   ├── session_budget.py       #   Rate limiting & cost tracking
│   │   ├── doctor.py               #   Security audit diagnostic
│   │   └── ips_agent.py            #   🛡️ Autonomous IPS (v4.1)
│   ├── skills/                     # 📦 Custom Skill System (v4.0)
│   │   ├── __init__.py
│   │   ├── registry.py             #   @tool decorator & ToolRegistry
│   │   └── loader.py               #   Auto-discover skill .py files
│   ├── scheduler/                  # ⏰ Task Scheduler (v4.0)
│   │   ├── __init__.py
│   │   ├── cron.py                 #   Persistent SQLite cron jobs
│   │   └── heartbeat.py            #   HEARTBEAT.md-driven agent wake-up
│   ├── evolution_agent.py          # 🧬 Self-Evolving Code Janitor (v4.1)
│   ├── hive_sync.py                # 🕸️ P2P Hive Sync (v4.1)
│   ├── scout_agent.py              # 🕵️ Security Recon Agent (v4.1)
│   └── advanced_features/          # 🚀 Advanced Features Package
│       ├── consciousness_collision.py
│       ├── code_dna.py
│       ├── time_machine.py
│       ├── memory_graph.py
│       ├── predictor.py
│       ├── contract_enforcer.py
│       ├── paradigm_translator.py
│       ├── natural_language_infra.py
│       ├── living_diagram.py
│       ├── autonomous_pm.py
│       ├── self_evolving_core.py
│       ├── security_research.py
│       └── launcher.py
├── skills/                       # 📦 Sample skills
│   └── sample_weather.py         #   Example @tool skill
├── kernel_bridge/                # C++/eBPF kernel monitor + IPS
├── modules/                      # 🧩 Feature Modules (v4.1)
│   ├── evolution/                #   Self-healing code janitor
│   │   ├── evolution_agent.py
│   │   ├── sandbox.py
│   │   └── config.yaml
│   ├── security/                 #   Shadow shell honeypot
│   │   ├── honeypot.cpp
│   │   ├── shadow_shell.py
│   │   └── iptables_helper.py
│   ├── scholar/                  #   Exam war-room scholar
│   │   ├── exam_intelligence.py
│   │   └── scholar_config.json
│   ├── startup/                  #   DevOps autopilot
│   │   └── saas_manager.py
│   ├── sensors/                  #   Bio-guardian
│   │   └── plant_monitor.py
│   ├── offensive/                #   Red Team tools
│   │   └── model_decensor.py     #   Heretic-LLM integration
│   ├── recon/                    #   Reconnaissance
│   │   └── stealth_scraper.py    #   Scrapling Turnstile bypass
│   ├── observability/            #   LLM Telemetry
│   │   └── langwatch_tracer.py   #   LangWatch prompt tracking
│   └── swarm_oracle/             #   🐋 50+ Agent Swarm Engine
│       ├── manager.py
│       ├── swarm_engine.py
│       ├── auditor.py
│       ├── knowledge.py
│       ├── config.py
│       ├── personas.py
│       └── ebpf_bridge/          #   Rust eBPF/ETW Sentinel
├── connectors/                   # 🔌 MCP + integrations
│   └── mcp_host.py               #   MCP server (fastmcp)
├── p2p/                          # 🕸️ P2P hive network
│   ├── crypto.py                 #   AES-256-GCM helpers
│   └── peers.json                #   Known peer list
├── mobile_app/                   # React Native super-app
├── omniclaw.py                   # Main entry point
├── setup.sh                      # One-click installer
└── requirements.txt              # Python dependencies
```

### Building Kernel Bridge

```bash
cd kernel_bridge
make          # Build everything (syscall monitor + IPS + bridge)
sudo make install

# Or build just the IPS eBPF monitor:
make ips      # Output: build/monitor.bpf.o
```

### Building Mobile App

```bash
cd mobile_app
npm install
npx react-native run-android  # or run-ios
```

## 🔒 Security

- **Multi-Layer Defense**: 6-layer security architecture — FileGuard, ShellSandbox, PromptGuard, SessionBudget, SecurityDoctor, **IPSAgent**
- **Autonomous IPS**: eBPF-backed intrusion prevention with LLM threat classification, autonomous IP blocking, dry-run safety, and admin whitelist
- **Workspace Sandboxing**: All file/shell operations restricted to the workspace directory
- **Command Filtering**: 40+ blocked dangerous patterns, 17 confirmation-required patterns
- **Prompt Injection Defense**: 27 injection detection patterns with Unicode normalization
- **Cost Control**: Automatic rate limiting and token budget enforcement
- **API Key Encryption**: All API keys are encrypted at rest
- **User Authorization**: Messaging gateway requires explicit user allowlisting
- **Audit Logging**: All actions logged for review (IPS actions → `ips_actions.jsonl`)

Run a security audit:
```bash
# Via messaging
/security audit

# Programmatically
from core.security.doctor import SecurityDoctor
doctor = SecurityDoctor(workspace_dir="./workspace")
report = doctor.run_audit()
print(report["summary"])
```

## 🌐 Hardware Detection

The installer automatically detects your hardware and configures appropriately:

| Hardware | RAM | CPU | Model |
|----------|-----|-----|-------|
| High-End | 16GB+ | 8+ cores | llama2:13b / GPT-5 |
| Medium | 8GB | 4+ cores | llama2:7b / GPT-4 |
| Low/Mobile | <8GB | 2-4 cores | phi / API fallback |

## 📊 Performance

Benchmarks on different hardware configurations:

| Task | High-End | Medium | Mobile |
|------|----------|--------|--------|
| Simple Query | 0.5s | 1.2s | 2.5s |
| Code Generation | 2.1s | 4.5s | 8.0s |
| Research Task | 5.3s | 12.0s | 25.0s |
| Multi-API Coordination | 3.2s | 7.0s | 15.0s |

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Fork and clone
git clone https://github.com/webspoilt/omniclaw.git

# Create branch
git checkout -b feature/amazing-feature

# Commit changes
git commit -m "Add amazing feature"

# Push and PR
git push origin feature/amazing-feature
```

## 📜 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- [eBPF](https://ebpf.io/) for kernel monitoring capabilities
- [FAISS](https://github.com/facebookresearch/faiss) for vector search
- [LangChain](https://langchain.com/) for AI orchestration patterns
- [React Native](https://reactnative.dev/) for mobile framework

## 📞 Support

- 📧 Email: heyzerodayhere@gmail.com
- 💬 Discord: [discord.gg/ZU4mQaqh](https://discord.gg/ZU4mQaqh)
- 🐛 Issues: [GitHub Issues](https://github.com/webspoilt/omniclaw/issues)
- 📖 Docs: [Host your docs using Vercel & Nextra!](https://vercel.com/new)

---

<p align="center">
  <b>OmniClaw</b> - The Future of Autonomous AI Agents
  <br>
  <sub>Built with ❤️ by Me</sub>
</p>
