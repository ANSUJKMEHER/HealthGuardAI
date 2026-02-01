import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Activity, AlertTriangle, CheckCircle, Clock, Cpu, Server, Shield, Terminal, Zap, Play, Square, Wrench } from 'lucide-react';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [metrics, setMetrics] = useState([]);
  const [latestMetric, setLatestMetric] = useState(null);
  const [logs, setLogs] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [activeFailure, setActiveFailure] = useState(null);
  const [targetUrl, setTargetUrl] = useState('');
  const logsEndRef = useRef(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const res = await axios.get(`${API_URL}/metrics`);
        const data = res.data;

        setLatestMetric(data);
        setActiveFailure(data.active_failure);

        setMetrics(prev => {
          const newMetrics = [...prev, { ...data, time: new Date().toLocaleTimeString() }];
          if (newMetrics.length > 50) newMetrics.shift(); // Keep last 50 points
          return newMetrics;
        });

      } catch (e) {
        // System likely off
        setLatestMetric(null);
      }
    };

    const fetchIncidents = async () => {
      try {
        const res = await axios.get(`${API_URL}/incidents`);
        setIncidents(res.data);
      } catch (e) { }
    }

    const interval = setInterval(() => {
      fetchData();
      fetchIncidents();
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const startSystem = async () => {
    await axios.post(`${API_URL}/system/start`);
    setIsRunning(true);
  };

  const stopSystem = async () => {
    await axios.post(`${API_URL}/system/stop`);
    setIsRunning(false);
  };

  const injectFailure = async (type) => {
    await axios.post(`${API_URL}/inject_failure`, { type });
  };

  const updateTargetUrl = async () => {
    if (!targetUrl) return;
    try {
      await axios.post(`${API_URL}/monitor/url`, { url: targetUrl });
      alert(`Now monitoring: ${targetUrl}`);
    } catch (e) {
      alert("Failed to update target");
    }
  };

  return (
    <div className="min-h-screen bg-black text-green-500 font-mono p-6 relative overflow-hidden select-none">
      <div className="scanline"></div>

      {/* HEADER */}
      <header className="flex justify-between items-center mb-8 border-b border-green-900 pb-4">
        <div className="flex items-center gap-2">
          <Shield className="w-8 h-8 text-green-400" />
          <h1 className="text-2xl font-bold tracking-widest text-green-400">HealthGuard AI <span className="text-xs ml-2 opacity-50">v1.1.0</span></h1>
        </div>

        {/* URL MONITOR INPUT */}
        <div className="flex items-center gap-2 mx-4 flex-1 max-w-xl">
          <div className="flex w-full bg-green-900/10 border border-green-800">
            <span className="px-3 py-2 text-green-700 bg-green-900/20 border-r border-green-800 text-xs flex items-center">Target</span>
            <input
              type="text"
              value={targetUrl}
              onChange={(e) => setTargetUrl(e.target.value)}
              placeholder="https://example.com"
              className="flex-1 bg-transparent border-none outline-none text-green-400 px-3 py-2 text-sm placeholder-green-800"
            />
            <button onClick={updateTargetUrl} className="px-4 py-2 bg-green-900/30 hover:bg-green-900/50 text-green-400 text-xs border-l border-green-800 uppercase">
              Monitor
            </button>
          </div>
        </div>

        <div className="flex gap-4">
          <button onClick={startSystem} className="flex items-center gap-2 px-4 py-2 bg-green-900/30 border border-green-600 hover:bg-green-900/50 transition-colors uppercase text-xs">
            <Play className="w-4 h-4" /> Start System
          </button>
          <button onClick={stopSystem} className="flex items-center gap-2 px-4 py-2 bg-red-900/30 border border-red-600 hover:bg-red-900/50 transition-colors uppercase text-xs">
            <Square className="w-4 h-4" /> Stop System
          </button>
          <button onClick={() => window.open(`${API_URL}/export/incidents`, '_blank')} className="flex items-center gap-2 px-4 py-2 bg-blue-900/30 border border-blue-600 hover:bg-blue-900/50 transition-colors uppercase text-xs">
            📥 Export Incidents
          </button>
          <button onClick={() => window.open(`${API_URL}/export/logs`, '_blank')} className="flex items-center gap-2 px-4 py-2 bg-purple-900/30 border border-purple-600 hover:bg-purple-900/50 transition-colors uppercase text-xs">
            📊 Export Logs
          </button>
        </div>
      </header>

      {/* DASHBOARD GRID */}
      <div className="grid grid-cols-12 gap-6">

        {/* KPI METRICS */}
        <div className="col-span-12 md:col-span-3 space-y-4">
          <MetricCard label="CPU Usage" value={latestMetric?.cpu_percent} unit="%" icon={Cpu} color={latestMetric?.cpu_percent > 80 ? "text-red-500" : "text-green-400"} />
          <MetricCard label="Memory" value={latestMetric?.memory_mb} unit="MB" icon={Activity} color={latestMetric?.memory_mb > 300 ? "text-red-500" : "text-green-400"} />
          <MetricCard label="Response Time / Lag" value={latestMetric?.response_time_ms} unit="ms" icon={Activity} color={latestMetric?.response_time_ms > 500 ? "text-red-500" : "text-green-400"} />
          <MetricCard label="Error Rate" value={latestMetric?.error_rate_percent} unit="%" icon={AlertTriangle} color={latestMetric?.error_rate_percent > 5 ? "text-red-500" : "text-green-400"} />
        </div>

        {/* CHARTS */}
        <div className="col-span-12 md:col-span-6 space-y-6">
          <div className="border border-green-800 bg-black/50 p-4 h-[300px]">
            <h3 className="text-xs uppercase text-green-600 mb-2">Live Telemetry</h3>
            <ResponsiveContainer width="100%" height="90%">
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" stroke="#14532d" vertical={false} />
                <XAxis dataKey="time" hide />
                <YAxis domain={[0, 100]} stroke="#15803d" fontSize={10} />
                <Tooltip contentStyle={{ backgroundColor: '#000', border: '1px solid #166534' }} />
                <Line type="monotone" dataKey="cpu_percent" stroke="#22c55e" strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="memory_mb" stroke="#eab308" strokeWidth={1} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="border border-green-800 bg-black/50 p-4 h-[300px] overflow-hidden flex flex-col">
            <h3 className="text-xs uppercase text-green-600 mb-2 flex items-center gap-2"><Terminal className="w-3 h-3" /> System State</h3>
            <div className="flex-1 overflow-auto font-mono text-xs space-y-1 p-2 bg-black/80">
              {metrics.slice().reverse().map((m, i) => (
                <div key={i} className={`flex gap-4 ${m.active_failure ? 'text-red-500' : 'text-green-800'}`}>
                  <span className="opacity-50">{m.time}</span>
                  <span>CPU: {m.cpu_percent}%  |  MEM: {m.memory_mb}MB  |  ERR: {m.error_rate_percent}% {m.active_failure ? `<<< ${m.active_failure}` : ''}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* INCIDENT LOG */}
        <div className="col-span-12 md:col-span-3">
          <div className="border border-green-800 bg-black/50 h-full flex flex-col">
            <h3 className="text-xs uppercase text-green-600 p-4 border-b border-green-900">Incident History</h3>
            <div className="flex-1 overflow-auto p-4 space-y-4">
              {incidents.map((incident, i) => (
                <div key={i} className="border border-green-900 bg-green-900/10 p-3 text-xs">
                  <div className="flex justify-between mb-2">
                    <span className="text-green-400">{incident.timestamp.split(' ')[1]}</span>
                    <span className={`px-1 ${incident.status === 'RESOLVED' ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>{incident.status}</span>
                  </div>
                  <div className="mb-2">
                    <div className="text-[10px] text-green-600 uppercase tracking-wider">Diagnosis</div>
                    <div className="font-bold text-green-100">{incident.failure_type}</div>
                  </div>

                  {incident.action_taken && (
                    <div className="mt-2 text-xs border-t border-green-900/50 pt-2">
                      <div className="text-[10px] text-blue-400 uppercase tracking-wider mb-0.5">Auto-Fix Action</div>
                      <div className="text-blue-200 flex items-center gap-1">
                        <Wrench className="w-3 h-3" /> {incident.action_taken}
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {incidents.length === 0 && <div className="text-center opacity-30 mt-10">No Incidents Detected</div>}
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}

function MetricCard({ label, value, unit, icon: Icon, color }) {
  return (
    <div className="p-4 border border-green-800 bg-black/50 flex items-center justify-between">
      <div>
        <div className="text-xs text-green-700 uppercase">{label}</div>
        <div className={`text-2xl font-bold ${color} font-mono mt-1`}>
          {value !== undefined ? value : '--'}
          <span className="text-sm opacity-50 ml-1">{unit}</span>
        </div>
      </div>
      {Icon && <Icon className={`w-6 h-6 ${color} opacity-80`} />}
    </div>
  )
}

export default App
