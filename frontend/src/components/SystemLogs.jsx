import { Terminal } from 'lucide-react';

export default function SystemLogs({ metrics, events }) {
  // Combine metrics log + agent events into unified feed
  const agentEventLabels = {
    anomaly_detected: { emoji: '⚠️', color: 'text-yellow-500', label: 'ANOMALY' },
    diagnosis_complete: { emoji: '🔍', color: 'text-blue-400', label: 'DIAGNOSIS' },
    fix_applied: { emoji: '🛠️', color: 'text-purple-400', label: 'FIX' },
    incident_resolved: { emoji: '✅', color: 'text-green-400', label: 'RESOLVED' },
    system_started: { emoji: '🟢', color: 'text-green-500', label: 'STARTED' },
    system_stopped: { emoji: '🔴', color: 'text-red-500', label: 'STOPPED' },
    error: { emoji: '💥', color: 'text-red-500', label: 'ERROR' },
  };

  return (
    <div className="border border-green-800/40 bg-black/50 p-4 h-[300px] overflow-hidden flex flex-col rounded">
      <h3 className="text-xs uppercase text-green-600 mb-2 flex items-center gap-2 tracking-wider">
        <Terminal className="w-3 h-3" /> Agent Activity Feed
      </h3>
      <div className="flex-1 overflow-auto font-mono text-[11px] space-y-0.5 p-2 bg-black/80 rounded scrollbar-thin">
        {/* Agent Events (most recent first) */}
        {events.slice().reverse().map((evt, i) => {
          const meta = agentEventLabels[evt.type] || { emoji: '📌', color: 'text-gray-400', label: evt.type };
          return (
            <div key={`evt-${i}`} className={`flex gap-3 ${meta.color} py-0.5`}>
              <span className="opacity-50 w-16 shrink-0">{evt.timestamp}</span>
              <span className="w-5">{meta.emoji}</span>
              <span className="font-bold w-20 shrink-0">[{meta.label}]</span>
              <span className="opacity-80 truncate">
                {evt.type === 'diagnosis_complete' && evt.data?.root_cause
                  ? `Root Cause: ${evt.data.root_cause} (${(evt.data.confidence * 100).toFixed(0)}% confidence)`
                  : evt.type === 'fix_applied' && evt.data?.action
                  ? `Action: ${evt.data.action}`
                  : evt.type === 'anomaly_detected'
                  ? `CPU: ${evt.data?.cpu_percent}% | MEM: ${evt.data?.memory_mb}MB`
                  : JSON.stringify(evt.data)}
              </span>
            </div>
          );
        })}

        {/* Metric stream (subtle, dimmed) */}
        {metrics.slice().reverse().slice(0, 15).map((m, i) => (
          <div key={`m-${i}`} className={`flex gap-4 ${m.error_rate_percent > 0 ? 'text-red-800' : 'text-green-900'}`}>
            <span className="opacity-40 w-16 shrink-0">{m.time}</span>
            <span>CPU: {m.cpu_percent?.toFixed(1)}% | MEM: {m.memory_mb?.toFixed(1)}MB | LAT: {m.response_time_ms?.toFixed(0)}ms | ERR: {m.error_rate_percent}%</span>
          </div>
        ))}

        {events.length === 0 && metrics.length === 0 && (
          <div className="text-center opacity-20 mt-16">Waiting for data...</div>
        )}
      </div>
    </div>
  );
}
