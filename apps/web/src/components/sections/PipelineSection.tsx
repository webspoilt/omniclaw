"use client";

const pipelineSteps = [
  { id: "input", label: "Event / Request", sub: "Sensor data, user intent, scheduled trigger" },
  { id: "parse", label: "Intent Parsing", sub: "LLM planner produces a proposed execution DAG" },
  { id: "validate", label: "Policy Validation", sub: "Capability gate — policy.yaml enforced", highlight: true },
  { id: "sandbox", label: "Sandbox Dispatch", sub: "unshare namespace, cgroup v2 limits applied" },
  { id: "execute", label: "Deterministic Execution", sub: "Bounded, replayable, syscall-monitored" },
  { id: "telemetry", label: "Telemetry Emission", sub: "OpenTelemetry spans, eBPF ring-buffer events" },
];

export function PipelineSection() {
  return (
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
          <div className="absolute left-1/2 -translate-x-1/2 top-[34%] w-full px-0">
            <div className="border-t border-dashed border-white/20 relative">
              <span className="absolute left-1/2 -translate-x-1/2 -top-2.5 bg-background px-3 text-[10px] font-mono text-white/30 uppercase tracking-widest">
                ← Trust Boundary →
              </span>
            </div>
          </div>

          <div className="flex flex-col gap-0">
            {pipelineSteps.map((step, i) => {
              const stepColor = step.highlight ? "border-white/40" : "border-border";
              return (
                <div key={step.id} className="flex items-start gap-4">
                  <div className="flex flex-col items-center">
                    <div className={`w-8 h-8 rounded-full border-2 ${stepColor} bg-background flex items-center justify-center text-xs font-mono text-muted-foreground flex-shrink-0`}>
                      {i + 1}
                    </div>
                    {i < pipelineSteps.length - 1 && (
                      <div className="w-px h-10 bg-border/50 mt-1" />
                    )}
                  </div>
                  <div className="pb-8 pt-1">
                    <p className={`text-sm font-medium ${step.highlight ? "text-foreground" : "text-foreground/80"}`}>{step.label}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{step.sub}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
