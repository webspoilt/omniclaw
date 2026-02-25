import { useEffect, useRef, useState } from 'react';
import { Terminal } from '@xterm/xterm';
import { FitAddon } from '@xterm/addon-fit';
import { WebLinksAddon } from '@xterm/addon-web-links';
import '@xterm/xterm/css/xterm.css';
import { useOmniClaw } from '@/hooks/useOmniClaw';
import { Terminal as TerminalIcon, Trash2, Download, Maximize2, Minimize2 } from 'lucide-react';

export function LiveTerminal() {
    const terminalRef = useRef<HTMLDivElement>(null);
    const xtermRef = useRef<Terminal | null>(null);
    const fitAddonRef = useRef<FitAddon | null>(null);
    const { terminalMessages, addTerminalMessage, clearTerminal } = useOmniClaw();
    const [isExpanded, setIsExpanded] = useState(false);
    const [isReady, setIsReady] = useState(false);

    useEffect(() => {
        if (!terminalRef.current || xtermRef.current) return;

        const term = new Terminal({
            theme: {
                background: '#0a0a0f',
                foreground: '#e0e0e0',
                cursor: '#00f0ff',
                selectionBackground: 'rgba(0, 240, 255, 0.3)',
                black: '#0a0a0f',
                red: '#ff0040',
                green: '#00ff88',
                yellow: '#ffb800',
                blue: '#00f0ff',
                magenta: '#ff00a0',
                cyan: '#00f0ff',
                white: '#e0e0e0',
                brightBlack: '#2a2a3e',
                brightRed: '#ff3366',
                brightGreen: '#33ffaa',
                brightYellow: '#ffcc33',
                brightBlue: '#33f5ff',
                brightMagenta: '#ff33b8',
                brightCyan: '#33f5ff',
                brightWhite: '#ffffff',
            },
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 13,
            lineHeight: 1.2,
            cursorBlink: true,
            cursorStyle: 'block',
            scrollback: 10000,
            allowTransparency: true,
        });

        const fitAddon = new FitAddon();
        const webLinksAddon = new WebLinksAddon();

        term.loadAddon(fitAddon);
        term.loadAddon(webLinksAddon);

        term.open(terminalRef.current);
        fitAddon.fit();

        xtermRef.current = term;
        fitAddonRef.current = fitAddon;
        setIsReady(true);

        // Initial welcome message
        term.writeln('\x1b[36m╔══════════════════════════════════════════════════════════════╗\x1b[0m');
        term.writeln('\x1b[36m║\x1b[0m \x1b[1m\x1b[32mOmniClaw Mission Control Terminal v1.0\x1b[0m                      \x1b[36m║\x1b[0m');
        term.writeln('\x1b[36m║\x1b[0m Connected to Python daemon via WebSocket                     \x1b[36m║\x1b[0m');
        term.writeln('\x1b[36m╚══════════════════════════════════════════════════════════════╝\x1b[0m');
        term.writeln('');

        const handleResize = () => {
            fitAddon.fit();
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            term.dispose();
            xtermRef.current = null;
        };
    }, []);

    useEffect(() => {
        if (!xtermRef.current || !isReady) return;

        const term = xtermRef.current;
        const lastMessage = terminalMessages[terminalMessages.length - 1];

        if (lastMessage) {
            const timestamp = new Date(lastMessage.timestamp).toLocaleTimeString();
            const prefix = `[${timestamp}] `;

            switch (lastMessage.type) {
                case 'stdout':
                    term.write(`\x1b[32m${prefix}\x1b[0m${lastMessage.content}\r\n`);
                    break;
                case 'stderr':
                    term.write(`\x1b[31m${prefix}\x1b[0m\x1b[31m${lastMessage.content}\x1b[0m\r\n`);
                    break;
                case 'system':
                    term.write(`\x1b[36m${prefix}\x1b[1m${lastMessage.content}\x1b[0m\r\n`);
                    break;
                case 'command':
                    term.write(`\x1b[33m${prefix}\x1b[1m> ${lastMessage.content}\x1b[0m\r\n`);
                    break;
            }
        }
    }, [terminalMessages, isReady]);

    const handleClear = () => {
        xtermRef.current?.clear();
        clearTerminal();
    };

    const handleDownload = () => {
        const content = terminalMessages
            .map(m => `[${new Date(m.timestamp).toISOString()}] [${m.type}] ${m.content}`)
            .join('\n');
        const blob = new Blob([content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `omniclaw-terminal-${Date.now()}.log`;
        a.click();
        URL.revokeObjectURL(url);
    };

    // Simulate incoming messages for demo
    useEffect(() => {
        if (!isReady) return;

        const messages = [
            { type: 'system' as const, content: 'Kernel Monitor initialized' },
            { type: 'stdout' as const, content: 'Scanning processes... 142 processes found' },
            { type: 'stdout' as const, content: 'Checking network connections...' },
            { type: 'stderr' as const, content: 'Warning: Suspicious outbound connection detected on port 4444' },
            { type: 'command' as const, content: 'netstat -an | grep ESTABLISHED' },
            { type: 'stdout' as const, content: 'tcp  192.168.1.100:54321  10.0.0.5:4444  ESTABLISHED' },
        ];

        let index = 0;
        const interval = setInterval(() => {
            if (index < messages.length) {
                addTerminalMessage({
                    id: crypto.randomUUID(),
                    timestamp: Date.now(),
                    ...messages[index],
                });
                index++;
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [isReady]);

    return (
        <div className={`flex flex-col transition-all duration-300 ${isExpanded ? 'h-[600px]' : 'h-[300px]'}`}>
            {/* Header */}
            <div className="flex items-center justify-between mb-2 px-1">
                <div className="flex items-center gap-2">
                    <TerminalIcon className="w-4 h-4 text-cyber-accent" />
                    <span className="text-sm font-semibold text-white">Live Execution Terminal</span>
                    <span className="text-xs text-gray-500 ml-2">xterm.js</span>
                </div>
                <div className="flex items-center gap-1">
                    <button
                        onClick={handleClear}
                        className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white"
                        title="Clear Terminal"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                    <button
                        onClick={handleDownload}
                        className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white"
                        title="Download Logs"
                    >
                        <Download className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400 hover:text-white"
                        title={isExpanded ? 'Minimize' : 'Maximize'}
                    >
                        {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                    </button>
                </div>
            </div>

            {/* Terminal Container */}
            <div className="flex-1 glass-card border border-cyber-accent/20 overflow-hidden relative">
                <div ref={terminalRef} className="w-full h-full p-2" />

                {/* Scanline Effect */}
                <div className="absolute inset-0 pointer-events-none opacity-[0.03]"
                    style={{
                        background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, #000 2px, #000 4px)',
                    }}
                />
            </div>
        </div>
    );
}
