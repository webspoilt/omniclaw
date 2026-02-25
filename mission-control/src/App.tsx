import { useState, useEffect } from 'react';
import { Header } from '@/components/Layout/Header';
import { Sidebar } from '@/components/Layout/Sidebar';
import { ToolGrid } from '@/components/Grid/ToolGrid';
import { SwarmPanel } from '@/components/Swarm/SwarmPanel';
import { LiveTerminal } from '@/components/Terminal/LiveTerminal';
import { ChatInterface } from '@/components/Chat/ChatInterface';
import { useOmniClaw } from '@/hooks/useOmniClaw';
import { Command, X, ChevronUp, ChevronDown } from 'lucide-react';

function App() {
    const [activeView, setActiveView] = useState('dashboard');
    const [isChatOpen, setIsChatOpen] = useState(false);
    const { activeTool } = useOmniClaw();

    // Auto-open chat when tool is activated
    useEffect(() => {
        if (activeTool) {
            setIsChatOpen(true);
        }
    }, [activeTool]);

    return (
        <div className="h-screen w-screen bg-cyber-black grid-bg flex flex-col overflow-hidden">
            {/* CRT Scanline Overlay */}
            <div className="scanline-overlay" />

            {/* Header */}
            <Header />

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Sidebar */}
                <Sidebar activeView={activeView} onViewChange={setActiveView} />

                {/* Primary Content Area */}
                <main className="flex-1 flex flex-col min-w-0">
                    {/* Top Section: Grid + Swarm */}
                    <div className="flex-1 flex overflow-hidden">
                        {/* Tool Grid */}
                        <div className="flex-1 p-6 overflow-hidden">
                            <ToolGrid />
                        </div>

                        {/* Swarm Panel (Right Side) */}
                        <div className="w-80 p-6 pl-0 border-l border-white/5 hidden xl:block">
                            <SwarmPanel />
                        </div>
                    </div>

                    {/* Bottom Section: Terminal */}
                    <div className="h-80 border-t border-white/10 p-6 pt-2">
                        <LiveTerminal />
                    </div>
                </main>

                {/* Slide-out Chat Panel */}
                <div
                    className={`
            fixed right-0 top-14 bottom-0 w-96 glass-panel border-l border-white/10
            transform transition-transform duration-300 ease-out z-40
            ${isChatOpen ? 'translate-x-0' : 'translate-x-full'}
          `}
                >
                    <div className="h-full flex flex-col">
                        {/* Chat Toggle Handle (visible when closed) */}
                        <button
                            onClick={() => setIsChatOpen(!isChatOpen)}
                            className={`
                absolute left-0 top-1/2 -translate-x-full -translate-y-1/2
                p-3 glass-panel border border-white/10 rounded-l-xl
                text-cyber-accent hover:bg-white/5 transition-all
                ${isChatOpen ? 'hidden' : 'flex'}
              `}
                        >
                            <Command className="w-5 h-5" />
                        </button>

                        {/* Chat Header */}
                        <div className="flex items-center justify-between p-4 border-b border-white/10">
                            <h3 className="font-semibold text-white">Chat Interface</h3>
                            <button
                                onClick={() => setIsChatOpen(false)}
                                className="p-1.5 hover:bg-white/10 rounded-lg transition-colors"
                            >
                                <X className="w-4 h-4 text-gray-400" />
                            </button>
                        </div>

                        {/* Chat Content */}
                        <div className="flex-1 overflow-hidden">
                            <ChatInterface />
                        </div>
                    </div>
                </div>
            </div>

            {/* Mobile Swarm Toggle */}
            <button
                className="xl:hidden fixed bottom-4 right-4 p-3 bg-cyber-accent/20 border border-cyber-accent/50 rounded-full text-cyber-accent z-50"
                onClick={() => { }}
            >
                <ChevronUp className="w-5 h-5" />
            </button>

            {/* Connection Status Toast */}
            <div className="fixed bottom-4 left-4 z-50">
                {/* Add connection status notifications here */}
            </div>
        </div>
    );
}

export default App;
