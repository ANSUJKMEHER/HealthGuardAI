import { Wrench, CheckCircle, XCircle, Clock } from 'lucide-react';

const statusConfig = {
  RESOLVED: { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-900/30', border: 'border-green-800/40' },
  FAILED: { icon: XCircle, color: 'text-red-400', bg: 'bg-red-900/30', border: 'border-red-800/40' },
  DETECTED: { icon: Clock, color: 'text-yellow-400', bg: 'bg-yellow-900/30', border: 'border-yellow-800/40' },
  DIAGNOSED: { icon: Clock, color: 'text-blue-400', bg: 'bg-blue-900/30', border: 'border-blue-800/40' },
  FIX_ATTEMPTED: { icon: Wrench, color: 'text-purple-400', bg: 'bg-purple-900/30', border: 'border-purple-800/40' },
};

export default function IncidentLog({ incidents }) {
  return (
    <div className="border border-green-800/40 bg-black/50 h-full flex flex-col rounded">
      <div className="flex justify-between items-center p-4 border-b border-green-900/50">
        <h3 className="text-xs uppercase text-green-600 tracking-wider">Incident History</h3>
        <span className="text-[10px] text-green-800">{incidents.length} records</span>
      </div>
      <div className="flex-1 overflow-auto p-3 space-y-3">
        {incidents.map((incident, i) => {
          const config = statusConfig[incident.status] || statusConfig.DETECTED;
          const StatusIcon = config.icon;
          const time = incident.created_at
            ? new Date(incident.created_at).toLocaleTimeString()
            : '---';

          return (
            <div key={incident.id || i} className={`border ${config.border} ${config.bg} p-3 text-xs rounded transition-all hover:brightness-110`}>
              {/* Header */}
              <div className="flex justify-between mb-2">
                <span className="text-green-500 font-mono text-[10px]">{time}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 ${config.color}`}>
                  <StatusIcon className="w-3 h-3" />
                  {incident.status}
                </span>
              </div>

              {/* Diagnosis */}
              <div className="mb-2">
                <div className="text-[9px] text-green-700 uppercase tracking-widest">Root Cause</div>
                <div className="font-bold text-green-100 text-[11px]">{incident.root_cause || incident.failure_type}</div>
              </div>

              {/* Confidence */}
              {incident.confidence && (
                <div className="mb-2">
                  <div className="text-[9px] text-green-700 uppercase tracking-widest">Confidence</div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 bg-green-900/50 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-green-500 rounded-full transition-all duration-500"
                        style={{ width: `${(incident.confidence * 100)}%` }}
                      />
                    </div>
                    <span className="text-green-400 text-[10px] font-mono">{(incident.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
              )}

              {/* Action */}
              {incident.action_taken && (
                <div className="mt-2 border-t border-green-900/30 pt-2">
                  <div className="text-[9px] text-cyan-600 uppercase tracking-widest mb-0.5">Auto-Fix</div>
                  <div className="text-cyan-300 flex items-center gap-1 text-[11px]">
                    <Wrench className="w-3 h-3" /> {incident.action_taken}
                  </div>
                </div>
              )}

              {/* Metrics at detection */}
              {incident.metrics_snapshot?.cpu_percent != null && (
                <div className="mt-2 border-t border-green-900/30 pt-2 grid grid-cols-2 gap-1 text-[9px] text-green-700">
                  <span>CPU: {incident.metrics_snapshot.cpu_percent?.toFixed(1)}%</span>
                  <span>MEM: {incident.metrics_snapshot.memory_mb?.toFixed(1)}MB</span>
                </div>
              )}
            </div>
          );
        })}

        {incidents.length === 0 && (
          <div className="text-center opacity-20 mt-16 text-sm">No Incidents Detected</div>
        )}
      </div>
    </div>
  );
}
