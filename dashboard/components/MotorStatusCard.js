export default function MotorStatusCard({ status, onStart, onStop }) {
  if (!status) return null;

  const overallStatus = status.overall_status || 'no_data';
  const isRunning = status.is_running;
  const last = status.last_reading;

  const statusConfig = {
    normal:   { label: 'Normal',   color: 'text-green-400',  bg: 'bg-green-500',  ring: 'ring-green-500/40' },
    alert:    { label: 'Alerta',   color: 'text-amber-400',  bg: 'bg-amber-500',  ring: 'ring-amber-500/40' },
    critical: { label: 'Crítico',  color: 'text-red-400',    bg: 'bg-red-500',    ring: 'ring-red-500/40'   },
    no_data:  { label: 'Sem Dado', color: 'text-slate-400',  bg: 'bg-slate-500',  ring: 'ring-slate-500/40' },
  };

  const cfg = statusConfig[overallStatus] || statusConfig.no_data;

  return (
    <div className="card p-5">
      <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4">Status do Motor</h2>

      {/* Indicador visual */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-4">
          <div className={`relative flex items-center justify-center w-16 h-16 rounded-full ring-4 ${cfg.ring} bg-slate-800`}>
            <div className={`w-8 h-8 rounded-full ${cfg.bg} ${overallStatus === 'critical' ? 'pulse-red' : ''}`} />
          </div>
          <div>
            <div className={`text-2xl font-bold ${cfg.color}`}>{cfg.label}</div>
            <div className="text-sm text-slate-400 mt-0.5">
              {isRunning ? '⚙️ Operando' : '⏹ Parado'}
            </div>
          </div>
        </div>

        {/* Botões de controle */}
        <div className="flex gap-2">
          <button
            onClick={onStart}
            disabled={isRunning}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-green-600 hover:bg-green-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ▶ Ligar
          </button>
          <button
            onClick={onStop}
            disabled={!isRunning}
            className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-700 hover:bg-red-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            ■ Parar
          </button>
        </div>
      </div>

      {/* Valores rápidos */}
      {last && (
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: 'Temperatura', value: `${last.temperature?.toFixed(1)}°C`, s: status.temp_status },
            { label: 'Vibração',    value: `${last.vibration?.toFixed(2)} mm/s`, s: status.vib_status },
            { label: 'Corrente',    value: `${last.current?.toFixed(2)} A`,      s: status.current_status },
            { label: 'Tensão',      value: `${last.voltage?.toFixed(1)} V`,      s: 'normal' },
          ].map(({ label, value, s }) => (
            <div key={label} className="bg-slate-800/60 rounded-lg px-3 py-2">
              <div className="text-xs text-slate-500">{label}</div>
              <div className={`text-sm font-semibold status-${s}`}>{value}</div>
            </div>
          ))}
        </div>
      )}

      {/* Fonte */}
      {last && (
        <div className="mt-3 text-xs text-slate-600 text-right">
          Fonte: {last.source === 'esp32' ? '📡 ESP32 Real' : '🖥 Simulador'} ·{' '}
          {new Date(last.timestamp).toLocaleTimeString('pt-BR')}
        </div>
      )}
    </div>
  );
}
