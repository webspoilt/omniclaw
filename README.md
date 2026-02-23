<p align="center">
  <img src="https://raw.githubusercontent.com/webspoilt/omniclaw/main/docs/assets/architecture.png" alt="OmniClaw Banner" width="100%" style="border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
</p>

<h1 align="center" style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; font-size: 3em; color: #4A90E2; margin-bottom: 0;">🌐 OmniClaw</h1>
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
## ðŸŒŸ Features

### 1. Hybrid Hive Architecture
- **Multi-API Orchestrator**: Manager-Worker loop handling 10+ AI API keys simultaneously
- **Task Division**: Automatic decomposition of complex goals into sub-tasks
- **Self-Correction**: Peer-review system where workers check each other's work
- **Single-API Mode**: Chain-of-Thought processing for bug-free results with one API

### 2. System & Kernel Integration
- **Kernel Bridge (C++/eBPF)**: Real-time Linux/Android system call and network monitoring
- **Vibe-Coded Execution**: Agent writes, compiles, and installs tools on-demand
- **Deep System Access**: Shell commands, file management, browser control

### 3. Mobile "Super-App"
- **"Allow Everything" Permissions**: React Native UI with Accessibility and Background Service
- **Human Proxy Mode**: Read screens and click buttons autonomously
- **Auto-Setup**: Self-configuring environment on first run
- **Messaging Gateway**: Telegram and WhatsApp Bot API integration

### 4. Automation & Earning
- **Financial Automation**: Trading platform hooks and earning workflows
- **Persistent Memory**: Local Vector Database for context retention
- **Bug Bounty Hunting**: Automated research and vulnerability detection

## ðŸš€ Quick Start

### One-Line Installation

```bash
curl -fsSL https://omniclaw.ai/install.sh | bash
```

Or with custom directory:
```bash
curl -fsSL https://omniclaw.ai/install.sh | OMNICLAW_DIR=/opt/omniclaw bash
```

### Manual Installation

```bash
# Clone repository
git clone https://github.com/omniclaw/omniclaw.git
cd omniclaw

# Install dependencies
pip install -r requirements.txt

# Configure
cp config.example.yaml config.yaml
nano config.yaml  # Add your API keys

# Run
python omniclaw.py chat
```

## ðŸ“± Platform Support

| Platform | Status | Features |
|----------|--------|----------|
| **Linux (Desktop/Server)** | âœ… Full | All features including eBPF kernel bridge |
| **Android (Termux)** | âœ… Full | Mobile super-app, messaging gateway |
| **macOS** | âœ… Partial | Core features (no eBPF) |
| **Windows (WSL)** | âš ï¸ Experimental | Core features only |

## ðŸ—ï¸ Architecture

```
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                    HYBRID HIVE                              â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”‚
â”‚  â”‚  Manager    â”‚â—„â”€â”€â–ºâ”‚   Worker 1  â”‚â—„â”€â”€â–ºâ”‚   Worker 2  â”‚     â”‚
â”‚  â”‚  (GPT-4)    â”‚    â”‚ (Claude-3)  â”‚    â”‚  (Gemini)   â”‚     â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â”‚
â”‚         â”‚                                                   â”‚
â”‚         â–¼                                                   â”‚
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”    â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”     â”‚
â”‚  â”‚   Worker 3  â”‚â—„â”€â”€â–ºâ”‚   Worker 4  â”‚â—„â”€â”€â–ºâ”‚   Worker N  â”‚     â”‚
â”‚  â”‚  (Ollama)   â”‚    â”‚  (Custom)   â”‚    â”‚   (API X)   â”‚     â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜     â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                              â”‚
                              â–¼
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                  SYSTEM INTEGRATION                         â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”  â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”         â”‚
â”‚  â”‚eBPF Monitor â”‚  â”‚ Vector DB   â”‚  â”‚  Messaging  â”‚         â”‚
â”‚  â”‚  (Kernel)   â”‚  â”‚  (FAISS)    â”‚  â”‚(TG/WhatsApp)â”‚         â”‚
â”‚  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜  â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜         â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

## ðŸ”§ Configuration

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

### Messaging Gateway

```yaml
messaging:
  telegram:
    enabled: true
    token: "YOUR_BOT_TOKEN"
    allowed_users: ["your_telegram_id"]
    
  whatsapp:
    enabled: true
    allowed_numbers: ["+1234567890"]
