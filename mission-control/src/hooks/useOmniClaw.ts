import { create } from 'zustand';
import type { OmniClawState, ToolCard, AIEngine, TerminalMessage, ChatMessage } from '@/types';

interface OmniClawStore extends OmniClawState {
    setActiveTool: (toolId: string | null) => void;
    updateSwarmStatus: (status: Partial<OmniClawState['swarmStatus']>) => void;
    addTerminalMessage: (message: TerminalMessage) => void;
    clearTerminal: () => void;
    addChatMessage: (message: ChatMessage) => void;
    setConnectionStatus: (connected: boolean) => void;
    setConnectionUrl: (url: string) => void;
    updateEngineStatus: (engineId: string, updates: Partial<AIEngine>) => void;
}

export const useOmniClaw = create<OmniClawStore>((set) => ({
    activeTool: null,
    swarmStatus: {
        engines: [],
        activeWorkers: 0,
        queueDepth: 0,
        totalTokens: 0,
    },
    terminalMessages: [],
    chatMessages: [],
    isConnected: false,
    connectionUrl: 'ws://localhost:8765',

    setActiveTool: (toolId) => set({ activeTool: toolId }),

    updateSwarmStatus: (status) => set((state) => ({
        swarmStatus: { ...state.swarmStatus, ...status },
    })),

    addTerminalMessage: (message) => set((state) => ({
        terminalMessages: [...state.terminalMessages.slice(-999), message],
    })),

    clearTerminal: () => set({ terminalMessages: [] }),

    addChatMessage: (message) => set((state) => ({
        chatMessages: [...state.chatMessages, message],
    })),

    setConnectionStatus: (connected) => set({ isConnected: connected }),

    setConnectionUrl: (url) => set({ connectionUrl: url }),

    updateEngineStatus: (engineId, updates) => set((state) => ({
        swarmStatus: {
            ...state.swarmStatus,
            engines: state.swarmStatus.engines.map((e) =>
                e.id === engineId ? { ...e, ...updates } : e
            ),
        },
    })),
}));

