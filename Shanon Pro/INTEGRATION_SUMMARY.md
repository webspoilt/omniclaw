# Shannon Pro — Integration Summary
## End-to-End Pipeline: Static Analysis → Correlation → Dynamic Validation

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         SHANNON PRO PLATFORM                                  │
├─────────────────────┬─────────────────────────────┬──────────────────────────┤
│   STAGE 1           │   STAGE 3                   │   STAGE 2                │
│   Static Analysis   │   Correlation Engine        │   Dynamic Pentesting     │
├─────────────────────┼─────────────────────────────┼──────────────────────────┤
│                     │                             │                          │
│  Git Clone Agent    │  Postgres Ingestion         │  Agent Controller        │
│       ↓             │       ↓                     │       ↓                  │
│  Joern CPG Gen      │  Reachability Analyzer      │  Injection Agent Pool    │
│       ↓             │       ↓                     │       ↓                  │
│  CPG Slicer (SQLi)  │  Priority Scorer            │  Playwright Mapper       │
│       ↓             │       ↓                     │       ↓                  │
│  LLM Inference      │  Exploit Queue (Redis)      │  Browser Farm            │
│       ↓             │       ↓                     │       ↓                  │
│  Static Findings    │  Dynamic Agent Dispatch     │  POC Validator           │
│  (PostgreSQL)       │                             │       ↓                  │
│                     │                             │  Evidence Store          │
│                     │                             │                          │
├─────────────────────┴─────────────────────────────┴──────────────────────────┤
│                          CONTROL PLANE                                        │
│  API Gateway (Kong) → Orchestrator (FastAPI) → Scheduler (Temporal)          │
│  Audit Logger (Sigstore/S3) → Webhooks → Dashboard (React/SSE)               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. Static Analysis Pipeline (Stage 1)

```
Repository URL + Token
    │
    ▼
┌─────────────────────┐
│ RepositoryCloner    │  → Ephemeral clone + gitleaks scan
│ (Go/libgit2)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ CPGGenerator        │  → Joern joern-parse multi-language
│ (Scala/Joern)       │    Output: cpg.bin (encrypted)
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ SQLiSlicer          │  → Cypher queries for taint sources → sinks
│ (Rust/petgraph)     │    Output: DataflowPath with sanitizers
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ SanitizationAnalyzer│  → Local LLM (vLLM/DeepSeek-Coder)
│ (Python/OpenAI)     │    System prompt: 5-dimension sanitization check
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ PostgreSQL          │  → static_findings + dataflow_slices tables
│ (TDE + TLS 1.3)     │
└─────────────────────┘
```

### 2. Correlation Engine (Stage 3)

```
static_findings table
    │
    ▼
┌─────────────────────┐
│ PostgresClient      │  → SELECT with confidence filter
│ (asyncpg)           │    Deduplication by evidence hash
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ ReachabilityAnalyzer│  → CPG call graph traversal
│ (Rust/Datalog)      │    HTTP entrypoint → sink path finding
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ PriorityScorer      │  → 4-dimension scoring (0-100)
│ (Python)            │    Severity + Reachability + Exploitability + Confidence
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ ExploitQueueManager │  → Redis Sorted Set (priority-ordered)
│ (Redis Streams)     │    Atomic ZPOPMIN for agent claiming
└─────────────────────┘
```

### 3. Dynamic Pentesting (Stage 2)

```
Exploit Queue (Redis)
    │
    ▼
┌─────────────────────┐
│ AgentController     │  → Pool of 5 agents, async execution
│ (Python/asyncio)    │    Task timeout: 300s, Max retries: 3
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ InjectionAgent      │  → Isolated browser context per task
│ (Playwright)        │    Stealth mode + HAR recording
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ StrategyRegistry    │  → SQLi, XSS, Cmdi, Path Traversal, SSRF
│ (Python)            │    Ordered payloads by invasiveness
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ POCValidator        │  → "POC-or-it-didn't-happen"
│ (Python)            │    Required indicators + forbidden indicators
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Evidence Store      │  → Screenshot + HAR + Video (SSE-S3)
│ (MinIO/Sigstore)    │    SHA-256 hashes for tamper detection
└─────────────────────┘
```

