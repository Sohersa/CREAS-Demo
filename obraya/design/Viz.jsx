/* global React */
const { useState, useEffect, useRef } = React;

// Burst chart — radial viz inspired by Stripe
function BurstChart() {
  const [active, setActive] = useState('month');
  const [pulse, setPulse] = useState(0);

  useEffect(() => {
    const t = setInterval(() => setPulse(p => (p + 1) % 60), 80);
    return () => clearInterval(t);
  }, []);

  const rays = 72;
  const cx = 500, cy = 420;
  const activeIdx = pulse % rays;

  return (
    <div className="burst-viz">
      <div className="burst-controls">
        <button className={active === 'week' ? 'on' : ''} onClick={() => setActive('week')}>7d</button>
        <button className={active === 'month' ? 'on' : ''} onClick={() => setActive('month')}>30d</button>
        <button className={active === 'year' ? 'on' : ''} onClick={() => setActive('year')}>12m</button>
      </div>

      <svg viewBox="0 0 1000 500" preserveAspectRatio="xMidYMax meet">
        <defs>
          <radialGradient id="burstGlow" cx="50%" cy="100%" r="50%">
            <stop offset="0%" stopColor="#635BFF" stopOpacity="0.25"/>
            <stop offset="60%" stopColor="#FF80B5" stopOpacity="0.08"/>
            <stop offset="100%" stopColor="#FFF" stopOpacity="0"/>
          </radialGradient>
          <linearGradient id="rayGrad" x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="#635BFF" stopOpacity="0.9"/>
            <stop offset="100%" stopColor="#635BFF" stopOpacity="0"/>
          </linearGradient>
          <linearGradient id="rayGradHot" x1="0%" y1="100%" x2="0%" y2="0%">
            <stop offset="0%" stopColor="#FF7A45" stopOpacity="1"/>
            <stop offset="100%" stopColor="#FF80B5" stopOpacity="0"/>
          </linearGradient>
        </defs>

        <ellipse cx={cx} cy={cy} rx="480" ry="380" fill="url(#burstGlow)"/>

        {Array.from({ length: rays }).map((_, i) => {
          const angle = (Math.PI * (i / (rays - 1))) - Math.PI; // -180° to 0°
          const baseLen = 200 + Math.abs(Math.sin(i * 0.7)) * 160 + (i % 5 === 0 ? 40 : 0);
          const len = i === activeIdx ? baseLen + 40 : baseLen;
          const x2 = cx + Math.cos(angle) * len;
          const y2 = cy + Math.sin(angle) * len;
          const dotX = cx + Math.cos(angle) * (len - 6);
          const dotY = cy + Math.sin(angle) * (len - 6);
          const hot = i === activeIdx;
          return (
            <g key={i}>
              <line x1={cx} y1={cy} x2={x2} y2={y2}
                stroke={hot ? 'url(#rayGradHot)' : 'url(#rayGrad)'}
                strokeWidth={hot ? 1.6 : 0.6}
                opacity={hot ? 1 : 0.4}/>
              <circle cx={dotX} cy={dotY} r={hot ? 3 : 1.6}
                fill={hot ? '#FF7A45' : '#635BFF'}
                opacity={hot ? 1 : 0.75}/>
            </g>
          );
        })}

        <circle cx={cx} cy={cy} r="6" fill="#635BFF"/>
        <circle cx={cx} cy={cy} r="14" fill="none" stroke="#635BFF" strokeWidth="1" opacity="0.3"/>
      </svg>

      <div className="burst-label" style={{ top: '22%', left: '18%' }}>
        <strong>1,247</strong><span style={{ color: '#697386' }}>proveedores</span> <span className="up">+14%</span>
      </div>
      <div className="burst-label" style={{ top: '38%', right: '16%' }}>
        <strong>MX · GDL</strong><span style={{ color: '#697386' }}>47 min</span> <span className="up">↑</span>
      </div>
      <div className="burst-label" style={{ bottom: '22%', left: '8%' }}>
        <strong>$248/bulto</strong><span className="down">-$5 vs hist.</span>
      </div>
      <div className="burst-label" style={{ bottom: '14%', right: '10%' }}>
        <strong>Cotizaciones hoy</strong> <span style={{ color: '#635BFF' }}>●</span> <strong>314</strong>
      </div>
    </div>
  );
}

// Animated bar chart
function BarChart({ accent = 'violet' }) {
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setTick(t => t + 1), 1200);
    return () => clearInterval(t);
  }, []);
  const bars = Array.from({ length: 28 }).map((_, i) => {
    const base = 30 + Math.abs(Math.sin((i + tick * 0.3) * 0.5) * 55) + (i === (tick % 28) ? 20 : 0);
    return Math.min(100, base);
  });
  const peakIdx = bars.indexOf(Math.max(...bars));
  return (
    <div className="bar-chart">
      {bars.map((h, i) => (
        <div key={i} className={`bar ${i === peakIdx ? 'peak' : ''}`} style={{ height: `${h}%` }} />
      ))}
    </div>
  );
}

