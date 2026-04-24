# OmniClaw
Your autonomous AI agent swarm for Linux. Deploy multiple AI models that collaborate to monitor, defend, and manage your systems.

<p align="center">
  <img src="https://raw.githubusercontent.com/webspoilt/omniclaw/main/public/logo.svg" width="180" height="180" alt="OmniClaw Logo">
</p>

<p align="center">
  <a href="https://github.com/webspoilt/omniclaw/actions">
    <img src="https://img.shields.io/github/actions/workflow/status/webspoilt/omniclaw/install-test.yml?style=flat-square" alt="CI Status">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square" alt="License">
  </a>
  <a href="https://python.org">
    <img src="https://img.shields.io/badge/python-3.10+-blue.svg?style=flat-square" alt="Python">
  </a>
  <a href="https://github.com/webspoilt/omniclaw/issues">
    <img src="https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square" alt="PRs Welcome">
  </a>
</p>

### ⚡ One-Click Install
Deploy the autonomous swarm instantly on Linux or Termux:
```bash
curl -fsSL https://omniclaw.vercel.app/setup.sh | bash
```

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure
```bash
cp config.example.yaml config.yaml
# Add your API keys (OpenAI, Anthropic, Gemini, etc.)
```

### 3. Launch
```bash
python core/main.py
```

---

## 🎯 What It Does

OmniClaw is a 2026-era autonomous system designed for security research and system automation.

-   **Swarm Intelligence**: Multiple AI models (GPT-4o, Claude 3.5, Gemini 2.0) collaborate on complex tasks through a manager-worker architecture.
-   **Kernel-Level Monitoring**: eBPF-powered intrusion prevention that observes system calls and blocks threats in real-time.
-   **Vision Module**: Optimized screen capture (1024px, JPEG 85%) for visual UI audits and automated computer use.
-   **Multimodal Analysis**: Sends screenshots to multimodal LLMs for high-fidelity understanding of UI elements and security leaks.
-   **Self-Healing**: Automatically detects runtime errors, analyzes them via LLM, and applies fixes to its own code.

---

## 📖 Documentation

The project has moved to a structured documentation system to reduce README clutter:

-   🛠️ **[Setup Guide](docs/setup.md)**: Detailed installation for Linux, macOS, and Termux (Android).
-   🧠 **[Architecture Deep Dive](docs/architecture.md)**: How the Hybrid Hive and Kernel Bridge work.
-   📋 **[Feature Catalog](docs/features.md)**: Full list of 30+ autonomous capabilities.
-   🎯 **[Real-World Use Cases](USE_CASES.md)**: Practical scenarios from SSH defense to bug bounty hunting.
-   📜 **[Changelog](docs/changelog.md)**: Version history and upcoming roadmap.

---

## 🛡️ Security & Privacy

-   **Isolation**: Designed to run in sandboxed environments (VMs/Docker).
-   **Local First**: Supports strictly offline execution via Ollama.
-   **No-Training Guarantee**: Programmatically opts-out of data retention for all major API providers.

Read our **[Security Policy](SECURITY.md)** for more details.

---

## 🤝 Contributing

We welcome contributions! Please see our **[Contributing Guide](CONTRIBUTING.md)** and **[Code of Conduct](CODE_OF_CONDUCT.md)**.

Built with ❤️ by **Biswajeet Arukha** and the open-source community. Inspired by OmniParser, AutoGPT, and the global security community.
