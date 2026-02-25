import { useOmniClaw, toolCards } from '@/hooks/useOmniClaw';
import { ToolCard } from './ToolCard';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Grid, Zap } from 'lucide-react';

export function ToolGrid() {
    const { activeTool, setActiveTool, connectionUrl } = useOmniClaw();
    const { send, isConnected } = useWebSocket({
        url: connectionUrl,
        onMessage: (data) => {
            console.log('Received:', data);
        },
    });

    const handleActivate = (toolId: string) => {
        const tool = toolCards.find(t => t.id === toolId);
        if (!tool) return;

        // Deactivate current if different
        if (activeTool && activeTool !== toolId) {
            send({
                type: 'deactivate_tool',
                payload: { toolId: activeTool },
                timestamp: Date.now(),
                id: crypto.randomUUID(),
            });
        }

        // Activate new tool
        send({
            type: 'activate_tool',
            payload: {
                toolId,
                systemPrompt: tool.systemPrompt,
                config: {
                    temperature: 0.7,
                    maxTokens: 4096,
                },
            },
            timestamp: Date.now(),
            id: crypto.randomUUID(),
        });

        setActiveTool(toolId);
    };

    const handleDeactivate = () => {
        if (activeTool) {
            send({
                type: 'deactivate_tool',
                payload: { toolId: activeTool },
                timestamp: Date.now(),
                id: crypto.randomUUID(),
            });
            setActiveTool(null);
        }
    };

    const categories = [
        { id: 'offensive', label: 'Offensive Security', color: 'text-red-400' },
        { id: 'defensive', label: 'Defensive Security', color: 'text-blue-400' },
        { id: 'analysis', label: 'Analysis & Research', color: 'text-green-400' },
        { id: 'companion', label: 'AI Companions', color: 'text-pink-400' },
    ];

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-cyber-accent/10 rounded-lg border border-cyber-accent/30">
                        <Grid className="w-5 h-5 text-cyber-accent" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-white">Tool Grid</h2>
                        <p className="text-sm text-gray-400">
                            {isConnected ? (
                                <span className="flex items-center gap-1.5">
                                    <span className="w-1.5 h-1.5 rounded-full bg-cyber-success animate-pulse" />
                                    Connected to OmniClaw daemon
                                </span>
                            ) : (
                                <span className="flex items-center gap-1.5 text-cyber-danger">
                                    <span className="w-1.5 h-1.5 rounded-full bg-cyber-danger" />
                                    Disconnected
                                </span>
                            )}
                        </p>
                    </div>
                </div>

                {activeTool && (
                    <div className="flex items-center gap-2 px-4 py-2 bg-cyber-success/10 border border-cyber-success/30 rounded-lg">
                        <Zap className="w-4 h-4 text-cyber-success" />
                        <span className="text-sm text-cyber-success font-medium">
                            {toolCards.find(t => t.id === activeTool)?.name} Active
                        </span>
                    </div>
                )}
            </div>

            {/* Grid */}
            <div className="flex-1 overflow-y-auto custom-scrollbar pr-2">
                {categories.map((category) => {
                    const tools = toolCards.filter(t => t.category === category.id);
                    if (tools.length === 0) return null;

                    return (
                        <div key={category.id} className="mb-8">
                            <h3 className={`text-sm font-semibold uppercase tracking-wider mb-4 ${category.color}`}>
                                {category.label}
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                                {tools.map((tool) => (
                                    <ToolCard
                                        key={tool.id}
                                        tool={tool}
                                        isActive={activeTool === tool.id}
                                        onActivate={() => handleActivate(tool.id)}
                                        onDeactivate={handleDeactivate}
                                    />
                                ))}
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
