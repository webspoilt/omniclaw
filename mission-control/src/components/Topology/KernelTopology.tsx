import { useEffect, useRef } from 'react';
import { Activity } from 'lucide-react';

export function KernelTopology() {
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let animationFrame: number;
        const particles: { x: number; y: number; vx: number; vy: number; life: number }[] = [];

        const resize = () => {
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetHeight;
        };

        window.addEventListener('resize', resize);
        resize();

        const draw = () => {
            ctx.fillStyle = 'rgba(10, 10, 10, 0.1)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            // Draw "Kernel Nodes"
            const nodes = [
                { id: 'fs', x: 0.2, y: 0.3, label: 'File System' },
                { id: 'net', x: 0.8, y: 0.3, label: 'Network' },
                { id: 'proc', x: 0.5, y: 0.7, label: 'Processes' },
                { id: 'mem', x: 0.5, y: 0.1, label: 'Memory' },
            ];

            nodes.forEach(node => {
                const nx = node.x * canvas.width;
                const ny = node.y * canvas.height;

                // Pulsing glow
                const pulse = Math.sin(Date.now() / 500) * 5 + 15;
                ctx.shadowBlur = pulse;
                ctx.shadowColor = '#00f2ff';
                
                ctx.beginPath();
                ctx.arc(nx, ny, 6, 0, Math.PI * 2);
                ctx.fillStyle = '#00f2ff';
                ctx.fill();
                ctx.shadowBlur = 0;

                ctx.font = '10px monospace';
                ctx.fillStyle = '#666';
                ctx.textAlign = 'center';
                ctx.fillText(node.label, nx, ny + 20);
            });

            // Particles representing "Kernel Events"
            if (Math.random() > 0.8) {
                const start = nodes[Math.floor(Math.random() * nodes.length)];
                const end = nodes[Math.floor(Math.random() * nodes.length)];
                if (start !== end) {
                    particles.push({
                        x: start.x * canvas.width,
                        y: start.y * canvas.height,
                        vx: (end.x - start.x) * 0.05,
                        vy: (end.y - start.y) * 0.05,
                        life: 1
                    });
                }
            }

            particles.forEach((p, i) => {
                p.x += p.vx * canvas.width;
                p.y += p.vy * canvas.height;
                p.life -= 0.02;

                ctx.beginPath();
                ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(0, 242, 255, ${p.life})`;
                ctx.fill();

                if (p.life <= 0) particles.splice(i, 1);
            });

            animationFrame = requestAnimationFrame(draw);
        };

        draw();
        return () => {
            window.removeEventListener('resize', resize);
            cancelAnimationFrame(animationFrame);
        };
    }, []);

    return (
        <div className="h-full w-full flex flex-col">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Activity className="w-4 h-4 text-cyber-accent animate-pulse" />
                    <h3 className="text-sm font-bold text-white tracking-widest uppercase">Kernel Topology</h3>
                </div>
                <span className="text-[10px] font-mono text-cyber-accent">LIVE_TELEMETRY</span>
            </div>
            <div className="flex-1 glass-panel border border-white/5 rounded-xl overflow-hidden relative">
                <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
                <div className="absolute top-2 right-2 flex flex-col items-end gap-1 pointer-events-none">
                    <div className="text-[8px] font-mono text-gray-500">HOOKS: 1,429</div>
                    <div className="text-[8px] font-mono text-gray-500">ANOMALIES: 0</div>
                </div>
            </div>
        </div>
    );
}
