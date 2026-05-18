# OmniClaw: Distributed Autonomous Cognition & Orchestration

> A distributed autonomous cognition and orchestration platform for edge, offensive simulation, cyber-defense automation, and resilient infrastructure coordination.

![OmniClaw Architecture](https://img.shields.io/badge/Architecture-Distributed%20Microservices-blue)
![State](https://img.shields.io/badge/State-Self--Healing-brightgreen)
![Resilience](https://img.shields.io/badge/Resilience-Fault--Tolerant-purple)

## Core Identity

OmniClaw has evolved from a monolithic LLM-agent experiment into a production-grade, distributed cyber-cognitive engine. Its architecture is explicitly designed for high-stakes, adversarial environments requiring deep resilience and physical-layer intelligence.

*   **Self-Healing & Resilient**: Temporal-backed durable execution ensures that no thought or workflow is lost to node failure.
*   **Adaptive & Distributed**: Agent cognition and physical tool execution are fully decoupled, allowing execution nodes to run in edge, cloud, or sandboxed environments.
*   **Kernel-Aware**: Deep system observability via eBPF bridges, ensuring prompt security and system telemetry at the OS-level.
*   **Event-Driven**: NATS-powered low-latency messaging backbone for instantaneous swarm coordination.
*   **Policy-Constrained**: Strict capability enforcement engine validating every LLM intention before execution.
*   **Observability-First**: Complete OpenTelemetry lineage tracking traces, logs, and token metrics from thought to action.

## Advanced Intelligence Modules

OmniClaw integrates bleeding-edge offensive intelligence capabilities:

1.  **RF Fingerprinting (SIGINT)**: Identifies and tracks unique hardware devices via SDR-captured RF physical layer anomalies.
2.  **Acoustic Side-Channel Keystroke Recovery**: Neural networks reconstructing keystrokes via microscopic accelerometer vibrations.
3.  **Generative Social Engineering (GSE)**: Autonomous infiltration personas leveraging LLM personality mirroring and generative rendering.
4.  **eBPF LLM Guard**: A kernel-level "firewall for words" that drops prompt injection payloads before they reach the cognition engine.

## Infrastructure Stack

*   **Orchestration**: Temporal
*   **State & Memory**: PostgreSQL
*   **Coordination**: Redis
*   **Message Bus**: NATS
*   **Observability**: OpenTelemetry, Prometheus, Jaeger, Grafana

## Quick Start

```bash
# Spin up the infrastructure backbone
docker-compose up -d postgres redis nats temporal prometheus jaeger

# Start the core cognition and telemetry services
python -m planner_service.main
python -m telemetry_service.main
python -m execution_service.main
```
