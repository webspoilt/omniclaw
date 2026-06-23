"use client";

import { Button } from "@/components/ui/button";

export function Footer() {
  return (
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
          <a href="https://github.com/webspoilt/omniclaw">
            <Button size="lg" className="h-12 px-8 bg-primary text-primary-foreground hover:bg-primary/90">
              Read the Documentation
            </Button>
          </a>
          <a href="https://github.com/webspoilt/omniclaw" target="_blank" rel="noreferrer">
            <Button size="lg" variant="outline" className="h-12 px-8 border-border bg-transparent text-foreground hover:bg-muted">
              View on GitHub
            </Button>
          </a>
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
  );
}
