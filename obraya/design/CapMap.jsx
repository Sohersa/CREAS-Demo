/* global React, Icon */
// CapMap — interactive capability map with cycling active column, travelling comet, and chip ripples
const { useState: cmS, useEffect: cmE, useRef: cmR } = React;

function CapMap({ lang = 'es' }) {
  const t = (es, en) => lang === 'es' ? es : en;
  const cols = [
    { g: t('El pedido llega','The order comes in'), n:'01', color:'#635BFF', node:'IN', items: [
      { ic:'chat',  t:t('Escribe o habla','Text or talk')},
      { ic:'mic',   t:t('Nota de voz','Voice note')},
      { ic:'pin',   t:t('Ubicación exacta','Exact location')},
      { ic:'book',  t:t('Entiende el slang','Jobsite slang')}
    ]},
    { g: t('Nico sale a cotizar','Nico quotes around'), n:'02', color:'#00D4FF', node:'COT', items: [
      { ic:'bolt',  t:t('Le pregunta a 20','Asks 20 at once')},
      { ic:'users', t:t('Al vendedor rápido','Hits fastest rep')},
      { ic:'send',  t:t('Mensaje por WhatsApp','WhatsApp message')},
      { ic:'clock', t:t('Insiste si no contestan','Nags the silent')}
    ]},
    { g: t('Compara y elige','Compares & picks'), n:'03', color:'#00A95F', node:'CMP', items: [
      { ic:'compare', t:t('Lee cada respuesta','Reads each reply')},
      { ic:'scale',   t:t('Peras con peras','Apples to apples')},
      { ic:'chart',   t:t('Sabe el precio justo','Knows fair price')},
      { ic:'alert',   t:t('Detecta mordidas','Flags bribes')}
    ]},
    { g: t('Autoriza y paga','Approves & pays'), n:'04', color:'#FFB84D', node:'APR', items: [
      { ic:'tree',    t:t('Quién puede firmar','Who can sign')},
      { ic:'shield',  t:t('Reglas de tu obra','Your jobsite rules')},
      { ic:'card',    t:t('Tarjeta o banco','Card or wire')},
      { ic:'invoice', t:t('Factura al contador','Invoice to accountant')}
    ]},
    { g: t('Llega a obra','Arrives on site'), n:'05', color:'#FF7A45', node:'END', items: [
      { ic:'truck',   t:t('Ubica el camión','Track the truck')},
      { ic:'camera',  t:t('Foto de entrega','Delivery photo')},
      { ic:'factory', t:t('1,247 proveedores','1,247 suppliers')},
      { ic:'pie',     t:t('Tablero director','Exec dashboard')},
      { ic:'plug',    t:t('Se conecta a tu ERP','Plugs into ERP')},
      { ic:'lang',    t:t('Español e inglés','Spanish & English')}
    ]}
  ];

  const [active, setActive] = cmS(0);
  const [locked, setLocked] = cmS(null); // user-hovered column locks the cycler
  cmE(() => {
    if (locked !== null) return;
    const iv = setInterval(() => setActive(a => (a + 1) % cols.length), 2200);
    return () => clearInterval(iv);
  }, [locked]);

  const currentCol = locked !== null ? locked : active;
  const total = cols.reduce((s, c) => s + c.items.length, 0);

  return (
    <div className="capmap2">
      {/* Animated spine */}
      <div className="capmap2-spine">
        <div className="capmap2-spine-line"/>
        {cols.map((c, i) => (
          <div
            key={i}
            className={`capmap2-spine-node ${currentCol === i ? 'on' : ''} ${i < currentCol ? 'done' : ''}`}
            style={{ left: `${10 + i * 20}%`, '--c': c.color }}
            onMouseEnter={() => setLocked(i)}
            onMouseLeave={() => setLocked(null)}
          >
            <div className="capmap2-spine-dot"/>
            <div className="capmap2-spine-label">{c.node}</div>
          </div>
        ))}
        {/* Travelling comet */}
        <div
          className="capmap2-comet"
          style={{
            left: `${10 + currentCol * 20}%`,
            background: `radial-gradient(circle, ${cols[currentCol].color} 0%, transparent 70%)`
          }}
        />
      </div>

      {/* Columns */}
      <div className="capmap2-cols">
        {cols.map((col, ci) => {
          const isActive = currentCol === ci;
          return (
            <div
              key={ci}
              className={`capmap2-col ${isActive ? 'live' : ''}`}
              style={{ '--c': col.color }}
              onMouseEnter={() => setLocked(ci)}
              onMouseLeave={() => setLocked(null)}
            >
              {/* Glow backdrop */}
              <div className="capmap2-col-glow"/>

              <div className="capmap2-col-hdr">
                <span className="capmap2-col-n">{col.n}</span>
                <span className="capmap2-col-name">{col.g}</span>
                <span className="capmap2-col-ct">{col.items.length}</span>
              </div>

              <div className="capmap2-chips">
                {col.items.map((it, ii) => (
                  <div
                    key={ii}
                    className="capmap2-chip"
                    style={{ '--i': ii, animationDelay: `${ii * 80}ms` }}
                  >
                    <div className="capmap2-chip-ic">
                      <Icon name={it.ic} size={14}/>
                      <span className="capmap2-chip-ripple"/>
                    </div>
                    <div className="capmap2-chip-t">{it.t}</div>
                    <div className="capmap2-chip-arrow">→</div>
                  </div>
                ))}
              </div>

              {/* Progress bar at bottom of active column */}
              <div className="capmap2-col-bar">
                <div className="capmap2-col-bar-fill"/>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer ticker */}
      <div className="capmap2-foot">
        <span className="capmap2-foot-pill" style={{ background: cols[currentCol].color }}>
          {String(currentCol+1).padStart(2,'0')} · {cols[currentCol].g}
        </span>
        <span className="capmap2-foot-sep">·</span>
        <span className="capmap2-foot-txt">
          {locked !== null
            ? t('Mantén el cursor para detener el tour.','Hover to pause the tour.')
            : t('Viendo cada capacidad en orden. Pasa el cursor para explorar.','Touring each capability in order. Hover to explore.')}
        </span>
        <span className="capmap2-foot-count mono">{total} {t('capacidades','capabilities')}</span>
      </div>
    </div>
  );
}

window.CapMap = CapMap;
