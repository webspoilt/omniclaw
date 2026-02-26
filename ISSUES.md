# OmniClaw Known Issues & Roadmap

## V3.0 Known Issues & Edge Cases

1. **Experimental eBPF Modules**: `ebpf_monitor` and `segfault_tracer` currently default to simulation mode on Windows/macOS. Actual kernel hooking requires Linux (Kernel 5.8+) and root permissions. Fallbacks need better user warnings in the UI.
2. **Recommendation Engine Token Cost**: The `rank_actions` LLM attention mechanism adds an extra completion call per tool request, which might increase latency and cloud API costs. Consider caching recent state-action pairs or using the local embedding model exclusively for ranking.
3. **Temporal Memory Persistence**: `TemporalMemoryV2` keeps vectors in-memory and re-initializes FAISS on boot. We need to serialize the FAISS index to disk (`memory_db/temporal.index`) to persist decay states across reboots.
4. **Biometric Vibe Limitations**: The keystroke dynamics baseline currently resets after every run and uses naive interval averaging. Needs a proper ML backend (e.g., Isolation Forest) over longer epochs to prevent false lockouts. Voice verification is strictly a stub. 
5. **Qiskit Dependencies**: Importing `qiskit` heavily inflates the application footprint. We should consider lazy loading the `quantum_gateway` module only if the user explicitly triggers it.

## Mission Control (Strategic Analysis Phase) Issues
1. **Stub Implementations**: `backend/ollama_fallback.py` and `backend/p2p_sync.py` are unfinished stubs. They need correct bindings to the local Ollama daemon and a libp2p network to achieve proper Local-First / P2P Hive Mind behaviors.
2. **Hardcoded Cost Calculation**: `backend/cost_tracker.py` calculates costs using a static token multiplier. We should utilize LiteLLM's built-in dynamic cost calculator to respect varying OpenRouter model prices.
3. **Simulated eBPF MCP Tool**: The `ebpf_monitor` MCP Tool returns simulated packet/memory events. It needs to pipe real data from the `kernel_bridge`.
4. **Dashboard Polling vs WebSockets**: The React Mission Control dashboard currently requires a full task finish or a manual refresh to update cost charts. We should switch to FastAPI WebSockets for real-time telemetry streaming of the Architect -> Coder -> Reviewer logic.


## Future Roadmap (V3.1+)
- Web-based Control Panel over Tauri for remote cloud deployments.
- Implementing the Orbiting Edge Swarm logic for true decentralized agents.
- Full Windows Registry support for native system control parity with Linux.