```

## ðŸ’¬ Usage

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

### Telegram Control

Send commands to your bot:
```
/task Research quantum computing advances
/status Check agent status
/memory Show memory statistics
```

## ðŸ› ï¸ Development

### Project Structure

```
omniclaw/
â”œâ”€â”€ core/                    # Core Python modules
â”‚   â”œâ”€â”€ orchestrator.py      # Hybrid Hive orchestrator
â”‚   â”œâ”€â”€ manager.py           # Manager agent
â”‚   â”œâ”€â”€ worker.py            # Worker agents
â”‚   â”œâ”€â”€ memory.py            # Vector memory system
â”‚   â”œâ”€â”€ api_pool.py          # API management
â”‚   â””â”€â”€ messaging_gateway.py # Telegram/WhatsApp integration
â”œâ”€â”€ kernel_bridge/           # C++/eBPF kernel monitor
â”‚   â”œâ”€â”€ src/bpf/            # eBPF programs
â”‚   â”œâ”€â”€ src/cpp/            # C++ bridge
â”‚   â””â”€â”€ python_bridge.py    # Python bindings
â”œâ”€â”€ mobile_app/             # React Native super-app
â”‚   â”œâ”€â”€ src/screens/        # UI screens
â”‚   â”œâ”€â”€ src/services/       # Background services
â”‚   â””â”€â”€ src/store/          # State management
â”œâ”€â”€ scripts/                # Deployment scripts
â”œâ”€â”€ omniclaw.py            # Main entry point
â”œâ”€â”€ install.sh             # Installation script
â””â”€â”€ requirements.txt       # Python dependencies
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

## ðŸ”’ Security

- **API Key Encryption**: All API keys are encrypted at rest
- **Sandboxed Execution**: Shell commands run in restricted environment
- **User Authorization**: Messaging gateway requires explicit user allowlisting
- **Audit Logging**: All actions logged for review

## ðŸŒ Hardware Detection

The installer automatically detects your hardware and configures appropriately:

| Hardware | RAM | CPU | Model |
|----------|-----|-----|-------|
| High-End | 16GB+ | 8+ cores | llama2:13b / GPT-4 |
| Medium | 8GB | 4+ cores | llama2:7b / GPT-3.5 |
| Low/Mobile | <8GB | 2-4 cores | phi / API fallback |

## ðŸ“Š Performance

Benchmarks on different hardware configurations:

| Task | High-End | Medium | Mobile |
|------|----------|--------|--------|
| Simple Query | 0.5s | 1.2s | 2.5s |
| Code Generation | 2.1s | 4.5s | 8.0s |
| Research Task | 5.3s | 12.0s | 25.0s |
| Multi-API Coordination | 3.2s | 7.0s | 15.0s |

## ðŸ¤ Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/omniclaw.git

# Create branch
git checkout -b feature/amazing-feature

# Commit changes
git commit -m "Add amazing feature"

# Push and PR
git push origin feature/amazing-feature
```

## ðŸ“œ License

MIT License - see [LICENSE](LICENSE) file.

## ðŸ™ Acknowledgments

- [eBPF](https://ebpf.io/) for kernel monitoring capabilities
- [FAISS](https://github.com/facebookresearch/faiss) for vector search
- [LangChain](https://langchain.com/) for AI orchestration patterns
- [React Native](https://reactnative.dev/) for mobile framework

## ðŸ“ž Support

- ðŸ“§ Email: support@omniclaw.ai
- ðŸ’¬ Discord: [discord.gg/omniclaw](https://discord.gg/omniclaw)
- ðŸ› Issues: [GitHub Issues](https://github.com/omniclaw/omniclaw/issues)
- ðŸ“– Docs: [docs.omniclaw.ai](https://docs.omniclaw.ai)

---

<p align="center">
  <b>OmniClaw</b> - The Future of Autonomous AI Agents
  <br>
  <sub>Built with â¤ï¸ by Me</sub>
</p>
