# 🌌 Shannon Pro: The Autonomous AppSec Monorepo

<div align="center">
  <img src="https://img.shields.io/badge/Security-Red_Team-red?style=for-the-badge&logo=kali-linux" />
  <img src="https://img.shields.io/badge/AI-Autonomous_Agents-blueviolet?style=for-the-badge&logo=openai" />
  <img src="https://img.shields.io/badge/Architecture-Monorepo-blue?style=for-the-badge&logo=turborepo" />
  <img src="https://img.shields.io/badge/Status-Beta-orange?style=for-the-badge" />
</div>

<p align="center">
  <strong>The world's most advanced autonomous security research platform.</strong><br />
  A unified "Hybrid Hive" architecture combining high-speed static analysis with intelligent, browser-based dynamic exploitation.
</p>

---

> [!CAUTION]
> **LEGAL DISCLAIMER:** This project is for **authorized security testing and academic research ONLY**. Unauthorized use of Shannon Pro against systems without explicit consent is illegal and strictly prohibited. The authors assume no liability for misuse.

---

## 🏛️ Architecture Overview

Shannon Pro is built as a modular **pnpm Monorepo**, designed for high performance and extensibility. It bridges the gap between TypeScript-based orchestration (Temporal/Node) and Python-driven security engines.

```mermaid
graph TD
    subgraph Monorepo ["📦 Shannon Pro Monorepo"]
        subgraph Apps ["🚀 Apps"]
            W[worker] --> Orchestration
            C[cli] --> Interaction
        end
        
        subgraph Engines ["🧠 Pro Engines (Python)"]
            RE[ReconEngine] --> Discovery
            SA[StaticSlicer] --> Analysis
            DA[DynamicAgent] --> Exploitation
            CE[CorrelationEngine] --> Intelligence
        end
        
        subgraph Packages ["🛠️ Shared Packages"]
            EC[@shannon/engine-client]
            ST[@shannon/shared-types]
        end
    end

    W <--> EC
    EC <--> Engines
```

---

## 🚀 Key Features

### 1. Hybrid Hive Orchestration (OmniClaw Core)
A Manager-Worker loop inspired by OmniClaw that handles goal decomposition, parallel execution, and peer-review validation.
- **Reasoning Lock**: Forces deep chain-of-thought analysis before exploitation.
- **Goal Decomposition**: Automatically breaks high-level pentest goals into atomic security tasks.

### 2. Autonomous Exploitation (Dynamic Agent)
A browser-based agent that implements the **"POC-or-it-didn't-happen"** principle.
- **Autonomous Fix**: Real-time error parsing and LLM-driven patching for failed exploit scripts.
- **Kernel Bridge**: eBPF-powered system call monitoring to detect "out-of-band" indicators (shell spawns, file access).
- **Stealth Mode**: Advanced EDR/WAF evasion techniques for behavioral detection bypass.

### 3. Outside-In Discovery (Recon Engine)
Broad-spectrum reconnaissance to supplement internal analysis.
- **Subdomain Enumeration**: Certificate Transparency (CT) logs and DNS brute-forcing.
- **Service Mapping**: Automated port scanning and fingerprinting.
- **API Discovery**: Intelligent crawling and endpoint mapping.

### 4. Correlation & Reachability
The "Brain" of the system that connects findings across the pipeline.
- **Taint-Aware Prioritization**: Ranks vulnerabilities based on real-world reachability.
- **Evidence Vault**: Immutable collection of screenshots, HAR files, and kernel traces.

---

## 📂 Monorepo Structure

```bash
shannon-pro/
├── apps/
│   ├── worker/           # Temporal Worker (TS) — The Orchestrator
│   └── cli/              # Management CLI for triggering audits
├── engines/
│   ├── correlation/      # Python logic for vulnerability linking
│   ├── dynamic-agent/    # Playwright-based autonomous exploit agent
│   ├── recon-engine/     # Outside-in discovery and mapping
│   └── static-slicer/    # High-speed static analysis pipeline
├── packages/
│   ├── engine-client/    # Type-safe bridge between TS and Python
│   └── shared-types/     # Common security models and schemas
├── docker-compose.yml    # Infrastructure (Temporal, Postgres, Redis)
└── pnpm-workspace.yaml   # Monorepo configuration
```

---

## 🛠️ Getting Started

### Prerequisites
- **Node.js 20+** & **pnpm 8+**
- **Python 3.10+** (with `pipenv` or `venv`)
- **Docker** (for Temporal infrastructure)

### Installation
```bash
# Clone the repository
git clone https://github.com/your-org/shannon-pro.git
cd shannon-pro

# Install dependencies
pnpm install

# Start infrastructure
docker-compose up -d

# Build packages
pnpm build
```

### Running in Pro Mode
To enable the full autonomous engine suite, start the worker with the `--pro` flag:
```bash
pnpm --filter worker run dev -- --pro --engines-dir ./engines --enable-reasoning-lock
```

---

## 🛡️ Safety & Security
Shannon Pro operates in a **Reasoning-First** mode. Before any action is taken, the agent performs a deep analysis inside `<reasoning>` tags to ensure the plan adheres to the focus rules and ethical boundaries defined in your `config.yaml`.

---

<div align="center">
  <p>Built with ❤️ by the Shannon Security Team</p>
  <img src="https://img.shields.io/badge/Made%20with-Antigravity-blue?style=flat-square" />
</div>
