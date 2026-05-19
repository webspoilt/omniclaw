# Changelog

All notable changes to OmniClaw are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [4.5.0] — 2026-05-19

### Architecture Overhaul
- **ZeroMQ Orchestrator** (`core/zmq_orchestrator.py`): Replaced the `asyncio.Queue`-based manager with a full `ROUTER-DEALER` topology. All inter-node communication now uses typed MessagePack schemas, eliminating pickle-based serialization risks.
- **Vector Sync Layer** (`core/vector_sync.py`): Implemented a dual-tier vector storage strategy. The Edge Node uses `sqlite-vec` as a high-speed local cache. The Compute Core uses `LanceDB` as the source-of-truth knowledge store. Synchronization is pull-based via `CONTEXT_HANDOFF_REQUEST` messages.
- **eBPF Forensic Bridge** (`kernel_bridge/`): Implemented `forensic_snapshot.c` — a `kprobe` on `do_exit` that captures CPU registers and stack state on anomalous process termination. The C++ userspace daemon freezes the offending `cgroup v2` slice and archives state to an offline forensic vault before issuing `SIGKILL`.

### Athena Engine
- **Transpiler Worker** (`modules/athena/transpiler_worker.py`): LLM-to-SymPy pipeline with self-correction. Generated scripts execute in strict `unshare` sandboxes with isolated network, PID, and mount namespaces.
- **Lean 4 Worker** (`modules/athena/lean_worker.py`): Headless Lean 4 interface for formal theorem verification, preventing AI hallucinations from propagating into the knowledge graph.

### Policy & Configuration
- **Unified Policy** (`config/policy.yaml`): Centralized capability control for eBPF heuristic thresholds, Athena GPU temperature limits, and ZeroMQ QoS DSCP markings.

### Security Hardening
- Banned `shell=True` from all execution paths. All subprocess calls now use explicit argument lists.
- Edge Node restricted to read-only vector queries and sensor ingestion. Cannot push execution commands to the Compute Core.

---

## [4.4.0] — 2026-04-24

### Added
- `pnpm` monorepo structure consolidating the TypeScript Durable Worker and Next.js web frontend.
- ZeroMQ-based P2P mesh with AES-256-GCM encrypted payloads for secure task offloading between nodes.
- Rust-based `libbpf-rs` kernel bridge module (packages/kernel-bridge).
- Tauri + React mission control dashboard for local desktop monitoring.

### Fixed
- `ShellSandbox` Windows cross-platform paths: `_safe_env()` now returns correct `System32` PATH on Windows.
- `SkillLoader` `os.getuid()`: Added explicit `os.name != 'nt'` guard preventing Windows crashes.

---

## [4.2.0] — 2026-03-18

### Added
- Lightweight async health check server (`core/health_server.py`) exposing `/health` with uptime and module status.
- Cross-platform screen capture module with `mss`, PIL, and headless-safe fallbacks.
- `PM2Monitor` structured class with `get_status()`, `get_process()`, and `restart()` methods.
- Evolution confidence threshold: low-confidence auto-fixes now require manual approval.

### Fixed
- Root logger reconfiguration conflict in `orchestrator.py`.
- Fire-and-forget tasks in `messaging_gateway.py` now tracked and cancellable on shutdown.

---

## [3.2.0] — 2026-02-26

### Added
- Real-time syscall monitoring via eBPF for kernel-level execution observability.
- Decision audit logging for LLM reasoning chain transparency.

### Fixed
- Daemon startup race condition in `setup.sh`.
- Duplicate module imports in main entry point.

---

## [3.0.0] — 2025-12-15

### Added
- Multi-agent task delegation with Manager-Worker orchestration.
- DIEN-based tool recommendation engine for predictive task routing.

---

## [2.0.0] — 2024-05-10

### Added
- Initial Telegram and Discord gateway integrations.
- Vector memory backend using ChromaDB.

---

## [1.0.0] — 2023-11-01

### Added
- Initial release: Python execution loop, terminal UI, single-LLM task execution.
