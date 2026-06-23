"use client";

import { Server, Container, Globe, Shield, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const topologies = [
  {
    icon: Server,
    title: "Bare Metal / VM",
    desc: "Direct Linux deployment with full cgroup v2, seccomp-BPF, and eBPF support. Maximum isolation and performance.",
    config: "systemd.unified_cgroup_hierarchy=1 cgroup_no_v1=all",
  },
  {
    icon: Container,
    title: "Docker / Podman",
    desc: "OCI-compatible containers with sandbox-worker isolation. The sandbox.Dockerfile drops all capabilities and uses read-only rootfs.",
    config: "docker compose --profile sandbox up",
  },
  {
    icon: Globe,
    title: "Kubernetes",
    desc: "Pod Security Policies, seccomp profiles, and NetworkPolicy for multi-tenant AI workload orchestration across a cluster.",
    config: "kubectl apply -f deploy/k8s/",
  },
  {
    icon: Shield,
    title: "Edge / ARM",
    desc: "Termux-compatible deployment on Android devices. No root required for the edge node. ZeroMQ mesh to the Compute Core.",
    config: "curl -fsSL https://omniclaw.dev/setup.sh | bash",
  },
];

export function DeploymentSection() {
  return (
    <section id="deployment" className="py-24 px-6 border-t border-border/50">
      <div className="container mx-auto max-w-6xl">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <h2 className="text-sm font-mono text-muted-foreground uppercase tracking-widest mb-4">Deployment</h2>
          <h3 className="text-3xl md:text-4xl font-semibold tracking-tight mb-4">
            Deploy anywhere. Control everything.
          </h3>
          <p className="text-muted-foreground">
            OmniClaw runs on bare metal, in containers, on Kubernetes, and on ARM edge devices — with the same security model.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-6">
          {topologies.map(({ icon: Icon, title, desc, config }) => (
            <div key={title} className="p-6 border border-border bg-card rounded-xl hover:border-border/80 transition-colors">
              <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center mb-4">
                <Icon className="w-5 h-5 text-muted-foreground" />
              </div>
              <h4 className="font-medium text-sm mb-2 text-foreground">{title}</h4>
              <p className="text-xs text-muted-foreground mb-4 leading-relaxed">{desc}</p>
              <div className="bg-background border border-border/50 rounded-lg p-3 font-mono text-[11px] text-muted-foreground">
                <span className="text-green-500">$</span> {config}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
