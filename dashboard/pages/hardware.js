import { memo, useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import {
  Wifi, WifiOff, Thermometer, Activity, Zap, Cpu, ChevronLeft, Clock,
  RefreshCw, Power, Play, Square, Radio, Copy, Download, LogOut, User,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import useMotorData from '../hooks/useMotorData';
import { API, apiFetch, getUser, logout } from '../lib/api';
import ConfiMinasLogo from '../components/ConfiMinasLogo';

const OFF_STYLE = { bg: '#f8fafc', color: '#64748b', border: '#e2e8f0' };
const ON_STYLE = { bg: '#ecfdf5', color: '#059669', border: '#a7f3d0' };

function DeviceCard({
  icon: Icon, name, type, powerOn, value, unit, status, detail, lastSeen, statusText, alwaysShowValue,
}) {
  const stColor = { normal: '#10b981', alert: '#f59e0b', critical: '#ef4444', no_data: '#94a3b8' }[status] || '#94a3b8';
  const badge = statusText ?? (powerOn ? 'Online' : 'OFF');
  const badgeStyle = powerOn ? ON_STYLE : OFF_STYLE;

  return (
    <div className="card p-5 flex flex-col gap-4"
         style={{ borderColor: powerOn ? `${stColor}40` : '#e2e8f0' }}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center"
               style={{ background: powerOn ? `${stColor}15` : '#f8fafc',
                        border: `1px solid ${powerOn ? stColor + '30' : '#e2e8f0'}` }}>
            <Icon size={18} style={{ color: powerOn ? stColor : '#94a3b8' }} />
          </div>
          <div>
            <div className="font-semibold text-sm" style={{ color: '#0f172a' }}>{name}</div>
            <div className="text-xs" style={{ color: '#64748b' }}>{type}</div>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full font-semibold uppercase tracking-wide"
             style={{ background: badgeStyle.bg, color: badgeStyle.color, border: `1px solid ${badgeStyle.border}` }}>
          {powerOn ? <Wifi size={10} /> : <Power size={10} />}
          {badge}
        </div>
      </div>

      <div>
        {(powerOn || alwaysShowValue) && value != null ? (
          <div>
            <span className="mono text-3xl font-bold" style={{ color: stColor }}>{value}</span>
            {unit && <span className="text-sm ml-1.5" style={{ color: '#64748b' }}>{unit}</span>}
          </div>
        ) : (
          <div className="mono text-2xl font-bold" style={{ color: '#94a3b8' }}>0.00</div>
        )}
        {detail && <div className="text-xs mt-1" style={{ color: '#64748b' }}>{detail}</div>}
      </div>

      <div className="flex items-center gap-1.5 text-xs" style={{ color: '#64748b' }}>
        <Clock size={10} />
        {lastSeen ? `Atualizado ${formatDistanceToNow(lastSeen, { addSuffix: true, locale: ptBR })}` : 'Aguardando leituras'}
      </div>
    </div>
  );
}

function SimulatorPanel({ onChanged }) {
  const [sim, setSim] = useState({ running: false, profiles: [] });
  const [profile, setProfile] = useState('normal');
  const [cycle, setCycle] = useState(false);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');

  const fetchStatus = useCallback(async () => {
    try {
      const res = await apiFetch(`/api/simulator/status`);
      if (res.ok) {
        const data = await res.json();
        setSim(data);
        if (data.profile) setProfile(data.profile);
        if (data.cycle != null) setCycle(data.cycle);
      }
    } catch { /* API offline */ }
  }, []);

  useEffect(() => {
    fetchStatus();
    const t = setInterval(fetchStatus, 3000);
    return () => clearInterval(t);
  }, [fetchStatus]);

  const parseApiError = (data) => {
    const d = data?.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d) && d[0]?.msg) return d[0].msg;
    return 'Falha na operação';
  };

  const prepareEsp32 = async () => {
    setLoading(true);
    setMsg('');
    try {
      const res = await apiFetch(`/api/simulator/prepare-esp32`, { method: 'POST' });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(parseApiError(data));
      setMsg(data.message || 'Modo placa ESP32 — simulador parado');
      await fetchStatus();
      onChanged?.();
    } catch (e) {
      setMsg(e.message || 'Erro ao preparar modo placa');
    } finally {
      setLoading(false);
    }
  };

  const toggle = async () => {
    setLoading(true);
    setMsg('');
    try {
      if (!sim.running && sim.esp32_active) {
        throw new Error(
          'Placa ESP32 enviando dados. Clique em "Usar placa ESP32" ou rode ./start.sh --real'
        );
      }
      const url = sim.running
        ? `/api/simulator/stop`
        : `/api/simulator/start`;
      const res = await apiFetch(url, {
        method: 'POST',
        body: sim.running ? undefined : JSON.stringify({ profile, cycle }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(parseApiError(data));
      setMsg(data.message || (sim.running ? 'Simulador parado' : 'Simulador iniciado'));
      await fetchStatus();
      onChanged?.();
    } catch (e) {
      setMsg(e.message || 'Erro ao controlar simulador');
    } finally {
      setLoading(false);
    }
  };

  const profiles = sim.profiles?.length
    ? sim.profiles
    : [
        { id: 'normal', label: 'Operação Normal' },
        { id: 'wear', label: 'Desgaste Progressivo' },
        { id: 'failure', label: 'Falha Iminente' },
        { id: 'overload', label: 'Sobrecarga Elétrica' },
      ];

  return (
    <section className="card p-6" style={{ borderTop: '3px solid #3b6cf4' }}>
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-5">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl flex items-center justify-center"
               style={{ background: '#eff4ff', border: '1px solid #bfdbfe' }}>
            <Radio size={20} style={{ color: '#2563eb' }} />
          </div>
          <div>
            <h2 className="text-base font-bold" style={{ color: '#0f172a' }}>Simulador de Sensores</h2>
            <p className="text-sm mt-0.5" style={{ color: '#64748b' }}>
              Envia leituras ao backend como se fosse a placa ESP32 (demonstração sem hardware).
            </p>
          </div>
        </div>
        <span className="text-xs px-3 py-1.5 rounded-full font-semibold self-start"
              style={{
                background: sim.running ? '#ecfdf5' : '#f8fafc',
                color: sim.running ? '#059669' : '#64748b',
                border: `1px solid ${sim.running ? '#a7f3d0' : '#e2e8f0'}`,
              }}>
          {sim.running ? `● Rodando${sim.profile_label ? ` — ${sim.profile_label}` : ''}` : '○ Parado'}
        </span>
      </div>

      {sim.esp32_active && (
        <p className="text-xs mb-4 px-3 py-2 rounded-lg"
           style={{ background: '#ecfdf5', color: '#047857', border: '1px solid #a7f3d0' }}>
          Placa ESP32 ativa — o simulador é encerrado automaticamente. Para usar o simulador, pare o envio da placa primeiro.
        </p>
      )}

      <div className="mb-4">
        <button type="button" onClick={prepareEsp32} disabled={loading} className="btn-ghost flex items-center gap-2 text-sm">
          <Cpu size={14} /> Usar placa ESP32 (parar simulador)
        </button>
      </div>

      <div className="flex flex-col sm:flex-row flex-wrap gap-4 items-end">
        <label className="flex flex-col gap-1.5 text-xs font-semibold" style={{ color: '#475569' }}>
          Perfil
          <select
            value={profile}
            onChange={(e) => setProfile(e.target.value)}
            disabled={sim.running || loading}
            className="rounded-xl px-3 py-2.5 text-sm min-w-[200px]"
            style={{ border: '1px solid #e2e8f0', background: sim.running ? '#f8fafc' : '#fff', color: '#0f172a' }}
          >
            {profiles.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
        </label>

        <label className="flex items-center gap-2 text-sm cursor-pointer pb-2.5" style={{ color: '#475569' }}>
          <input
            type="checkbox"
            checked={cycle}
            onChange={(e) => setCycle(e.target.checked)}
            disabled={sim.running || loading}
            className="rounded"
          />
          Ciclo automático de perfis
        </label>

        <button
          type="button"
          onClick={toggle}
          disabled={loading || (!sim.running && sim.esp32_active)}
          className="btn-primary flex items-center justify-center gap-2 px-6 py-2.5 min-w-[180px]"
          style={{
            background: sim.running ? '#fef2f2' : undefined,
            color: sim.running ? '#dc2626' : undefined,
            border: sim.running ? '1px solid #fecaca' : undefined,
          }}
        >
          {loading ? (
            'Aguarde...'
          ) : sim.running ? (
            <><Square size={14} /> Parar simulador</>
          ) : (
            <><Play size={14} /> Ligar simulador</>
          )}
        </button>
      </div>

      {msg && (
        <p className="text-xs mt-4 px-3 py-2 rounded-lg"
           style={{ background: '#f8fafc', color: '#475569', border: '1px solid #e2e8f0' }}>
          {msg}
        </p>
      )}
    </section>
  );
}

const ESP32Card = memo(function ESP32Card({ espLinked, hasData, lastSeen, readings, sourceLabel }) {
  const label = espLinked ? 'Conectada' : (hasData ? 'OFF' : 'Desconectada');
  const badgeStyle = espLinked ? ON_STYLE : OFF_STYLE;

  return (
    <div className="card p-5"
         style={{
           borderColor: espLinked ? 'rgba(16,185,129,0.35)' : '#e2e8f0',
           borderTop: espLinked ? '3px solid #059669' : undefined,
         }}>
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center"
               style={{ background: espLinked ? '#ecfdf5' : '#f8fafc',
                        border: `1px solid ${espLinked ? '#a7f3d0' : '#e2e8f0'}` }}>
            <Cpu size={22} style={{ color: espLinked ? '#059669' : '#94a3b8' }} />
          </div>
          <div>
            <div className="font-bold" style={{ color: '#0f172a' }}>ESP32</div>
            <div className="text-xs mt-0.5" style={{ color: '#64748b' }}>Microcontrolador de monitoramento</div>
          </div>
          <div className="flex items-center gap-2 text-sm px-3 py-1.5 rounded-lg font-semibold"
               style={{ background: badgeStyle.bg, color: badgeStyle.color, border: `1px solid ${badgeStyle.border}` }}>
            {espLinked ? <Wifi size={14} /> : <WifiOff size={14} />}
            {label}
          </div>
        </div>

        <div className="flex gap-6 text-xs flex-wrap">
          {[
            { label: 'Fonte', value: sourceLabel },
            { label: 'Última leitura', value: lastSeen ? lastSeen.toLocaleTimeString('pt-BR') : '—' },
          ].map(({ label: lbl, value }) => (
            <div key={lbl}>
              <div style={{ color: '#64748b' }}>{lbl}</div>
              <div className="mono font-semibold mt-0.5" style={{ color: espLinked ? '#059669' : '#94a3b8' }}>{value}</div>
            </div>
          ))}
        </div>
      </div>

      {espLinked && readings.length > 0 && (
        <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { key: 'temperature', label: 'Temp', unit: '°C', color: '#e07a5f' },
            { key: 'vibration',   label: 'Vibr', unit: 'mm/s', color: '#9b7fd4' },
            { key: 'current',     label: 'Corr', unit: 'A',    color: '#d4a843' },
            { key: 'voltage',     label: 'Tens', unit: 'V',    color: '#5b8fd4' },
          ].map(({ key, label, unit, color }) => (
            <div key={key} className="rounded-lg p-3"
                 style={{ background: '#f8fafc', border: '1px solid #e2e8f0' }}>
              <div className="text-xs mb-1" style={{ color: '#64748b' }}>{label}</div>
              <span className="mono text-lg font-bold" style={{ color }}>
                {(readings[readings.length - 1]?.[key] ?? 0).toFixed(key === 'voltage' ? 1 : 2)}
              </span>
              <span className="text-xs ml-1" style={{ color: '#64748b' }}>{unit}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

function ESP32SetupCard() {
  const [user, setUser] = useState(null);
  const [host, setHost] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setUser(getUser());
    if (typeof window !== 'undefined') {
      try {
        const u = new URL(API);
        setHost(u.hostname);
      } catch { setHost('localhost'); }
    }
  }, []);

  const copyHost = async () => {
    try {
      await navigator.clipboard.writeText(host);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {}
  };

  const downloadConfig = async () => {
    try {
      const res = await fetch(`${API}/api/esp32/config`);
      const text = await res.text();
      const blob = new Blob([text], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'config.h';
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (e) {
      alert('Falha ao baixar config.h: ' + e.message);
    }
  };

  return (
    <section className="card p-6" style={{ borderTop: '3px solid #059669' }}>
      <div className="flex items-start justify-between gap-3 mb-4 flex-wrap">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-xl flex items-center justify-center"
               style={{ background: '#ecfdf5', border: '1px solid #a7f3d0' }}>
            <Cpu size={20} style={{ color: '#059669' }} />
          </div>
          <div>
            <h2 className="text-base font-bold" style={{ color: '#0f172a' }}>Configurar Placa ESP32</h2>
            <p className="text-sm mt-0.5" style={{ color: '#64748b' }}>
              Use os passos abaixo para apontar sua placa real para este servidor.
            </p>
          </div>
        </div>
        <button onClick={downloadConfig} className="btn-primary">
          <Download size={12} /> Baixar config.h
        </button>
      </div>

      <ol className="space-y-3 text-sm" style={{ color: '#334155' }}>
        <li className="flex gap-3">
          <span className="w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center shrink-0"
                style={{ background: '#ecfdf5', color: '#059669', border: '1px solid #a7f3d0' }}>1</span>
          <div>
            <div className="font-semibold" style={{ color: '#0f172a' }}>Aponte para este servidor</div>
            <div className="mt-1 flex items-center gap-2 flex-wrap">
              <code className="mono text-xs px-2.5 py-1.5 rounded-md"
                    style={{ background: '#f1f5f9', border: '1px solid #e2e8f0', color: '#0f172a' }}>
                #define API_HOST "{host || 'localhost'}"
              </code>
              <button onClick={copyHost} className="btn-ghost text-xs">
                <Copy size={11} /> {copied ? 'Copiado' : 'Copiar IP'}
              </button>
            </div>
          </div>
        </li>
        <li className="flex gap-3">
          <span className="w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center shrink-0"
                style={{ background: '#eff4ff', color: '#2563eb', border: '1px solid #bfdbfe' }}>2</span>
          <div>
            <div className="font-semibold" style={{ color: '#0f172a' }}>Edite WiFi em <code className="mono">config.h</code></div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>
              Defina <code className="mono">WIFI_SSID</code> e <code className="mono">WIFI_PASSWORD</code> com sua rede.
            </div>
          </div>
        </li>
        <li className="flex gap-3">
          <span className="w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center shrink-0"
                style={{ background: '#fffbeb', color: '#d97706', border: '1px solid #fde68a' }}>3</span>
          <div>
            <div className="font-semibold" style={{ color: '#0f172a' }}>Grave o firmware</div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>
              Arduino IDE ou PlatformIO. Endpoint usado: <code className="mono">POST /api/readings</code> (sem token).
            </div>
          </div>
        </li>
        <li className="flex gap-3">
          <span className="w-6 h-6 rounded-full text-xs font-bold flex items-center justify-center shrink-0"
                style={{ background: '#fef2f2', color: '#dc2626', border: '1px solid #fecaca' }}>4</span>
          <div>
            <div className="font-semibold" style={{ color: '#0f172a' }}>Pare o simulador</div>
            <div className="text-xs mt-1" style={{ color: '#64748b' }}>
              Painel logo abaixo · botão "Usar placa ESP32". Assim que a placa enviar dados, o cabeçalho mostra "Conectada".
            </div>
          </div>
        </li>
      </ol>

      {user && (
        <p className="mt-4 text-xs px-3 py-2 rounded-lg"
           style={{ background: '#f8fafc', color: '#475569', border: '1px solid #e2e8f0' }}>
          Logado como <strong>{user.username}</strong>. O endpoint da placa é público (não precisa de token).
        </p>
      )}
    </section>
  );
}


export default function HardwarePage() {
  const { status, readings, online, lastAt, refresh, hasLiveData } = useMotorData();
  const [, setSimTick] = useState(0);
  const [user, setUser] = useState(null);
  useEffect(() => setUser(getUser()), []);

  const hasData = hasLiveData;
  const last = status?.last_reading;
  const motorRunning = hasData && status?.is_running;
  const isESP = last?.source === 'esp32';
  const espLinked = motorRunning && isESP;
  const sourceLabel = !hasData ? '—' : (isESP ? 'Placa' : 'Simulador');
  const lastSeen = hasData ? lastAt : null;

  const sensors = [
    { icon: Thermometer, name: 'Sensor de Temperatura', type: 'DHT22 / LM35', key: 'temperature', unit: '°C',
      statusKey: 'temp_status', detail: 'GPIO 4 — I2C / ADC' },
    { icon: Activity, name: 'Sensor de Vibração', type: 'SW-420 / ADXL345', key: 'vibration', unit: 'mm/s',
      statusKey: 'vib_status', detail: 'GPIO 35 — Digital / I2C' },
    { icon: Zap, name: 'Sensor de Corrente', type: 'SCT-013-030', key: 'current', unit: 'A',
      statusKey: 'current_status', detail: 'GPIO 32 — ADC (RMS)' },
    { icon: Zap, name: 'Sensor de Tensão', type: 'ZMPT101B / Divisor R', key: 'voltage', unit: 'V',
      statusKey: null, detail: 'GPIO 33 — ADC' },
  ];

  const fmt = (v, d = 2) => (motorRunning && v != null ? Number(v).toFixed(d) : '0.00');

  return (
    <>
      <Head><title>Hardware — Motor Monitor</title></Head>
      <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>

        <header className="sticky top-0 z-50 px-6 py-3 flex items-center justify-between"
                style={{ background: '#fff', borderBottom: '1px solid var(--border)', boxShadow: '0 1px 3px rgba(15,23,42,0.06)', minHeight: 60 }}>
          <div className="flex items-center gap-4 min-w-0">
            <ConfiMinasLogo height={40} maxWidth={200} />
            <a href="/" className="btn-ghost flex items-center gap-1 shrink-0">
              <ChevronLeft size={12} /> Dashboard
            </a>
            <span className="hidden md:inline font-semibold text-sm" style={{ color: '#0f172a' }}>
              Painel de Hardware
            </span>
          </div>
          <div className="flex items-center gap-3">
            <button type="button" onClick={refresh} className="btn-primary">
              <RefreshCw size={12} /> Atualizar
            </button>
            <div className="flex items-center gap-2 text-xs pl-2" style={{ borderLeft: '1px solid var(--border)' }}>
              <div className="w-2 h-2 rounded-full" style={{ background: online ? '#10b981' : '#ef4444' }} />
              <span style={{ color: online ? '#059669' : '#dc2626', fontWeight: 500 }}>
                {online ? `API Online · ${lastAt?.toLocaleTimeString('pt-BR')}` : 'API Offline'}
              </span>
            </div>
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

        <main className="px-6 py-6 max-w-screen-xl mx-auto space-y-5">
          <ESP32SetupCard />
          <ESP32Card
            hasData={hasData}
            espLinked={espLinked}
            lastSeen={lastSeen}
            readings={motorRunning ? readings : []}
            sourceLabel={sourceLabel}
          />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {sensors.map((s) => (
              <DeviceCard
                key={s.key}
                icon={s.icon}
                name={s.name}
                type={s.type}
                powerOn={motorRunning}
                value={fmt(last?.[s.key], s.key === 'voltage' ? 1 : 2)}
                unit={s.unit}
                status={motorRunning ? (s.statusKey ? status?.[s.statusKey] : 'normal') : 'no_data'}
                detail={s.detail}
                lastSeen={lastSeen}
              />
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <DeviceCard
              icon={Cpu}
              name="Motor"
              type="Trifásico WEG W22"
              powerOn={motorRunning}
              alwaysShowValue={hasData}
              value={hasData ? (motorRunning ? 'Operando' : 'Parado') : '0.00'}
              unit=""
              status={motorRunning ? status?.overall_status : 'no_data'}
              statusText={motorRunning ? 'Online' : 'OFF'}
              detail={`Fonte: ${sourceLabel} · GPIO 26 — Relé`}
              lastSeen={lastSeen}
            />

            <div className="card p-5 lg:col-span-2">
              <div className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: '#475569' }}>
                Guia de Conexão — ESP32
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {[
                  { pino: 'GPIO 4',  sensor: 'DHT22 DATA',         cor: '#e07a5f' },
                  { pino: 'GPIO 32', sensor: 'SCT-013 (corrente)',  cor: '#d4a843' },
                  { pino: 'GPIO 33', sensor: 'ZMPT101B (tensão)',   cor: '#5b8fd4' },
                  { pino: 'GPIO 35', sensor: 'SW-420 (vibração)',   cor: '#9b7fd4' },
                  { pino: 'GPIO 21', sensor: 'SDA — ADXL345',      cor: '#9b7fd4' },
                  { pino: 'GPIO 22', sensor: 'SCL — ADXL345',      cor: '#9b7fd4' },
                  { pino: 'GPIO 26', sensor: 'Relé motor',          cor: '#059669' },
                  { pino: '3.3V / GND', sensor: 'Alimentação',     cor: '#94a3b8' },
                ].map(({ pino, sensor, cor }) => (
                  <div key={pino} className="flex items-center gap-2 rounded-lg px-3 py-2"
                       style={{ background: '#f8fafc', border: '1px solid #e2e8f0' }}>
                    <span className="mono font-bold w-20 shrink-0" style={{ color: cor, fontSize: 10 }}>{pino}</span>
                    <span style={{ color: '#475569' }}>{sensor}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <SimulatorPanel onChanged={() => { refresh(); setSimTick((n) => n + 1); }} />
        </main>
      </div>
    </>
  );
}
