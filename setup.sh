#!/bin/bash
# OmniClaw One-Click Installer 🚀 (v4.0.0)
echo "Starting OmniClaw Environment Setup for version 4.0.0..."

# 1. Detect Hardware & OS
RAM_GB=$(free -g 2>/dev/null | awk '/^Mem:/{print $2}')
OS_TYPE=$(uname -o 2>/dev/null || echo "Unknown")

echo "Detected OS: $OS_TYPE"
echo "Detected RAM: ${RAM_GB:-unknown}GB"

# 2. Install Dependencies (Termux/Linux)
echo "Installing System Dependencies..."
if [[ "$OS_TYPE" == "Android" ]]; then
    pkg update && pkg install -y ollama nodejs-lts rust binutils python
else
    # Install Ollama for standard Linux environments
    curl -fsSL https://ollama.com/install.sh | sh
    
    # Install standard python dependencies
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3-pip python3-venv
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip python3
    elif command -v pacman &> /dev/null; then
        sudo pacman -Sy --noconfirm python-pip python
    fi
fi

# 3. Setup Python environment
echo "Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# 4. Install Python dependencies
echo "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
fi

# 5. Auto-Configure AI Models
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

# 6. Setup Configuration
if [ ! -f "config.yaml" ]; then
    echo "Creating config.yaml from example..."
    cp config.example.yaml config.yaml
    echo "⚠️  Edit config.yaml with your API keys and Telegram token."
fi

# 7. Create workspace and skills directories
echo "Setting up workspace and skills directories..."
mkdir -p ./workspace
mkdir -p ~/.omniclaw/skills
mkdir -p ./data
mkdir -p ./logs

# 8. Run Security Doctor check
echo "Running security audit..."
python3 -c "
try:
    from core.security.doctor import SecurityDoctor
    doc = SecurityDoctor(workspace_dir='./workspace')
    report = doc.run_audit()
    print(f'Security audit: {report[\"status\"]}')
    print(report['summary'])
except Exception as e:
    print(f'Security audit skipped: {e}')
" 2>/dev/null || echo "Security audit skipped (module not loaded)"

# 9. Start OmniClaw Core & Bridge
echo "Starting OmniClaw Core..."
# Launch it as a daemon for background operation
nohup python3 omniclaw.py daemon > omniclaw.log 2>&1 &

echo "========================================================="
echo "✅ OmniClaw v4.0.0 is READY!"
echo ""
echo "Quick Start:"
echo "  python3 omniclaw.py chat          # Interactive chat"
echo "  python3 omniclaw.py daemon        # Background daemon mode"
echo ""
echo "New in v4.0.0:"
echo "  🛡️  5-layer security sandbox"
echo "  📦 Custom skill system (~/.omniclaw/skills/)"
echo "  ⏰ Persistent cron scheduler"
echo "  🫀 Heartbeat service (HEARTBEAT.md)"
echo ""
echo "Check config.yaml to set your Telegram Token and API keys."
echo "If configured, send 'PAIR' to your Telegram Bot to link."
echo "========================================================="
