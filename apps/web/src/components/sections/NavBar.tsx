"use client";

import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export function NavBar() {
  return (
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
          <a href="#benchmarks" className="hover:text-foreground transition-colors">Benchmarks</a>
          <a href="#security" className="hover:text-foreground transition-colors">Security</a>
          <a href="#deployment" className="hover:text-foreground transition-colors">Deployment</a>
          <a href="https://github.com/webspoilt/omniclaw" target="_blank" rel="noreferrer" className="hover:text-foreground transition-colors">Docs</a>
        </div>
        <div className="flex items-center gap-4">
          <a href="https://github.com/webspoilt/omniclaw" target="_blank" rel="noreferrer">
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              GitHub
            </Button>
          </a>
          <a href="https://github.com/webspoilt/omniclaw">
            <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90 font-medium">
              Deploy Runtime
              <ArrowRight className="ml-2 w-3 h-3" />
            </Button>
          </a>
        </div>
      </div>
    </nav>
  );
}
