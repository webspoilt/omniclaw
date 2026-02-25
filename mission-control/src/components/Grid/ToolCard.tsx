import { useState } from 'react';
import {
    Target, TrendingUp, Brain, Shield, Heart, Bug, Cloud, Search,
    Play, Square, Activity, Clock, CheckCircle, AlertCircle
} from 'lucide-react';
import type { ToolCard as ToolCardType } from '@/types';

const iconMap: Record<string, React.ElementType> = {
    Target,
    TrendingUp,
    Brain,
    Shield,
    Heart,
    Bug,
    Cloud,
    Search,
};

const statusConfig = {
    idle: { color: 'text-gray-400', bg: 'bg-gray-500/20', icon: Activity },
    active: { color: 'text-cyber-success', bg: 'bg-cyber-success/20', icon: Play },
    error: { color: 'text-cyber-danger', bg: 'bg-cyber-danger/20', icon: AlertCircle },
    loading: { color: 'text-cyber-warning', bg: 'bg-cyber-warning/20', icon: Clock },
};

const categoryColors = {
    offensive: 'border-red-500/30 hover:border-red-500/60',
    defensive: 'border-blue-500/30 hover:border-blue-500/60',
    analysis: 'border-green-500/30 hover:border-green-500/60',
    companion: 'border-pink-500/30 hover:border-pink-500/60',
    system: 'border-purple-500/30 hover:border-purple-500/60',
};

interface ToolCardProps {
    tool: ToolCardType;
    isActive: boolean;
    onActivate: () => void;
    onDeactivate: () => void;
}

export function ToolCard({ tool, isActive, onActivate, onDeactivate }: ToolCardProps) {
    const [isHovered, setIsHovered] = useState(false);
    const Icon = iconMap[tool.icon] || Activity;
    const status = statusConfig[tool.status];
    const StatusIcon = status.icon;

    return (
        <div
            className={`
        relative group cursor-pointer transition-all duration-300 ease-out
        ${isActive ? 'scale-[1.02]' : 'hover:scale-[1.01]'}
      `}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            onClick={isActive ? onDeactivate : onActivate}
        >
            {/* Glow Effect */}
            <div
                className={`
          absolute -inset-0.5 rounded-xl opacity-0 transition-opacity duration-300
          bg-gradient-to-r ${tool.color} blur-sm
          ${isHovered || isActive ? 'opacity-40' : ''}
        `}
            />

            {/* Card Content */}
            <div
                className={`
          relative glass-card p-5 h-full flex flex-col
          border ${categoryColors[tool.category]}
          ${isActive ? 'ring-2 ring-cyber-accent/50 shadow-lg shadow-cyber-accent/10' : ''}
          transition-all duration-300
        `}
            >
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                    <div
                        className={`
              p-2.5 rounded-lg bg-gradient-to-br ${tool.color} 
              shadow-lg transition-transform duration-300
              ${isHovered ? 'scale-110' : ''}
            `}
                    >
                        <Icon className="w-5 h-5 text-white" />
                    </div>

                    <div className={`
            flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium
            ${status.bg} ${status.color}
          `}>
                        <StatusIcon className="w-3 h-3" />
                        <span className="capitalize">{tool.status}</span>
                    </div>
                </div>

                {/* Title & Description */}
                <h3 className="text-lg font-semibold text-white mb-1 group-hover:text-cyber-accent transition-colors">
                    {tool.name}
                </h3>
                <p className="text-sm text-gray-400 line-clamp-2 mb-4 flex-grow">
                    {tool.description}
                </p>

                {/* Metrics */}
                {tool.metrics && (
                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-500 mb-3">
                        <div className="flex items-center gap-1">
                            <CheckCircle className="w-3 h-3" />
                            <span>{tool.metrics.tasksCompleted} tasks</span>
                        </div>
                        <div className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            <span>{tool.metrics.uptime}</span>
                        </div>
                    </div>
                )}

                {/* Action Button */}
                <button
                    className={`
            w-full py-2 px-4 rounded-lg font-medium text-sm
            flex items-center justify-center gap-2
            transition-all duration-200
            ${isActive
                            ? 'bg-cyber-danger/20 text-cyber-danger border border-cyber-danger/30 hover:bg-cyber-danger/30'
                            : 'bg-cyber-accent/10 text-cyber-accent border border-cyber-accent/30 hover:bg-cyber-accent/20'
                        }
          `}
                    onClick={(e) => {
                        e.stopPropagation();
                        isActive ? onDeactivate() : onActivate();
                    }}
                >
                    {isActive ? (
                        <>
                            <Square className="w-4 h-4" />
                            Deactivate
                        </>
                    ) : (
                        <>
                            <Play className="w-4 h-4" />
                            Activate
                        </>
                    )}
                </button>

                {/* Active Indicator */}
                {isActive && (
                    <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-cyber-success animate-pulse" />
                )}
            </div>
        </div>
    );
}
