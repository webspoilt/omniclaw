"use client";

import { ShieldCheck, Lock, FileSearch, AlertTriangle, ScrollText, Siren } from "lucide-react";

const layers = [
  { icon: Lock, title: "Seccomp-BPF Filtering", desc: "~70 syscalls allowed. execve, mount, bpf, ptrace, personality blocked at kernel level. Default action SCMP_ACT_ERRNO." },
  { icon: ShieldCheck, title: "Cgroup v2 Isolation", desc: "Per-process memory.max, cpu.max, pids.max limits. PID immediately written to cgroup.procs after spawn." },
  { icon: FileSearch, title: "Capability-Based Policy", desc: "All 16 tool handlers are individually allowlisted. RBAC roles (admin, engineer, viewer) map to fine-grained tool permissions." },
  { icon: AlertTriangle, title: "Shell Injection Protection", desc: "All subprocess execution uses exec-form via shlex.split(). Shell metacharacters (;, $, `, |, &) are rejected before dispatch." },
  { icon: ScrollText, title: "Audit Trail", desc: "Every tool call is logged with agent_id, tool name, risk score, approval status, and execution result. Tamper-evident logging." },
  { icon: Siren, title: "Zombie Reaper", desc: "Background os.waitpid(-1, WNOHANG) loop every 1s prevents PID table exhaustion from rapid tool execution." },
];

export function SecuritySection() {
  return (
    <section id="security" className="py-24 px-6 border-t border-border/50">
      <div className="container mx-auto max-w-6xl">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-sm font-mono text-muted-foreground uppercase tracking-widest mb-4">Security & Policy</h2>
          <h3 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4">
            Defense in depth, from kernel to application.
          </h3>
          <p className="text-muted-foreground">
            OmniClaw enforces a multi-layer security model. Every execution path is validated at the policy layer,
            isolated at the kernel layer, and monitored at the hardware layer.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {layers.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="p-6 border border-border bg-card rounded-xl hover:border-border/80 transition-colors">
              <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center mb-4">
                <Icon className="w-5 h-5 text-muted-foreground" />
              </div>
              <h4 className="font-medium text-sm mb-2 text-foreground">{title}</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 p-6 border border-border/50 bg-card/50 rounded-xl">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-xs font-mono text-muted-foreground uppercase tracking-widest">Threat Model — Top Risks Mitigated</span>
          </div>
          <div className="grid md:grid-cols-2 gap-4 text-xs font-mono text-muted-foreground">
            {[
              { id: "T1", desc: "LLM Code Execution", severity: "8/10", status: "Mitigated" },
              { id: "T3", desc: "Shell Injection via Agent Output", severity: "8/10", status: "Mitigated" },
              { id: "T4", desc: "Seccomp Bypass", severity: "6/10", status: "Mitigated" },
              { id: "T5", desc: "eBPF Privilege Escalation", severity: "9/10", status: "Mitigated" },
              { id: "T6", desc: "Zombie Process Leak", severity: "5/10", status: "Mitigated" },
              { id: "T8", desc: "Unbounded Memory Growth", severity: "4/10", status: "Mitigated" },
            ].map(({ id, desc, severity, status }) => (
              <div key={id} className="flex items-center justify-between p-2 border border-border/30 rounded-lg">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] text-white/40">{id}</span>
                  <span>{desc}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-white/40">{severity}</span>
                  <span className="text-green-500">{status}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
