import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';

export default function LiveChart({ metrics }) {
  return (
    <div className="border border-green-800/40 bg-black/50 p-4 h-[300px] rounded">
      <div className="flex justify-between items-center mb-2">
        <h3 className="text-xs uppercase text-green-600 tracking-wider">Live Telemetry</h3>
        <div className="flex gap-4 text-[10px]">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-green-500 inline-block"></span> CPU
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-yellow-500 inline-block"></span> Memory
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block"></span> Latency
          </span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height="88%">
        <AreaChart data={metrics}>
          <defs>
            <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#22c55e" stopOpacity={0.3} />
              <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="memGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#eab308" stopOpacity={0.2} />
              <stop offset="100%" stopColor="#eab308" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#14532d" vertical={false} />
          <XAxis dataKey="time" hide />
          <YAxis stroke="#15803d" fontSize={10} domain={[0, 'auto']} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#0a0a0a',
              border: '1px solid #166534',
              borderRadius: '6px',
              fontSize: '11px',
            }}
            labelStyle={{ color: '#22c55e' }}
          />
          <Area type="monotone" dataKey="cpu_percent" stroke="#22c55e" strokeWidth={2} fill="url(#cpuGrad)" dot={false} isAnimationActive={false} name="CPU %" />
          <Area type="monotone" dataKey="memory_mb" stroke="#eab308" strokeWidth={1.5} fill="url(#memGrad)" dot={false} isAnimationActive={false} name="Memory MB" />
          <Line type="monotone" dataKey="response_time_ms" stroke="#22d3ee" strokeWidth={1} dot={false} isAnimationActive={false} name="Latency ms" strokeDasharray="4 2" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
