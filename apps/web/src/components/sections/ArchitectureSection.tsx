"use client";

import { ShieldCheck, Workflow, GitBranch } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

export function ArchitectureSection() {
  return (
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
  );
}
