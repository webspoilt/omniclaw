"use client";

import { motion } from "framer-motion";
import { ArrowRight, ShieldCheck, Activity, Terminal, Workflow, Server, Cpu, Database, GitBranch, Lock, Layers } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ArchitectureGraph } from "@/components/visualizations/ArchitectureGraph";
import { TelemetryOverlay } from "@/components/visualizations/TelemetryOverlay";

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

const stagger = {
  visible: { transition: { staggerChildren: 0.1 } }
};

// Execution pipeline steps — shows the trust boundary clearly
const pipelineSteps = [
  { id: "input", label: "Event / Request", sub: "Sensor data, user intent, scheduled trigger", color: "border-border" },
  { id: "parse", label: "Intent Parsing", sub: "LLM planner produces a proposed execution DAG", color: "border-border" },
  { id: "validate", label: "Policy Validation", sub: "Capability gate — policy.yaml enforced", color: "border-white/40" },
  { id: "sandbox", label: "Sandbox Dispatch", sub: "unshare namespace, cgroup v2 limits applied", color: "border-border" },
  { id: "execute", label: "Deterministic Execution", sub: "Bounded, replayable, syscall-monitored", color: "border-border" },
  { id: "telemetry", label: "Telemetry Emission", sub: "OpenTelemetry spans, eBPF ring-buffer events", color: "border-border" },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden selection:bg-primary/20">
      
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 glass-panel border-b border-border/50">
        <div className="container mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 bg-primary rounded-sm" />
            <span className="font-semibold tracking-tight text-sm">OmniClaw</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-muted-foreground">
            <a href="#architecture" className="hover:text-foreground transition-colors">Architecture</a>
            <a href="#pipeline" className="hover:text-foreground transition-colors">Execution Model</a>
            <a href="#observability" className="hover:text-foreground transition-colors">Observability</a>
            <a href="#edge" className="hover:text-foreground transition-colors">Edge Runtime</a>
            <a href="https://github.com/webspoilt/omniclaw" target="_blank" rel="noreferrer" className="hover:text-foreground transition-colors">Docs</a>
          </div>
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="sm" className="hidden md:flex text-muted-foreground hover:text-foreground">
              GitHub
            </Button>
            <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90 font-medium">
              Deploy Runtime
            </Button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-40 pb-20 px-6 lg:pt-52 lg:pb-32 overflow-hidden">
        <div className="absolute inset-0 bg-grid-white opacity-[0.03] pointer-events-none" />
        <div className="absolute inset-0 bg-gradient-to-b from-background via-transparent to-background pointer-events-none" />
        
        <div className="container mx-auto max-w-6xl relative z-10">
          <motion.div 
            initial="hidden" 
            animate="visible" 
            variants={stagger}
            className="flex flex-col items-center text-center max-w-4xl mx-auto"
          >
            <motion.div variants={fadeUp}>
              <Badge variant="outline" className="mb-8 bg-background/50 backdrop-blur border-border/50 text-xs px-3 py-1 text-muted-foreground uppercase tracking-widest font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-green-500 mr-2 animate-pulse" />
                v4.5.0 — Production Stable
              </Badge>
            </motion.div>
            
            <motion.h1 variants={fadeUp} className="text-5xl md:text-7xl font-bold tracking-tighter leading-[1.1] mb-6 text-foreground">
              Deterministic Orchestration{" "}
              <br className="hidden lg:block" />
              <span className="text-muted-foreground">for Distributed AI Systems.</span>
            </motion.h1>
            
            <motion.p variants={fadeUp} className="text-lg md:text-xl text-muted-foreground mb-10 max-w-2xl leading-relaxed">
              OmniClaw is a secure, event-driven runtime for autonomous AI workflows.
              Policy-constrained execution. Kernel-level observability. Edge-native scheduling.
            </motion.p>
            
            <motion.div variants={fadeUp} className="flex flex-col sm:flex-row items-center gap-4 w-full justify-center">
              <Button size="lg" className="w-full sm:w-auto h-12 px-8 bg-primary text-primary-foreground hover:bg-primary/90 text-sm font-medium">
                Read the Docs
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
              <Button size="lg" variant="outline" className="w-full sm:w-auto h-12 px-8 bg-background border-border text-foreground hover:bg-muted text-sm font-medium font-mono">
                <Terminal className="mr-2 w-4 h-4 text-muted-foreground" />
                git clone webspoilt/omniclaw
              </Button>
            </motion.div>

            {/* Stats row */}
            <motion.div variants={fadeUp} className="mt-16 grid grid-cols-3 gap-8 w-full max-w-lg border-t border-border/50 pt-12">
              {[
                { value: "< 2ms", label: "Policy Overhead" },
                { value: "ZMQ", label: "ROUTER-DEALER Mesh" },
                { value: "eBPF", label: "Kernel-Level Shield" },
              ].map((stat) => (
                <div key={stat.label} className="flex flex-col items-center gap-1">
                  <span className="text-2xl font-bold tracking-tight font-mono">{stat.value}</span>
                  <span className="text-xs text-muted-foreground">{stat.label}</span>
                </div>
              ))}
            </motion.div>
          </motion.div>

          {/* Architecture Graph Hero */}
          <motion.div 
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="mt-20 w-full relative"
          >
            <div className="absolute -inset-0.5 bg-gradient-to-b from-border to-transparent rounded-2xl opacity-20 blur-sm" />
            <div className="relative rounded-2xl border border-border bg-card p-2 md:p-4 shadow-2xl">
              <div className="w-full h-8 flex items-center gap-2 px-3 border-b border-border/50 mb-4 pb-2">
                <div className="w-2.5 h-2.5 rounded-full bg-border" />
                <div className="w-2.5 h-2.5 rounded-full bg-border" />
                <div className="w-2.5 h-2.5 rounded-full bg-border" />
                <span className="ml-2 text-[10px] uppercase font-mono text-muted-foreground tracking-widest">Runtime Topology — Compute Core + Edge Node</span>
              </div>
              <ArchitectureGraph />
            </div>
          </motion.div>
        </div>
      </section>

      {/* Architecture Overview */}
      <section id="architecture" className="py-24 px-6 border-t border-border/50 bg-card/30">
        <div className="container mx-auto max-w-6xl">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-sm font-mono text-muted-foreground uppercase tracking-widest mb-4">Architecture</h2>
              <h3 className="text-3xl md:text-4xl font-semibold tracking-tight mb-6">
                Deterministic infrastructure{" "}
                <br />
                <span className="text-muted-foreground">for probabilistic planners.</span>
              </h3>
              <p className="text-muted-foreground text-lg mb-8 leading-relaxed">
                LLMs are planners, not trusted operating systems. OmniClaw enforces strict capability-based 
                policy between the planner and the execution sandbox, ensuring autonomous workflows remain 
                bounded, observable, and reversible.
              </p>
              
              <div className="space-y-6">
                <div className="flex gap-4">
                  <div className="mt-1"><ShieldCheck className="w-5 h-5 text-primary" /></div>
                  <div>
                    <h4 className="font-medium text-foreground mb-1">Runtime Isolation</h4>
                    <p className="text-sm text-muted-foreground">Workers execute inside <code className="text-xs bg-muted px-1 py-0.5 rounded">unshare</code> namespaces with explicit cgroup v2 memory and CPU limits. The eBPF Shield monitors syscall patterns at the kernel level.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="mt-1"><Workflow className="w-5 h-5 text-primary" /></div>
                  <div>
                    <h4 className="font-medium text-foreground mb-1">Replayable Workflow DAGs</h4>
                    <p className="text-sm text-muted-foreground">Tasks are structured as deterministic DAGs. Failed subtasks are retried with full execution lineage preserved — no silent failures.</p>
                  </div>
                </div>
                <div className="flex gap-4">
                  <div className="mt-1"><GitBranch className="w-5 h-5 text-primary" /></div>
                  <div>
                    <h4 className="font-medium text-foreground mb-1">ZeroMQ ROUTER-DEALER Mesh</h4>
                    <p className="text-sm text-muted-foreground">MessagePack-typed payloads over ZeroMQ provide sub-millisecond routing without the overhead of HTTP. Workers register with explicit capability declarations.</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-tr from-primary/5 to-transparent rounded-xl" />
              <div className="border border-border bg-card rounded-xl p-8 shadow-xl">
                <div className="flex items-center justify-between mb-8 pb-4 border-b border-border">
                  <span className="font-mono text-xs text-muted-foreground">POLICY_VALIDATION_TRACE</span>
                  <Badge variant="outline" className="text-green-500 border-green-500/20 bg-green-500/10 text-[10px]">PASS</Badge>
                </div>
                <div className="space-y-4 font-mono text-sm">
                  {[
                    { label: "Capability: NETWORK_EGRESS", value: "DENIED", ok: false },
                    { label: "Capability: FS_READ /tmp/*", value: "GRANTED", ok: true },
                    { label: "Memory Bound: 512MB", value: "WITHIN", ok: true },
                    { label: "Syscall: execve", value: "MONITORED", ok: true },
                  ].map((row) => (
                    <div key={row.label} className="flex justify-between items-center text-muted-foreground">
                      <span className="text-xs">{row.label}</span>
                      <span className={`text-xs ${row.ok ? "text-green-500" : "text-red-400"}`}>{row.value}</span>
                    </div>
                  ))}
                  <Separator className="bg-border my-4" />
                  <div className="flex justify-between items-center text-primary">
                    <span className="text-xs">Policy Overhead</span>
                    <span className="font-semibold text-xs">1.57ms</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Execution Pipeline — Trust Boundary */}
      <section id="pipeline" className="py-24 px-6 border-t border-border/50">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-sm font-mono text-muted-foreground uppercase tracking-widest mb-4">Execution Model</h2>
            <h3 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4">
              Every action passes through the policy gate.
            </h3>
            <p className="text-muted-foreground">
              Intent parsing and execution are fully decoupled. No LLM output reaches the host until it clears capability validation.
            </p>
          </div>

          <div className="relative max-w-lg mx-auto">
            {/* Trust boundary marker */}
            <div className="absolute left-1/2 -translate-x-1/2 top-[34%] w-full px-0">
              <div className="border-t border-dashed border-white/20 relative">
                <span className="absolute left-1/2 -translate-x-1/2 -top-2.5 bg-background px-3 text-[10px] font-mono text-white/30 uppercase tracking-widest">
                  ← Trust Boundary →
                </span>
              </div>
            </div>

            <div className="flex flex-col gap-0">
              {pipelineSteps.map((step, i) => (
                <div key={step.id} className="flex items-start gap-4">
                  <div className="flex flex-col items-center">
                    <div className={`w-8 h-8 rounded-full border-2 ${step.color} bg-background flex items-center justify-center text-xs font-mono text-muted-foreground flex-shrink-0`}>
                      {i + 1}
                    </div>
                    {i < pipelineSteps.length - 1 && (
                      <div className="w-px h-10 bg-border/50 mt-1" />
                    )}
                  </div>
                  <div className="pb-8 pt-1">
                    <p className={`text-sm font-medium ${step.id === "validate" ? "text-foreground" : "text-foreground/80"}`}>{step.label}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{step.sub}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Observability Stack */}
      <section id="observability" className="py-24 px-6 border-t border-border/50 bg-card/30">
        <div className="container mx-auto max-w-6xl">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-sm font-mono text-muted-foreground uppercase tracking-widest mb-4">Observability</h2>
            <h3 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4">
              You cannot secure what you cannot see.
            </h3>
            <p className="text-muted-foreground">
              OpenTelemetry spans, eBPF ring-buffer events, and queue telemetry provide complete visibility into every execution decision.
            </p>
          </div>
          
          <div className="grid lg:grid-cols-3 gap-8">
            <Card className="col-span-full lg:col-span-2 bg-card border-border overflow-hidden">
              <TelemetryOverlay />
            </Card>
            
            <Card className="p-6 bg-card border-border flex flex-col justify-center space-y-6">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Activity className="w-4 h-4 text-primary" />
                  <h4 className="font-medium text-sm">Execution Lineage</h4>
                </div>
                <p className="text-xs text-muted-foreground">Cryptographic audit trails for every workflow decision. Exportable to any SIEM or log aggregator.</p>
              </div>
              <Separator className="bg-border" />
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Server className="w-4 h-4 text-primary" />
                  <h4 className="font-medium text-sm">Queue Telemetry</h4>
                </div>
                <p className="text-xs text-muted-foreground">Per-worker queue depth, backpressure signals, and task propagation latency across the distributed cluster.</p>
              </div>
              <Separator className="bg-border" />
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <Lock className="w-4 h-4 text-primary" />
                  <h4 className="font-medium text-sm">eBPF Forensics</h4>
                </div>
                <p className="text-xs text-muted-foreground">Anomalous process terminations trigger forensic register captures. Cgroup freeze preserves state before SIGKILL.</p>
              </div>
            </Card>
          </div>
        </div>
      </section>

      {/* Edge Runtime */}
      <section id="edge" className="py-24 px-6 border-t border-border/50">
        <div className="container mx-auto max-w-6xl">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="order-2 lg:order-1 grid grid-cols-2 gap-4">
              {[
                { icon: Cpu, title: "Adaptive Scheduling", desc: "Thermal and battery-aware task routing. Workloads offload to the Compute Core when edge resources are constrained." },
                { icon: Database, title: "Local Vector Cache", desc: "SQLite-vec stores recent context embeddings locally. CONTEXT_HANDOFF_REQUEST syncs to LanceDB on demand." },
                { icon: Layers, title: "Offline Inference", desc: "Lightweight quantized models run locally on Termux. The network is not required for cached inference." },
                { icon: ShieldCheck, title: "Userspace Isolation", desc: "The Edge Node operates without root privileges. It cannot push execution commands to the Compute Core." },
              ].map(({ icon: Icon, title, desc }) => (
                <div key={title} className="p-5 border border-border bg-background rounded-xl">
                  <Icon className="w-5 h-5 text-muted-foreground mb-3" />
                  <h4 className="font-medium text-sm mb-1.5">{title}</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">{desc}</p>
                </div>
              ))}
            </div>
            
            <div className="order-1 lg:order-2">
              <h2 className="text-sm font-mono text-muted-foreground uppercase tracking-widest mb-4">Edge Runtime</h2>
              <h3 className="text-3xl md:text-4xl font-semibold tracking-tight mb-6">
                Engineered for{" "}
                <br />
                <span className="text-muted-foreground">constrained environments.</span>
              </h3>
              <p className="text-muted-foreground text-lg mb-8 leading-relaxed">
                OmniClaw scales down to Android/ARM edge nodes without compromising on observability or policy enforcement. 
                Resource-aware scheduling, token budgeting, and opportunistic vector sync enable reliable execution on 2W hardware.
              </p>
              <div className="font-mono text-xs bg-card border border-border rounded-lg p-4 text-muted-foreground">
                <div className="text-[10px] text-muted-foreground/60 mb-2 uppercase tracking-widest">Edge Resource Governor</div>
                <div>battery_threshold: <span className="text-foreground">20%</span></div>
                <div>cpu_abort_threshold: <span className="text-foreground">70%</span></div>
                <div>memory_abort_threshold: <span className="text-foreground">80%</span></div>
                <div>handoff_on_exceed: <span className="text-foreground">true</span></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA / Footer */}
      <footer className="border-t border-border/50 bg-background pt-24 pb-12 px-6">
        <div className="container mx-auto max-w-6xl text-center mb-24">
          <h2 className="text-3xl md:text-5xl font-semibold tracking-tight mb-6">
            Built for engineering teams<br />
            <span className="text-muted-foreground">who demand precision.</span>
          </h2>
          <p className="text-muted-foreground text-lg mb-10 max-w-2xl mx-auto">
            Open source. Deterministic. Policy-enforced. Integrate OmniClaw into your infrastructure and bring structured execution to your autonomous AI workflows.
          </p>
          <div className="flex justify-center gap-4 flex-wrap">
            <Button size="lg" className="h-12 px-8 bg-primary text-primary-foreground hover:bg-primary/90">
              Read the Documentation
            </Button>
            <Button size="lg" variant="outline" className="h-12 px-8 border-border bg-transparent text-foreground hover:bg-muted">
              View on GitHub
            </Button>
          </div>
        </div>
        
        <div className="container mx-auto max-w-6xl flex flex-col md:flex-row items-center justify-between pt-8 border-t border-border/50 text-sm text-muted-foreground">
          <div className="flex items-center gap-2 mb-4 md:mb-0">
            <div className="w-4 h-4 bg-primary rounded-sm opacity-50" />
            <span>&copy; {new Date().getFullYear()} OmniClaw Contributors. MIT License.</span>
          </div>
          <div className="flex gap-6">
            <a href="https://github.com/webspoilt/omniclaw" className="hover:text-foreground transition-colors">GitHub</a>
            <a href="https://discord.gg/ZU4mQaqh" className="hover:text-foreground transition-colors">Discord</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
