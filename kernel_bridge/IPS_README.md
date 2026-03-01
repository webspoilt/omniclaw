# OmniClaw IPS — Intrusion Prevention System

Autonomous network defense powered by eBPF kernel tracing and LLM-based threat classification.

## Architecture

```
┌──────────────────────────────┐
│  monitor.bpf.c  (kernel)     │  Traces tcp_v4_connect, inet_csk_accept
│  Ring buffer → ips_events    │  Per-IP failed login counter (LRU hash)
└───────────┬──────────────────┘
            │ ring buffer poll
┌───────────▼──────────────────┐
│  ips_agent.py  (userspace)   │  LLM classifier → IPBlocker → JSONL log
│  SecurityLayer.ips_agent     │  Dry-run mode / admin whitelist
└──────────────────────────────┘
```

## Prerequisites

| Dependency | Purpose | Install |
|---|---|---|
| `clang` ≥ 11 | BPF compiler | `apt install clang` |
| `libbpf-dev` | CO-RE BPF loader | `apt install libbpf-dev` |
| `linux-headers` | Kernel headers | `apt install linux-headers-$(uname -r)` |
| `bpftool` | Generate `vmlinux.h` | `apt install bpftool` |
| `bcc` (optional) | Python BPF bindings | `pip install bcc` |

On **Termux/Android**, eBPF is unavailable. The agent automatically falls back to `/var/log/auth.log` parsing or mock event simulation.

## Build

### Generate vmlinux.h (one-time setup)

```bash
# If not already present in kernel_bridge/src/bpf/
bpftool btf dump file /sys/kernel/btf/vmlinux format c > kernel_bridge/src/bpf/vmlinux.h
```

### Compile the IPS eBPF monitor only

```bash
cd kernel_bridge
make ips
# Output: build/monitor.bpf.o
```

### Compile everything (syscall_monitor + IPS + bridge)

```bash
cd kernel_bridge
make all
```

## Configuration

Edit `config.yaml` → `security.ips`:

```yaml
security:
  ips:
    enabled: true
    dry_run: true              # SAFETY: always start with true
    admin_whitelist:
      - "127.0.0.1"
      - "YOUR_VPS_IP"          # ← Replace with your admin IP
    fail_threshold: 5
    time_window_sec: 300
    block_tool: "iptables"     # or "nftables"
    llm_analysis: true
```

> **⚠️ Warning:** Set `dry_run: false` only after testing. A misconfigured IPS can lock you out of your own server.

## Usage

The IPS agent starts automatically with OmniClaw when `security.ips.enabled` is `true`:

```python
from core.security import SecurityLayer

sec = SecurityLayer(workspace_dir="./workspace")
sec.ips_agent.start()        # Background thread

# Check status
print(sec.ips_agent.get_status())

# Review recent actions (for Manager agent)
actions = sec.ips_agent.get_recent_actions(10)

# Runtime controls
sec.ips_agent.add_to_whitelist("1.2.3.4")
sec.ips_agent.set_dry_run(False)  # Go live

sec.ips_agent.stop()
```

## Directory Structure

```
kernel_bridge/
├── src/bpf/
│   ├── vmlinux.h            # Kernel BTF header (generated)
│   ├── syscall_monitor.c    # Existing syscall tracer
│   └── monitor.bpf.c        # ← NEW: IPS eBPF program
├── build/
│   ├── monitor.bpf.o        # Compiled BPF object
│   └── syscall_monitor.bpf.o
├── Makefile
└── IPS_README.md             # ← This file

core/security/
├── __init__.py               # SecurityLayer (6 layers)
├── ips_agent.py              # ← NEW: Python IPS agent
├── file_guard.py
├── shell_sandbox.py
├── prompt_guard.py
└── session_budget.py
```

## Action Log Format

Every IPS action is appended to `logs/ips_actions.jsonl`:

```json
{
  "timestamp": "2026-03-01T11:08:42+00:00",
  "event": {"src_ip": "45.33.32.156", "fail_count": 8, "alert_name": "brute_force"},
  "analysis": "brute_force",
  "verdict": "block",
  "command": "iptables -A INPUT -s 45.33.32.156 -j DROP",
  "executed": true,
  "dry_run": false,
  "blocked_ip": "45.33.32.156",
  "reason": "eBPF brute-force alert: 8 failures"
}
```

## Fallback Modes

| Environment | Event Source | Notes |
|---|---|---|
| Linux + root + BCC | eBPF ring buffer | Full kernel-level visibility |
| Linux + root (no BCC) | `/var/log/auth.log` | Parses SSH failures from syslog |
| Linux (non-root) | `/var/log/auth.log` | May need `adm` group for read access |
| Termux / Android | Mock events | Simulates brute-force cycles for testing |
| Windows / macOS | Mock events | Development/testing only |
