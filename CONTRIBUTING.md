<p align="center">
  <img src="https://raw.githubusercontent.com/webspoilt/omniclaw/main/public/logo.svg" width="120" height="120" alt="OmniClaw Logo">
</p>

# Contributing to OmniClaw

First off, thank you for considering contributing to OmniClaw! It's people like you that make OmniClaw such a great tool.

## ⚠️ Important Disclaimer 

Before contributing, please be aware that OmniClaw is currently in **Beta and is highly experimental**. Because of its deep system access capabilities (including Kernel features via eBPF), please ensure you develop and test your changes inside a safe Virtual Machine (VMware, VirtualBox, etc.). 

## 🤖 Local AI Support (Privacy First)

OmniClaw natively supports running **Local AI Models** as fully autonomous agents! You do not have to rely on paid APIs like OpenAI or Anthropic. 
If you want to contribute using completely free, offline models, simply install [Ollama](https://ollama.com/), pull your preferred local model (e.g., `llama3` or `mistral`), and ensure it is selected in your `config.yaml`. Local Agentic AIs ensure 100% data privacy while running the hybrid architecture.

## How to Contribute

### 1. Reporting Bugs
- Make sure you are on the latest version (`main` branch).
- Check if the bug has already been reported in the [Issues](https://github.com/webspoilt/omniclaw/issues) tab.
- If it hasn't, open a new issue. Include your OS, Python version, hardware specs, and clear steps to reproduce the bug.

### 2. Suggesting Enhancements
- Open a feature request in the [Issues](https://github.com/webspoilt/omniclaw/issues) tab.
- Describe the feature clearly and provide a use case demonstrating why it would be beneficial for the OmniClaw ecosystem.

### 3. Submitting Pull Requests
1. **Fork the Repository**: Create your own fork of `webspoilt/omniclaw`.
2. **Clone your Fork**: `git clone https://github.com/YOUR_USERNAME/omniclaw.git`
3. **Create a Branch**: Create a new branch for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make your Changes**: Write your code, ensuring you follow the existing coding style and document your new functions.
5. **Test your Changes**: Make sure your modifications haven't broken existing functionality. If modifying the Kernel Bridge layer, strictly test within a Linux VM.
6. **Commit Details**: Commit your changes with a descriptive commit message.
   ```bash
   git commit -m "feat: Add Claude 3.5 support to API pool"
   ```
7. **Push to Your Fork**: 
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Open a Pull Request**: Go to the original OmniClaw repository and click "Compare & pull request". Fill out the PR template describing your changes.

## Development Setup

To set up a local development environment:

```bash
git clone https://github.com/webspoilt/omniclaw.git
cd omniclaw
pip install -r requirements.txt
cp config.example.yaml config.yaml
# Edit config.yaml with API keys
python omniclaw.py chat
```

## Community

If you want to discuss your ideas before building them, or if you need help with the architecture:
- 📧 Email: heyzerodayhere@gmail.com
- 💬 Discord: [discord.gg/ZU4mQaqh](https://discord.gg/ZU4mQaqh)

Thank you for contributing!
