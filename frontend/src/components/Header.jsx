import { Shield, Wifi, WifiOff } from 'lucide-react';

export default function Header({ isRunning, connected, targetUrl, setTargetUrl, onStart, onStop, onUpdateTarget, onExportIncidents, onExportLogs }) {
  return (
    <header className="flex flex-col lg:flex-row justify-between items-start lg:items-center mb-8 border-b border-green-900/50 pb-4 gap-4">
      <div className="flex items-center gap-3">
        <div className="relative">
          <Shield className="w-8 h-8 text-green-400" />
          <span className={`absolute -top-1 -right-1 w-3 h-3 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></span>
        </div>
        <div>
          <h1 className="text-2xl font-bold tracking-widest text-green-400">
            HealthGuard AI
            <span className="text-[10px] ml-2 opacity-40 font-normal">v2.0.0</span>
          </h1>
          <div className="flex items-center gap-2 mt-0.5">
            {connected ? (
              <span className="flex items-center gap-1 text-[10px] text-green-600"><Wifi className="w-3 h-3" /> SSE CONNECTED</span>
            ) : (
              <span className="flex items-center gap-1 text-[10px] text-red-500"><WifiOff className="w-3 h-3" /> DISCONNECTED</span>
            )}
          </div>
        </div>
      </div>

      {/* Target URL Input */}
      <div className="flex items-center gap-2 flex-1 max-w-xl">
        <div className="flex w-full bg-green-900/10 border border-green-800 rounded">
          <span className="px-3 py-2 text-green-700 bg-green-900/20 border-r border-green-800 text-xs flex items-center whitespace-nowrap">
            Target
          </span>
          <input
            type="text"
            value={targetUrl}
            onChange={(e) => setTargetUrl(e.target.value)}
            placeholder="https://your-app.onrender.com/api"
            className="flex-1 bg-transparent border-none outline-none text-green-400 px-3 py-2 text-sm placeholder-green-800"
          />
          <button
            onClick={onUpdateTarget}
            className="px-4 py-2 bg-green-900/30 hover:bg-green-900/50 text-green-400 text-xs border-l border-green-800 uppercase transition-colors"
          >
            Monitor
          </button>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={onStart}
          disabled={isRunning}
          className="flex items-center gap-2 px-4 py-2 bg-green-900/30 border border-green-600 hover:bg-green-900/50 transition-all uppercase text-xs rounded disabled:opacity-30 disabled:cursor-not-allowed"
        >
          ▶ Start
        </button>
        <button
          onClick={onStop}
          disabled={!isRunning}
          className="flex items-center gap-2 px-4 py-2 bg-red-900/30 border border-red-600 hover:bg-red-900/50 transition-all uppercase text-xs rounded disabled:opacity-30 disabled:cursor-not-allowed"
        >
          ■ Stop
        </button>
        <button
          onClick={onExportIncidents}
          className="flex items-center gap-2 px-4 py-2 bg-blue-900/30 border border-blue-600 hover:bg-blue-900/50 transition-all uppercase text-xs rounded"
        >
          📥 Export
        </button>
      </div>
    </header>
  );
}
