import { useEffect } from 'react';
import { useOmniClaw, initialEngines } from '@/hooks/useOmniClaw';
import { EngineNode } from './EngineNode';
import { Cpu, Activity, Layers, Zap, RefreshCw } from 'lucide-react';

export function SwarmPanel() {
    const { swarmStatus, updateSwarmStatus, isConnected } = useOmniClaw();

    useEffect(() => {
        // Initialize engines if empty
        if (swarmStatus.engines.length === 0) {
            updateSwarmStatus({ engines: initialEngines });
        }

        // Simulate status updates
        const interval = setInterval(() => {
            updateSwarmStatus({
                engines: initialEngines.map(engine => ({
                    ...engine,
                    load: Math.max(0, Math.min(1, engine.load + (Math.random() - 0.5) * 0.2)),
                    lastPing: Date.now(),
                })),
            });
        }, 3000);

        return () => clearInterval(interval);
    }, []);

    const onlineEngines = swarmStatus.engines.filter(e => e.status === 'online' || e.status === 'busy');
    const avgLoad = onlineEngines.length > 0
        ? onlineEngines.reduce((acc, e) => acc + e.load, 0) / onlineEngines.length
        : 0;

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <div className="p-1.5 bg-cyber-secondary/10 rounded-lg border border-cyber-secondary/30">
                        <Cpu className="w-4 h-4 text-cyber-secondary" />
                    </div>
                    <div>
                        <h3 className="text-sm font-bold text-white">Swarm Status</h3>
                        <p className="text-xs text-gray-400">{onlineEngines.length} engines online</p>
                    </div>
                </div>
                <button
                    onClick={() => updateSwarmStatus({ engines: initialEngines })}
                    className="p-1.5 hover:bg-white/5 rounded-lg transition-colors"
                >
                    <RefreshCw className="w-4 h-4 text-gray-400" />
                </button>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-2 mb-4">
                <div className="glass-card p-2.5 border border-white/5">
                    <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1">
                        <Activity className="w-3 h-3" />
                        <span>Load</span>
                    </div>
                    <div className="text-lg font-bold text-white font-mono">
                        {Math.round(avgLoad * 100)}%
                    </div>
                </div>
                <div className="glass-card p-2.5 border border-white/5">
                    <div className="flex items-center gap-1.5 text-xs text-gray-400 mb-1">
                        <Layers className="w-3 h-3" />
                        <span>Queue</span>
                    </div>
                    <div className="text-lg font-bold text-white font-mono">
                        {swarmStatus.queueDepth}
                    </div>
                </div>
            </div>

            {/* Engine List */}
            <div className="flex-1 overflow-y-auto custom-scrollbar space-y-3 pr-1">
                {swarmStatus.engines.map((engine) => (
                    <EngineNode key={engine.id} engine={engine} />
                ))}
            </div>

            {/* Footer Stats */}
            <div className="mt-4 pt-3 border-t border-white/10">
                <div className="flex items-center justify-between text-xs">
                    <span className="text-gray-500">Total Tokens</span>
                    <span className="text-cyber-accent font-mono">
                        {(swarmStatus.totalTokens / 1000).toFixed(1)}k
                    </span>
                </div>
                <div className="flex items-center justify-between text-xs mt-1">
                    <span className="text-gray-500">Active Workers</span>
                    <span className="text-cyber-success font-mono">
                        {swarmStatus.activeWorkers}
                    </span>
                </div>
            </div>
        </div>
    );
}
