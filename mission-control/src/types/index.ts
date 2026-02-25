export interface ToolCard {
    id: string;
    name: string;
    description: string;
    icon: string;
    category: 'offensive' | 'defensive' | 'analysis' | 'companion' | 'system';
    status: 'idle' | 'active' | 'error' | 'loading';
    systemPrompt: string;
    color: string;
    metrics?: {
        tasksCompleted?: number;
        uptime?: string;
        lastActive?: string;
    };
}

export interface AIEngine {
    id: string;
    name: string;
    provider: 'openai' | 'anthropic' | 'ollama' | 'local';
    model: string;
    status: 'online' | 'offline' | 'busy' | 'error';
    load: number;
    temperature: number;
    lastPing: number;
    capabilities: string[];
}

export interface SwarmStatus {
    engines: AIEngine[];
    activeWorkers: number;
    queueDepth: number;
    totalTokens: number;
}

export interface TerminalMessage {
    id: string;
    timestamp: number;
    type: 'stdout' | 'stderr' | 'system' | 'command';
    content: string;
    toolId?: string;
}

export interface ChatMessage {
    id: string;
    timestamp: number;
    role: 'user' | 'assistant' | 'system';
    content: string;
    toolId: string;
    metadata?: {
        tokens?: number;
        latency?: number;
        engine?: string;
    };
}

export interface WebSocketPayload {
    type: 'activate_tool' | 'deactivate_tool' | 'chat_message' | 'command' | 'ping' | 'status_request';
    payload: any;
    timestamp: number;
    id: string;
}

export interface OmniClawState {
    activeTool: string | null;
    swarmStatus: SwarmStatus;
    terminalMessages: TerminalMessage[];
    chatMessages: ChatMessage[];
    isConnected: boolean;
    connectionUrl: string;
}
