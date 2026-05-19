# OmniClaw — Deployment Guide

This guide covers deploying OmniClaw across the two supported hardware profiles: the **Compute Core** (Linux x86-64) and the **Edge Node** (Android/ARM via Termux).

> **Security note:** OmniClaw's eBPF Security Bridge requires `CAP_BPF` and kernel 5.8+. Always run kernel-adjacent components on an isolated Linux host, not a shared production machine.

---

## Hardware Profiles

| Requirement | Compute Core | Edge Node |
|---|---|---|
| **OS** | Linux (Ubuntu 22.04+) | Android (Termux) |
| **Python** | 3.10+ | 3.10+ via `pkg` |
| **ZeroMQ** | `pip install pyzmq` | `pip install pyzmq` |
| **Vector DB** | `pip install lancedb` | `pip install sqlite-vec` |
| **eBPF toolchain** | `clang`, `libbpf`, `bpftool`, kernel 5.8+ | ❌ Not supported |
| **LLM Runtime** | Ollama (local) or API provider | Ollama (if thermal budget allows) |
| **Root** | Required for eBPF only | ❌ Not required |

---

## 1. Compute Core Deployment

### 1.1 System Dependencies

```bash
sudo apt-get update && sudo apt-get install -y \
    clang llvm \
    libbpf-dev \
    linux-headers-$(uname -r) \
    build-essential \
    portaudio19-dev
```

### 1.2 Python Environment

```bash
git clone https://github.com/webspoilt/omniclaw.git
cd omniclaw

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 1.3 Policy Configuration

Copy and edit the policy file before starting any workers:

```bash
cp config/policy.yaml.example config/policy.yaml
```

Key parameters to configure:

```yaml
# config/policy.yaml
ebpf_heuristics:
  oom_prediction_lead_seconds: 30   # Lead time before OOM kill
  exit_anomaly_sensitivity: 0.85

athena:
  max_gpu_temp_c: 82                # Kill GPU tasks above this threshold
  max_sandbox_memory_mb: 512

network_qos:
  orchestration_dscp: 46            # Expedited Forwarding — highest priority
  vector_sync_dscp: 26              # Assured Forwarding
  sensor_data_dscp: 0               # Best effort
```

### 1.4 eBPF Shield Compilation

```bash
cd kernel_bridge
make all
# Loads the forensic_snapshot probe. Requires CAP_BPF.
sudo ./user_daemon --policy ../config/policy.yaml
```

### 1.5 Start the Orchestrator

```bash
# In a separate terminal, start the ZeroMQ Manager
python3 -m core.zmq_orchestrator --bind tcp://0.0.0.0:5555

# In another terminal, start the Athena GPU worker
python3 -m modules.athena.transpiler_worker --connect tcp://localhost:5555
```

---

## 2. Edge Node Deployment (Termux / Android)

The Edge Node runs entirely in userspace. No root access is required or expected.

### 2.1 Install Termux

Install from [F-Droid](https://f-droid.org) — the Play Store version is outdated and unsupported.

### 2.2 Initial Setup

```bash
# Update package index
pkg update && pkg upgrade -y

# Install core dependencies
pkg install python git

# Install ZeroMQ bindings
pip install pyzmq sqlite-vec msgpack
```

### 2.3 Remote Development via SSH

Working directly on a phone touchscreen is impractical. Use SSH:

```bash
# On the phone
pkg install openssh
passwd          # Set a session password
sshd            # Start SSH daemon on port 8022
ifconfig        # Note the wlan0 IP address

# From your workstation (same network)
ssh -p 8022 u0_a_YOUR_USER@192.168.x.x
```

### 2.4 Start the Edge Gateway

```bash
# Point to your Compute Core's Tailscale or LAN IP
export OMNICLAW_MANAGER_IP=192.168.1.50
export OMNICLAW_NODE_ID=edge-poco-x3

pip install -r requirements-edge.txt
python3 -m edge.gateway
```

---

## 3. Resource Governance

All OmniClaw modules respect hardware constraints via `resource_check()`:

```python
from core.resource_utils import resource_check

# Blocks heavy operations when resources are constrained
if resource_check(profile="edge"):
    run_heavy_inference()
```

**Edge thresholds** (configurable in `policy.yaml`):

| Metric | Abort Threshold |
|---|---|
| Battery | < 20% |
| CPU usage | > 70% for > 10s |
| Memory | > 80% of device RAM |

When thresholds are breached, pending tasks are serialized to the local SQLite-vec cache and offloaded to the Compute Core on next reconnection.

---

## 4. Kill Switch

A global kill switch halts all autonomous execution immediately:

```python
from core.kill_switch import activate, deactivate, check_kill_switch

check_kill_switch()  # Raises RuntimeError if active — call before any autonomous action
activate()           # Halt all workers
deactivate()         # Resume after manual review
```

The kill switch can also be toggled via the MCP tool `toggle_kill_switch` or the web dashboard.

---

## 5. Troubleshooting

| Symptom | Cause | Resolution |
|---|---|---|
| `eBPF load failed: permission denied` | Insufficient kernel capabilities | Run the daemon with `sudo` or grant `CAP_BPF` |
| `ZMQ: Connection refused on 5555` | Orchestrator not running | Start `core.zmq_orchestrator` first |
| `LanceDB not found` | Missing dependency | `pip install lancedb` on the Compute Core |
| `ollama: connection refused` | Ollama not running | Run `ollama serve` in a background shell |
| Edge node disconnects on idle | Android battery optimization | Set Termux to "Unrestricted" in Battery settings |
| `resource_check failed: CPU > 70%` | Thermal throttling on Edge | Reduce inference frequency or offload to Core |
| `CONTEXT_HANDOFF timeout` | Network interruption | The Edge caches locally and retries on reconnect |

---

## 6. Legal Notice

OmniClaw is provided for legitimate research, infrastructure automation, and AI orchestration use cases. Using this software to access or compromise systems without explicit authorization is illegal and is not condoned by this project.
