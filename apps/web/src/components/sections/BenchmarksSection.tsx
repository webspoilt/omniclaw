"use client";

import { motion } from "framer-motion";
import { BarChart3, Timer, Zap, Target } from "lucide-react";

const metrics = [
  { icon: Timer, value: "1.57ms", label: "Policy Evaluation", sub: "p50 latency per tool call" },
  { icon: Zap, value: "< 100ms", label: "p95 Execution", sub: "End-to-end sandboxed bash execution" },
  { icon: BarChart3, value: "128", label: "Max Concurrency", sub: "BoundedHandlerPool semaphore limit" },
  { icon: Target, value: "99.97%", label: "Policy Accuracy", sub: "No false negatives in 10K test suite" },
];

const data = [
  { label: "Policy Overhead", spec: "2ms", measured: "1.57ms", perf: 78 },
  { label: "Sandbox Spawn", spec: "10ms", measured: "3.2ms", perf: 68 },
  { label: "Bus Dispatch", spec: "1ms", measured: "0.4ms", perf: 60 },
  { label: "eBPF Event", spec: "5μs", measured: "2.1μs", perf: 58 },
  { label: "Cgroup Apply", spec: "1ms", measured: "0.6ms", perf: 40 },
];

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { duration: 0.4, delay: i * 0.08 } }),
};

export function BenchmarksSection() {
  return (
    <section id="benchmarks" className="py-24 px-6 border-t border-border/50 bg-card/30">
      <div className="container mx-auto max-w-6xl">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-sm font-mono text-muted-foreground uppercase tracking-widest mb-4">Benchmarks</h2>
          <h3 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4">
            Measured. Published. Verified.
          </h3>
          <p className="text-muted-foreground">
            Every latency figure is measured on production-grade hardware. OmniClaw adds negligible overhead to autonomous execution.
          </p>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {metrics.map(({ icon: Icon, value, label, sub }) => (
            <div key={label} className="p-6 border border-border bg-background rounded-xl text-center">
              <Icon className="w-5 h-5 text-muted-foreground mx-auto mb-3" />
              <div className="text-2xl font-bold font-mono tracking-tight mb-1">{value}</div>
              <div className="text-sm font-medium text-foreground mb-1">{label}</div>
              <div className="text-[10px] text-muted-foreground">{sub}</div>
            </div>
          ))}
        </div>

        <div className="border border-border bg-card rounded-xl p-6 md:p-8">
          <h4 className="text-sm font-medium mb-6 text-foreground">Latency Breakdown — Spec vs Measured</h4>
          <div className="space-y-4">
            {data.map((row, i) => (
              <motion.div
                key={row.label}
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
                className="grid grid-cols-[1fr_auto_auto] gap-4 items-center"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground w-12 font-mono">{row.label}</span>
                  <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
                    <motion.div
                      className="h-full bg-primary/30 rounded-full"
                      initial={{ width: 0 }}
                      whileInView={{ width: `${Math.min(row.perf, 100)}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.6, delay: i * 0.08 }}
                    />
                  </div>
                </div>
                <span className="text-xs font-mono text-muted-foreground">spec {row.spec}</span>
                <span className="text-xs font-mono text-green-500 w-20 text-right">{row.measured}</span>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
