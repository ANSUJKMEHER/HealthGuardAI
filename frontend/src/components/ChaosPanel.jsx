import { useState } from 'react';
import { Flame, Cpu, MemoryStick, Wifi, Clock, Ban, Zap } from 'lucide-react';

const failures = [
  { type: 'MEMORY_LEAK', label: 'Memory Leak', icon: MemoryStick, color: 'from-pink-600 to-rose-700', desc: 'Allocates 10MB/request' },
  { type: 'CPU_SPIKE', label: 'CPU Spike', icon: Cpu, color: 'from-red-600 to-orange-600', desc: 'Burns 100% CPU core' },
  { type: 'ERROR_BURST', label: 'Server Crash', icon: Flame, color: 'from-red-700 to-red-900', desc: 'HTTP 500 errors' },
  { type: 'LATENCY', label: 'High Latency', icon: Clock, color: 'from-yellow-600 to-amber-700', desc: '3s response delay' },
  { type: 'RATE_LIMIT', label: 'Rate Limit', icon: Ban, color: 'from-purple-600 to-violet-700', desc: 'HTTP 429 throttling' },
  { type: 'NETWORK_PARTITION', label: 'Network Split', icon: Wifi, color: 'from-blue-600 to-indigo-700', desc: '30% packet loss' },
];

export default function ChaosPanel({ onInject, disabled }) {
  const [lastInjected, setLastInjected] = useState(null);

  const handleInject = (type) => {
    onInject(type);
    setLastInjected(type);
    setTimeout(() => setLastInjected(null), 2000);
  };

  return (
    <div className="border border-green-800/40 bg-black/50 p-4 rounded">
      <div className="flex items-center gap-2 mb-3">
        <Zap className="w-4 h-4 text-yellow-500" />
        <h3 className="text-xs uppercase text-green-600 tracking-wider">Chaos Engineering</h3>
      </div>
      <p className="text-[10px] text-green-800 mb-3">Inject real failures into the target system. HealthGuard will detect and heal autonomously.</p>
      <div className="grid grid-cols-2 gap-2">
        {failures.map(({ type, label, icon: Icon, color, desc }) => (
          <button
            key={type}
            onClick={() => handleInject(type)}
            disabled={disabled}
            className={`flex items-center gap-2 p-2.5 rounded text-left text-xs font-medium
              bg-gradient-to-r ${color} text-white
              hover:brightness-110 hover:scale-[1.02] active:scale-95
              transition-all duration-150
              disabled:opacity-20 disabled:cursor-not-allowed
              ${lastInjected === type ? 'ring-2 ring-white/50 scale-95' : ''}`}
          >
            <Icon className="w-4 h-4 shrink-0" />
            <div>
              <div className="font-bold text-[11px]">{label}</div>
              <div className="text-[9px] opacity-70">{desc}</div>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