---

## Key Integration Points

### Stage 1 → Stage 3

```python
# PipelineResult from Static Analysis produces findings that are
# ingested by CorrelationEngine via PostgresClient

from stage1_static_analysis.engine.pipeline import StaticAnalysisPipeline
from stage3_correlation.correlation_engine import CorrelationEngine

# Stage 1 produces
pipeline_result = await static_pipeline.analyze(repo_url, token_id)

# Findings automatically persisted to PostgreSQL
# Stage 3 picks them up
report = await correlation_engine.correlate_scan(pipeline_result.scan_id)
```

### Stage 3 → Stage 2

```python
# CorrelationEngine generates QueueItems that are enqueued in Redis
# AgentController dequeues and executes them

from stage3_correlation.exploit_queue import ExploitQueueManager
from stage2_dynamic_agent.agent_controller import AgentController

# Stage 3 enqueues
await queue_manager.enqueue(queue_item)

# Stage 2 dequeues and executes
task_payload = await queue_manager.dequeue(agent_id="agent-0")
result = await agent_controller.submit_task(ExploitTask(**task_payload))
```

### Stage 2 → Stage 3 (Feedback Loop)

```python
# Dynamic results feed back into correlation records
# Confirmed findings are marked as 'dynamic_validated'
# False positives update correlation_type to 'false_positive'

if result.is_validated:
    await postgres_client.upsert_correlation(
        finding_id=result.finding_id,
        result_id=result.task_id,
        correlation_type="dynamic_validated",
        correlation_score=result.confidence_score,
        is_reachable=True,
        priority="critical" if result.confidence_score > 0.9 else "high",
    )
```

---

## Security Model Implementation

| Layer | Implementation | Status |
|-------|---------------|--------|
| Air-gapped static analysis | Kubernetes NetworkPolicy (no egress) | ✅ |
| Local LLM inference | vLLM/ollama on localhost only | ✅ |
| Encrypted CPG storage | AES-256-GCM per-scan keys | ✅ |
| mTLS inter-service | Istio/Linkerd + SPIFFE | ✅ |
| Credential vault | HashiCorp Vault + SOPS | ✅ |
| Evidence integrity | Sigstore cosign + SHA-256 | ✅ |
| Immutable audit log | WORM S3 + Merkle tree | ✅ |
| Container sandbox | gVisor + seccomp-bpf | ✅ |

---

## Technology Stack Summary

| Component | Language | Framework/Tool |
|-----------|----------|----------------|
| CPG Slicer | Rust | petgraph, Souffle Datalog |
| Correlation Engine | Rust | serde, tokio |
| Static Analysis Pipeline | Python 3.12 | FastAPI, asyncpg |
| Dynamic Agent | Python 3.12 | Playwright, asyncio |
| API Gateway | Go | Kong, oauth2-proxy |
| Dashboard | TypeScript | React, SSE |
| CPG Generator | Scala | Joern |
| Orchestration | Python | Temporal.io |
| Database | SQL | PostgreSQL 16 + pg_graph |
| Queue/Cache | - | Redis 7 Cluster |
| Object Storage | - | MinIO (SSE-S3) |
| Event Bus | - | NATS JetStream |
| Infrastructure | - | Kubernetes 1.29+, gVisor, Istio |

---

## Production Readiness Checklist

- [x] Architecture document with Mermaid diagrams
- [x] Module definitions and API contracts
- [x] gRPC protobuf specifications
- [x] PostgreSQL schema with indexes
- [x] Data privacy and security model
- [x] Network policies (Kubernetes)
- [x] Encryption strategy (in transit + at rest)
- [x] Self-hosted runner deployment model
- [x] Stage 1: Static Analysis Engine (Joern → CPG → Slicer → LLM)
- [x] Stage 2: Dynamic Pentesting Agent (Playwright → POC Validator)
- [x] Stage 3: Correlation Engine (Reachability → Priority → Queue)
- [x] Exploit Queue (Redis-backed priority queue)
- [x] Evidence collection (screenshots, HAR, video)
- [x] Audit logging and tamper detection

---

**END OF DOCUMENT**
