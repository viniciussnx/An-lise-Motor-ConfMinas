import { memo, useState, useEffect } from 'react';
import { AlertTriangle, XOctagon, X } from 'lucide-react';

function AlertBanner({ status }) {
  const s = status?.overall_status;
  const key = `${s}-${(status?.anomalies || []).join('|')}`;
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    setDismissed(false);
  }, [key]);

  if (!s || s === 'normal' || s === 'no_data' || dismissed) return null;
  const crit = s === 'critical';

  return (
    <div className="rounded-2xl p-4 flex gap-3 items-start relative"
         style={{
           background: crit ? '#fef2f2' : '#fffbeb',
           border: `1px solid ${crit ? '#fecaca' : '#fde68a'}`,
           boxShadow: '0 2px 8px rgba(15,23,42,0.06)',
         }}>
      <div className="mt-0.5 shrink-0">
        {crit
          ? <XOctagon size={18} color="#ef4444" />
          : <AlertTriangle size={18} color="#f59e0b" />}
      </div>
      <div className="flex-1 pr-6">
        <p className="font-semibold text-sm" style={{ color: crit ? '#dc2626' : '#d97706' }}>
          {crit ? 'Alerta crítico — ação imediata necessária' : 'Atenção — verificação recomendada'}
        </p>
        <ul className="mt-1.5 space-y-0.5">
          {(status.anomalies || []).map((a, i) => (
            <li key={i} className="text-xs" style={{ color: crit ? '#b91c1c' : '#92400e' }}>• {a}</li>
          ))}
        </ul>
      </div>
      <button
        type="button"
        onClick={() => setDismissed(true)}
        aria-label="Fechar alerta"
        className="absolute top-3 right-3 p-1 rounded-lg"
        style={{ color: crit ? '#ef4444' : '#d97706' }}
      >
        <X size={16} />
      </button>
    </div>
  );
}

export default memo(AlertBanner);
