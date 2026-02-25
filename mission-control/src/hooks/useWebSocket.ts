import { useEffect, useRef, useState, useCallback } from 'react';
import type { WebSocketPayload } from '@/types';

interface UseWebSocketOptions {
    url: string;
    onMessage?: (data: any) => void;
    onConnect?: () => void;
    onDisconnect?: () => void;
    onError?: (error: Event) => void;
    reconnectAttempts?: number;
    reconnectInterval?: number;
}

export function useWebSocket({
    url,
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectAttempts = 5,
    reconnectInterval = 3000,
}: UseWebSocketOptions) {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const ws = useRef<WebSocket | null>(null);
    const reconnectCount = useRef(0);
    const reconnectTimer = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        if (ws.current?.readyState === WebSocket.OPEN) return;

        setIsConnecting(true);

        try {
            ws.current = new WebSocket(url);

            ws.current.onopen = () => {
                setIsConnected(true);
                setIsConnecting(false);
                reconnectCount.current = 0;
                onConnect?.();
            };

            ws.current.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    onMessage?.(data);
                } catch (e) {
                    onMessage?.(event.data);
                }
            };

            ws.current.onclose = () => {
                setIsConnected(false);
                setIsConnecting(false);
                onDisconnect?.();

                if (reconnectCount.current < reconnectAttempts) {
                    reconnectTimer.current = setTimeout(() => {
                        reconnectCount.current++;
                        connect();
                    }, reconnectInterval);
                }
            };

            ws.current.onerror = (error) => {
                onError?.(error);
                ws.current?.close();
            };
        } catch (error) {
            setIsConnecting(false);
            onError?.(error as Event);
        }
    }, [url, onMessage, onConnect, onDisconnect, onError, reconnectAttempts, reconnectInterval]);

    const disconnect = useCallback(() => {
        if (reconnectTimer.current) {
            clearTimeout(reconnectTimer.current);
        }
        ws.current?.close();
    }, []);

    const send = useCallback((payload: WebSocketPayload) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify(payload));
            return true;
        }
        return false;
    }, []);

    useEffect(() => {
        connect();
        return () => disconnect();
    }, [connect, disconnect]);

    return {
        isConnected,
        isConnecting,
        connect,
        disconnect,
        send,
    };
}
