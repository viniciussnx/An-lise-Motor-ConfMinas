import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Tooltip, Legend, Filler
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

const ALERT_THRESHOLD    = 25;
const CRITICAL_THRESHOLD = 35;

export default function VibrationChart({ readings }) {
  const labels = readings.map(r => new Date(r.timestamp).toLocaleTimeString('pt-BR'));
  const vibs   = readings.map(r => r.vibration);

  const data = {
    labels,
    datasets: [
      {
        label: 'Vibração (mm/s)',
        data: vibs,
        borderColor: '#a78bfa',
        backgroundColor: 'rgba(167,139,250,0.08)',
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.4,
        fill: true,
      },
      {
        label: `Alerta (${ALERT_THRESHOLD} mm/s)`,
        data: vibs.map(() => ALERT_THRESHOLD),
        borderColor: '#f59e0b',
        borderWidth: 1.5,
        borderDash: [6, 4],
        pointRadius: 0,
        fill: false,
      },
      {
        label: `Crítico (${CRITICAL_THRESHOLD} mm/s)`,
        data: vibs.map(() => CRITICAL_THRESHOLD),
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
        min: 0,
        ticks: { color: '#64748b', callback: v => `${v} mm/s` },
        grid:  { color: 'rgba(255,255,255,0.04)' },
      },
    },
  };

  return (
    <div className="card p-5">
      <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4">
        📳 Vibração
      </h2>
      <div style={{ height: 200 }}>
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
