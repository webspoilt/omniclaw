import { useOmniClaw } from '@/hooks/useOmniClaw';
import {
    Terminal, Activity, Settings, Bell, Wifi, WifiOff,
    Cpu, Zap, Shield
} from 'lucide-react';

export function Header() {
    const { isConnected, swarmStatus } = useOmniClaw();

    return (
        <header className="h-14 glass-panel border-b border-white/10 flex items-center justify-between px-4 shrink-0">
            {/* Logo */}
            <div className="flex items-center gap-3">
                <div className="relative">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyber-accent to-cyber-secondary flex items-center justify-center">
                        <Shield className="w-5 h-5 text-white" />
                    </div>
                    <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-cyber-success rounded-full border-2 border-cyber-black" />
                </div>
                <div>
                    <h1 className="text-lg font-bold text-white tracking-tight">
                        OmniClaw
                        <span className="text-cyber-accent">.mission</span>
                    </h1>
                </div>
            </div>

            {/* Center Stats */}
            <div className="hidden md:flex items-center gap-6">
                <div className="flex items-center gap-2 text-xs">
                    <Cpu className="w-3.5 h-3.5 text-cyber-accent" />
                    <span className="text-gray-400">Engines:</span>
                    <span className="text-white font-mono">
                        {swarmStatus.engines.filter(e => e.status === 'online').length}/{swarmStatus.engines.length}
                    </span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                    <Zap className="w-3.5 h-3.5 text-cyber-warning" />
                    <span className="text-gray-400">Load:</span>
                    <span className="text-white font-mono">
                        {Math.round((swarmStatus.engines.reduce((a, e) => a + e.load, 0) / (swarmStatus.engines.length || 1)) * 100)}%
                    </span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                    <Activity className="w-3.5 h-3.5 text-cyber-success" />
                    <span className="text-gray-400">Workers:</span>
                    <span className="text-white font-mono">{swarmStatus.activeWorkers}</span>
                </div>
            </div>

            {/* Right Actions */}
            <div className="flex items-center gap-2">
                {/* Connection Status */}
                <div className={`
          flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium
          ${isConnected
                        ? 'bg-cyber-success/10 text-cyber-success border border-cyber-success/30'
                        : 'bg-cyber-danger/10 text-cyber-danger border border-cyber-danger/30'
                    }
        `}>
                    {isConnected ? (
                        <>
                            <Wifi className="w-3.5 h-3.5" />
                            <span>Connected</span>
                        </>
                    ) : (
                        <>
                            <WifiOff className="w-3.5 h-3.5" />
                            <span>Offline</span>
                        </>
                    )}
                </div>

                <div className="w-px h-6 bg-white/10 mx-1" />

                <button className="p-2 hover:bg-white/5 rounded-lg transition-colors relative">
                    <Bell className="w-4 h-4 text-gray-400" />
                    <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-cyber-danger rounded-full" />
                </button>

                <button className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                    <Settings className="w-4 h-4 text-gray-400" />
                </button>

                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyber-gray to-cyber-dark border border-white/10 flex items-center justify-center">
                    <span className="text-xs font-medium text-cyber-accent">OP</span>
                </div>
            </div>
        </header>
    );
}
