import { useState, useEffect } from 'react';
import Head from 'next/head';
import { ChevronLeft, Save, RotateCcw, LogOut, User } from 'lucide-react';
import ConfiMinasLogo from '../components/ConfiMinasLogo';
import { apiFetch, getUser, logout } from '../lib/api';

const DEFAULTS = {
  temp_alert: 75, temp_critical: 85,
  vib_alert: 25, vib_critical: 35,
  current_alert_pct: 20, current_critical_pct: 35,
  nominal_current: 8.0,
};

function SliderField({ label, name, value, min, max, step = 1, unit, color, onChange }) {
  const pct = ((value - min) / (max - min)) * 100;
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--text2)' }}>
          {label}
        </label>
        <div
          className="mono text-sm font-bold px-2.5 py-0.5 rounded-lg"
          style={{ background: `${color}15`, color, border: `1px solid ${color}30` }}
        >
          {value}{unit}
        </div>
      </div>
      <div className="relative h-2 rounded-full" style={{ background: 'var(--surface2)' }}>
        <div
          className="absolute top-0 left-0 h-full rounded-full transition-all"
          style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}60, ${color})` }}
        />
        <input
          type="range" min={min} max={max} step={step} value={value}
          onChange={(e) => onChange(name, parseFloat(e.target.value))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer h-full"
        />
        <div
          className="absolute top-1/2 -translate-y-1/2 w-4 h-4 rounded-full border-2 transition-all"
          style={{
            left: `calc(${pct}% - 8px)`,
            background: color,
            borderColor: 'var(--bg)',
            boxShadow: `0 0 8px ${color}80`,
          }}
        />
      </div>
      <div className="flex justify-between text-xs" style={{ color: 'var(--muted)' }}>
        <span>{min}{unit}</span><span>{max}{unit}</span>
      </div>
    </div>
  );
}

export default function ThresholdsPage() {
  const [vals, setVals] = useState(DEFAULTS);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [user, setUser] = useState(null);

  useEffect(() => {
    setUser(getUser());
    Promise.all([
      apiFetch(`/api/thresholds`).then((r) => r.ok ? r.json() : null).catch(() => null),
      apiFetch(`/api/status`).then((r) => r.ok ? r.json() : null).catch(() => null),
    ]).then(([t, s]) => {
      setVals((v) => ({
        ...v,
        ...(t || {}),
        nominal_current: s?.nominal_current ?? v.nominal_current,
      }));
    });
  }, []);

  const change = (name, val) => {
    setVals((v) => ({ ...v, [name]: val }));
    setSaved(false);
    setError('');
  };

  const save = async () => {
    setLoading(true);
    setError('');
    try {
      await apiFetch(`/api/motor/config`, {
        method: 'PUT',
        body: JSON.stringify({ nominal_current: vals.nominal_current }),
      });
      await apiFetch(`/api/thresholds`, {
        method: 'PUT',
        body: JSON.stringify({
          temp_alert: vals.temp_alert,
          temp_critical: vals.temp_critical,
          vib_alert: vals.vib_alert,
          vib_critical: vals.vib_critical,
          current_alert_pct: vals.current_alert_pct,
          current_critical_pct: vals.current_critical_pct,
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      setError(e.message || 'Erro ao salvar');
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setVals(DEFAULTS);
    setSaved(false);
  };

  const sections = [
    {
      title: 'Temperatura', color: '#f87171',
      fields: [
        { label: 'Limite de Alerta', name: 'temp_alert', min: 40, max: 90, unit: '°C' },
        { label: 'Limite Crítico',   name: 'temp_critical', min: 60, max: 110, unit: '°C' },
      ],
    },
    {
      title: 'Vibração', color: '#a78bfa',
      fields: [
        { label: 'Limite de Alerta', name: 'vib_alert', min: 5, max: 40, unit: ' mm/s' },
        { label: 'Limite Crítico',   name: 'vib_critical', min: 15, max: 60, unit: ' mm/s' },
      ],
    },
    {
      title: 'Corrente Elétrica', color: '#fbbf24',
      fields: [
        { label: 'Corrente Nominal do Motor', name: 'nominal_current', min: 1, max: 30, step: 0.5, unit: ' A' },
        { label: 'Desvio para Alerta',        name: 'current_alert_pct', min: 5, max: 40, unit: '%' },
        { label: 'Desvio para Crítico',       name: 'current_critical_pct', min: 10, max: 60, unit: '%' },
      ],
    },
  ];

  return (
    <>
      <Head><title>Limites — Motor Monitor</title></Head>
      <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>

        <header
          className="sticky top-0 z-50 px-6 py-3 flex items-center justify-between"
          style={{ background: '#fff', borderBottom: '1px solid var(--border)', boxShadow: '0 1px 3px rgba(15,23,42,0.06)', minHeight: 60 }}
        >
          <div className="flex items-center gap-4 min-w-0">
            <ConfiMinasLogo height={40} maxWidth={200} />
            <a href="/" className="btn-ghost flex items-center gap-1 shrink-0">
              <ChevronLeft size={12} /> Dashboard
            </a>
            <span className="hidden md:inline font-semibold text-sm" style={{ color: '#0f172a' }}>
              Limites de alarme
            </span>
          </div>
          <div className="flex gap-2 items-center">
            <button onClick={reset} className="btn-ghost">
              <RotateCcw size={11} /> Restaurar padrões
            </button>
            <button
              onClick={save}
              disabled={loading}
              className="btn-primary font-semibold"
              style={saved ? { background: '#ecfdf5', color: '#059669', borderColor: '#a7f3d0' } : {}}
            >
              <Save size={11} />
              {loading ? 'Salvando...' : saved ? 'Salvo!' : 'Salvar'}
            </button>
            {user && (
              <div className="flex items-center gap-2 pl-3" style={{ borderLeft: '1px solid var(--border)' }}>
                <span className="text-xs font-semibold flex items-center gap-1.5" style={{ color: '#475569' }}>
                  <User size={12} /> {user.username}
                </span>
                <button type="button" onClick={logout} className="btn-ghost flex items-center gap-1" title="Sair">
                  <LogOut size={12} /> Sair
                </button>
              </div>
            )}
          </div>
        </header>

        <main className="px-6 py-8 max-w-3xl mx-auto space-y-6">

          <div className="text-sm" style={{ color: 'var(--text2)' }}>
            Configure os limites de alerta e crítico para cada sensor. O sistema gerará alertas e
            Ordens de Serviço automáticas quando os valores ultrapassarem estes limites.
          </div>

          {error && (
            <div
              className="text-sm px-4 py-2.5 rounded-xl"
              style={{ background: '#fef2f2', color: '#b91c1c', border: '1px solid #fecaca' }}
            >
              {error}
            </div>
          )}

          {sections.map((sec) => (
            <div key={sec.title} className="card p-6 space-y-5">
              <div className="flex items-center gap-2 text-sm font-bold" style={{ color: sec.color }}>
                <div className="w-2 h-2 rounded-full" style={{ background: sec.color }} />
                {sec.title}
              </div>
              {sec.fields.map((f) => (
                <SliderField
                  key={f.name}
                  {...f}
                  value={vals[f.name]}
                  color={sec.color}
                  step={f.step || 1}
                  onChange={change}
                />
              ))}
            </div>
          ))}

          <div className="card p-5">
            <div className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: 'var(--text2)' }}>
              Regra de Geração de OS
            </div>
            <div className="space-y-2 text-xs" style={{ color: 'var(--text2)' }}>
              <div
                className="flex items-center gap-2 p-2 rounded-lg"
                style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}
              >
                <span style={{ color: '#ef4444' }}>●</span>
                <span>OS <strong style={{ color: '#ef4444' }}>CRÍTICA</strong>: qualquer sensor ultrapassar o limite crítico</span>
              </div>
              <div
                className="flex items-center gap-2 p-2 rounded-lg"
                style={{ background: 'rgba(245,158,11,0.08)', border: '1px solid rgba(245,158,11,0.2)' }}
              >
                <span style={{ color: '#f59e0b' }}>●</span>
                <span>OS <strong style={{ color: '#f59e0b' }}>ALTA</strong>: 2 ou mais sensores em estado de alerta</span>
              </div>
            </div>
            <div
              className="mt-4 p-3 rounded-lg text-xs"
              style={{ background: 'rgba(99,179,237,0.06)', color: 'var(--muted)', border: '1px solid var(--border)' }}
            >
              As alterações são aplicadas imediatamente no backend. Para persistir entre reinicializações,
              ajuste também os defaults em <code>backend/predictive.py</code>.
            </div>
          </div>

        </main>
      </div>
    </>
  );
}
