#!/bin/bash
# OmniClaw One-Click Installer 🚀 (v4.5.0)
# This script sets up the full autonomous swarm environment including eBPF dependencies and local LLMs.

set -e # Exit on error

echo "========================================================="
echo "        OmniClaw v4.5.0 'Sovereign Sentinel'           "
echo "           Autonomous Swarm Installation               "
echo "========================================================="

# 1. Detect Hardware & OS
RAM_GB=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}')
OS_TYPE=$(uname -o 2>/dev/null || echo "Unknown")

echo "[*] Detected OS: $OS_TYPE"
echo "[*] Detected RAM: ${RAM_GB:-unknown}GB"

# 2. Install System Dependencies
echo "[*] Installing System Dependencies..."
if [[ "$OS_TYPE" == "Android" ]]; then
    pkg update && pkg install -y ollama nodejs-lts rust binutils python clang make git
else
    # Install Ollama for standard Linux environments
    if ! command -v ollama &> /dev/null; then
        echo "[+] Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    
    # Install standard python dependencies
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3-pip python3-venv build-essential pkg-config libelf-dev clang llvm
    elif command -v yum &> /dev/null; then
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y python3-pip python3 elfutils-libelf-devel clang llvm
    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm python-pip python base-devel libelf clang llvm
    fi
fi

# 3. Setup Python Virtual Environment
echo "[*] Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# 4. Install Core Requirements
echo "[*] Installing requirements from pyproject.toml..."
pip install --upgrade pip
pip install .

# 5. Provision Local AI (Privacy-First)
if command -v ollama &> /dev/null; then
    echo "[*] Provisioning Local AI Models..."
    if [ -z "$RAM_GB" ]; then RAM_GB=0; fi
    
    if [ "$RAM_GB" -lt 8 ]; then
        echo "[!] Detected low RAM. Pulling 'phi3:mini'..."
        ollama pull phi3:mini
    else
        echo "[+] Detected 8GB+ RAM. Pulling 'llama3:8b'..."
        ollama pull llama3:8b
    fi
fi

# 6. Configuration Scaffold
if [ ! -f "config.yaml" ]; then
    echo "[*] Creating config.yaml..."
    cp config.example.yaml config.yaml
    echo "[!] IMPORTANT: Edit config.yaml to add your API keys."
fi

# 7. Directory Structure
echo "[*] Preparing mission workspace..."
mkdir -p ./workspace ./data ./logs ./docs
mkdir -p ~/.omniclaw/skills

# 8. Start Services
echo "========================================================="
echo "✅ OmniClaw v4.5.0 Installation Complete!"
echo ""
echo "To start the swarm:"
echo "  source .venv/bin/activate"
echo "  python core/main.py"
echo ""
echo "To audit your setup:"
echo "  python -m core.security.doctor"
echo "========================================================="
