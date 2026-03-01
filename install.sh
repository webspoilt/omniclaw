#!/bin/bash
#
# OmniClaw Installation Script
# Detects hardware and installs appropriate components
# Usage: curl -fsSL https://omniclaw.ai/install.sh | bash
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="${OMNICLAW_DIR:-$HOME/.omniclaw}"
CONFIG_DIR="$HOME/.config/omniclaw"
LOG_FILE="/tmp/omniclaw_install.log"
REPO_URL="https://github.com/webspoilt/omniclaw"
VERSION="4.1.0"

# Logging
log() {
    echo -e "${BLUE}[OmniClaw]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${CYAN}[i]${NC} $1" | tee -a "$LOG_FILE"
}

# Banner
print_banner() {
    echo -e "${PURPLE}"
    cat << "EOF"
   ____  __  ___________  ____________    __ 
  / __ \/ / / / ___/ __ \/ ____/  _/ /   / / 
 / / / / /_/ / /  / / / / /    / // /   / /  
/ /_/ / __  / /__/ /_/ / /____/ // /___/ /___
\____/_/ /_/\___/_____/\____/___/_____/_____/
                                              
EOF
    echo -e "${NC}"
    echo -e "${CYAN}Hybrid Hive AI Agent System - v${VERSION}${NC}"
    echo -e "${CYAN}https://omniclaw.ai${NC}"
    echo ""
}

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-android"* ]] || [[ -d "/data/data/com.termux" ]]; then
        echo "android"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [[ -f "/etc/os-release" ]]; then
            . /etc/os-release
            echo "$ID"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Detect architecture
detect_arch() {
    local arch=$(uname -m)
    case "$arch" in
        x86_64|amd64) echo "amd64" ;;
        aarch64|arm64) echo "arm64" ;;
        armv7l|armhf) echo "arm" ;;
        i386|i686) echo "386" ;;
        *) echo "$arch" ;;
    esac
}

# Detect hardware capabilities
detect_hardware() {
    log "Detecting hardware capabilities..."
    
    local os=$(detect_os)
    local arch=$(detect_arch)
    local cpu_cores=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo "1")
    local total_ram=$(free -m 2>/dev/null | awk '/^Mem:/{print $2}' || sysctl -n hw.memsize 2>/dev/null | awk '{print int($1/1024/1024)}' || echo "0")
    local gpu_info=""
    
    # Detect GPU
    if command -v nvidia-smi &> /dev/null; then
        gpu_info=$(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | head -1)
    elif command -v rocm-smi &> /dev/null; then
        gpu_info=$(rocm-smi --showproductname 2>/dev/null | grep "GPU" | head -1)
    fi
    
    # Determine device class
    local device_class="low"
    if [[ "$total_ram" -ge 16000 ]] && [[ "$cpu_cores" -ge 8 ]]; then
        device_class="high"
    elif [[ "$total_ram" -ge 8000 ]] && [[ "$cpu_cores" -ge 4 ]]; then
        device_class="medium"
    fi
    
    # Android/Termux specific
    if [[ "$os" == "android" ]]; then
        device_class="mobile"
    fi
    
    log_info "OS: $os"
    log_info "Architecture: $arch"
    log_info "CPU Cores: $cpu_cores"
    log_info "RAM: ${total_ram}MB"
    log_info "GPU: ${gpu_info:-None detected}"
    log_info "Device Class: $device_class"
    
    echo "$os|$arch|$cpu_cores|$total_ram|$device_class|$gpu_info"
}

# Check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    local missing_deps=()
    
    # Essential tools
    for cmd in curl wget git python3 pip3; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_warning "Missing dependencies: ${missing_deps[*]}"
        return 1
    fi
    
    log_success "All essential dependencies found"
    return 0
}

