import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement,
  LineElement, Tooltip, Legend, Filler
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

export default function ElectricalChart({ readings, nominalCurrent = 8.0 }) {
  const labels    = readings.map(r => new Date(r.timestamp).toLocaleTimeString('pt-BR'));
  const currents  = readings.map(r => r.current);
  const voltages  = readings.map(r => r.voltage / 10); // escala secundária visual

  const data = {
    labels,
    datasets: [
      {
        label: 'Corrente (A)',
        data: currents,
        borderColor: '#fbbf24',
        backgroundColor: 'rgba(251,191,36,0.06)',
        borderWidth: 2,
        pointRadius: 2,
        tension: 0.4,
        fill: true,
        yAxisID: 'y',
      },
      {
        label: 'Nominal (A)',
        data: currents.map(() => nominalCurrent),
        borderColor: '#22c55e',
        borderWidth: 1.5,
        borderDash: [5, 4],
        pointRadius: 0,
        fill: false,
        yAxisID: 'y',
      },
      {
        label: 'Tensão ÷10 (V/10)',
        data: voltages,
        borderColor: '#60a5fa',
        backgroundColor: 'rgba(96,165,250,0.04)',
        borderWidth: 1.5,
        pointRadius: 1,
        tension: 0.4,
        fill: false,
        yAxisID: 'y',
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 300 },
    plugins: {
      legend: { labels: { color: '#94a3b8', font: { size: 11 } } },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          label: ctx => {
            if (ctx.dataset.label.includes('Tensão'))
              return `Tensão: ${(ctx.raw * 10).toFixed(1)} V`;
            return `${ctx.dataset.label}: ${ctx.raw?.toFixed(2)}`;
          },
        },
      },
    },
    scales: {
      x: {
        ticks: { color: '#64748b', maxTicksLimit: 8, font: { size: 10 } },
        grid:  { color: 'rgba(255,255,255,0.04)' },
      },
      y: {
        ticks: { color: '#64748b' },
        grid:  { color: 'rgba(255,255,255,0.04)' },
      },
    },
  };

  return (
    <div className="card p-5">
      <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-widest mb-4">
        ⚡ Elétrico — Corrente &amp; Tensão
      </h2>
      <div style={{ height: 200 }}>
        <Line data={data} options={options} />
      </div>
    </div>
  );
}