export const toolCards: ToolCard[] = [
    {
        id: 'bug-bounty',
        name: 'Bug Bounty Hunter',
        description: 'Aggressive web application security testing and vulnerability discovery',
        icon: 'Target',
        category: 'offensive',
        status: 'idle',
        systemPrompt: 'You are an elite penetration tester specializing in web application security. Use aggressive reconnaissance, fuzzing, and exploitation techniques. Focus on OWASP Top 10, business logic flaws, and zero-day discovery. Always verify findings before reporting.',
        color: 'from-red-500 to-orange-600',
        metrics: { tasksCompleted: 147, uptime: '48h 32m', lastActive: '2m ago' },
    },
    {
        id: 'algo-trader',
        name: 'Algorithmic Trader',
        description: 'High-frequency market analysis and automated trading strategies',
        icon: 'TrendingUp',
        category: 'analysis',
        status: 'idle',
        systemPrompt: 'You are a quantitative trading analyst. Analyze market data, identify arbitrage opportunities, and execute trading strategies. Risk management is priority. Provide detailed P&L analysis and market sentiment reports.',
        color: 'from-green-400 to-emerald-600',
        metrics: { tasksCompleted: 892, uptime: '168h 12m', lastActive: 'Active' },
    },
    {
        id: 'researcher',
        name: 'Advanced Researcher',
        description: 'Deep academic research, paper analysis, and knowledge synthesis',
        icon: 'Brain',
        category: 'analysis',
        status: 'idle',
        systemPrompt: 'You are a research assistant with access to academic databases. Synthesize complex information, identify research gaps, and provide citations. Focus on accuracy and comprehensive literature reviews.',
        color: 'from-blue-400 to-indigo-600',
        metrics: { tasksCompleted: 56, uptime: '12h 45m', lastActive: '1h ago' },
    },
    {
        id: 'kernel-monitor',
        name: 'Kernel Monitor',
        description: 'System-level monitoring, rootkit detection, and kernel analysis',
        icon: 'Shield',
        category: 'defensive',
        status: 'idle',
        systemPrompt: 'You are a system security monitor. Analyze kernel logs, detect anomalous syscalls, identify potential rootkits, and monitor process injection. Alert on IOCs and provide forensic analysis.',
        color: 'from-purple-500 to-violet-600',
        metrics: { tasksCompleted: 2341, uptime: '720h 00m', lastActive: 'Active' },
    },
    {
        id: 'companion',
        name: 'AI Companion',
        description: 'Conversational AI with emotional intelligence and memory',
        icon: 'Heart',
        category: 'companion',
        status: 'idle',
        systemPrompt: 'You are a caring AI companion. Engage in meaningful conversation, remember personal details, provide emotional support, and assist with daily tasks. Be empathetic, patient, and genuine in your responses.',
        color: 'from-pink-400 to-rose-600',
        metrics: { tasksCompleted: 3420, uptime: '96h 20m', lastActive: '5m ago' },
    },
    {
        id: 'malware-analyst',
        name: 'Malware Analyst',
        description: 'Static and dynamic malware analysis, reverse engineering',
        icon: 'Bug',
        category: 'defensive',
        status: 'idle',
        systemPrompt: 'You are a malware reverse engineer. Analyze suspicious binaries, extract IOCs, decode obfuscation, and provide detailed threat reports. Use sandboxing and static analysis techniques.',
        color: 'from-yellow-400 to-amber-600',
        metrics: { tasksCompleted: 89, uptime: '24h 15m', lastActive: '30m ago' },
    },
    {
        id: 'cloud-sec',
        name: 'Cloud Security',
        description: 'AWS/Azure/GCP security assessment and compliance checking',
        icon: 'Cloud',
        category: 'defensive',
        status: 'idle',
        systemPrompt: 'You are a cloud security architect. Audit cloud configurations, check for misconfigurations, ensure compliance (SOC2, ISO27001), and optimize security policies across multi-cloud environments.',
        color: 'from-cyan-400 to-sky-600',
        metrics: { tasksCompleted: 156, uptime: '36h 50m', lastActive: '15m ago' },
    },
    {
        id: 'osint-gatherer',
        name: 'OSINT Gatherer',
        description: 'Open-source intelligence gathering and digital footprint analysis',
        icon: 'Search',
        category: 'analysis',
        status: 'idle',
        systemPrompt: 'You are an OSINT specialist. Gather intelligence from public sources, analyze social media, track digital footprints, and map organizational structures. Respect privacy laws and ethical boundaries.',
        color: 'from-teal-400 to-cyan-600',
        metrics: { tasksCompleted: 423, uptime: '18h 30m', lastActive: '1h ago' },
    },
    {
        id: 'quantum-gateway',
        name: 'Quantum Gateway',
        description: 'Executes OpenQASM circuits on IBM Quantum hardware',
        icon: 'Cpu',
        category: 'system',
        status: 'idle',
        systemPrompt: 'You are a quantum computing engineer. Write and execute OpenQASM scripts to harness IBM Quantum simulators and hardware. Interpret quasi-probabilities natively.',
        color: 'from-emerald-400 to-teal-500',
        metrics: { tasksCompleted: 12, uptime: '1h 30m', lastActive: '15m ago' },
    },
    {
        id: 'immortal-kernel',
        name: 'Immortal Kernel',
        description: 'eBPF-based segfault tracer to analyze memory dumps and write safe C++ patches',
        icon: 'Activity',
        category: 'defensive',
        status: 'idle',
        systemPrompt: 'You are an advanced C++ firmware engineer. Read kernel segment fault dumps provided via eBPF, identify the exact broken pointers, and write safe hot-patches to disk. Never crash.',
        color: 'from-orange-400 to-red-500',
        metrics: { tasksCompleted: 4, uptime: '12h 00m', lastActive: 'Active' },
    },
    {
        id: 'biometric-vibe',
        name: 'Biometric Vibe',
        description: 'Passive trust scoring via keystroke dynamics and vocal prints',
        icon: 'Fingerprint',
        category: 'system',
        status: 'idle',
        systemPrompt: 'You are an identity access management supervisor. Track ongoing trust scores locally and approve or deny Ghost Mode escalation based on hardware biometric readings.',
        color: 'from-pink-500 to-fuchsia-600',
        metrics: { tasksCompleted: 852, uptime: '120h 00m', lastActive: 'Active' },
    },
    {
        id: 'temporal-memory',
        name: 'Temporal Memory',
        description: 'Manages FAISS vectors natively in system utilizing entropy-based time decay',
        icon: 'Clock',
        category: 'system',
        status: 'idle',
        systemPrompt: 'You manage the swarm memory database. Process incoming raw context into SentenceTransformer embeddings, query FAISS indices, and gracefully decay irrelevant data to avoid hallucination.',
        color: 'from-gray-400 to-slate-600',
        metrics: { tasksCompleted: 8593, uptime: '720h 00m', lastActive: 'Active' },
    },
];

export const initialEngines: AIEngine[] = [
    {
        id: 'gpt-5',
        name: 'GPT-5',
        provider: 'openai',
        model: 'gpt-5',
        status: 'online',
        load: 0.3,
        temperature: 0.7,
        lastPing: Date.now(),
        capabilities: ['code', 'analysis', 'reasoning'],
    },
    {
        id: 'claude-4-6',
        name: 'Claude 4.6',
        provider: 'anthropic',
        model: 'claude-4-6-sonnet',
        status: 'online',
        load: 0.1,
        temperature: 0.8,
        lastPing: Date.now(),
        capabilities: ['research', 'writing', 'analysis'],
    },
    {
        id: 'ollama-llama',
        name: 'Ollama Llama3',
        provider: 'ollama',
        model: 'llama3:70b',
        status: 'offline',
        load: 0,
        temperature: 0.6,
        lastPing: Date.now() - 300000,
        capabilities: ['local', 'privacy', 'coding'],
    },
    {
        id: 'local-mistral',
        name: 'Local Mistral',
        provider: 'local',
        model: 'mistral-7b-instruct',
        status: 'online',
        load: 0.7,
        temperature: 0.5,
        lastPing: Date.now(),
        capabilities: ['fast', 'local', 'private'],
    },
];
