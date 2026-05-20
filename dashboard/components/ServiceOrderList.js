import { memo, useState } from 'react';
import { Download, CheckCircle2, Clock, Archive } from 'lucide-react';

const API = 'http://localhost:8000';

const PRIORITY = {
  critica: { label: 'Crítica', color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
  alta:    { label: 'Alta',    color: '#d97706', bg: '#fffbeb', border: '#fde68a' },
};

function OrderCard({ os, onConfirm, confirming }) {
  const p = PRIORITY[os.priority] || PRIORITY.alta;
  const isOpen = os.status === 'aberta';

  return (
    <div
      className="rounded-xl p-3.5 flex items-start justify-between gap-3 animate-fade-in"
      style={{
        background: '#fff',
        border: `1px solid ${isOpen ? '#d4dce8' : '#e2e8f0'}`,
        boxShadow: '0 1px 3px rgba(15,23,42,0.05)',
      }}
    >
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="mono text-xs font-bold" style={{ color: '#2563eb' }}>{os.os_number}</span>
          <span
            className="text-xs px-2 py-0.5 rounded-full font-semibold"
            style={{ background: p.bg, color: p.color, border: `1px solid ${p.border}` }}
          >
            {p.label}
          </span>
        </div>
        <div className="text-sm mt-1" style={{ color: '#475569', fontWeight: 500 }}>
          {new Date(os.created_at).toLocaleString('pt-BR')}
        </div>
        {os.closed_at && (
          <div className="text-xs mt-0.5" style={{ color: '#059669' }}>
            Finalizada em {new Date(os.closed_at).toLocaleString('pt-BR')}
          </div>
        )}
        <div className="text-xs mt-2 flex gap-4" style={{ color: '#64748b' }}>
          <span>{os.temperature?.toFixed(1)}°C</span>
          <span>{os.vibration?.toFixed(2)} mm/s</span>
          <span>{os.current?.toFixed(2)} A</span>
        </div>
      </div>

      <div className="flex flex-col gap-1.5 shrink-0">
        {os.has_pdf && (
          <a
            href={`${API}/api/service-orders/${os.id}/pdf`}
            download={`Ordem de Servico ${os.os_number}.pdf`}
            target="_blank"
            rel="noreferrer"
            className="flex items-center justify-center gap-1.5 text-xs px-3 py-2 rounded-lg font-medium"
            style={{ background: '#eff4ff', color: '#2563eb', border: '1px solid #bfdbfe' }}
          >
            <Download size={12} /> PDF
          </a>
        )}
        {isOpen && onConfirm && (
          <button
            type="button"
            onClick={() => onConfirm(os.id)}
            disabled={confirming === os.id}
            className="flex items-center justify-center gap-1.5 text-xs px-3 py-2 rounded-lg font-semibold"
            style={{
              background: confirming === os.id ? '#f1f5f9' : '#ecfdf5',
              color: confirming === os.id ? '#94a3b8' : '#059669',
              border: '1px solid #a7f3d0',
              cursor: confirming === os.id ? 'wait' : 'pointer',
            }}
          >
            <CheckCircle2 size={12} />
            {confirming === os.id ? '...' : 'Confirmar'}
          </button>
        )}
      </div>
    </div>
  );
}

function OrderColumn({ title, icon: Icon, count, accent, children, emptyText }) {
  return (
    <div className="card card-accent flex flex-col h-full min-h-[320px]" style={{ '--accent': accent }}>
      <div className="p-4 border-b flex items-center justify-between" style={{ borderColor: '#e8ecf1' }}>
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: `${accent}14`, color: accent }}
          >
            <Icon size={16} />
          </div>
          <div>
            <div className="text-sm font-bold" style={{ color: '#0f172a' }}>{title}</div>
            <div className="text-xs" style={{ color: '#64748b' }}>
              {count} registro{count !== 1 ? 's' : ''}
            </div>
          </div>
        </div>
        <span
          className="mono text-xs font-bold px-2.5 py-1 rounded-full"
          style={{ background: `${accent}12`, color: accent, border: `1px solid ${accent}30` }}
        >
          {count}
        </span>
      </div>
      <div className="p-4 flex-1 overflow-y-auto space-y-2" style={{ maxHeight: 340 }}>
        {count === 0 ? (
          <div className="flex flex-col items-center justify-center py-10 gap-2" style={{ color: '#94a3b8' }}>
            <Icon size={28} strokeWidth={1.5} />
            <span className="text-sm font-medium">{emptyText}</span>
          </div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}

function ServiceOrderList({ orders, onConfirm }) {
  const [confirming, setConfirming] = useState(null);

  const openOrders = orders.filter(o => o.status === 'aberta');
  const closedOrders = orders.filter(o => o.status === 'fechada');

  const handleConfirm = async (id) => {
    setConfirming(id);
    try {
      await onConfirm(id);
    } finally {
      setConfirming(null);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <OrderColumn
        title="OS Abertas"
        icon={Clock}
        count={openOrders.length}
        accent="#f59e0b"
        emptyText="Nenhuma OS aberta"
      >
        {openOrders.map(os => (
          <OrderCard key={os.id} os={os} onConfirm={handleConfirm} confirming={confirming} />
        ))}
      </OrderColumn>

      <OrderColumn
        title="OS Finalizadas"
        icon={Archive}
        count={closedOrders.length}
        accent="#059669"
        emptyText="Nenhuma OS finalizada"
      >
        {closedOrders.map(os => (
          <OrderCard key={os.id} os={os} />
        ))}
      </OrderColumn>
    </div>
  );
}

export default memo(ServiceOrderList);
