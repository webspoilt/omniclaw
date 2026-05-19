# OmniClaw — Architecture & Threat Model Audit

## EXECUTIVE SUMMARY

**Security & Production Readiness Posture:** ENTERPRISE STABLE

This document outlines the architectural boundaries, threat models, and mitigation strategies implemented in the OmniClaw distributed runtime. The system has been explicitly designed to treat AI planners as "hostile or hallucinating by default," relying on strict kernel-level and namespace-level sandboxing to guarantee deterministic and safe execution.

---

## 1. ARCHITECTURAL BOUNDARIES

OmniClaw implements a strict separation of concerns across multiple trust domains.

### 1.1 Runtime Architecture

| Component | Implementation | Trust Level |
| ----------- | -------------- | ----------- |
| **Manager Node** | ZeroMQ `ROUTER` Socket | High (Orchestration plane) |
| **Policy Engine** | `policy.yaml` capability validator | High (Validation plane) |
| **eBPF Shield** | C++ Userspace Daemon + kprobes | Ring-0 (Kernel plane) |
| **Edge Gateway** | Android Termux / `proot` | Low (Unprivileged Sensor) |
| **Worker Sandbox** | `unshare` namespaces / cgroups | Untrusted (Execution plane) |

### 1.2 IPC & State Management

- **Inter-Process Communication:** All cross-boundary communication occurs via ZeroMQ sockets using explicitly typed MessagePack schemas. This entirely removes the risk of insecure deserialization (e.g., Python `pickle`).
- **Vector State:** Knowledge graphs are dual-tiered. The Edge Node relies on `sqlite-vec` for transient offline data, while the Compute Core maintains the source of truth in `LanceDB`. Synchronization is pull-based to prevent edge nodes from poisoning the global core state.

---

## 2. THREAT MODEL & MITIGATIONS

### Threat 1: LLM Hallucination / Arbitrary Code Execution (RCE)

**Vector:** A planner attempts to output a malicious payload to the host shell (e.g., `subprocess.run(..., shell=True)`).

**Mitigation:**

- `shell=True` is entirely disabled in the execution plane.
- All code generation (e.g., SymPy scripts) is written to a temporary overlay file system and executed within an `unshare` chroot.
- The `unshare` environment drops all networking capabilities unless explicitly whitelisted in `policy.yaml`.

### Threat 2: Out-of-Bounds Syscalls

**Vector:** A malicious worker attempts to overwrite memory or exploit a kernel vulnerability.

**Mitigation:**

- The `forensic_snapshot.c` eBPF module attaches to critical syscalls (e.g., `execve`, `mprotect`).
- Anomalous behavior results in the immediate freezing of the worker's `cgroup v2` slice.
- The C++ daemon dumps the process registers to an offline forensic vault and issues a `SIGKILL`.

### Threat 3: Denial of Service (OOM / Thermal Exhaustion)

**Vector:** An infinite loop in an execution task consumes all RAM, or a heavy GPU workload melts the Edge Node.

**Mitigation:**

- **Edge:** The Edge Node utilizes lightweight token budgeting. If inference cannot run locally, it is shunted via ZeroMQ to the Compute Core.
- **Core:** The orchestrator utilizes DSCP QoS markings to prioritize telemetry and orchestration packets over heavy payload transfers. Tasks are violently killed if they exceed `cgroup` memory limits.

### Threat 4: Edge Node Compromise

**Vector:** A physical attacker compromises the Android Edge Node.

**Mitigation:**

- The Edge Node runs strictly in userspace without root privileges.
- ZeroMQ credentials are rotated, and the Core Manager restricts Edge capabilities purely to sensor ingestion and context queries. The Edge Node cannot push raw execution commands to the Core.

---

## 3. OPEN TELEMETRY & OBSERVABILITY

OmniClaw ensures that every routing decision and policy enforcement action is traceable.

- **Distributed Tracing:** Spans are injected at the ZeroMQ boundary, allowing administrators to track a request from Edge Sensor -> Core Manager -> Sandboxed Worker -> Database.
- **Audit Logging:** Every capability denial by the Policy Engine is logged immutably, ensuring that security analysts can trace exactly why a specific AI workflow was halted.

---

## 4. CONCLUSION

By moving away from "trusting the LLM" to a model of **Policy-Constrained Execution**, OmniClaw provides a deterministic and secure platform for orchestrating autonomous systems. The integration of eBPF, ZeroMQ, and cgroup-based sandboxing elevates the runtime to enterprise-grade production readiness.
