import { useEffect, useState } from 'react';
import { Cpu, Activity, Thermometer, Zap, Server, Brain, Cloud, Box } from 'lucide-react';
import type { AIEngine } from '@/types';

const providerIcons = {
    openai: Brain,
    anthropic: Cloud,
    ollama: Box,
    local: Server,
};

const statusColors = {
    online: 'bg-cyber-success',
    offline: 'bg-gray-500',
    busy: 'bg-cyber-warning',
    error: 'bg-cyber-danger',
};

interface EngineNodeProps {
    engine: AIEngine;
}

export function EngineNode({ engine }: EngineNodeProps) {
    const [pulseIntensity, setPulseIntensity] = useState(0);
    const ProviderIcon = providerIcons[engine.provider];

    useEffect(() => {
        const interval = setInterval(() => {
            setPulseIntensity(Math.random());
        }, 2000);
        return () => clearInterval(interval);
    }, []);

    const getLoadColor = (load: number) => {
        if (load < 0.3) return 'text-cyber-success';
        if (load < 0.7) return 'text-cyber-warning';
        return 'text-cyber-danger';
    };

    return (
        <div className="relative group">
            {/* Glow Effect */}
            <div
                className={`
          absolute -inset-0.5 rounded-lg opacity-0 transition-opacity duration-500
          ${engine.status === 'online' ? 'bg-cyber-success/30' : ''}
          ${engine.status === 'busy' ? 'bg-cyber-warning/30' : ''}
          ${engine.status === 'error' ? 'bg-cyber-danger/30' : ''}
          blur-md group-hover:opacity-60
        `}
                style={{
                    opacity: engine.status === 'busy' ? 0.3 + (pulseIntensity * 0.3) : undefined,
                }}
            />

            <div className="relative glass-card p-4 border border-white/5 hover:border-white/10 transition-all">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                        <div className={`
              p-1.5 rounded-md 
              ${engine.status === 'online' ? 'bg-cyber-success/20' : 'bg-gray-500/20'}
            `}>
                            <ProviderIcon className={`w-4 h-4 ${engine.status === 'online' ? 'text-cyber-success' : 'text-gray-500'
                                }`} />
                        </div>
                        <div>
                            <h4 className="text-sm font-medium text-white">{engine.name}</h4>
                            <p className="text-xs text-gray-500">{engine.model}</p>
                        </div>
                    </div>
                    <div className={`
            w-2 h-2 rounded-full ${statusColors[engine.status]}
            ${engine.status === 'online' || engine.status === 'busy' ? 'animate-pulse' : ''}
          `} />
                </div>

                {/* Metrics */}
                <div className="space-y-2">
                    {/* Load Bar */}
                    <div className="flex items-center gap-2">
                        <Activity className="w-3 h-3 text-gray-500" />
                        <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                            <div
                                className={`h-full rounded-full transition-all duration-500 ${engine.load < 0.3 ? 'bg-cyber-success' :
                                        engine.load < 0.7 ? 'bg-cyber-warning' : 'bg-cyber-danger'
                                    }`}
                                style={{ width: `${engine.load * 100}%` }}
                            />
                        </div>
                        <span className={`text-xs font-mono ${getLoadColor(engine.load)}`}>
                            {Math.round(engine.load * 100)}%
                        </span>
                    </div>

                    {/* Temperature */}
                    <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5 text-gray-400">
                            <Thermometer className="w-3 h-3" />
                            <span>Temp</span>
                        </div>
                        <span className="font-mono text-gray-300">{engine.temperature.toFixed(1)}</span>
                    </div>

                    {/* Capabilities */}
                    <div className="flex flex-wrap gap-1 pt-1">
                        {engine.capabilities.slice(0, 3).map((cap) => (
                            <span
                                key={cap}
                                className="text-[10px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400 border border-white/5"
                            >
                                {cap}
                            </span>
                        ))}
                    </div>
                </div>

                {/* Footer */}
                <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-xs text-gray-500">
                    <span className="capitalize">{engine.provider}</span>
                    <span className="font-mono">
                        {new Date(engine.lastPing).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                </div>
            </div>
        </div>
    );
}
