<p align="center">
  <img src="https://raw.githubusercontent.com/webspoilt/omniclaw/main/public/logo.svg" width="180" height="180" alt="OmniClaw Logo">
</p>

<h1 align="center" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 3em; color: #4A90E2; margin-bottom: 0;">OmniClaw</h1>
<h3 align="center" style="font-weight: 300; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #666; margin-top: 5px;">The Hybrid Hive AI Agent System</h3>

<p align="center">
  <a href="https://github.com/webspoilt/omniclaw/releases">
    <img src="https://img.shields.io/badge/version-1.0.0-blue.svg?style=for-the-badge&logo=appveyor" alt="Version">
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

## 🚀 Quick Start

> **🍼 NEW TO ALL THIS?** Read our **[Explain Like I'm 10: 24/7 Deployment Guide](DEPLOYMENT_GUIDE.md)** for a complete step-by-step walkthrough on how to set up Telegram, rent a Cloud Computer, and install OmniClaw easily using the `setup.sh` Blueprint.

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

## 📱 Platform Support

| Platform | Status | Features |
|----------|--------|----------|
| **Linux (Desktop/Server)** | ✅ Full | All features including eBPF kernel bridge |
| **Android (Termux)** | ✅ Full | Mobile super-app, messaging gateway |
| **macOS** | ✅ Partial | Core features (no eBPF) |
| **Windows (WSL)** | ⚠️ Experimental | Core features only |

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID HIVE                              │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐      │
│  │  Manager    │◄──►│   Worker 1  │◄──►│   Worker 2  │      │
│  │  (GPT-4)    │    │ (Claude-3)  │    │  (Gemini)   │      │
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
apis:
  - provider: openai
    key: "sk-..."
    model: gpt-4
    priority: 1
    
  - provider: anthropic
    key: "sk-ant-..."
    model: claude-3-opus-20240229
    priority: 2
    
  - provider: google
    key: "..."
    model: gemini-pro
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
├── core/                    # Core Python modules
│   ├── orchestrator.py      # Hybrid Hive orchestrator
│   ├── manager.py           # Manager agent
│   ├── worker.py            # Worker agents
│   ├── memory.py            # Vector memory system
│   ├── api_pool.py          # API management
│   └── messaging_gateway.py # Telegram/WhatsApp integration
├── kernel_bridge/           # C++/eBPF kernel monitor
│   ├── src/bpf/            # eBPF programs
│   ├── src/cpp/            # C++ bridge
│   └── python_bridge.py    # Python bindings
├── mobile_app/             # React Native super-app
│   ├── src/screens/        # UI screens
│   ├── src/services/       # Background services
│   └── src/store/          # State management
├── scripts/                # Deployment scripts
├── omniclaw.py            # Main entry point
├── install.sh             # Installation script
└── requirements.txt       # Python dependencies
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
| High-End | 16GB+ | 8+ cores | llama2:13b / GPT-4 |
| Medium | 8GB | 4+ cores | llama2:7b / GPT-3.5 |
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
- 💬 Discord: [discord.gg/omniclaw](https://discord.gg/omniclaw)
- 🐛 Issues: [GitHub Issues](https://github.com/webspoilt/omniclaw/issues)
- 📖 Docs: [Host your docs using Vercel & Nextra!](https://vercel.com/new)

---

<p align="center">
  <b>OmniClaw</b> - The Future of Autonomous AI Agents
  <br>
  <sub>Built with ❤️ by Me</sub>
</p>
