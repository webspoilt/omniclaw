## Resolved in V3.2 "Sovereign Sentinel" ✅
1. **Syntax Error in contract_enforcer.py (#13)**: Fixed mangled method signature that caused `SyntaxError: unmatched ')'` on startup. 
2. **Repository Bloat & Sync Latency**: Optimized `.gitignore` to exclude `node_modules/` and build artifacts, resolving the "too many changes" warning and speeding up Git synchronization.
3. **Atomic State Synchronization**: Implemented unified push logic to ensure README, ISSUES, and UI updates stay in sync with core feature pushes.

## Resolved in V3.3 "Red Team Automation" ✅
1. **Headless Environment Fallbacks**: Detection for environments without a display/GUI to prevent Tauri/NiceGUI startup errors.
2. **Temporal Memory Persistence**: Fixed FAISS index serialization handle when empty and saved to disk (`memory_db/temporal.index`).

## Resolved in V4.0 "Mission Control" ✅
1. **Broken Dependencies**: Fixed `omniclaw.py` startup crashing by adding missing requirements (litellm, faiss-cpu, GitPython, sentence-transformers, watchdog) to `setup.sh` and `install.sh`. 
2. **Module Import Errors**: Resolved `ImportError` mapped to importing lowercase `list` from `typing` in `contract_enforcer.py`.
3. **F-String Syntax Errors**: Fixed malformed string interpolation blocks carrying invalid `@` placements in `autonomous_pm.py`.
4. **Unterminated Literals**: Fixed unterminated print strings in `self_evolving_core.py`.

## Resolved in V4.2 "Sovereign Mesh" ✅
1. **#14 ShellSandbox Windows Paths**: `_safe_env()` now returns Windows `System32` PATH and `COMSPEC` instead of Unix-only `/usr/local/bin` and `/bin/sh`.
2. **#15 SkillLoader os.getuid()**: Confirmed already gated with `if os.name != 'nt'`. Added explicit clarifying comment.
3. **#16 CronScheduler croniter docs**: `INSTALLATION.md` now has Optional Feature Dependencies table documenting `croniter`, `mss`, `lancedb`, `networkx`.
4. **#17 Heartbeat LLM fallback**: `HeartbeatService` docstring now fully documents keyword-detection fallback. Startup log indicates active mode.
5. **#23 Evolution Confidence Threshold**: Added `confidence_threshold: 0.7` config + `_estimate_confidence()`. Low-confidence fixes always require manual approval.

## New in V4.2 "Sovereign Mesh" ✨
1. **#18 MCP Server**: Added `get_scheduler_status`, `get_evolution_status`, `get_mesh_peers` tools. Fixed plant health resource to read from disk.
2. **#19 Health Check Server**: `core/health_server.py` — `GET /health` JSON endpoint with uptime, system metrics, and module status.
3. **#20 Neural Mesh AES Key**: Warning emitted if default demo key detected. DH key exchange planned for v4.3.
4. **#21 Vision Screen Capture**: `modules/vision/screen_capture.py` — mss/PIL/CLI backends with headless detection.
5. **#22 Memory Module**: `vector_store.py` + `graph_store.py` already had proper fallbacks. Documented in INSTALLATION.md.
6. **#24 Shadow Shell Honeypot**: `modules/security/honeypot.py` — asyncio TCP decoy shell, logs all attacker activity to `logs/honeypot.log`.
7. **#25 Exam Scholar Notifications**: `schedule_reminders(cron_scheduler)` + `generate_practice_question()` + `get_next_deadline()` added.
8. **#26 Startup PM2 Monitor**: `PM2Monitor` class + `LeadStore` JSON persistence added to `saas_manager.py`.
9. **#27 Orchestrator Daemon**: `core/main.py` now has `--no-mcp`, `--no-health`, `--no-mesh` CLI flags. Health server and honeypot wired in.

## Roadmap & Pending Issues (V4.3+)
1. **Experimental eBPF Modules**: `ebpf_monitor` and `segfault_tracer` currently default to simulation mode on Windows/macOS. Actual kernel hooking requires Linux (Kernel 5.8+) and root permissions.
2. **Biometric Vibe Limitations**: Keystroke dynamics baseline needs a proper ML backend for robust authentication.
3. **IPS Live Blocking**: The `ips_agent.py` autonomous IP blocking requires root privileges to execute `iptables`/`nftables` rules. On non-root or Termux, the agent falls back to dry-run logging only.
4. **IPS LLM Classification**: Threat classification accuracy depends on LLM quality. Without API access or local Ollama, the agent uses a heuristic fallback that may produce occasional false positives on borderline cases.
5. **IPS IPv6 Support**: The current `monitor.bpf.c` only traces `tcp_v4_connect` (IPv4). IPv6 support via `tcp_v6_connect` is planned for v4.3.
6. **Evolution Agent Safety (#23 continued)**: `_estimate_confidence()` is a heuristic. A proper ML-based confidence scorer (e.g., perplexity from the LLM logprobs) is planned for v4.3.
7. **Hive Sync Key Exchange (#20 continued)**: `hive_sync.py` P2P module currently uses a static pre-shared AES-256 key. ECDH Diffie-Hellman key exchange planned for v4.3.
8. **Scout Agent Tool Coverage**: Only subfinder, nmap, and nuclei are integrated. Additional tools (ffuf, whatweb, feroxbuster) planned for v4.3.
9. **Real eBPF Honeypot (#24 continued)**: The honeypot uses asyncio simulation. Real eBPF kernel probes via `bcc`/`bpftool` require Linux 5.8+ with root.
