# OmniClaw Enterprise Use Cases

OmniClaw provides deterministic, policy-constrained orchestration for environments that require both autonomy and high assurance. Below are real-world application topologies for the OmniClaw runtime.

## 1. Edge-Native Sensor Ingestion & Triage

**Topology:** Termux (Android Edge Node) -> ZeroMQ -> Compute Core

**Scenario:** Monitoring distributed hardware environments where connectivity is intermittent and power constraints are strict.

**OmniClaw Implementation:**

- The Edge Node acts as an unprivileged sensor gateway.
- High-frequency telemetry (e.g., thermal logs, localized acoustic data) is ingested by the Edge Node and cached locally using SQLite-vec.
- When critical anomalies are detected locally via small deterministic heuristics, a `CONTEXT_HANDOFF_REQUEST` is dispatched over ZeroMQ to the Compute Core for heavyweight inference and analysis.

## 2. Kernel-Level Forensic Enforcement

**Topology:** eBPF Shield (Compute Core) -> ZeroMQ Orchestrator

**Scenario:** Maintaining execution integrity of large, untrusted AI planning models handling sensitive operations.

**OmniClaw Implementation:**

- A kprobe attached to `execve` and `mprotect` monitors the runtime behavior of the AI sandboxes.
- If a sandbox attempts out-of-bounds execution (e.g., initiating a reverse shell), the eBPF module intercepts the exit.
- The C++ userspace daemon freezes the cgroup, captures a forensic capsule containing registers and memory, and safely terminates the process, immediately alerting the Orchestrator.

## 3. Distributed Theorem Formalization

**Topology:** Manager Node -> GPU Workers + Lean 4 Workers

**Scenario:** Accelerating materials research by combining probabilistic LLM hypotheses with strict formal verification.

**OmniClaw Implementation:**

- The Orchestrator accepts a mathematical problem statement and dispatches it to the Transpiler Worker.
- The worker executes an LLM-generated SymPy script inside a strict `unshare` namespace.
- Results are then pipelined into a headless Lean 4 Worker. This enforces mathematical determinism over the LLM output, proving the theorem before committing the result to the LanceDB knowledge graph.

## 4. Policy-Constrained Workflow Automation

**Topology:** Orchestrator -> Code Janitor (Sandboxed)

**Scenario:** Autonomous patching of legacy codebases without compromising production stability.

**OmniClaw Implementation:**

- OmniClaw builds an execution DAG for updating a codebase.
- The Manager routes file system read/write subtasks to a specifically restricted overlayfs mount.
- Explicit capability grants from `policy.yaml` ensure the execution cannot access the network or modify unauthorized files. The entire operation is logged via OpenTelemetry spans.
