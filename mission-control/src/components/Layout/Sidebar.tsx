import { useState } from 'react';
import {
    LayoutDashboard, MessageSquare, Terminal, Settings,
    HelpCircle, ChevronLeft, ChevronRight, Github, BookOpen
} from 'lucide-react';

interface SidebarProps {
    activeView: string;
    onViewChange: (view: string) => void;
}

const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'chat', label: 'Chat', icon: MessageSquare },
    { id: 'terminal', label: 'Terminal', icon: Terminal },
];

const bottomItems = [
    { id: 'docs', label: 'Documentation', icon: BookOpen },
    { id: 'settings', label: 'Settings', icon: Settings },
    { id: 'help', label: 'Help', icon: HelpCircle },
];

export function Sidebar({ activeView, onViewChange }: SidebarProps) {
    const [isCollapsed, setIsCollapsed] = useState(false);

    return (
        <aside
            className={`
        h-full glass-panel border-r border-white/10 flex flex-col
        transition-all duration-300
        ${isCollapsed ? 'w-16' : 'w-56'}
      `}
        >
            {/* Navigation */}
            <nav className="flex-1 p-3 space-y-1">
                {navItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = activeView === item.id;

                    return (
                        <button
                            key={item.id}
                            onClick={() => onViewChange(item.id)}
                            className={`
                w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                transition-all duration-200 group
                ${isActive
                                    ? 'bg-cyber-accent/10 text-cyber-accent border border-cyber-accent/30'
                                    : 'text-gray-400 hover:bg-white/5 hover:text-white border border-transparent'
                                }
                ${isCollapsed ? 'justify-center' : ''}
              `}
                        >
                            <Icon className={`w-5 h-5 ${isActive ? 'text-cyber-accent' : ''}`} />
                            {!isCollapsed && (
                                <span className="text-sm font-medium">{item.label}</span>
                            )}
                            {isActive && !isCollapsed && (
                                <div className="ml-auto w-1 h-1 rounded-full bg-cyber-accent" />
                            )}
                        </button>
                    );
                })}
            </nav>

            {/* Divider */}
            <div className="mx-3 h-px bg-white/10" />

            {/* Bottom Items */}
            <div className="p-3 space-y-1">
                {bottomItems.map((item) => {
                    const Icon = item.icon;
                    return (
                        <button
                            key={item.id}
                            className={`
                w-full flex items-center gap-3 px-3 py-2 rounded-lg
                text-gray-400 hover:bg-white/5 hover:text-white
                transition-all duration-200
                ${isCollapsed ? 'justify-center' : ''}
              `}
                        >
                            <Icon className="w-4 h-4" />
                            {!isCollapsed && (
                                <span className="text-sm">{item.label}</span>
                            )}
                        </button>
                    );
                })}

                {/* GitHub Link */}
                <a
                    href="https://github.com/webspoilt/omniclaw"
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`
            w-full flex items-center gap-3 px-3 py-2 rounded-lg
            text-gray-400 hover:bg-white/5 hover:text-white
            transition-all duration-200 mt-4
            ${isCollapsed ? 'justify-center' : ''}
          `}
                >
                    <Github className="w-4 h-4" />
                    {!isCollapsed && (
                        <span className="text-sm">GitHub</span>
                    )}
                </a>
            </div>

            {/* Collapse Toggle */}
            <div className="p-3 border-t border-white/10">
                <button
                    onClick={() => setIsCollapsed(!isCollapsed)}
                    className="
            w-full flex items-center justify-center p-2 rounded-lg
            text-gray-400 hover:bg-white/5 hover:text-white
            transition-all duration-200
          "
                >
                    {isCollapsed ? (
                        <ChevronRight className="w-4 h-4" />
                    ) : (
                        <ChevronLeft className="w-4 h-4" />
                    )}
                </button>
            </div>
        </aside>
    );
}
