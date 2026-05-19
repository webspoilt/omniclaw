# OmniClaw — Operations Runbook

This document supersedes the earlier `deployment_v2.md`. It covers the operational details for running OmniClaw in a multi-node topology.

---

## Node Roles

| Role | Process | Bind Address |
|---|---|---|
| **Manager** | `core.zmq_orchestrator` | `tcp://0.0.0.0:5555` (ROUTER) |
| **Athena GPU Worker** | `modules.athena.transpiler_worker` | connects → 5555 (DEALER) |
| **eBPF Daemon** | `kernel_bridge/user_daemon` | IPC with orchestrator via ZMQ IPC socket |
| **Edge Gateway** | `edge.gateway` | connects → Manager IP:5555 (DEALER) |

---

## Startup Sequence (Compute Core)

Start services in dependency order:

```bash
# 1. Activate environment
source .venv/bin/activate

# 2. Load policy and start eBPF daemon (requires CAP_BPF)
sudo ./kernel_bridge/user_daemon --policy config/policy.yaml &

# 3. Start the ZeroMQ orchestrator (Manager)
python3 -m core.zmq_orchestrator --bind tcp://0.0.0.0:5555 &

# 4. Start Athena workers
python3 -m modules.athena.transpiler_worker --connect tcp://localhost:5555 &
python3 -m modules.athena.lean_worker --connect tcp://localhost:5555 &

# 5. (Optional) Start MCP server for IDE integration
python3 connectors/mcp_host.py &
```

---

## Startup Sequence (Edge Node)

```bash
# On Android via Termux
export OMNICLAW_MANAGER_IP=100.64.1.2   # Tailscale IP of Compute Core
export OMNICLAW_NODE_ID=$(hostname)

python3 -m edge.gateway \
    --manager tcp://$OMNICLAW_MANAGER_IP:5555 \
    --node-id $OMNICLAW_NODE_ID
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `OMNICLAW_MANAGER_IP` | `127.0.0.1` | IP of the ZeroMQ Manager Node |
| `OMNICLAW_NODE_ID` | `$(hostname)` | Unique identifier for this node |
| `OMNICLAW_POLICY_PATH` | `config/policy.yaml` | Path to the runtime policy file |
| `OMNICLAW_AES_KEY` | — | Base64-encoded 32-byte pre-shared key for P2P mesh |

---

## eBPF Shield Operational Details

The eBPF probe attaches at `do_exit` and `mprotect`. When an anomaly threshold is breached:

1. The ring buffer emits a `forensic_event` to `user_daemon`.
2. `user_daemon` writes CPU registers and 256 bytes of stack to `/var/omniclaw/forensics/<pid>_<ts>.bin`.
3. The process's `cgroup v2` slice is frozen via `cgroup.freeze`.
4. A `ANOMALY_ALERT` message is dispatched to the Manager over ZeroMQ IPC.
5. The Manager logs the event and issues `SIGKILL` to the frozen process.

```bash
# Monitor forensic vault output in real-time
sudo journalctl -f -u omniclaw-daemon
```

---

## MCP Server (IDE Integration)

The MCP server exposes orchestrator state and control tools to external IDEs.

```bash
python3 connectors/mcp_host.py --port 8000
```

**Available Resources:**

| Resource URI | Description |
|---|---|
| `system://cpu` | Current CPU utilization |
| `system://memory` | Memory pressure metrics |
| `security://kill_switch` | Kill switch state |

**Available Tools:**

| Tool | Description |
|---|---|
| `toggle_kill_switch` | Activate or deactivate the global execution halt |
| `get_orchestrator_status` | Returns active worker count and queue depth |
| `get_vector_sync_status` | Returns LanceDB / SQLite-vec sync state |

---

## Kill Switch

```bash
# Activate via Python
python3 -c "from core.kill_switch import activate; activate()"

# Deactivate after manual review
python3 -c "from core.kill_switch import deactivate; deactivate()"
```

When active, all workers exit their task loops cleanly, pending tasks are serialized to the local state store, and no new tasks are dispatched.

---

## Troubleshooting

| Symptom | Cause | Resolution |
|---|---|---|
| `Permission denied: bpf()` | Missing `CAP_BPF` | Run daemon with `sudo` or set capability on binary |
| `ZMQ: Connection refused` | Manager not yet bound | Ensure orchestrator starts before workers |
| Edge gateway disconnects | Android kills background Termux | Set Termux to "Unrestricted" in Battery settings |
| `eBPF load error: BTF not supported` | Kernel < 5.8 or BTF not compiled | Upgrade to Ubuntu 22.04 kernel |
| Vector sync stalls | LanceDB locked by another process | Stop the conflicting process; LanceDB uses file locking |
| Lean 4 worker exits immediately | Lean binary not found in PATH | Install Lean4 and ensure `lean` is on `$PATH` |
