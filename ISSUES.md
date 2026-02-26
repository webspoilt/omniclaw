# OmniClaw Known Issues & Roadmap

## V3.0 Known Issues & Edge Cases

1. **Experimental eBPF Modules**: `ebpf_monitor` and `segfault_tracer` currently default to simulation mode on Windows/macOS. Actual kernel hooking requires Linux (Kernel 5.8+) and root permissions. Fallbacks need better user warnings in the UI.
2. **Recommendation Engine Token Cost**: The `rank_actions` LLM attention mechanism adds an extra completion call per tool request, which might increase latency and cloud API costs. Consider caching recent state-action pairs or using the local embedding model exclusively for ranking.
3. **Temporal Memory Persistence**: `TemporalMemoryV2` keeps vectors in-memory and re-initializes FAISS on boot. We need to serialize the FAISS index to disk (`memory_db/temporal.index`) to persist decay states across reboots.
4. **Biometric Vibe Limitations**: The keystroke dynamics baseline currently resets after every run and uses naive interval averaging. Needs a proper ML backend (e.g., Isolation Forest) over longer epochs to prevent false lockouts. Voice verification is strictly a stub. 
5. **Qiskit Dependencies**: Importing `qiskit` heavily inflates the application footprint. We should consider lazy loading the `quantum_gateway` module only if the user explicitly triggers it.

## Future Roadmap (V3.1+)
- Web-based Control Panel over Tauri for remote cloud deployments.
- Implementing the Orbiting Edge Swarm logic for true decentralized agents.
- Full Windows Registry support for native system control parity with Linux.
