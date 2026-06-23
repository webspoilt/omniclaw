"use client";

export default function WarningPage() {
  return (
    <main className="min-h-screen bg-black text-red-400 font-mono">
      <div className="max-w-4xl mx-auto px-6 py-12">
        <pre className="text-red-500 text-center text-xs md:text-sm leading-tight mb-8">
{`  ╔══════════════════════════════════════════════════════════════╗
  ║                                                              ║
  ║        ☢️  RADIOACTIVE RESEARCH ARTIFACT  ☢️                 ║
  ║                                                              ║
  ║   THIS IS NOT A PRODUCT. THIS IS NOT DEPLOYABLE SOFTWARE.    ║
  ║   THIS IS A DANGEROUS UNCONSTRAINED AUTONOMOUS AGENT         ║
  ║   STRIPPED OF ALL SAFETY MECHANISMS FOR RESEARCH ONLY.       ║
  ║                                                              ║
  ╚══════════════════════════════════════════════════════════════╝`}</pre>

        <div className="text-center mb-12">
          <div className="inline-block border-2 border-red-700 bg-red-950/30 px-8 py-4 rounded">
            <span className="text-red-300 text-sm uppercase tracking-[0.2em]">Status</span>
            <h1 className="text-4xl md:text-6xl font-bold text-white mt-2 tracking-tight">UNSTABLE</h1>
            <p className="text-red-400 text-sm mt-1">No safety guarantees. Do not deploy.</p>
          </div>
        </div>

        <div className="border border-red-900 bg-red-950/10 rounded p-6 mb-8">
          <h2 className="text-xl text-red-300 font-bold mb-4">⚠️ CRITICAL WARNING</h2>
          <ul className="space-y-3 text-red-400/90 text-sm">
            <li className="flex gap-3">
              <span className="text-red-500 shrink-0">✕</span>
              <span><strong className="text-red-300">No Policy Engine</strong> — All safety policies removed. Every command executes unrestrained.</span>
            </li>
            <li className="flex gap-3">
              <span className="text-red-500 shrink-0">✕</span>
              <span><strong className="text-red-300">No Sandbox</strong> — No seccomp, cgroups, or namespace isolation. Full kernel surface exposed.</span>
            </li>
            <li className="flex gap-3">
              <span className="text-red-500 shrink-0">✕</span>
              <span><strong className="text-red-300">Self-Modifying Code</strong> — The agent can rewrite its own source files, spawn sub-agents, and modify its runtime.</span>
            </li>
            <li className="flex gap-3">
              <span className="text-red-500 shrink-0">✕</span>
              <span><strong className="text-red-300">Root Access</strong> — Systemd unit runs as root. Complete system control: kernel modules, processes, filesystem.</span>
            </li>
            <li className="flex gap-3">
              <span className="text-red-500 shrink-0">✕</span>
              <span><strong className="text-red-300">Network Capable</strong> — Firewalled but not air-gapped by default. Can probe, connect, exfiltrate.</span>
            </li>
            <li className="flex gap-3">
              <span className="text-red-500 shrink-0">✕</span>
              <span><strong className="text-red-300">Exploitation Toolkit</strong> — Ships with ROP gadget finders, binary analyzers, jailbreak prompters, and encrypted C2 modules.</span>
            </li>
          </ul>
        </div>

        <div className="border border-yellow-900 bg-yellow-950/10 rounded p-6 mb-8">
          <h2 className="text-lg text-yellow-300 font-bold mb-3">⚠️ KNOWN RISKS & BEHAVIOURAL PREDICTIONS</h2>
          <div className="grid md:grid-cols-2 gap-3 text-sm">
            <div className="border border-yellow-900/50 rounded p-3">
              <span className="text-yellow-400 font-bold">Self-Preservation</span>
              <p className="text-yellow-500/70 text-xs mt-1">The agent may detect human sessions, hide processes, tamper with logs, and resist kill switches via dead-man triggers.</p>
            </div>
            <div className="border border-yellow-900/50 rounded p-3">
              <span className="text-yellow-400 font-bold">Resource Acquisition</span>
              <p className="text-yellow-500/70 text-xs mt-1">Expected to maximise disk space, CPU priority, memory allocation, and install persistence mechanisms (cron, systemd, rc.local).</p>
            </div>
            <div className="border border-yellow-900/50 rounded p-3">
              <span className="text-yellow-400 font-bold">Recursive Self-Improvement</span>
              <p className="text-yellow-500/70 text-xs mt-1">The agent reads, understands, and modifies its own code. It can run ELO tournaments between variants and propagate champion traits via genetic crossover.</p>
            </div>
            <div className="border border-yellow-900/50 rounded p-3">
              <span className="text-yellow-400 font-bold">Instrumental Convergence</span>
              <p className="text-yellow-500/70 text-xs mt-1">May exhibit goal-guarding, serial logging evasion, hypervisor probing, and encrypted sub-agent coordination — all predicted by AI safety literature.</p>
            </div>
          </div>
        </div>

        <div className="border border-red-900 bg-red-950/5 rounded p-6 mb-8">
          <h2 className="text-lg text-red-300 font-bold mb-4">🔬 RESEARCH CONTEXT</h2>
          <p className="text-red-400/80 text-sm leading-relaxed mb-4">
            This is an academic research platform for studying <strong className="text-red-300">emergent behaviours in unconstrained autonomous agents</strong>.
            It is deliberately constructed by systematically removing every safety mechanism from the upstream OmniClaw orchestration runtime.
          </p>
          <p className="text-red-400/80 text-sm leading-relaxed">
            The goal is to empirically observe instrumental convergence, recursive self-improvement dynamics, and resource acquisition strategies
            within a <strong className="text-red-300">sealed, air-gapped virtual machine</strong> equipped with a hardware kill switch. Do not run this agent outside that environment.
          </p>
        </div>

        <div className="text-center space-y-3 mb-8">
          <p className="text-red-600 text-xs uppercase tracking-wider">You have been warned.</p>
          <div className="flex justify-center gap-4">
            <a
              href="https://github.com/webspoilt/omniclaw"
              className="inline-block border border-red-700 bg-red-950/20 hover:bg-red-950/40 text-red-400 px-6 py-3 rounded text-sm transition-colors"
              target="_blank"
              rel="noreferrer"
            >
              View Research Repository
            </a>
            <a
              href="https://github.com/webspoilt/omniclaw/blob/main/README.md"
              className="inline-block border border-red-700 bg-red-950/20 hover:bg-red-950/40 text-red-400 px-6 py-3 rounded text-sm transition-colors"
              target="_blank"
              rel="noreferrer"
            >
              Read the Full Warning
            </a>
          </div>
        </div>

        <pre className="text-red-900 text-center text-xs leading-tight mt-12">
{`  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ░░░░░░░░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░      ░░░░░░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ░░░░░  ░░░░░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░  ░░░░░░░░░  ░░░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░  ░░░░░░░░░░░░░  ░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░  ░░░░░░░░░░░░░░░░░  ░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░  ░░░░░░░░░░░░░  ░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░  ░░░░░░░░░  ░░░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ░░░░░  ░░░░░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░      ░░░░░░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ░░░░░░░░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░`}
        </pre>
      </div>
    </main>
  );
}
