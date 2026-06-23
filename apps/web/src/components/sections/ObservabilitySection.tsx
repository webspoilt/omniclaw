"use client";

import { Activity, Server, Lock } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { TelemetryOverlay } from "@/components/visualizations/TelemetryOverlay";

export function ObservabilitySection() {
  return (
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
  );
}
