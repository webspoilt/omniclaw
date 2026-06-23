"use client";

import { Cpu, Database, Layers, ShieldCheck } from "lucide-react";

const features = [
  { icon: Cpu, title: "Adaptive Scheduling", desc: "Thermal and battery-aware task routing. Workloads offload to the Compute Core when edge resources are constrained." },
  { icon: Database, title: "Local Vector Cache", desc: "SQLite-vec stores recent context embeddings locally. CONTEXT_HANDOFF_REQUEST syncs to LanceDB on demand." },
  { icon: Layers, title: "Offline Inference", desc: "Lightweight quantized models run locally on Termux. The network is not required for cached inference." },
  { icon: ShieldCheck, title: "Userspace Isolation", desc: "The Edge Node operates without root privileges. It cannot push execution commands to the Compute Core." },
];

export function EdgeSection() {
  return (
    <section id="edge" className="py-24 px-6 border-t border-border/50">
      <div className="container mx-auto max-w-6xl">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="order-2 lg:order-1 grid grid-cols-2 gap-4">
            {features.map(({ icon: Icon, title, desc }) => (
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
  );
}
