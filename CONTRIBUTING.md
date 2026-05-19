# Contributing to OmniClaw

OmniClaw is an open-source distributed orchestration runtime. We welcome contributions from engineers who care about deterministic execution, systems-level observability, and secure AI infrastructure. This document outlines how to contribute effectively.

> **Important:** The eBPF Security Bridge and kernel-level components (`kernel_bridge/`) require a Linux host with kernel 5.8+ and `CAP_BPF`. Always develop and test kernel-adjacent changes inside an isolated Linux VM — never on a production host.

---

## Contribution Areas

We actively welcome contributions in the following domains:

| Area | Scope |
|---|---|
| **Orchestration Core** | ZeroMQ router logic, message schema evolution, worker lifecycle |
| **eBPF Shield** | Probe coverage, cgroup enforcement, ring-buffer performance |
| **Athena Engine** | SymPy transpilation accuracy, Lean 4 integration, sandbox hardening |
| **Vector Sync Layer** | LanceDB query optimization, SQLite-vec edge caching, sync heuristics |
| **Observability** | OpenTelemetry span coverage, structured logging, telemetry pipelines |
| **Policy Engine** | `policy.yaml` schema, capability validation, enforcement logic |
| **Edge Runtime** | Termux compatibility, resource-aware scheduling, adaptive inference |
| **Documentation** | Architecture diagrams, API references, deployment runbooks |

---

## Development Setup

### Prerequisites

- Python 3.10+
- Linux OS (Ubuntu 22.04+ recommended for eBPF work)
- ZeroMQ (`libzmq`) system library

### Compute Core Setup

```bash
git clone https://github.com/webspoilt/omniclaw.git
cd omniclaw

# Create an isolated virtual environment
python -m venv .venv && source .venv/bin/activate

# Install core dependencies
pip install -r requirements.txt

# Verify the orchestrator starts cleanly
python3 -m core.zmq_orchestrator --dry-run
```

### eBPF Development (Linux only)

```bash
# Install kernel build tools
sudo apt-get install -y clang llvm libbpf-dev linux-headers-$(uname -r)

# Compile the forensic snapshot probe
cd kernel_bridge && make
```

---

## Submitting a Pull Request

1. **Fork** the repository and create a feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```
2. **Write tests** for any logic changes. PRs without test coverage for new code paths will not be merged.
3. **Document your changes.** If you modify a ZeroMQ message schema or policy enforcement rule, update the relevant architecture diagram or `ARCHITECTURE_AUDIT.md`.
4. **Commit** using the conventional commit format:
   ```bash
   git commit -m "feat(orchestrator): add backpressure handling for stalled DEALER sockets"
   ```
5. **Open a Pull Request** describing the problem, the solution, and any tradeoffs made.

---

## Code Standards

- **Python:** Follow PEP 8. Use type annotations on all public functions.
- **C++/eBPF:** BPF programs must pass `bpf_verifier` without warnings. Userspace daemons must be valgrind-clean.
- **No `shell=True`:** All subprocess calls must use explicit argument lists. This is enforced in CI.
- **No hardcoded secrets:** API keys and credentials must be sourced from environment variables or the system vault. Any commit introducing a plaintext secret will be rejected.

---

## Reporting Issues

- **Security vulnerabilities:** Email `heyzerodayhere@gmail.com` directly. Do not open a public issue.
- **Bugs:** Open a GitHub Issue with your OS version, Python version, kernel version (if relevant), and a minimal reproduction case.
- **Feature Requests:** Open a GitHub Discussion before implementing large changes. Alignment on architecture early prevents wasted effort.

---

## Community

- **Email:** heyzerodayhere@gmail.com
- **Discord:** [discord.gg/ZU4mQaqh](https://discord.gg/ZU4mQaqh)
