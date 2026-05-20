import { useCallback, useMemo, memo } from 'react';
import Head from 'next/head';
import { Thermometer, Activity, Zap, Cpu, Bell, RefreshCw, Play, Square, Settings } from 'lucide-react';
import useMotorData, { API } from '../hooks/useMotorData';
import SensorChart from '../components/SensorChart';
import StatusGauge from '../components/StatusGauge';
import ServiceOrderList from '../components/ServiceOrderList';
import AlertBanner from '../components/AlertBanner';
import DashboardHeader from '../components/DashboardHeader';

const STATUS_CFG = {
  normal:   { label: 'Normal',   color: '#059669', bg: '#ecfdf5', border: '#a7f3d0' },
  alert:    { label: 'Alerta',   color: '#d97706', bg: '#fffbeb', border: '#fde68a' },
  critical: { label: 'Crítico',  color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
  no_data:  { label: 'Sem dado', color: '#94a3b8', bg: '#f8fafc', border: '#e2e8f0' },
  stopped:  { label: 'Parado',   color: '#64748b', bg: '#f8fafc', border: '#e2e8f0' },
};

const MetricCard = memo(function MetricCard({ icon: Icon, label, value, unit, status, sub }) {
  const cfg = STATUS_CFG[status] || STATUS_CFG.no_data;
  return (
    <div className="card card-accent p-5 flex flex-col gap-3" style={{ '--accent': cfg.color }}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2" style={{ fontSize: 11, fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          <Icon size={14} style={{ color: cfg.color }} />
          {label}
        </div>
        <span className="text-xs px-2 py-0.5 rounded-full font-semibold"
              style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.border}` }}>
          {cfg.label}
        </span>
      </div>
      <div className="flex items-end gap-1.5">
        <span className="mono text-3xl font-bold leading-none" style={{ color: '#0f172a' }}>{value}</span>
        <span className="text-sm mb-0.5" style={{ color: '#64748b' }}>{unit}</span>
      </div>
      {sub && <div className="text-xs" style={{ color: '#64748b' }}>{sub}</div>}
    </div>
  );
});

const MotorStatus = memo(function MotorStatus({ status, hasData, onStart, onStop }) {
  const running = hasData && status?.is_running;
  const src = status?.last_reading?.source;

  const cfg = running
    ? STATUS_CFG.normal
    : (hasData ? STATUS_CFG.stopped : STATUS_CFG.no_data);

  const motorLabel = running ? 'Operando' : (hasData ? 'Parado' : 'Sem dado');
  const sourceLabel = !hasData ? '—' : (src === 'esp32' ? 'Placa' : 'Simulador');

  return (
    <div className="card card-accent p-5 flex flex-col gap-4" style={{ '--accent': cfg.color }}>
      <div className="flex items-center justify-between">
        <span style={{ fontSize: 11, fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Motor
        </span>
        <span className="text-xs px-2 py-0.5 rounded-full font-medium"
              style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0' }}>
          {sourceLabel}
        </span>
      </div>
      <div className="flex items-center gap-4">
        <div className="relative flex items-center justify-center" style={{ width: 56, height: 56 }}>
          <div className="absolute inset-0 rounded-full" style={{ background: cfg.bg, border: `2px solid ${cfg.border}` }} />
          <div className="relative w-10 h-10 rounded-full flex items-center justify-center" style={{ background: '#fff' }}>
            <Cpu size={20} style={{ color: cfg.color }} />
          </div>
        </div>
        <div>
          <div style={{ fontSize: 18, fontWeight: 700, color: cfg.color }}>
            {motorLabel}
          </div>
          <div className="text-sm mt-0.5" style={{ color: '#64748b' }}>
            {hasData ? (running ? 'Em operação' : 'Motor desligado') : 'Aguardando leituras'}
          </div>
        </div>
      </div>
      <div className="flex gap-2">
        <button type="button" onClick={onStart} disabled={!hasData || running}
          className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-xs font-semibold"
          style={{
            background: running ? '#f8fafc' : '#ecfdf5',
            color: !hasData || running ? '#cbd5e1' : '#059669',
            border: `1px solid ${running || !hasData ? '#e2e8f0' : '#a7f3d0'}`,
            cursor: !hasData || running ? 'not-allowed' : 'pointer',
          }}>
          <Play size={12} /> Ligar
        </button>
        <button type="button" onClick={onStop} disabled={!hasData || !running}
          className="flex-1 flex items-center justify-center gap-1.5 py-2.5 rounded-xl text-xs font-semibold"
          style={{
            background: !running ? '#f8fafc' : '#fef2f2',
            color: !hasData || !running ? '#cbd5e1' : '#dc2626',
            border: `1px solid ${!running || !hasData ? '#e2e8f0' : '#fecaca'}`,
            cursor: !hasData || !running ? 'not-allowed' : 'pointer',
          }}>
          <Square size={12} /> Parar
        </button>
      </div>
    </div>
  );
});

const ChartsRow = memo(function ChartsRow({ readings, hasData, nominal }) {
  const currentAlert = nominal * 1.2;
  const currentCritical = nominal * 1.35;
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <SensorChart readings={readings} hasData={hasData} dataKey="temperature" label="Temperatura" unit="°C"
        alertVal={75} criticalVal={85} yMin={20} yMax={100} icon={<Thermometer size={14} />} />
      <SensorChart readings={readings} hasData={hasData} dataKey="vibration" label="Vibração" unit="mm/s"
        alertVal={25} criticalVal={35} yMin={0} yMax={50} icon={<Activity size={14} />} />
      <SensorChart readings={readings} hasData={hasData} dataKey="current" label="Corrente" unit="A"
        alertVal={currentAlert} criticalVal={currentCritical}
        yMin={0} yMax={Math.max(15, Math.ceil(nominal * 1.5))}
        extraKey="voltage" extraColor="#5b8fd4" extraLabel="Tensão" extraDivisor={40}
        icon={<Zap size={14} />} />
    </div>
  );
});

export default function Dashboard() {
  const { readings, status, orders, online, lastAt, refresh, hasLiveData } = useMotorData();

  const hasData = hasLiveData;
  const last = status?.last_reading;
  const nominal = status?.nominal_current ?? 8;

  const motorAction = useCallback(async (a) => {
    await fetch(`${API}/api/motor/${a}`, { method: 'POST' });
    refresh();
  }, [refresh]);

  const confirmOrder = useCallback(async (id) => {
    const res = await fetch(`${API}/api/service-orders/${id}/fechar`, { method: 'PATCH' });
    if (!res.ok) throw new Error('Falha ao confirmar OS');
    refresh();
  }, [refresh]);

  const openOrders = useMemo(() => orders.filter((o) => o.status === 'aberta').length, [orders]);
  const closedOrders = useMemo(() => orders.filter((o) => o.status === 'fechada').length, [orders]);

  const fmt = (v, d = 1) => (hasData && v != null ? Number(v).toFixed(d) : (d === 1 ? '0.0' : '0.00'));

  return (
    <>
      <Head>
        <title>ConfiMinas Engenharia — Monitoramento Preditivo</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
        <DashboardHeader
          online={online}
          lastAt={lastAt}
          openOrders={openOrders}
          onRefresh={refresh}
        />

        <main className="px-6 py-6 max-w-screen-2xl mx-auto space-y-5">
          <AlertBanner status={status} />

          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            <MotorStatus status={status} hasData={hasData}
              onStart={() => motorAction('start')}
              onStop={() => motorAction('stop')} />
            <MetricCard icon={Thermometer} label="Temperatura" value={fmt(last?.temperature, 1)} unit="°C"
              status={hasData ? status?.temp_status : 'no_data'} sub="Alerta >75°C · Crítico >85°C" />
            <MetricCard icon={Activity} label="Vibração" value={fmt(last?.vibration, 2)} unit="mm/s"
              status={hasData ? status?.vib_status : 'no_data'} sub="Alerta >25 · Crítico >35 mm/s" />
            <MetricCard icon={Zap} label="Corrente" value={fmt(last?.current, 2)} unit="A"
              status={hasData ? status?.current_status : 'no_data'} sub={`Nominal: ${nominal}A`} />
            <MetricCard icon={Zap} label="Tensão" value={fmt(last?.voltage, 1)} unit="V"
              status={hasData ? 'normal' : 'no_data'} sub="Trifásico 380V" />
          </div>

          <ChartsRow readings={readings} hasData={hasData} nominal={nominal} />

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <StatusGauge label="Temperatura" value={hasData ? last?.temperature : 0} unit="°C"
              min={20} max={100} alertAt={75} criticalAt={85} hasData={hasData} />
            <StatusGauge label="Vibração" value={hasData ? last?.vibration : 0} unit="mm/s"
              min={0} max={50} alertAt={25} criticalAt={35} hasData={hasData} />
            <StatusGauge label="Corrente" value={hasData ? last?.current : 0} unit="A"
              min={0} max={Math.max(15, Math.ceil(nominal * 1.5))}
              alertAt={nominal * 1.2} criticalAt={nominal * 1.35}
              hasData={hasData} decimals={2}
              sensorStatus={hasData ? status?.current_status : 'no_data'} />
          </div>

          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-base font-bold" style={{ color: '#0f172a' }}>Ordens de Serviço</h2>
              <span className="text-xs font-medium" style={{ color: '#64748b' }}>
                {openOrders} aberta{openOrders !== 1 ? 's' : ''} · {closedOrders} finalizada{closedOrders !== 1 ? 's' : ''}
              </span>
            </div>
            <ServiceOrderList orders={orders} onConfirm={confirmOrder} />
          </section>
        </main>
      </div>
    </>
  );
}
