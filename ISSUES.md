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

## Roadmap & Pending Issues (V4.1+)
1. **Experimental eBPF Modules**: `ebpf_monitor` and `segfault_tracer` currently default to simulation mode on Windows/macOS. Actual kernel hooking requires Linux (Kernel 5.8+) and root permissions.
2. **Biometric Vibe Limitations**: Keystroke dynamics baseline needs a proper ML backend for robust authentication.
3. **IPS Live Blocking**: The `ips_agent.py` autonomous IP blocking requires root privileges to execute `iptables`/`nftables` rules. On non-root or Termux, the agent falls back to dry-run logging only.
4. **IPS LLM Classification**: Threat classification accuracy depends on LLM quality. Without API access or local Ollama, the agent uses a heuristic fallback that may produce occasional false positives on borderline cases.
5. **IPS IPv6 Support**: The current `monitor.bpf.c` only traces `tcp_v4_connect` (IPv4). IPv6 support via `tcp_v6_connect` is planned for v4.2.
