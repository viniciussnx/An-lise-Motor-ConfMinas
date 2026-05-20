import { memo, useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ReferenceLine, ResponsiveContainer,
} from 'recharts';
import { format } from 'date-fns';

const LINE_COLORS = {
  temperature: '#e07a5f',
  vibration:   '#9b7fd4',
  current:     '#d4a843',
};

const CHART_MARGIN = { top: 6, right: 6, left: 0, bottom: 0 };
const MAX_POINTS = 28;

const TooltipBody = memo(function TooltipBody({ active, payload, unit, extraLabel, extraDivisor }) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#fff',
      border: '1px solid #e2e8f0',
      borderRadius: 10,
      padding: '8px 12px',
      fontSize: 12,
      boxShadow: '0 4px 12px rgba(15,23,42,0.08)',
    }}>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color, fontFamily: 'JetBrains Mono, monospace', fontWeight: 600, fontSize: 12 }}>
          {i === 1 && extraLabel
            ? `${extraLabel}: ${(p.value * (extraDivisor || 1)).toFixed(1)}`
            : `${p.value?.toFixed(2)} ${unit}`}
        </div>
      ))}
    </div>
  );
});

function SensorChartInner({
  readings, dataKey, label, unit, hasData,
  alertVal, criticalVal, icon,
  extraKey, extraColor, extraLabel, extraDivisor,
  yMin, yMax,
}) {
  const lineColor = LINE_COLORS[dataKey] || '#64748b';
  const gradId = `grad-${dataKey}`;

  const data = useMemo(() => {
    if (!hasData || !readings.length) {
      return [{ time: '--', value: 0, extra: extraKey ? 0 : undefined }];
    }
    const slice = readings.length > MAX_POINTS ? readings.slice(-MAX_POINTS) : readings;
    return slice.map((r) => ({
      time: format(new Date(r.timestamp), 'HH:mm'),
      value: r[dataKey] ?? 0,
      extra: extraKey ? (r[extraKey] ?? 0) / (extraDivisor || 1) : undefined,
    }));
  }, [readings, dataKey, extraKey, extraDivisor, hasData]);

  const yDomain = useMemo(() => [yMin ?? 0, yMax ?? 100], [yMin, yMax]);

  const displayLast = useMemo(() => {
    if (!hasData || !readings.length) return '0.00';
    const v = readings[readings.length - 1]?.[dataKey] ?? 0;
    return Number(v).toFixed(2);
  }, [hasData, readings, dataKey]);

  return (
    <div className="card card-chart p-5" style={{ minHeight: 268, contentVisibility: 'auto' }}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2.5">
          <div style={{
            width: 32, height: 32, borderRadius: 10,
            background: `${lineColor}18`,
            border: `1px solid ${lineColor}40`,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: lineColor,
          }}>
            {icon}
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>{label}</div>
            {(alertVal != null || criticalVal != null) && (
              <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>
                Alerta {alertVal}{unit} · Crítico {criticalVal}{unit}
              </div>
            )}
          </div>
        </div>
        <div className="mono" style={{ fontSize: 22, fontWeight: 700, color: '#0f172a', lineHeight: 1 }}>
          {displayLast}
          <span style={{ fontSize: 11, fontWeight: 500, color: '#64748b', marginLeft: 4 }}>{unit}</span>
        </div>
      </div>

      <div className="chart-inner" style={{ height: 190 }}>
        <ResponsiveContainer width="100%" height="100%" debounce={120}>
          <AreaChart data={data} margin={CHART_MARGIN}>
            <defs>
              <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={lineColor} stopOpacity={0.28} />
                <stop offset="100%" stopColor={lineColor} stopOpacity={0} />
              </linearGradient>
              {extraKey && (
                <linearGradient id={`grad-${extraKey}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={extraColor || '#5b8fd4'} stopOpacity={0.18} />
                  <stop offset="100%" stopColor={extraColor || '#5b8fd4'} stopOpacity={0} />
                </linearGradient>
              )}
            </defs>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 10, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              interval="preserveStartEnd"
              minTickGap={48}
              dy={4}
            />
            <YAxis
              domain={yDomain}
              tick={{ fontSize: 10, fill: '#64748b' }}
              tickLine={false}
              axisLine={false}
              width={36}
              allowDataOverflow
            />
            <Tooltip
              content={<TooltipBody unit={unit} extraLabel={extraLabel} extraDivisor={extraDivisor} />}
              isAnimationActive={false}
              cursor={{ stroke: lineColor, strokeWidth: 1, strokeOpacity: 0.3 }}
            />
            {alertVal != null && (
              <ReferenceLine y={alertVal} stroke="#d4a843" strokeDasharray="4 6" strokeWidth={1} strokeOpacity={0.7} />
            )}
            {criticalVal != null && (
              <ReferenceLine y={criticalVal} stroke="#e07a5f" strokeDasharray="4 6" strokeWidth={1} strokeOpacity={0.7} />
            )}
            <Area
              type="monotone"
              dataKey="value"
              stroke={lineColor}
              strokeWidth={2}
              fill={`url(#${gradId})`}
              dot={false}
              isAnimationActive={false}
              connectNulls
              activeDot={{ r: 4, strokeWidth: 2, stroke: '#fff', fill: lineColor }}
            />
            {extraKey && (
              <Area
                type="monotone"
                dataKey="extra"
                stroke={extraColor || '#5b8fd4'}
                strokeWidth={1.5}
                strokeOpacity={0.7}
                fill={`url(#grad-${extraKey})`}
                dot={false}
                isAnimationActive={false}
                connectNulls
                activeDot={false}
              />
            )}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function propsEqual(prev, next) {
  if (prev.hasData !== next.hasData) return false;
  if (prev.dataKey !== next.dataKey) return false;
  if (prev.readings !== next.readings) {
    const pl = prev.readings?.length ?? 0;
    const nl = next.readings?.length ?? 0;
    if (pl !== nl) return false;
    if (nl && prev.readings[nl - 1]?.id !== next.readings[nl - 1]?.id) return false;
    if (nl && prev.readings[nl - 1]?.[prev.dataKey] !== next.readings[nl - 1]?.[next.dataKey]) return false;
  }
  return (
    prev.alertVal === next.alertVal &&
    prev.criticalVal === next.criticalVal &&
    prev.yMin === next.yMin &&
    prev.yMax === next.yMax
  );
}

export default memo(SensorChartInner, propsEqual);