# Install system dependencies
install_system_deps() {
    local os=$1
    
    log "Installing system dependencies for $os..."
    
    case "$os" in
        ubuntu|debian)
            sudo apt-get update
            sudo apt-get install -y \
                python3-pip python3-venv python3-dev \
                build-essential libffi-dev libssl-dev \
                clang llvm libbpf-dev linux-headers-$(uname -r) \
                nodejs npm cargo rustc libwebkit2gtk-4.1-dev \
                build-essential curl wget file libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev \
                ffmpeg \
                2>&1 | tee -a "$LOG_FILE"
            ;;
        fedora|rhel|centos)
            sudo dnf install -y \
                python3-pip python3-devel \
                gcc gcc-c++ make \
                clang llvm bpftrace kernel-devel \
                nodejs npm cargo rust gtk3-devel webkit2gtk4.1-devel \
                ffmpeg \
                2>&1 | tee -a "$LOG_FILE"
            ;;
        arch|manjaro)
            sudo pacman -S --noconfirm \
                python-pip python-virtualenv base-devel \
                clang llvm libbpf linux-headers \
                nodejs npm cargo rust webkit2gtk-4.1 \
                ffmpeg \
                2>&1 | tee -a "$LOG_FILE"
            ;;
        macos)
            if command -v brew &> /dev/null; then
                brew install python node rust ffmpeg 2>&1 | tee -a "$LOG_FILE"
            else
                log_error "Homebrew not found. Please install Homebrew first."
                exit 1
            fi
            ;;
        android)
            pkg update
            pkg install -y \
                python python-pip clang llvm \
                nodejs rust ffmpeg \
                git curl wget \
                2>&1 | tee -a "$LOG_FILE"
            ;;
        *)
            log_warning "Unknown OS. Please install dependencies manually."
            ;;
    esac
    
    # Ensure Rust is fully available if we didn't get it via package manager
    if ! command -v cargo &> /dev/null; then
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source $HOME/.cargo/env
    fi
    
    log_success "System dependencies installed"
}

# Install Python dependencies
install_python_deps() {
    local device_class=$1
    
    log "Installing Python dependencies..."
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel 2>&1 | tee -a "$LOG_FILE"
    
    # Core dependencies
    pip install \
        asyncio aiohttp websockets \
        numpy pandas \
        requests httpx \
        python-telegram-bot \
        psutil nicegui \
        litellm sentence-transformers GitPython watchdog \
        2>&1 | tee -a "$LOG_FILE"
    
    # AI/ML libraries based on device class
    case "$device_class" in
        high)
            log_info "Installing high-end ML libraries..."
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 2>&1 | tee -a "$LOG_FILE" || true
            pip install transformers accelerate bitsandbytes 2>&1 | tee -a "$LOG_FILE" || true
            ;;
        medium)
            log_info "Installing medium-tier ML libraries..."
            pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu 2>&1 | tee -a "$LOG_FILE" || true
            pip install transformers 2>&1 | tee -a "$LOG_FILE" || true
            ;;
        low|mobile)
            log_info "Installing lightweight ML libraries..."
            pip install onnxruntime tflite-runtime 2>&1 | tee -a "$LOG_FILE" || true
            ;;
    esac
    
    # Vector database
    pip install faiss-cpu 2>&1 | tee -a "$LOG_FILE" || pip install faiss-gpu 2>&1 | tee -a "$LOG_FILE" || true
    
    log_success "Python dependencies installed"
}

# Install Ollama (local LLM)
install_ollama() {
    local device_class=$1
    
    if [[ "$device_class" == "mobile" ]]; then
        log_warning "Skipping Ollama on mobile (resource intensive)"
        return
    fi
    
    log "Installing Ollama..."
    
    if ! command -v ollama &> /dev/null; then
        curl -fsSL https://ollama.ai/install.sh | sh 2>&1 | tee -a "$LOG_FILE"
        
        # Pull appropriate model based on hardware
        local model="llama2"
        if [[ "$device_class" == "high" ]]; then
            model="llama2:13b"
        elif [[ "$device_class" == "medium" ]]; then
            model="llama2:7b"
        else
            model="phi"
        fi
        
        log_info "Pulling Ollama model: $model"
        ollama pull "$model" 2>&1 | tee -a "$LOG_FILE" || true
        
        log_success "Ollama installed with model: $model"
    else
        log_success "Ollama already installed"
    fi
}

