# OmniClaw System Installation Guide (v3.3.0+)

This guide contains the OS-specific system prerequisites required to run OmniClaw's advanced features (eBPF, audio capabilities, and binary requirements) natively before pip installing the Python requirements.

---

## 🐧 Ubuntu / Debian
Run the following commands to install the necessary compiler tools, audio headers, and eBPF dependencies:

```bash
sudo apt-get update
sudo apt-get install -y \
    python3-dev \
    libaudiodev-dev \
    portaudio19-dev \
    build-essential \
    linux-headers-$(uname -r) \
    bpfcc-tools \
    linux-headers-generic
```

## 🍏 macOS
If you use macOS, you will only have partial features (no true eBPF ring-0 kernel hooks), but you can still run OmniClaw with full audio and API support.

```bash
# Ensure Homebrew is installed, then run:
brew install portaudio
brew install python-dev
```

## 🪟 Windows (WSL2)
Native Windows is NOT supported for the kernel bridge. You must use WSL2 (Ubuntu).

1. Install WSL2 and Ubuntu from the Microsoft Store.
2. Open the WSL terminal and run the Ubuntu/Debian commands above. 
3. *Note: Advanced audio (PyAudio) routing from WSL2 into Windows requires additional PulseAudio network configurations.*

---

## Optional Feature Dependencies

Some OmniClaw features require additional packages not listed in the core `requirements.txt`:

| Package | Feature | Install |
|---|---|---|
| `croniter>=1.4.0` | Cron expression scheduling (CronScheduler) | `pip install croniter` |
| `mss>=9.0.0` | Cross-platform screen capture (Vision module) | `pip install mss` |
| `lancedb>=0.6.0` | Vector store memory backend | `pip install lancedb` |
| `networkx>=3.0` | Knowledge graph memory backend | `pip install networkx` |

> **Note (Issue #16):** `croniter` is optional. Without it, the CronScheduler will skip cron-expression jobs and only run interval-based jobs. A warning will be logged.

---

## Next Steps
Once these system dependencies are installed, you can proceed with the standard Python environment setup:
```bash
# 1. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install Python requirements
pip install -r requirements.txt

# 3. (Optional) Install extra feature deps
pip install croniter mss lancedb networkx
```
