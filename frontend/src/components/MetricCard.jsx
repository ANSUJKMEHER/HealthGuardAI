export default function MetricCard({ label, value, unit, icon: Icon, color, threshold }) {
  const isAlert = threshold && value > threshold;
  const displayColor = isAlert ? 'text-red-500' : (color || 'text-green-400');
  const borderColor = isAlert ? 'border-red-800/60' : 'border-green-800/40';
  const bgColor = isAlert ? 'bg-red-950/20' : 'bg-black/50';

  return (
    <div className={`p-4 border ${borderColor} ${bgColor} flex items-center justify-between rounded transition-all duration-500 ${isAlert ? 'shadow-[0_0_15px_rgba(239,68,68,0.15)]' : ''}`}>
      <div>
        <div className="text-[10px] text-green-700 uppercase tracking-wider">{label}</div>
        <div className={`text-2xl font-bold ${displayColor} font-mono mt-1 transition-colors duration-300`}>
          {value !== undefined && value !== null ? (
            typeof value === 'number' ? value.toFixed(1) : value
          ) : '--'}
          <span className="text-xs opacity-40 ml-1">{unit}</span>
        </div>
      </div>
      <div className={`${displayColor} opacity-60`}>
        {Icon && <Icon className="w-6 h-6" />}
      </div>
    </div>
  );
}
