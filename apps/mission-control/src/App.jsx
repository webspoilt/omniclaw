import React, { useState, useEffect } from 'react';

const Dashboard = () => {
  const [telemetry, setTelemetry] = useState([]);

  useEffect(() => {
    // WebSocket connection to Sovereign Sentinel Orchestrator
    const ws = new WebSocket('ws://localhost:8080');
    ws.onmessage = (event) => {
      setTelemetry((prev) => [...prev, JSON.parse(event.data)]);
    };
    return () => ws.close();
  }, []);

  return (
    <div style={{ background: '#0a0a0a', color: '#00ff00', minHeight: '100vh', padding: '20px', fontFamily: 'monospace' }}>
      <header style={{ borderBottom: '1px solid #00ff00', marginBottom: '20px' }}>
        <h1>🛰️ Sovereign Sentinel Mission Control</h1>
        <button style={{ background: 'red', color: 'white', border: 'none', padding: '10px' }}>KILL-SWITCH</button>
      </header>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        <section>
          <h2>📡 Real-time Telemetry</h2>
          <div style={{ border: '1px solid #333', padding: '10px', height: '400px', overflowY: 'auto' }}>
            {telemetry.map((log, i) => (
              <div key={i}>> {log.message}</div>
            ))}
            <div>> [INFO] Hybrid Hive Swarm active.</div>
            <div>> [SCAN] CVE-2026-1337 analysis in progress...</div>
          </div>
        </section>

        <section>
          <h2>🛡️ Kernel Bridge Status</h2>
          <div style={{ color: '#00ccff' }}>
            <div>BPF SENTINEL: ACTIVE</div>
            <div>STEALTH LAYER: ENABLED</div>
            <div>IP ROTATION: READY (TorHive)</div>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
