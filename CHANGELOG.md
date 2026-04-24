# Changelog

All notable changes to the OmniClaw project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.4.0] - "Sovereign Sentinel 2026" - 2026-04-24
 
+### Added
+- **#30 Sovereign Sentinel Fusion**: Unified pnpm monorepo structure for high-performance security operations.
+- **#31 CVE-to-PoC Factory**: Autonomous reconnaissance and reachability-aware static analysis engine.
+- **#32 eBPF Sentinel (Rust)**: `libbpf-rs` kernel bridge for Ring-0 stealth and EDR detection.
+- **#33 Durable Worker (TS)**: TypeScript-based durable orchestrator inspired by Temporal.io.
+- **#34 P2P Knowledge Mesh**: ZeroMQ + AES-256-GCM mesh for secure task offloading and vector sync.
+- **#35 Enterprise Dashboard**: Tauri + React mission control for real-time telemetry.
+
 ## [4.2.0] - "Sovereign Mesh" - 2026-03-18

### Fixed
- **#14 ShellSandbox Windows Paths**: `_safe_env()` now returns Windows-appropriate `System32` PATH and `COMSPEC` instead of Unix-only `/usr/local/bin` and `/bin/sh`. Cross-platform safe.
- **#15 SkillLoader os.getuid()**: Added explicit clarifying comment confirming the `os.name != 'nt'` guard prevents any `os.getuid()` call on Windows.

### Added
- **#19 Health Check Server** (`core/health_server.py`): Lightweight async HTTP server exposing `GET /health` with uptime, system metrics, and module status. Uses `aiohttp` if available, pure asyncio socket fallback.
- **#21 Screen Capture** (`modules/vision/screen_capture.py`): Cross-platform screen capture with `mss` (fastest), `PIL.ImageGrab`, and CLI tool fallbacks. API mirrors `TermuxCamera`. Headless detection prevents hang in CI.
- **#24 Shadow Shell Honeypot** (`modules/security/honeypot.py`): Asyncio TCP decoy shell on port 2222. Logs all attacker activity to `logs/honeypot.log`. Realistic canned responses for `ls`, `whoami`, `cat /etc/passwd`, etc.
- **#18 MCP Server Expansion**: Added `get_scheduler_status`, `get_evolution_status`, and `get_mesh_peers` MCP tools. Fixed `plant://latest_health` to read from disk. Fixed `pm2 not found` error handling.
- **#26 PM2Monitor + LeadStore**: Structured `PM2Monitor` class with `get_status()`, `get_process()`, `restart()`. `LeadStore` for JSON-persisted lead tracking.
- **#25 Exam Scheduler Integration**: `ExamScholar.schedule_reminders(cron_scheduler)` registers daily 07:00 briefings and Monday countdown notifications with `CronScheduler`. Added `generate_practice_question(topic)` and `get_next_deadline()` for MCP integration.
- **#27 Orchestrator Daemon Wiring**: `core/main.py` now accepts `--no-mcp`, `--no-health`, `--no-mesh` CLI flags. Health server and honeypot started automatically. Kill switch logs timestamp on trigger.

### Changed
- **#16 CronScheduler Docs**: `INSTALLATION.md` now has Optional Feature Dependencies table; `croniter`, `mss`, `lancedb`, `networkx` documented with install commands.
- **#17 Heartbeat LLM Fallback**: `HeartbeatService.__init__` docstring now fully documents keyword-detection fallback mode. Startup log indicates whether LLM or keyword mode is active.
- **#20 Neural Mesh AES Key Warning**: `NeuralMeshNode` now emits `DeprecationWarning` and a log warning if the default demo AES key is detected. DH key exchange roadmap added to docstring.
- **#22 Memory Module Docs**: `vector_store.py` and `graph_store.py` already had proper `try/except` fallbacks — confirmed and noted in INSTALLATION.md.
- **#23 Evolution Confidence Threshold**: `evolution_agent.py` now has `confidence_threshold: 0.7` config key. `_estimate_confidence()` scores fixes by line similarity; low-confidence fixes force manual approval with score display.

## [3.2.0] - "Sovereign Sentinel" - 2026-02-26

### Added
- **Sovereign Sentinel Security Hardening**: Real-time syscall monitoring and kernel perimeter protection.
- **Advanced eBPF Integration**: Deep Linux kernel hooks for system observability and hardware monitoring.
- **Git-Aware Synchronization**: Intelligent repository management with optimized `.gitignore` for faster synchronization.
- **Atomic Push Capability**: One-click sync of all agent intelligence to GitHub.
- **Decision Archaeology**: Comprehensive logging of LLM reasoning chains for architectural transparency.
- **Enterprise-Grade Launchers**: New terminal and web-based dashboards for managing advanced features.

### Changed
- **Hybrid Hive v3 Architecture**: Enhanced peer-review protocols and multi-agent cognitive loops.
- **Temporal Memory Optimization**: Switched to entropy-based FAISS indices for efficient 24/7 context management.
- **Refined Messaging Gateway**: Improved stability and unified command handling across all channels (Telegram, Discord, etc.).
- **Foolproof Deployment**: Rewritten `DEPLOYMENT_GUIDE.md` and streamlined `install.sh`.

### Fixed
- **Background Execution Bug**: Resolved issue in `setup.sh` where daemon mode failed to launch correctly.
- **Logging Conflicts**: Fixed root logger reconfiguration in `orchestrator.py`.
- **Import Redundancy**: Cleaned up duplicate imports in `omniclaw.py`.
- **Syntax Stability**: Comprehensive character-by-character audit of core logic.

## [3.0.0] - 2025-12-15

### Added
- **Hybrid Hive Orchestrator**: Multi-agent task delegation and team-of-rivals voting logic.
- **Quantum Gateway**: IBM Qasm 3 integration for routed quantum-as-a-service.
- **DIEN Recommendation Engine**: Deep Interest Evolution Network for predictive tool selection.
- **Tauri Native GUI**: High-performance Rust-based mission control.

## [2.1.0] - 2024-08-20

### Added
- **Advanced Features Suite**: Consciousness Collision, CodeDNA, and Time Machine Debugger.
- **Natural Language Infrastructure**: Automated Terraform and k8s generation.

## [2.0.0] - 2024-05-10

### Added
- **Multi-Channel Gateway**: Telegram and Discord bot integrations.
- **Vector Memory**: Initial RAG implementation using chromadb.

## [1.0.0] - 2023-11-01

### Added
- Initial release of OmniClaw.
- Basic autonomous Python execution loop.
- Simple terminal UI.