// Mini supplier pill map
function SupplierPills() {
  const items = [
    { n: 'Cemex', c: '#635BFF', x: 20, y: 30 },
    { n: 'JAL', c: '#FF7A45', x: 55, y: 20 },
    { n: 'Cruz Azul', c: '#FF80B5', x: 75, y: 45 },
    { n: 'Obregón', c: '#00D4FF', x: 30, y: 60 },
    { n: 'San Juan', c: '#FFB84D', x: 65, y: 70 },
    { n: 'Occidente', c: '#635BFF', x: 15, y: 78 }
  ];
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: 220 }}>
      {items.map((s, i) => (
        <div key={i} style={{
          position: 'absolute',
          left: `${s.x}%`, top: `${s.y}%`,
          padding: '6px 12px',
          background: 'white',
          border: '1px solid rgba(10,37,64,0.1)',
          borderRadius: 100,
          fontSize: 12,
          fontWeight: 500,
          boxShadow: '0 4px 12px -4px rgba(10,37,64,0.12)',
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          animation: `msgIn 500ms ${i * 120}ms backwards`
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: s.c }} />
          {s.n}
        </div>
      ))}
      {/* connecting lines */}
      <svg style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }} viewBox="0 0 100 100" preserveAspectRatio="none">
        {items.map((s, i) => (
          <line key={i} x1="50" y1="50" x2={s.x + 5} y2={s.y + 4}
            stroke="#635BFF" strokeWidth="0.15" strokeDasharray="1 1" opacity="0.4"/>
        ))}
        <circle cx="50" cy="50" r="3" fill="#635BFF"/>
      </svg>
    </div>
  );
}

// Quote comparison panel v2
function QuotesPanelV2({ lang = 'es' }) {
  const base = [
    { p: 'Cemex Zapopan', city: 'Zapopan · 4.2 km', price: 246, delta: -5, eta: lang === 'es' ? 'mañ. 7:00' : 'tom. 7:00', t: 800 },
    { p: 'Materiales JAL', city: 'Tlaquepaque · 8.1 km', price: 249, delta: -2, eta: lang === 'es' ? 'mañ. 8:00' : 'tom. 8:00', t: 1800 },
    { p: 'Cruz Azul dist.', city: 'Guadalajara · 11.4 km', price: 251, delta: 0, eta: lang === 'es' ? 'mañ. 9:00' : 'tom. 9:00', t: 3000 },
    { p: 'Ferretería Obregón', city: 'Tonalá · 14.2 km', price: 258, delta: 7, eta: lang === 'es' ? 'mañ. 11:00' : 'tom. 11:00', t: 4400 },
    { p: 'Distribuidora Occ.', city: 'Tlajomulco · 18.7 km', price: 262, delta: 11, eta: lang === 'es' ? 'mañ. 13:00' : 'tom. 13:00', t: 6000 }
  ];
  const waiting = [{ p: 'Materiales del Valle', city: '— · GDL' }, { p: 'Constru-Fast', city: '— · Zapopan' }, { p: 'Cementera S. Juan', city: '— · El Salto' }];
  const [revealed, setRevealed] = useState([]);

  useEffect(() => {
    setRevealed([]);
    const ts = base.map((b, i) => setTimeout(() => setRevealed(r => [...r, i]), b.t));
    const loop = setTimeout(() => {
      setRevealed([]);
      base.forEach((b, i) => ts.push(setTimeout(() => setRevealed(r => [...r, i]), b.t)));
    }, 10000);
    return () => { ts.forEach(clearTimeout); clearTimeout(loop); };
  }, [lang]);

  const fmt = (n) => new Intl.NumberFormat('en-US').format(n);

  return (
    <div className="quotes-panel-v2">
      <div className="quotes-hdr">
        <div>
          <div className="quotes-title-v2">
            <small>{lang === 'es' ? 'Pedido activo · #4821' : 'Active request · #4821'}</small>
            50 × {lang === 'es' ? 'cemento CPC 30R' : 'CPC 30R cement'}
          </div>
          <div style={{ fontSize: 12, color: 'var(--ink-muted)', marginTop: 4 }}>
            {lang === 'es' ? 'Mañana 7am · Zapopan, Jal.' : 'Tomorrow 7am · Zapopan, Jal.'}
          </div>
        </div>
        <div className="quotes-count-v2">
          <span style={{ color: 'var(--violet-ink)', fontWeight: 600 }}>{revealed.length}</span> / 8
        </div>
      </div>
      <div className="quote-bar-v2" style={{ opacity: revealed.length < 5 ? 1 : 0, transition: 'opacity 400ms' }}></div>
      {base.map((b, i) => {
        const on = revealed.includes(i);
        const isWinner = on && i === 0;
        return (
          <div key={i} className={`quote-row-v2 ${on ? '' : 'waiting'} ${isWinner ? 'winner' : ''}`}>
            <div className="rank">{on && isWinner ? '★' : (i + 1)}</div>
            <div className="provider">{b.p}<small>{b.city}</small></div>
            <div className="price"><span>{on && `$${fmt(b.price)}`}</span></div>
            <div className={`delta ${b.delta < 0 ? 'down' : b.delta > 0 ? 'up' : ''}`}>{on ? (b.delta < 0 ? `-$${Math.abs(b.delta)}` : b.delta > 0 ? `+$${b.delta}` : '±0') : ''}</div>
            <div className="eta">{on ? b.eta : ''}</div>
          </div>
        );
      })}
      {waiting.map((w, i) => (
        <div key={`w${i}`} className="quote-row-v2 waiting">
          <div className="rank">·</div>
          <div className="provider">{w.p}<small>{w.city}</small></div>
          <div className="price"><span></span></div><div className="delta"></div><div className="eta"></div>
        </div>
      ))}
    </div>
  );
}

Object.assign(window, { BurstChart, BarChart, SupplierPills, QuotesPanelV2 });
