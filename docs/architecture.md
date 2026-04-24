# OmniClaw Architecture

OmniClaw v4.5.0 utilizes a **Hybrid Hive** architecture, combining high-level reasoning models with low-level kernel observers to create an autonomous system that is both intelligent and hardware-aware.

## 🏗️ 1. The Hybrid Hive (HPTSA)
The Hierarchical Planning Team of Specialized Agents (HPTSA) is the brain of OmniClaw.

-   **The Manager**: Typically a model like **Claude 3.5 Sonnet** or **GPT-4o**. It receives high-level goals (e.g., "Secure this server") and breaks them into a DAG of sub-tasks.
-   **The Workers**: Specialized agents (often running **Llama 3** locally or **Gemini 2.0 Flash**) that execute specific sub-tasks like port scanning, code analysis, or file manipulation.
-   **The Critic**: A peer-review agent that validates the output of workers before the next step in the plan is executed.

## 🌉 2. eBPF Kernel Bridge
The "Claw" of OmniClaw. Built in C and compiled on-the-fly, the eBPF bridge provides kernel-level observability.

-   **Syscall Monitoring**: Tracks `execve`, `openat`, and `connect` calls across the system.
-   **Network Filtering**: Implements XDP (Express Data Path) for ultra-fast packet dropping of detected threats.
-   **Telemetry**: Feeds raw kernel events into the Knowledge Graph for the agents to analyze.

## 🛡️ 3. Multi-Tier Sandboxing
Safety is ensured through three layers of isolation:

1.  **ShellSandbox**: A Python-based filter that blocks dangerous commands (e.g., `rm -rf /`, `chmod +x` on unauthorized paths).
2.  **PromptGuard**: An LLM-based filter that detects and blocks "jailbreak" attempts or malicious intent in the agent's own reasoning.
3.  **OS-Level Isolation**: Recommended deployment in Docker or a KVM-based virtual machine.

## 👁️ 4. Vision Module (v4.5)
The computer-use engine.
-   **Optimized Pipeline**: Resizes screenshots to 1024px width and encodes as 85% JPEG to minimize token usage while maintaining 99% recognition accuracy for text and UI elements.
-   **Native Integration**: Uses DXGI (Windows), SCStream (macOS), and Wayland portals (Linux) for zero-latency screen access.
