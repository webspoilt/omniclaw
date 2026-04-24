# 🍼 24/7 Deployment & Setup Guide

This guide covers the quickest path to getting OmniClaw v4.5.0 running continuously on your hardware.

## 🖥️ 1. Linux Desktop / Server (Recommended)

Linux is the native home of OmniClaw, offering the best performance for the eBPF Kernel Bridge.

### Quick Install
```bash
# Clone the repo
git clone https://github.com/webspoilt/omniclaw.git
cd omniclaw

# Install dependencies
pip install -r requirements.txt

# Run the verify script to check for kernel headers
python scripts/verify_install.py
```

### 24/7 Operation with PM2
To keep OmniClaw running even if the process crashes or the server reboots:
```bash
npm install -g pm2
pm2 start core/main.py --name omniclaw
pm2 save
pm2 startup
```

---

## 📱 2. Mobile (Android via Termux)

Run OmniClaw 24/7 on an old Android phone. It consumes very little electricity and acts as a perfect mobile security node.

### Prerequisites
1.  Install **Termux** from F-Droid.
2.  Enable "Run in Background" in Android settings for Termux.

### Commands
```bash
pkg update && pkg upgrade
pkg install python git clang make
pip install -r requirements.txt

# Start the daemon
python core/main.py
```

---

## 🍎 3. macOS (Apple Silicon)

OmniClaw uses ScreenCaptureKit on macOS for high-performance vision.

### Quick Install
```bash
pip install -r requirements.txt

# Ensure you give your terminal 'Screen Recording' permissions
python core/main.py
```

---

## ⚙️ Configuration (config.yaml)

OmniClaw requires at least one API key to function as an autonomous agent.

1.  `cp config.example.yaml config.yaml`
2.  Open `config.yaml` and set your provider:
    -   **Ollama (Local)**: Set `provider: "ollama"` (Zero cost, maximum privacy).
    -   **OpenAI/Anthropic**: Add your keys in the `keys` section.

---

## ⚠️ Security Checklist
-   [ ] **Run in a VM**: Highly recommended for the eBPF module.
-   [ ] **Set a Kill Switch**: Configure `KILL_SWITCH_SECRET` in your environment.
-   [ ] **Permissions**: Don't run as root unless you specifically need eBPF monitoring.
