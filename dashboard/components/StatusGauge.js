import { memo, useMemo } from 'react';

/** Semicírculo superior: t=0 (min) à esquerda, t=1 (max) à direita */
const VB = { w: 220, h: 132, cx: 110, cy: 108, r: 76, sw: 10 };

function polar(t) {
  const a = Math.PI + t * Math.PI;
  return {
    x: VB.cx + VB.r * Math.cos(a),
    y: VB.cy + VB.r * Math.sin(a),
  };
}

/** Arco menor sempre pelo topo (largeArc = 0) */
function arc(t0, t1) {
  if (t1 <= t0 + 0.0001) return '';
  const p0 = polar(t0);
  const p1 = polar(t1);
  return `M ${p0.x.toFixed(1)} ${p0.y.toFixed(1)} A ${VB.r} ${VB.r} 0 0 1 ${p1.x.toFixed(1)} ${p1.y.toFixed(1)}`;
}

const STATUS_COLOR = {
  normal: '#10b981',
  alert: '#f59e0b',
  critical: '#ef4444',
  no_data: '#94a3b8',
};

function StatusGaugeInner({
  label, value, unit, min, max, alertAt, criticalAt, hasData,
  sensorStatus, decimals = 1,
}) {
  const displayValue = hasData && value != null ? Number(value) : 0;
  const range = max - min || 1;

  const { pct, alertT, criticalT, color } = useMemo(() => {
    const p = Math.min(Math.max((displayValue - min) / range, 0), 1);
    const fromStatus = sensorStatus && STATUS_COLOR[sensorStatus];
    const fromValue = !hasData
      ? '#94a3b8'
      : displayValue >= criticalAt
        ? '#ef4444'
        : displayValue >= alertAt
          ? '#f59e0b'
          : '#10b981';
    return {
      pct: p,
      alertT: Math.min(Math.max((alertAt - min) / range, 0), 1),
      criticalT: Math.min(Math.max((criticalAt - min) / range, 0), 1),
      color: fromStatus || fromValue,
    };
  }, [displayValue, min, range, alertAt, criticalAt, hasData, sensorStatus]);

  const tip = polar(pct);
  const left = polar(0);
  const right = polar(1);

  return (
    <div className="card card-accent p-5 flex flex-col items-center" style={{ '--accent': color }}>
      <p
        style={{
          margin: '0 0 6px',
          fontSize: 11,
          fontWeight: 600,
          color: '#475569',
          textTransform: 'uppercase',
          letterSpacing: '0.06em',
        }}
      >
        {label}
      </p>

      <div style={{ width: '100%', maxWidth: 240, position: 'relative', height: 118 }}>
        <svg
          viewBox={`0 0 ${VB.w} ${VB.h}`}
          width="100%"
          height="118"
          style={{ display: 'block' }}
          role="img"
          aria-label={`${label}: ${displayValue.toFixed(1)} ${unit}`}
        >
          {/* Trilho */}
          <path d={arc(0, 1)} fill="none" stroke="#e2e8f0" strokeWidth={VB.sw} strokeLinecap="round" />

          {/* Faixas fixas (sempre arco menor) */}
          {alertT > 0.001 && (
            <path d={arc(0, alertT)} fill="none" stroke="#bbf7d0" strokeWidth={VB.sw} strokeLinecap="butt" />
          )}
          {criticalT > alertT + 0.001 && (
            <path d={arc(alertT, criticalT)} fill="none" stroke="#fde68a" strokeWidth={VB.sw} strokeLinecap="butt" />
          )}
          {criticalT < 0.999 && (
            <path d={arc(criticalT, 1)} fill="none" stroke="#fecaca" strokeWidth={VB.sw} strokeLinecap="butt" />
          )}

          {/* Valor atual */}
          {hasData && pct > 0.002 && (
            <path d={arc(0, pct)} fill="none" stroke={color} strokeWidth={VB.sw} strokeLinecap="round" />
          )}

          {/* Marcadores de limite */}
          <circle cx={polar(alertT).x} cy={polar(alertT).y} r={2} fill="#d97706" opacity={0.7} />
          <circle cx={polar(criticalT).x} cy={polar(criticalT).y} r={2} fill="#dc2626" opacity={0.7} />

          {/* Ponteiro */}
          {hasData && (
            <g>
              <line
                x1={VB.cx}
                y1={VB.cy}
                x2={tip.x}
                y2={tip.y}
                stroke={color}
                strokeWidth={2.5}
                strokeLinecap="round"
              />
              <circle cx={VB.cx} cy={VB.cy} r={5} fill="#fff" stroke={color} strokeWidth={2} />
            </g>
          )}

          <text x={left.x} y={VB.cy + 14} fontSize="10" fill="#94a3b8" textAnchor="middle">
            {min}
          </text>
          <text x={right.x} y={VB.cy + 14} fontSize="10" fill="#94a3b8" textAnchor="middle">
            {max}
          </text>
        </svg>

        <div
          style={{
            position: 'absolute',
            left: '50%',
            top: 52,
            transform: 'translateX(-50%)',
            textAlign: 'center',
            pointerEvents: 'none',
          }}
        >
          <span className="mono" style={{ fontSize: 22, fontWeight: 700, color, whiteSpace: 'nowrap' }}>
            {displayValue.toFixed(decimals)}
          </span>
          <span style={{ fontSize: 11, color: '#64748b', marginLeft: 4 }}>{unit}</span>
        </div>
      </div>
    </div>
  );
}

function propsEqual(a, b) {
  return (
    a.label === b.label &&
    a.value === b.value &&
    a.hasData === b.hasData &&
    a.min === b.min &&
    a.max === b.max &&
    a.sensorStatus === b.sensorStatus &&
    a.decimals === b.decimals
  );
}

export default memo(StatusGaugeInner, propsEqual);
