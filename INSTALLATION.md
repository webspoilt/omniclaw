# OmniClaw System Installation Guide (v4.0.0+)

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

## Next Steps
Once these system dependencies are installed, you can proceed with the standard Python environment setup:
```bash
# 1. Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install Python requirements
pip install -r requirements.txt
```
