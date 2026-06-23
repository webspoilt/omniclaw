"use client";

import { useEffect, useState } from "react";
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

const generateData = () => {
  const data = [];
  const now = new Date().getTime();
  for (let i = 0; i < 30; i++) {
    data.push({
      time: new Date(now - (30 - i) * 1000).toLocaleTimeString([], { second: "2-digit", minute: "2-digit" }),
      throughput: Math.floor(Math.random() * 100) + 10,
      latency: Math.floor(Math.random() * 20) + 5,
    });
  }
  return data;
};

export function TelemetryOverlay() {
  const [data, setData] = useState(generateData());

  useEffect(() => {
    const interval = setInterval(() => {
      setData((current) => {
        const newData = [...current.slice(1)];
        const now = new Date();
        newData.push({
          time: now.toLocaleTimeString([], { second: "2-digit", minute: "2-digit" }),
          throughput: Math.floor(Math.random() * 100) + 10,
          latency: Math.floor(Math.random() * 20) + 5,
        });
        return newData;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full h-[300px] bg-background/50 border border-border rounded-xl p-6 relative overflow-hidden">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h4 className="text-sm font-semibold text-foreground">Live Telemetry</h4>
          <p className="text-xs text-muted-foreground">Queue Throughput & Execution Latency</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-xs font-mono text-muted-foreground">STREAMING</span>
        </div>
      </div>
      
      <div className="h-[200px] w-full min-h-0">
        <ResponsiveContainer width="100%" height={200}>
          <AreaChart data={data} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorThroughput" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#fff" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#fff" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <XAxis dataKey="time" stroke="#333" fontSize={10} tickMargin={10} />
            <YAxis stroke="#333" fontSize={10} />
            <Tooltip 
              contentStyle={{ backgroundColor: "#0a0a0a", border: "1px solid #333", borderRadius: "8px", fontSize: "12px" }}
              itemStyle={{ color: "#fff" }}
            />
            <Area type="monotone" dataKey="throughput" stroke="#fff" fillOpacity={1} fill="url(#colorThroughput)" isAnimationActive={false} />
            <Area type="monotone" dataKey="latency" stroke="#666" fillOpacity={0} isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
