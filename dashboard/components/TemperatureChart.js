import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Title, Tooltip, Legend, Filler
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler);

const ALERT_THRESHOLD    = 75;
const CRITICAL_THRESHOLD = 85;

export default function TemperatureChart({ readings }) {
  const labels = readings.map(r => new Date(r.timestamp).toLocaleTimeString('pt-BR'));
  const temps  = readings.map(r => r.temperature);

  const data = {
    labels,
    datasets: [
      {
        label: 'Temperatura (°C)',
        data: temps,
        borderColor: '#f87171',
        backgroundColor: 'rgba(248,113,113,0.08)',
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.4,
        fill: true,
      },
      {
        label: `Alerta (${ALERT_THRESHOLD}°C)`,
        data: temps.map(() => ALERT_THRESHOLD),
        borderColor: '#f59e0b',
        borderWidth: 1.5,
        borderDash: [6, 4],
        pointRadius: 0,
        fill: false,
      },
      {
        label: `Crítico (${CRITICAL_THRESHOLD}°C)`,
        data: temps.map(() => CRITICAL_THRESHOLD),
        borderColor: '#ef4444',
        borderWidth: 1.5,
        borderDash: [3, 3],
        pointRadius: 0,
        fill: false,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { size: 11 } } },
      tooltip: { mode: 'index', intersect: false },
    },
    scales: {
      x: {
        ticks: { color: '#64748b', maxTicksLimit: 8, font: { size: 10 } },
        grid:  { color: 'rgba(255,255,255,0.04)' },
      },
      y: {
        min: 20,
        ticks: { color: '#64748b', callback: v => `${v}°C` },
        grid:  { color: 'rgba(255,255,255,0.04)' },
      },
    },
  };

  return (
    <div className="card p-5">
      <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4">
        🌡 Temperatura
      </h2>
      <div style={{ height: 200 }}>
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
