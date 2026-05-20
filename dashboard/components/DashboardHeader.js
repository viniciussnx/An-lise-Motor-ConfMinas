import { memo } from 'react';
import { Activity, Bell, RefreshCw, Settings } from 'lucide-react';

function DashboardHeader({ online, lastAt, openOrders, onRefresh }) {
  return (
    <header className="sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between"
            style={{
              background: '#fff',
              borderBottom: '1px solid var(--border)',
              boxShadow: '0 1px 3px rgba(15,23,42,0.06)',
            }}>
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center"
             style={{ background: 'linear-gradient(135deg, #3b6cf4, #6366f1)' }}>
          <Activity size={15} color="#fff" />
        </div>
        <div>
          <span className="font-bold text-sm" style={{ color: '#0f172a' }}>Motor Monitor</span>
          <span className="text-xs ml-2" style={{ color: '#64748b' }}>CONFIMINAS</span>
        </div>
      </div>

      <div className="flex items-center gap-3">
        {openOrders > 0 && (
          <div className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-full font-medium"
               style={{ background: '#fffbeb', color: '#d97706', border: '1px solid #fde68a' }}>
            <Bell size={12} /> {openOrders} OS abertas
          </div>
        )}
        <a href="/hardware" className="btn-ghost">Hardware</a>
        <a href="/thresholds" className="btn-ghost flex items-center gap-1">
          <Settings size={12} /> Limites
        </a>
        <button type="button" onClick={onRefresh} className="btn-primary">
          <RefreshCw size={12} /> Atualizar
        </button>
        <div className="flex items-center gap-2 text-xs pl-2" style={{ borderLeft: '1px solid var(--border)' }}>
          <div className="w-2 h-2 rounded-full" style={{ background: online ? '#10b981' : '#ef4444' }} />
          <span style={{ color: online ? '#059669' : '#dc2626', fontWeight: 500 }}>
            {online ? `Online · ${lastAt?.toLocaleTimeString('pt-BR')}` : 'Offline'}
          </span>
        </div>
      </div>
    </header>
  );
}

export default memo(DashboardHeader);
