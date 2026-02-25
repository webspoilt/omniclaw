import { useState, useRef, useEffect } from 'react';
import { useOmniClaw, toolCards } from '@/hooks/useOmniClaw';
import { useWebSocket } from '@/hooks/useWebSocket';
import {
    Send, Bot, User, Sparkles, MoreVertical,
    Paperclip, Mic, Command, X
} from 'lucide-react';
import type { ChatMessage } from '@/types';

export function ChatInterface() {
    const { activeTool, chatMessages, addChatMessage, connectionUrl } = useOmniClaw();
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);

    const { send } = useWebSocket({
        url: connectionUrl,
        onMessage: (data) => {
            if (data.type === 'chat_response') {
                addChatMessage({
                    id: crypto.randomUUID(),
                    timestamp: Date.now(),
                    role: 'assistant',
                    content: data.content,
                    toolId: activeTool || 'general',
                    metadata: data.metadata,
                });
                setIsTyping(false);
            }
        },
    });

    const activeToolData = toolCards.find(t => t.id === activeTool);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [chatMessages]);

    const handleSend = () => {
        if (!input.trim() || !activeTool) return;

        const message: ChatMessage = {
            id: crypto.randomUUID(),
            timestamp: Date.now(),
            role: 'user',
            content: input.trim(),
            toolId: activeTool,
        };

        addChatMessage(message);

        send({
            type: 'chat_message',
            payload: {
                message: input.trim(),
                toolId: activeTool,
                context: chatMessages.slice(-10),
            },
            timestamp: Date.now(),
            id: crypto.randomUUID(),
        });

        setInput('');
        setIsTyping(true);
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const filteredMessages = chatMessages.filter(m =>
        activeTool ? m.toolId === activeTool : true
    );

    return (
        <div className="h-full flex flex-col glass-card border border-white/10">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/10">
                <div className="flex items-center gap-3">
                    <div className={`
            w-10 h-10 rounded-lg flex items-center justify-center
            ${activeTool ? 'bg-gradient-to-br ' + activeToolData?.color : 'bg-gray-700'}
          `}>
                        {activeTool ? (
                            <Sparkles className="w-5 h-5 text-white" />
                        ) : (
                            <Bot className="w-5 h-5 text-gray-400" />
                        )}
                    </div>
                    <div>
                        <h3 className="font-semibold text-white">
                            {activeToolData?.name || 'General Assistant'}
                        </h3>
                        <p className="text-xs text-gray-400">
                            {activeTool ? 'Context-aware mode active' : 'Select a tool to begin'}
                        </p>
                    </div>
                </div>
                <button className="p-2 hover:bg-white/5 rounded-lg transition-colors">
                    <MoreVertical className="w-5 h-5 text-gray-400" />
                </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
                {filteredMessages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-500">
                        <Bot className="w-12 h-12 mb-4 opacity-20" />
                        <p className="text-sm">
                            {activeTool
                                ? `Start chatting with ${activeToolData?.name}`
                                : 'Activate a tool from the grid to start chatting'
                            }
                        </p>
                    </div>
                ) : (
                    filteredMessages.map((message) => (
                        <div
                            key={message.id}
                            className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
                        >
                            <div className={`
                w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                ${message.role === 'user'
                                    ? 'bg-cyber-accent/20'
                                    : 'bg-cyber-secondary/20'
                                }
              `}>
                                {message.role === 'user' ? (
                                    <User className="w-4 h-4 text-cyber-accent" />
                                ) : (
                                    <Bot className="w-4 h-4 text-cyber-secondary" />
                                )}
                            </div>
                            <div className={`
                max-w-[80%] rounded-2xl px-4 py-2.5
                ${message.role === 'user'
                                    ? 'bg-cyber-accent/10 border border-cyber-accent/30 text-white'
                                    : 'bg-white/5 border border-white/10 text-gray-200'
                                }
              `}>
                                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                                {message.metadata && (
                                    <div className="mt-2 flex items-center gap-3 text-xs text-gray-500">
                                        {message.metadata.tokens && (
                                            <span>{message.metadata.tokens} tokens</span>
                                        )}
                                        {message.metadata.latency && (
                                            <span>{message.metadata.latency}ms</span>
                                        )}
                                        {message.metadata.engine && (
                                            <span className="text-cyber-accent">{message.metadata.engine}</span>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    ))
                )}

                {isTyping && (
                    <div className="flex gap-3">
                        <div className="w-8 h-8 rounded-lg bg-cyber-secondary/20 flex items-center justify-center">
                            <Bot className="w-4 h-4 text-cyber-secondary" />
                        </div>
                        <div className="bg-white/5 border border-white/10 rounded-2xl px-4 py-3">
                            <div className="flex gap-1">
                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                            </div>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-4 border-t border-white/10">
                <div className="flex items-end gap-2">
                    <div className="flex-1 relative">
                        <textarea
                            ref={inputRef}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder={activeTool ? "Type your message..." : "Activate a tool first..."}
                            disabled={!activeTool}
                            className="
                w-full bg-cyber-dark/50 border border-white/10 rounded-xl
                px-4 py-3 pr-12 text-sm text-white placeholder-gray-500
                focus:outline-none focus:border-cyber-accent/50 focus:ring-1 focus:ring-cyber-accent/30
                resize-none transition-all
                disabled:opacity-50 disabled:cursor-not-allowed
              "
                            rows={1}
                            style={{ minHeight: '44px', maxHeight: '120px' }}
                        />
                        <div className="absolute right-2 bottom-2 flex items-center gap-1">
                            <button
                                className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400"
                                disabled={!activeTool}
                            >
                                <Paperclip className="w-4 h-4" />
                            </button>
                            <button
                                className="p-1.5 hover:bg-white/10 rounded-lg transition-colors text-gray-400"
                                disabled={!activeTool}
                            >
                                <Mic className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || !activeTool}
                        className="
              p-3 bg-cyber-accent/20 border border-cyber-accent/50 rounded-xl
              text-cyber-accent hover:bg-cyber-accent/30
              disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-cyber-accent/20
              transition-all
            "
                    >
                        <Send className="w-5 h-5" />
                    </button>
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-gray-500">
                    <div className="flex items-center gap-2">
                        <span className="flex items-center gap-1">
                            <Command className="w-3 h-3" />
                            <span>Enter to send</span>
                        </span>
                        <span>•</span>
                        <span>Shift+Enter for new line</span>
                    </div>
                    <span>{input.length} chars</span>
                </div>
            </div>
        </div>
    );
}
