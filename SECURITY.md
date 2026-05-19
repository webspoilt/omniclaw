# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| v4.5.x (current) | ✅ Yes |
| < v4.5 | ❌ No |

---

## Reporting a Vulnerability

If you discover a security vulnerability in OmniClaw, **do not open a public GitHub issue.**

Please report it to: **heyzerodayhere@gmail.com**

All reports are acknowledged within 24 hours. We will work with you to validate and remediate the issue before any coordinated disclosure.

---

## Security Design Principles

OmniClaw is built on a threat model that assumes the AI planner is compromised or hallucinating. The following controls are non-negotiable:

### Execution Isolation
- All AI-generated code runs inside `unshare` namespaces with isolated mount, network, and PID namespaces.
- Processes are constrained by `cgroup v2` memory and CPU limits defined in `policy.yaml`.
- `shell=True` is explicitly prohibited at the code level. All subprocess calls use structured argument lists.

### eBPF Shield (Linux Compute Core only)
- A `kprobe` on `do_exit` captures forensic process state before anomalous terminations.
- Detected out-of-bounds syscalls freeze the offending `cgroup` slice before termination, preserving a tamper-proof forensic vault.

### Credential Management
- API keys must never be committed to the repository. Use environment variables or the system credential vault.
- ZeroMQ peer authentication uses pre-shared keys distributed via secure out-of-band channels. The default demo key emits a `DeprecationWarning` at startup.

### Edge Node Trust
- The Android/Termux Edge Node operates with strictly no root privileges. It cannot push execution commands to the Compute Core.
- Vector state updates from the Edge Node are always pull-based, preventing edge compromise from poisoning the central LanceDB knowledge graph.

### Policy Enforcement
- The Policy Engine (`policy.yaml`) acts as a mandatory capability gate between the LLM planner and the execution sandbox. No task executes without passing capability validation.

---

## Security Hygiene for Contributors

- **Never disable sandboxing** in test code or CI configurations.
- **Never commit `policy.yaml`** with overly permissive capability grants.
- **Never use mock data** in eBPF event consumers in production code paths — this masks real telemetry.
