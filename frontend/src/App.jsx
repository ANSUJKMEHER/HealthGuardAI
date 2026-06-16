import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Cpu, Activity, AlertTriangle, Gauge } from 'lucide-react';

import { API_URL } from './config';
import { useSSE } from './hooks/useSSE';
import Header from './components/Header';
import MetricCard from './components/MetricCard';
import LiveChart from './components/LiveChart';
import SystemLogs from './components/SystemLogs';
import IncidentLog from './components/IncidentLog';
import ChaosPanel from './components/ChaosPanel';

function App() {
  const { metrics, latestMetric, events, connected, connect, disconnect, clearMetrics } = useSSE();
  const [incidents, setIncidents] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [targetUrl, setTargetUrl] = useState('');

  // Poll incidents (these don't need SSE, simple REST is fine)
  useEffect(() => {
    const fetchIncidents = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/v1/incidents`);
        setIncidents(res.data);
      } catch (e) { /* System likely off */ }
    };

    const interval = setInterval(fetchIncidents, 3000);
    fetchIncidents();
    return () => clearInterval(interval);
  }, []);

  // Check initial system status
  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/v1/system/status`);
        setIsRunning(res.data.engine_running);
        if (res.data.target_url) {
          setTargetUrl(res.data.target_url);
        }
        if (res.data.engine_running) {
          connect();
        }
      } catch (e) { /* Server not up yet */ }
    };
    checkStatus();
  }, [connect]);

  const startSystem = useCallback(async () => {
    try {
      await axios.post(`${API_URL}/api/v1/system/start`);
      setIsRunning(true);
      connect();
    } catch (e) {
      alert('Failed to start system. Is the backend running?');
    }
  }, [connect]);

  const stopSystem = useCallback(async () => {
    try {
      await axios.post(`${API_URL}/api/v1/system/stop`);
      setIsRunning(false);
      disconnect();
    } catch (e) {
      alert('Failed to stop system');
    }
  }, [disconnect]);

  const injectFailure = useCallback(async (type) => {
    try {
      await axios.post(`${API_URL}/api/v1/inject_failure`, { type });
    } catch (e) {
      alert(`Failed to inject: ${type}`);
    }
  }, []);

  const updateTargetUrl = useCallback(async () => {
    if (!targetUrl) return;
    try {
      await axios.post(`${API_URL}/api/v1/monitor/url`, { url: targetUrl });
    } catch (e) {
      alert('Failed to update target URL');
    }
  }, [targetUrl]);

  const exportIncidents = useCallback(() => {
    window.open(`${API_URL}/api/v1/export/incidents`, '_blank');
  }, []);

  return (
    <div className="min-h-screen bg-[#030712] text-green-500 font-mono p-4 lg:p-6 relative overflow-hidden select-none">
      {/* Background grid effect */}
      <div className="fixed inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: 'linear-gradient(rgba(34,197,94,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(34,197,94,0.3) 1px, transparent 1px)',
          backgroundSize: '40px 40px'
        }}
      />

      {/* Scanline effect */}
      <div className="scanline"></div>

      <div className="relative z-10 max-w-[1600px] mx-auto">
        <Header
          isRunning={isRunning}
          connected={connected}
          targetUrl={targetUrl}
          setTargetUrl={setTargetUrl}
          onStart={startSystem}
          onStop={stopSystem}
          onUpdateTarget={updateTargetUrl}
          onExportIncidents={exportIncidents}
        />

        {/* Dashboard Grid */}
        <div className="grid grid-cols-12 gap-4 lg:gap-6">

          {/* Left Column: Metrics + Chaos */}
          <div className="col-span-12 lg:col-span-3 space-y-4">
            <MetricCard label="CPU Usage" value={latestMetric?.cpu_percent} unit="%" icon={Cpu} threshold={50} />
            <MetricCard label="Memory" value={latestMetric?.memory_mb} unit="MB" icon={Activity} threshold={100} />
            <MetricCard label="Latency" value={latestMetric?.response_time_ms} unit="ms" icon={Gauge} threshold={2000} />
            <MetricCard label="Error Rate" value={latestMetric?.error_rate_percent} unit="%" icon={AlertTriangle} threshold={1} />
            <ChaosPanel onInject={injectFailure} disabled={!isRunning} />
          </div>

          {/* Center Column: Charts + Logs */}
          <div className="col-span-12 lg:col-span-6 space-y-4">
            <LiveChart metrics={metrics} />
            <SystemLogs metrics={metrics} events={events} />
          </div>

          {/* Right Column: Incidents */}
          <div className="col-span-12 lg:col-span-3">
            <IncidentLog incidents={incidents} />
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-8 text-center text-[10px] text-green-900 border-t border-green-900/20 pt-4">
          HealthGuard AI v2.0.0 — Autonomous Infrastructure Sentinel
          {' '} | {' '}
          <span className="text-green-700">
            {isRunning ? '🟢 Engine Running' : '🔴 Engine Stopped'}
            {' '} • {' '}
            {connected ? '📡 SSE Connected' : '📡 SSE Disconnected'}
          </span>
        </footer>
      </div>
    </div>
  );
}

export default App;