# Setup kernel bridge
setup_kernel_bridge() {
    local os=$1
    
    if [[ "$os" == "android" ]] || [[ "$os" == "macos" ]]; then
        log_warning "Kernel bridge not supported on $os"
        return
    fi
    
    log "Setting up kernel bridge..."
    
    cd "$INSTALL_DIR/kernel_bridge"
    make clean 2>/dev/null || true
    make 2>&1 | tee -a "$LOG_FILE" || log_warning "Kernel bridge build failed (optional)"
    
    # Also build the IPS eBPF monitor
    make ips 2>&1 | tee -a "$LOG_FILE" || log_warning "IPS monitor build failed (optional, requires libbpf)"
    
    log_success "Kernel bridge setup complete"
}

# Download OmniClaw source
download_source() {
    log "Downloading OmniClaw source..."
    
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        cd "$INSTALL_DIR"
        git pull origin main 2>&1 | tee -a "$LOG_FILE"
    else
        git clone --depth 1 "$REPO_URL" "$INSTALL_DIR" 2>&1 | tee -a "$LOG_FILE" || {
            log_warning "Git clone failed, creating directory structure..."
            mkdir -p "$INSTALL_DIR"
        }
    fi
    
    log_success "Source downloaded to $INSTALL_DIR"
}

# Create configuration
create_config() {
    log "Creating configuration..."
    
    mkdir -p "$CONFIG_DIR"
    
    cat > "$CONFIG_DIR/config.yaml" << EOF
# OmniClaw Configuration
version: "$VERSION"

# Device settings
device:
  class: "auto"
  max_workers: 4
  memory_limit: "2GB"

# API Configuration
apis:
  # Add your API keys here
  # - provider: openai
  #   key: "your-key-here"
  #   model: gpt-4
  #   priority: 1

# Memory settings
memory:
  db_path: "$CONFIG_DIR/memory"
  embedding_provider: "ollama"
  max_history: 1000

# Kernel bridge
kernel_bridge:
  enabled: true
  monitor_syscalls: true
  monitor_files: false
  monitor_network: false

# Messaging gateway
messaging:
  telegram:
    enabled: false
    token: ""
    allowed_users: []
  whatsapp:
    enabled: false
    allowed_numbers: []

# Automation settings
automation:
  trading:
    enabled: false
    platforms: []
  bug_bounty:
    enabled: false
    targets: []

# Logging
logging:
  level: "INFO"
  file: "$CONFIG_DIR/omniclaw.log"
  max_size: "100MB"
  backup_count: 5

# Security — IPS Agent (v4.1)
security:
  ips:
    enabled: true
    dry_run: true
    admin_whitelist:
      - "127.0.0.1"
    fail_threshold: 5
    time_window_sec: 300
    block_tool: "iptables"
    llm_analysis: true
EOF
    
    log_success "Configuration created at $CONFIG_DIR/config.yaml"
}

# Create systemd service (Linux only)
create_service() {
    local os=$1
    
    if [[ "$os" == "android" ]] || [[ "$os" == "macos" ]]; then
        return
    fi
    
    log "Creating systemd service..."
    
    sudo tee /etc/systemd/system/omniclaw.service > /dev/null << EOF
[Unit]
Description=OmniClaw AI Agent
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment=PATH=$INSTALL_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$INSTALL_DIR
Environment=OMNICLAW_CONFIG=$CONFIG_DIR/config.yaml
ExecStart=$INSTALL_DIR/venv/bin/python -m omniclaw.daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    sudo systemctl daemon-reload
    log_success "Systemd service created"
    log_info "Start with: sudo systemctl start omniclaw"
    log_info "Enable auto-start: sudo systemctl enable omniclaw"
}

# Setup Tauri Mission Control GUI
setup_mission_control() {
    log "Setting up Tauri Mission Control GUI..."
    
    if [[ -d "$INSTALL_DIR/mission-control" ]]; then
        cd "$INSTALL_DIR/mission-control"
        npm install 2>&1 | tee -a "$LOG_FILE" || log_warning "npm install for GUI failed"
        
        # We don't build it during global install to save time
        # Users can run 'npm run tauri build' when desired
        log_success "Mission Control GUI dependencies installed"
    else
        log_warning "Mission Control GUI source not found"
    fi
}

