#!/bin/bash
# OmniClaw One-Click Installer 🚀
echo "Starting OmniClaw Environment Setup..."

# 1. Detect Hardware & OS
RAM_GB=$(free -g | awk '/^Mem:/{print $2}')
OS_TYPE=$(uname -o)

echo "Detected OS: $OS_TYPE"
echo "Detected RAM: ${RAM_GB}GB"

# 2. Install Dependencies (Termux/Linux)
echo "Installing System Dependencies..."
if [[ "$OS_TYPE" == "Android" ]]; then
    pkg update && pkg install -y ollama nodejs-lts rust binutils
else
    # Install Ollama for standard Linux environments
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Install standard python dependencies
    sudo apt-get update && sudo apt-get install -y python3-pip python3-venv
fi

# 3. Auto-Configure AI Models
echo "Auto-Provisioning Local AI Models..."
# Fallback to 0 if RAM_GB is somehow not parsed correctly
if [ -z "$RAM_GB" ]; then RAM_GB=0; fi

if [ "$RAM_GB" -lt 6 ]; then
    echo "Detected <6GB RAM. Pulling smaller 'gemma:1b' model..."
    ollama pull gemma:1b
else
    echo "Detected 6GB+ RAM. Pulling capable 'llama3.1:8b' model..."
    ollama pull llama3.1:8b
fi

# 4. Start OmniClaw Core & Bridge
echo "Starting Defensive eBPF Bridge & OmniClaw Core..."
# Check if python dependencies need installing
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
fi

# Example Command to run the agent in the background (nohup)
echo "Launching OmniClaw..."
nohup python3 omniclaw.py chat > omniclaw.log 2>&1 &

echo "========================================================="
echo "✅ OmniClaw is READY!"
echo "Check your config.yaml to ensure your Telegram Token is set."
echo "If configured, send 'PAIR' to your Telegram Bot to link this device."
echo "========================================================="
