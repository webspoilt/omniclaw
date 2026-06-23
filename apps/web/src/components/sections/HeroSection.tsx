"use client";

import { motion } from "framer-motion";
import { ArrowRight, Terminal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ArchitectureGraph } from "@/components/visualizations/ArchitectureGraph";

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

const stagger = {
  visible: { transition: { staggerChildren: 0.1 } }
};

const stats = [
  { value: "< 2ms", label: "Policy Overhead" },
  { value: "ZMQ", label: "ROUTER-DEALER Mesh" },
  { value: "eBPF", label: "Kernel-Level Shield" },
];

export function HeroSection() {
  return (
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

          <motion.div variants={fadeUp} className="mt-16 grid grid-cols-3 gap-8 w-full max-w-lg border-t border-border/50 pt-12">
            {stats.map((stat) => (
              <div key={stat.label} className="flex flex-col items-center gap-1">
                <span className="text-2xl font-bold tracking-tight font-mono">{stat.value}</span>
                <span className="text-xs text-muted-foreground">{stat.label}</span>
              </div>
            ))}
          </motion.div>
        </motion.div>

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
  );
}
