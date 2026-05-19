# OmniClaw Project Summary

## Overview

OmniClaw is an event-driven, distributed orchestration runtime for autonomous AI workflows. It provides deterministic task routing, unified observability, and strict policy-enforced execution sandboxing. The platform spans robust Compute Cores (Linux/eBPF) to constrained Edge Nodes (Android/ARM), enabling seamless, low-latency task distribution.

## Architecture & Repositories

```text
omniclaw/
├── apps/                          # Monorepo Applications (pnpm)
│   ├── worker/                    # Durable Orchestrator (TypeScript/Temporal)
│   └── web/                       # Next.js 15 Landing Page & Infrastructure UI
│
├── core/                          # Orchestration & State Management
│   ├── zmq_orchestrator.py        # ZeroMQ ROUTER-DEALER event loop
│   ├── vector_sync.py             # LanceDB / SQLite-vec synchronization layer
│   └── manager.py                 # Core workflow routing logic
│
├── kernel_bridge/                 # eBPF Shield & Telemetry (Compute Core)
│   ├── ebpf/
│   │   └── forensic_snapshot.c   # BPF probe for anomalous exit detection
│   └── user_daemon.cpp            # C++ userspace consumer for ring buffers
│
├── modules/                       # Sandboxed Execution Domains
│   └── athena/                    # Mathematics & Physics Engine
│       ├── transpiler_worker.py   # LLM-to-SymPy bounded execution
│       └── lean_worker.py         # Headless Lean 4 proof verification
│
└── config/                        # Universal Configurations
    ├── policy.yaml                # eBPF, Athena, and QoS bounds
    └── otel-collector.yml         # OpenTelemetry telemetry export config
```

## Core Infrastructure Capabilities

### 1. Deterministic Orchestration

- **ZeroMQ Mesh:** A decentralized `ROUTER-DEALER` topology ensuring millisecond latency between nodes.
- **Workflow DAG Resolution:** Translates probabilistic LLM intents into strict execution DAGs.
- **Resilient State Management:** Workflows can resume automatically in the event of hardware or node failure.

### 2. Edge-Native Constraints

- **Adaptive Telemetry:** Dynamic QoS applying DSCP packet marking based on thermal profiles.
- **Vector DB Handoffs:** SQLite-vec on the edge seamlessly offloads high-dimensional semantic search to the LanceDB backend via ZeroMQ `CONTEXT_HANDOFF_REQUEST` payloads.
- **Asymmetric Trust:** Edge nodes operate entirely in userspace without root (`strace`/`proot`), shifting heavy sandboxing onto the Compute Core.

### 3. Policy-Enforced Isolation

- **eBPF Shield:** Custom `kprobes` monitor memory allocation (`mprotect`) and system calls for execution anomalies.
- **Forensic Snapshots:** Malicious subtasks are frozen via cgroups and their register state is exported to offline tamper-proof vaults prior to termination.
- **Chroot Sandboxing:** Unshare namespaces constrain process limits (memory, network, disk) dynamically based on explicit capability grants from `policy.yaml`.

### 4. Mathematical Determinism (Athena Engine)

- **Symbolic Transpilation:** Natural language problems are converted to Python `SymPy` operations, executed in tightly isolated unshare sandboxes.
- **Lean 4 Proofs:** Employs headless Lean 4 environments for formal verification of theorem conjectures to ensure mathematical correctness over AI hallucinations.

## API Compatibility Matrix

| Provider       | Status         | Models              | Support Scope                   |
| -------------- | -------------- | ------------------- | ------------------------------- |
| OpenAI         | Production     | GPT-4o, GPT-4       | Native API Support              |
| Anthropic      | Production     | Claude-3.5 Sonnet   | Context Caching Support         |
| Local (Ollama) | Production     | Llama-3, Mistral    | Full Sandbox Offline Integration|

## Platform Support Matrix

| Hardware Profile  | Environment              | Capabilities                                         |
| ----------------- | ------------------------ | ---------------------------------------------------- |
| **Compute Core**  | Linux (Ubuntu 22.04+)    | eBPF, LanceDB, ZeroMQ ROUTER, GPU Simulation         |
| **Edge Node**     | Android (Termux) / ARM   | Sensor ingestion, SQLite-vec caching, ZeroMQ DEALER  |

## Roadmap

- [ ] Complete OpenTelemetry tracing across all ZeroMQ hops.
- [ ] Implement robust `cgroup` v2 resource exhaustion management for the Athena GPU tasks.
- [ ] Kubernetes manifest integration for scalable cluster deployments.