# Create launcher scripts
create_launchers() {
    log "Creating launcher scripts..."
    
    # Main CLI
    cat > "$INSTALL_DIR/omniclaw" << 'EOF'
#!/bin/bash
source "$HOME/.omniclaw/venv/bin/activate"
export OMNICLAW_CONFIG="$HOME/.config/omniclaw/config.yaml"
python -m omniclaw.cli "$@"
EOF
    chmod +x "$INSTALL_DIR/omniclaw"
    
    # Daemon
    cat > "$INSTALL_DIR/omniclaw-daemon" << 'EOF'
#!/bin/bash
source "$HOME/.omniclaw/venv/bin/activate"
export OMNICLAW_CONFIG="$HOME/.config/omniclaw/config.yaml"
python -m omniclaw.daemon "$@"
EOF
    chmod +x "$INSTALL_DIR/omniclaw-daemon"
    
    # Create symlink
    mkdir -p "$HOME/.local/bin"
    ln -sf "$INSTALL_DIR/omniclaw" "$HOME/.local/bin/omniclaw"
    ln -sf "$INSTALL_DIR/omniclaw-daemon" "$HOME/.local/bin/omniclaw-daemon"
    
    log_success "Launchers created"
}

# Main installation
main() {
    print_banner
    
    log "Starting OmniClaw installation..."
    log_info "Install directory: $INSTALL_DIR"
    log_info "Config directory: $CONFIG_DIR"
    
    # Detect hardware
    IFS='|' read -r os arch cpu_cores ram device_class gpu_info <<< "$(detect_hardware)"
    
    # Check dependencies
    if ! check_dependencies; then
        log "Installing system dependencies..."
        install_system_deps "$os"
    fi
    
    # Create directories
    mkdir -p "$INSTALL_DIR" "$CONFIG_DIR"
    
    # Download source
    download_source
    
    # Install Python dependencies
    install_python_deps "$device_class"
    
    # Install Ollama (optional)
    install_ollama "$device_class"
    
    # Setup kernel bridge
    setup_kernel_bridge "$os"
    
    # Create configuration
    create_config
    
    # Create service
    create_service "$os"
    
    # Setup Mission Control GUI
    setup_mission_control
    
    # Create launchers
    create_launchers
    
    # Print completion
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          OmniClaw Installation Complete!                   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    log_success "OmniClaw v${VERSION} installed successfully!"
    echo ""
    echo -e "${CYAN}Quick Start:${NC}"
    echo "  1. Edit config: nano $CONFIG_DIR/config.yaml"
    echo "  2. Add API keys to enable cloud models"
    echo "  3. Start daemon: omniclaw-daemon"
    echo "  4. Run CLI: omniclaw"
    echo ""
    echo -e "${CYAN}Commands:${NC}"
    echo "  omniclaw --help          Show help"
    echo "  omniclaw status          Check agent status"
    echo "  omniclaw task <goal>     Execute a task"
    echo "  omniclaw chat            Start interactive chat"
    echo ""
    echo -e "${CYAN}Documentation:${NC} https://docs.omniclaw.ai"
    echo -e "${CYAN}Support:${NC} https://github.com/omniclaw/omniclaw/issues"
    echo ""
    
    if [[ "$os" != "android" ]]; then
        echo -e "${YELLOW}Note:${NC} Add $HOME/.local/bin to your PATH if not already there"
        echo ""
    fi
}

# Handle arguments
case "${1:-}" in
    --uninstall)
        log "Uninstalling OmniClaw..."
        rm -rf "$INSTALL_DIR" "$CONFIG_DIR"
        rm -f "$HOME/.local/bin/omniclaw" "$HOME/.local/bin/omniclaw-daemon"
        sudo rm -f /etc/systemd/system/omniclaw.service
        log_success "OmniClaw uninstalled"
        ;;
    --update)
        log "Updating OmniClaw..."
        cd "$INSTALL_DIR"
        git pull origin main
        source "$INSTALL_DIR/venv/bin/activate"
        pip install -e . --upgrade
        log_success "OmniClaw updated"
        ;;
    *)
        main
        ;;
esac
