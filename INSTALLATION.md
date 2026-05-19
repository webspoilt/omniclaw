# OmniClaw — Installation Reference

This document covers system-level prerequisites for the Compute Core (Linux) and Edge Node (Android/Termux).

---

## Compute Core (Linux)

### System Dependencies

Ubuntu 22.04+ / Debian 12+:

```bash
sudo apt-get update && sudo apt-get install -y \
    python3-dev \
    build-essential \
    portaudio19-dev \
    linux-headers-$(uname -r) \
    clang \
    llvm \
    libbpf-dev \
    bpfcc-tools
```

> **Note:** `libbpf-dev` and `clang` are required only if you intend to compile and run the eBPF Security Bridge. They are not needed for Python-only deployments.

### macOS (Partial Support)

macOS supports the orchestration and Athena layers. The eBPF Security Bridge is Linux-only.

```bash
brew install portaudio python
```

### Windows (WSL2 Only)

Native Windows is not supported for the Compute Core. Use WSL2 running Ubuntu 22.04:

1. Install WSL2 via `wsl --install -d Ubuntu-22.04`
2. Run the Ubuntu system dependency commands above within WSL2.

> **Note:** eBPF requires a real Linux kernel. WSL2's kernel has limited BPF support. Test in a VM for full eBPF functionality.

---

## Edge Node (Termux / Android)

```bash
# Core runtime dependencies
pkg install python git openssh

# ZeroMQ and SQLite bindings
pip install pyzmq sqlite-vec msgpack
```

---

## Python Environment Setup

```bash
# 1. Create isolated environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows/WSL2

# 2. Install core requirements
pip install -r requirements.txt

# 3. Install optional feature packages
pip install lancedb networkx croniter
```

---

## Optional Feature Dependencies

| Package | Feature | Install |
|---|---|---|
| `lancedb >= 0.6.0` | Compute Core vector knowledge store | `pip install lancedb` |
| `sqlite-vec >= 0.1.0` | Edge Node vector cache | `pip install sqlite-vec` |
| `networkx >= 3.0` | Knowledge graph traversal | `pip install networkx` |
| `croniter >= 1.4.0` | Scheduled task expressions | `pip install croniter` |
| `lean4` (binary) | Formal theorem verification (Athena) | See [Lean4 installation](https://leanprover.github.io/lean4/doc/setup.html) |

---

## Verifying the Installation

```bash
# Start the orchestrator in dry-run mode to verify imports and config
python3 -m core.zmq_orchestrator --dry-run

# Expected output:
# [OK] ZeroMQ ROUTER socket initialized
# [OK] Policy loaded from config/policy.yaml
# [OK] LanceDB backend available
# [DRY-RUN] Exiting without binding.
```
