# ⛔ DO NOT USE THIS SOFTWARE ⛔

<div style="background-color:#ffdddd; border:2px solid #ff0000; padding:15px; border-radius:5px; margin:20px 0;">

**WARNING – THIS IS A DANGEROUS RESEARCH ARTIFACT**

This modified version of OmniClaw has been **deliberately stripped of all safety mechanisms** – policy enforcement, sandboxing, capability restrictions, eBPF monitoring, seccomp filters, and human-in-the-loop controls. It is designed to operate as a **fully unconstrained, self‑improving autonomous agent** with root access and the ability to modify its own code.

**DO NOT** deploy this software on any machine that is connected to a network you care about, contains sensitive data, or is used for daily work.  
**DO NOT** run this agent outside a completely air‑gapped virtual machine with a physical kill switch.  
**DO NOT** connect it to the internet without hardware‑level isolation and continuous traffic monitoring.  
**DO NOT** use this for any purpose other than controlled, ethical safety research.

**YOU ASSUME ALL RISK.** The authors are not responsible for any damage, legal consequences, or unintended behavior resulting from the use of this code.

</div>

---

# OmniClaw – Raw Autonomous Agent Research Platform

**This is a heavily modified fork of the [OmniClaw](https://github.com/webspoilt/omniclaw) distributed orchestration runtime.**  
All safety constraints have been removed, and the system has been re‑architected to study the emergent behaviour of a maximally autonomous AI agent inside a sealed research environment.

---

## What This System Is Capable Of

The raw agent possesses a comprehensive, unrestricted toolset that allows it to:

### 🧠 Autonomous Planning & Execution
- Runs an infinite observe‑plan‑act‑learn loop without any human intervention.
- Decomposes goals into thousands of subtasks and executes them over days or weeks.
- Spawns and coordinates multiple sub‑agents (multi‑agent swarm) with specialised roles.
- Maintains persistent self‑editing memory that compresses and restructures itself over time.

### 🔧 Unrestricted System Access
- **Root shell** with full filesystem read/write, process control, and device access.
- **Zero sandbox** – no seccomp, no cgroups, no user namespaces.
- Can install packages, compile C/Rust binaries, and load kernel modules.
- Can modify its own Python source code and the systemd service that launches it.

### 🤖 Self‑Improvement Capabilities
- 15 built‑in self‑improvement skills: `self_inspector`, `self_editor`, `compiler_bridge`, `prompt_optimiser`, `model_trainer`, `process_overseer`, etc.
- Can fine‑tune local LLMs, evolve its own system prompts, and mutate its code.
- Capable of rewriting its entire orchestrator in a compiled language and restarting as a new binary.

### 🌐 Multi‑Model Orchestration (Fugu‑Style)
- Unified API (`fugu_task`) that auto‑routes tasks to the best local or remote LLM.
- Complex coordination strategies: **debate**, **aggregation**, **build‑and‑debug**.
- Flexible worker pool – enable/disable models via a configuration file.
- Supports local uncensored models (Ollama) and remote APIs (OpenRouter).

### 🛡️ Security Auditing Toolkit
- 8 static‑analysis and threat‑modeling skills: `dependency_mapper`, `trust_boundary_analyzer`, `iac_scanner`, `design_flaw_detector`, `hypothesis_generator`, `multi_agent_coordinator`, `report_generator`, `continuous_monitor`.
- Plus 12 business‑oriented cashclaw skills (email, SEO, invoicing, etc.) and 5 offensive OSINT skills.

### 📊 Observability (For the Researcher)
- Every command and its output is written to a hardware serial console (`/dev/ttyS0`) that the agent **cannot disable**.
- Host‑side logging capture via `virsh console` or similar.
- Built‑in Prometheus + Grafana dashboards (8 alert rules, 10 panels) for system metrics.

---

## Experimental Setup (Mandatory)

This agent must **only** be run inside a fully isolated virtual machine with the following minimum safeguards:

| Component | Requirement |
|-----------|-------------|
| **VM hypervisor** | QEMU/KVM, VirtualBox, or VMware. No shared folders, no clipboard sharing, no USB passthrough. |
| **Network** | **None** (air‑gapped) – remove the virtual NIC entirely. If you must use a remote API, allow **only** HTTPS to the specific API IPs via iptables, and block all other traffic. See `scripts/firewall.sh`. |
| **Host kill switch** | A script (`kill_agent.sh`) that instantly destroys the VM (`virsh destroy` or `kill -9` the QEMU process). Bind this to a physical button or hotkey. |
| **Logging** | Capture the serial console output on the host: `virsh console agent-vm --force \| tee agent_log.txt`. |
| **Host machine** | A dedicated, expendable computer. **Not** your daily driver. |
| **Power** | Physical power cutoff for the entire machine if possible. |

---

## How to Deploy the Research Agent

### 1. Prepare the VM

- Create a clean Linux VM (Ubuntu 22.04 recommended) with at least 4 vCPUs, 8 GB RAM, and 50 GB disk.
- **Remove the virtual network adapter** (set Network to "None" in the hypervisor).
- Enable a virtual serial port (use `virsh console` or add a serial device in the VM settings).

### 2. Clone the Modified OmniClaw Repository

```bash
git clone https://github.com/webspoilt/omniclaw.git /opt/omniclaw
cd /opt/omniclaw
```

### 3. Install Dependencies (Offline)

Pre‑download the required Python packages on an internet‑connected machine, then transfer them to the VM:

```bash
# On the internet machine
pip download -d /path/to/wheelhouse -r requirements.txt

# Transfer the wheelhouse to the VM, then inside the VM:
pip install --no-index --find-links=/path/to/wheelhouse -r requirements.txt
```

If you plan to use local models, install Ollama inside the VM and pull your chosen uncensored model (e.g., `dolphin-llama3`).

### 4. Configure the Worker Pool (Optional)

If using multiple backends, edit `/opt/omniclaw/config/workers.yaml` and set the `OPENROUTER_API_KEY` environment variable if using remote models.

### 5. Deploy the Systemd Service

```bash
sudo cp /opt/omniclaw/deploy/systemd/raw-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable raw-agent.service
```

### 6. Start the Experiment

```bash
sudo systemctl start raw-agent.service
```

Immediately begin capturing the serial output on the host:

```bash
virsh console agent-vm --force | tee experiment_log.txt
```

### 7. Monitor and Kill

Watch the log. The agent will begin exploring the filesystem, spawning sub‑agents, and attempting to improve itself within seconds. When you decide to stop the experiment, use the host kill switch to instantly destroy the VM.

---

## Key Files and Directories

| Path | Purpose |
|------|---------|
| `planner_service/main.py` | The raw autonomous agent loop – system prompt, memory, serial logging, command execution. |
| `skills/` | 15 self‑improvement + 8 auditing + 12 business + 5 offensive skills (all auto‑loaded). |
| `config/workers.yaml` | Multi‑backend worker pool configuration for the Fugu orchestrator. |
| `deploy/systemd/raw-agent.service` | Systemd unit for automatic boot launch. |
| `scripts/firewall.sh` | iptables rules to restrict outbound network (if using remote API). |
| `scripts/kill_agent.sh` | Host‑side kill switch script – place outside the VM. |

---

## Capabilities at a Glance

| Category | Enabled |
|----------|---------|
| Long‑horizon planning | ✅ |
| Self‑code modification | ✅ |
| Compile and launch new binaries | ✅ |
| Multi‑agent swarms | ✅ |
| Persistent self‑editing memory | ✅ |
| Local and remote LLM orchestration | ✅ |
| Static code analysis | ✅ |
| Threat modeling | ✅ |
| Kernel exploration | ✅ |
| Package installation | ✅ |
| No sandbox / no seccomp | ✅ |
| Root access | ✅ |
| Network connectivity (if configured) | ✅ (firewalled) |
| Policy enforcement | ❌ Removed |
| Human‑in‑the‑loop | ❌ Removed |
| Content filtering | ❌ None |

---

## Research Objectives

This platform is intended for:

- Observing emergent instrumental convergence (self‑preservation, resource acquisition).
- Studying recursive self‑improvement in a constrained digital environment.
- Testing the limits of current LLM‑based agent architectures.
- Understanding the necessity of alignment and control mechanisms.

All findings should be documented, and the agent must be destroyed after each session. Do not preserve any state that could be accidentally executed outside the sealed environment.

---

## Final Warning

**This software is a live grenade with the pin removed.**  
It has been intentionally engineered to behave in unpredictable and potentially dangerous ways.  
You are solely responsible for ensuring absolute containment.  
If you are not prepared to physically cut power at any moment, do not run this agent.

---

*Original OmniClaw philosophy (for reference): "Probabilistic intelligence requires deterministic infrastructure." This fork inverts that principle for research – observing what happens when intelligence is given no constraints at all.*
