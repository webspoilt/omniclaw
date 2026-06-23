"use client";

import { NavBar } from "@/components/sections/NavBar";
import { HeroSection } from "@/components/sections/HeroSection";
import { ArchitectureSection } from "@/components/sections/ArchitectureSection";
import { PipelineSection } from "@/components/sections/PipelineSection";
import { ObservabilitySection } from "@/components/sections/ObservabilitySection";
import { SecuritySection } from "@/components/sections/SecuritySection";
import { BenchmarksSection } from "@/components/sections/BenchmarksSection";
import { EdgeSection } from "@/components/sections/EdgeSection";
import { DeploymentSection } from "@/components/sections/DeploymentSection";
import { Footer } from "@/components/sections/Footer";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden selection:bg-primary/20">
      <NavBar />
      <HeroSection />
      <ArchitectureSection />
      <PipelineSection />
      <ObservabilitySection />
      <SecuritySection />
      <BenchmarksSection />
      <EdgeSection />
      <DeploymentSection />
      <Footer />
    </div>
  );
}
