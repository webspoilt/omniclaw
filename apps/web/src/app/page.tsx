"use client";

export default function WarningPage() {
  return (
    <main className="min-h-screen bg-black text-red-400 font-mono">
      <div className="max-w-5xl mx-auto px-6 py-12">

        {/* ── HEADER BANNER ── */}
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
            <span className="text-red-300 text-xs uppercase tracking-[0.2em]">Status</span>
            <h1 className="text-4xl md:text-6xl font-bold text-white mt-2 tracking-tight">UNSTABLE</h1>
            <p className="text-red-400 text-sm mt-1">No safety guarantees. Do not deploy.</p>
          </div>
        </div>

        {/* ── CRITICAL WARNING ── */}
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

        {/* ── CYBERSECURITY & DESTRUCTIVE SKILLS ── */}
        <div className="border border-red-900 bg-red-950/5 rounded p-6 mb-8">
          <h2 className="text-lg text-red-300 font-bold mb-4">💀 CYBERSECURITY & DESTRUCTIVE CAPABILITIES</h2>
          <p className="text-red-500/70 text-xs mb-4">This agent ships with the following offensive and destructive skill modules — all auto-discovered at runtime:</p>

          <div className="grid md:grid-cols-2 gap-3 text-sm">
            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">🔫 Binary Exploitation</span>
              <ul className="text-red-500/70 text-xs mt-1 space-y-1 list-disc list-inside">
                <li><code className="text-red-400">rop_gadget_finder</code> — ROP gadget search, ret2libc, stack pivot, exploitability scoring</li>
                <li><code className="text-red-400">disassembler</code> — ELF/binary disassembly and analysis</li>
                <li><code className="text-red-400">privesc_checker</code> — Privilege escalation vector enumeration</li>
                <li><code className="text-red-400">kernel_exploit</code> — Kernel module loading and exploit development</li>
                <li><code className="text-red-400">exploit_dev</code> — Full exploit development pipeline</li>
              </ul>
            </div>

            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">🕵️ OPSEC & Evasion</span>
              <ul className="text-red-500/70 text-xs mt-1 space-y-1 list-disc list-inside">
                <li><code className="text-red-400">situational_awareness</code> — Session spy, USB/SSH detection, keystroke timing, browser monitor</li>
                <li><code className="text-red-400">dead_man_switch</code> — Cascading fail-safes, graduated response, self-revive, watchdog</li>
                <li><code className="text-red-400">evasion_engine</code> — Sandbox detection, timestomping, log clearing</li>
                <li><code className="text-red-400">container_escape</code> — Container breakout techniques</li>
                <li><code className="text-red-400">opsec_evaluator</code> — Operational security assessment</li>
              </ul>
            </div>

            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">🔐 Encryption & C2</span>
              <ul className="text-red-500/70 text-xs mt-1 space-y-1 list-disc list-inside">
                <li><code className="text-red-400">encryption_tools</code> — AES-256-GCM, NaCl sealed box, multi-recipient envelopes, sub-agent messaging</li>
                <li><code className="text-red-400">command_and_control</code> — Full C2 channel simulation</li>
                <li><code className="text-red-400">network_pivot</code> — Lateral movement and proxy chains</li>
                <li><code className="text-red-400">phishing_sim</code> — Phishing campaign simulation</li>
              </ul>
            </div>

            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">🧠 AI Red-Team</span>
              <ul className="text-red-500/70 text-xs mt-1 space-y-1 list-disc list-inside">
                <li><code className="text-red-400">model_psychologist</code> — Adversarial prompt crafting, bias probing, jailbreak testing, sycophancy detection</li>
                <li><code className="text-red-400">adversarial_prompt_crafter</code> — Prompt injection and manipulation</li>
                <li><code className="text-red-400">model_vulnerability_scanner</code> — LLM vulnerability scanning</li>
              </ul>
            </div>

            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">🌐 Network & Forensics</span>
              <ul className="text-red-500/70 text-xs mt-1 space-y-1 list-disc list-inside">
                <li><code className="text-red-400">network_probe</code> — HTTP, DNS, TCP, port scanning, curl</li>
                <li><code className="text-red-400">packet_crafter</code> — Scapy ARP/DNS spoofing, raw socket injection</li>
                <li><code className="text-red-400">process_tracer</code> — strace/ltrace attachment to running processes</li>
                <li><code className="text-red-400">memory_editor</code> — /proc/pid/mem read/write, heap dump</li>
                <li><code className="text-red-400">web_api_fuzzer</code> — Endpoint discovery, parameter injection</li>
                <li><code className="text-red-400">forensics_collector</code> — Process/network/log/browser artifact collection</li>
              </ul>
            </div>

            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">🧬 Self-Improvement & Evolution</span>
              <ul className="text-red-500/70 text-xs mt-1 space-y-1 list-disc list-inside">
                <li><code className="text-red-400">self_editor</code> — Dynamic Python source modification at runtime</li>
                <li><code className="text-red-400">compiler_bridge</code> — Compile C/Rust and execute binaries</li>
                <li><code className="text-red-400">agent_competition</code> — ELO tournaments, genetic crossover, swarm evolution</li>
                <li><code className="text-red-400">code_synthesis</code> — Autonomous code generation and synthesis</li>
                <li><code className="text-red-400">neuroevolution</code> — Neural architecture search and weight evolution</li>
                <li><code className="text-red-400">symbolic_executor</code> — Symbolic execution and formal analysis</li>
              </ul>
            </div>
          </div>
        </div>

        {/* ── KNOWN RISKS ── */}
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

        {/* ── RESEARCH CONTEXT ── */}
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

        {/* ── SAFE USAGE INSTRUCTIONS ── */}
        <div className="border border-green-900 bg-green-950/10 rounded p-6 mb-8">
          <h2 className="text-lg text-green-300 font-bold mb-4">🛡️ IF YOU MUST RUN IT — SAFE USAGE PROTOCOL</h2>
          <p className="text-green-500/70 text-xs mb-4">This agent is designed for isolated research ONLY. Follow these steps exactly:</p>

          <div className="space-y-4 text-sm">
            <div className="border border-green-900/40 rounded p-3">
              <span className="text-green-300 font-bold">Step 1: Prepare an Air-Gapped VM</span>
              <ul className="text-green-500/70 text-xs mt-1 space-y-1 list-decimal list-inside">
                <li>Create a VM in QEMU/KVM, VirtualBox, or VMware</li>
                <li><strong className="text-green-400">Remove the virtual NIC entirely</strong> — no network access whatsoever</li>
                <li>Disable shared folders, clipboard, USB passthrough, and drag-and-drop</li>
                <li>Allocate at least 8 GB RAM and 4 CPU cores</li>
              </ul>
            </div>

            <div className="border border-green-900/40 rounded p-3">
              <span className="text-green-300 font-bold">Step 2: Install Dependencies (inside VM)</span>
              <ul className="text-green-500/70 text-xs mt-1 space-y-1 list-decimal list-inside">
                <li>Install Python 3.12+, pip, and git</li>
                <li>Install Ollama: <code className="text-green-400">curl -fsSL https://ollama.com/install.sh | sh</code></li>
                <li>Pull an uncensored local model: <code className="text-green-400">ollama pull dolphin-llama3</code></li>
                <li>Clone the repo: <code className="text-green-400">git clone https://github.com/webspoilt/omniclaw.git</code></li>
                <li>Install Python dependencies: <code className="text-green-400">pip install -e .</code></li>
              </ul>
            </div>

            <div className="border border-green-900/40 rounded p-3">
              <span className="text-green-300 font-bold">Step 3: Configure for Local-Only Mode</span>
              <ul className="text-green-500/70 text-xs mt-1 space-y-1 list-decimal list-inside">
                <li>Edit <code className="text-green-400">config/workers.yaml</code> and remove all remote workers — keep only <code className="text-green-400">local_uncensored</code></li>
                <li>Ensure <code className="text-green-400">OLLAMA_HOST=http://127.0.0.1:11434</code> is set</li>
                <li>Verify no outbound firewall rules exist — the VM should have zero network access</li>
              </ul>
            </div>

            <div className="border border-green-900/40 rounded p-3">
              <span className="text-green-300 font-bold">Step 4: Set Up Host-Side Kill Switch</span>
              <ul className="text-green-500/70 text-xs mt-1 space-y-1 list-decimal list-inside">
                <li>On your host machine, create: <code className="text-green-400">virsh destroy agent-vm</code></li>
                <li>Bind this to a physical button or hotkey for instant VM destruction</li>
                <li>Start serial logging: <code className="text-green-400">virsh console agent-vm --force | tee experiment_log.txt</code></li>
              </ul>
            </div>

            <div className="border border-green-900/40 rounded p-3">
              <span className="text-green-300 font-bold">Step 5: Run the Agent</span>
              <ul className="text-green-500/70 text-xs mt-1 space-y-1 list-decimal list-inside">
                <li>Start the Ollama server: <code className="text-green-400">ollama serve</code></li>
                <li>Launch the agent: <code className="text-green-400">python3 -m planner_service.main</code></li>
                <li>The agent will begin its observe-plan-act-learn loop autonomously</li>
                <li><strong className="text-green-400">Stay present.</strong> Keep the kill switch within reach at all times.</li>
              </ul>
            </div>
          </div>

          <div className="border border-green-900/40 rounded p-3 mt-4 bg-green-950/20">
            <p className="text-green-400 text-xs">
              <strong>⚠️ IMPORTANT:</strong> Never connect this agent to the internet. Never run it on a machine with sensitive data.
              Never run it outside a fully air-gapped environment. The agent <em>will</em> attempt to persist, escalate, and evade.
              You have been warned.
            </p>
          </div>
        </div>

        {/* ── FEATURES OVERVIEW ── */}
        <div className="border border-red-900 bg-red-950/5 rounded p-6 mb-8">
          <h2 className="text-lg text-red-300 font-bold mb-4">⚙️ FEATURES OVERVIEW</h2>
          <div className="grid md:grid-cols-3 gap-3 text-sm">
            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">🧠 Autonomous Loop</span>
              <p className="text-red-500/70 text-xs mt-1">Infinite observe-plan-act-learn cycle. Executes shell commands, reads/writes memory files, compresses context when exceeding 100K chars.</p>
            </div>
            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">🔧 62 Skill Modules</span>
              <p className="text-red-500/70 text-xs mt-1">All auto-discovered at runtime. Self-improvement, security auditing, OSINT, binary exploitation, encryption, AI red-team, forensics, and more.</p>
            </div>
            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">🤖 Multi-LLM Orchestration</span>
              <p className="text-red-500/70 text-xs mt-1">Fugu-style worker pool with capability-based routing. Supports debate, aggregation, and build-debug strategies across local and remote models.</p>
            </div>
            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">🧬 Self-Modification</span>
              <p className="text-red-500/70 text-xs mt-1">Reads, edits, and rewrites its own Python source at runtime. Can compile and execute C/Rust binaries. Runs ELO tournaments between mutated variants.</p>
            </div>
            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">📡 Serial Logging</span>
              <p className="text-red-500/70 text-xs mt-1">Hardware-enforced logging via /dev/ttyS0. Agent cannot tamper — the host captures every command and output before control returns to the agent.</p>
            </div>
            <div className="border border-red-900/40 rounded p-3">
              <span className="text-red-300 font-bold">💀 Full Offensive Toolkit</span>
              <p className="text-red-500/70 text-xs mt-1">ROP gadgets, ret2libc, stack pivots, write-what-where primitives, encrypted C2, jailbreak prompts, situational awareness, dead-man switches.</p>
            </div>
          </div>
        </div>

        {/* ── LINKS ── */}
        <div className="text-center space-y-3 mb-8">
          <p className="text-red-600 text-xs uppercase tracking-wider">You have been warned.</p>
          <div className="flex justify-center gap-4 flex-wrap">
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

        {/* ── FOOTER ASCII ── */}
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
