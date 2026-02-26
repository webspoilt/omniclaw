<p align="center">
  <img src="https://raw.githubusercontent.com/webspoilt/omniclaw/main/public/logo.svg" width="180" height="180" alt="OmniClaw Logo">
</p>

<h1 align="center" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 3em; color: #4A90E2; margin-bottom: 0;">OmniClaw</h1>
<h3 align="center" style="font-weight: 300; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #666; margin-top: 5px;">The Hybrid Hive AI Agent System</h3>

<p align="center">
  <a href="https://github.com/webspoilt/omniclaw/releases">
    <img src="https://img.shields.io/badge/version-3.0.0-blue.svg?style=for-the-badge&logo=appveyor" alt="Version">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge&logo=open-source-initiative" alt="License">
  </a>
  <a href="https://python.org">
    <img src="https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python">
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
```

## 🛠️ Development

### Project Structure

```
omniclaw/
├── core/                         # Core Python modules
│   ├── orchestrator.py           # Hybrid Hive orchestrator
│   ├── manager.py                # Manager agent
│   ├── worker.py                 # Worker agents
│   ├── memory.py                 # Vector memory system
│   ├── api_pool.py               # API management
│   ├── messaging_gateway.py      # Telegram/WhatsApp integration
│   ├── reasoning_config.py       # 🧠 Reasoning Lock
│   ├── context_mapper.py         # 📋 Context Mapper
│   ├── autonomous_fix.py         # 🔧 Autonomous Fix
│   ├── audit_diff.py             # 📝 Audit Diff
│   ├── temporal_memory.py        # 📸 Temporal Context
│   ├── decision_archaeology.py   # 🏛️ Decision Archaeology
│   ├── pattern_sentinel.py       # 🛡️ Pattern Sentinel
│   ├── echo_chambers.py          # 🔮 Echo Chambers
│   ├── living_docs.py            # 📐 Living Documentation
│   ├── semantic_diff.py          # 🔬 Semantic Diff
│   └── advanced_features/        # 🚀 Advanced Features Package
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
├── kernel_bridge/                # C++/eBPF kernel monitor
├── mobile_app/                   # React Native super-app
├── omniclaw.py                   # Main entry point
├── setup.sh                      # One-click installer
└── requirements.txt              # Python dependencies
```

### Building Kernel Bridge

```bash
cd kernel_bridge
make
sudo make install
```

### Building Mobile App

```bash
cd mobile_app
npm install
npx react-native run-android  # or run-ios
```

## 🔒 Security

- **API Key Encryption**: All API keys are encrypted at rest
- **Sandboxed Execution**: Shell commands run in restricted environment
- **User Authorization**: Messaging gateway requires explicit user allowlisting
- **Audit Logging**: All actions logged for review

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
