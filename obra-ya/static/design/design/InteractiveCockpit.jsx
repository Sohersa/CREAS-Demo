/* global React */
// Interactive Cockpit v2 — orchestrated tour: 8 narrative steps, faster, with cursor & toasts
const { useState: uS, useEffect: uE, useRef: uR } = React;

const SCREENS = {
  es: [
    { id: 'inbox', name: 'Pedidos', icon: '📥' },
    { id: 'compare', name: 'Comparar', icon: '⚖️' },
    { id: 'suppliers', name: 'Proveedores', icon: '🏭' },
    { id: 'delivery', name: 'Entregas', icon: '🚚' },
    { id: 'invoice', name: 'Facturas', icon: '📄' }
  ],
  en: [
    { id: 'inbox', name: 'Requests', icon: '📥' },
    { id: 'compare', name: 'Compare', icon: '⚖️' },
    { id: 'suppliers', name: 'Suppliers', icon: '🏭' },
    { id: 'delivery', name: 'Deliveries', icon: '🚚' },
    { id: 'invoice', name: 'Invoices', icon: '📄' }
  ]
};

// Narrative script — 8 steps, ~3s each = 24s total loop
const TOUR = (lang) => [
  { tab: 'inbox',    dur: 2200, focus: null,      title: lang==='es'?'1. Llega un pedido nuevo por WhatsApp':'1. A new request arrives via WhatsApp',  cursor: { x: 8, y: 45 } },
  { tab: 'inbox',    dur: 2200, focus: 'row-hot', title: lang==='es'?'2. Nico ya cotizó con 5 de 8 proveedores':'2. Nico already quoted 5 of 8 suppliers',      cursor: { x: 85, y: 35 }, toast: { txt: lang==='es'?'+2 cotizaciones':'+2 quotes' } },
  { tab: 'compare',  dur: 2400, focus: null,      title: lang==='es'?'3. Comparativa lista: precio, ETA, rating':'3. Comparison ready: price, ETA, rating', cursor: { x: 20, y: 55 } },
  { tab: 'compare',  dur: 2200, focus: 'pick',    title: lang==='es'?'4. Eliges al ganador — un clic':'4. Pick the winner — one click',                      cursor: { x: 18, y: 90 }, click: true },
  { tab: 'suppliers',dur: 2200, focus: null,      title: lang==='es'?'5. Actualiza el rating del proveedor':'5. Updates the supplier\'s rating',              cursor: { x: 50, y: 40 } },
  { tab: 'delivery', dur: 2600, focus: 'live',    title: lang==='es'?'6. Entrega en tránsito — tracking en vivo':'6. Delivery in transit — live tracking',   cursor: { x: 80, y: 60 }, toast: { txt: lang==='es'?'🚚 a 4 km de obra':'🚚 4 km from site' } },
  { tab: 'delivery', dur: 2200, focus: null,      title: lang==='es'?'7. Residente confirma con foto':'7. Foreman confirms with a photo',                      cursor: { x: 30, y: 20 } },
  { tab: 'invoice',  dur: 2800, focus: null,      title: lang==='es'?'8. CFDI 4.0 timbrada y enviada al contador ✓':'8. CFDI 4.0 stamped and sent to accounting ✓', cursor: { x: 75, y: 50 }, toast: { txt: lang==='es'?'Factura timbrada':'Invoice stamped', ok: true } }
];

function InteractiveCockpit({ lang = 'es' }) {
  const screens = SCREENS[lang];
  const [stepIdx, setStepIdx] = uS(0);
  const [playing, setPlaying] = uS(true);
  const [progress, setProgress] = uS(0);
  const [toast, setToast] = uS(null);
  const [clickPulse, setClickPulse] = uS(false);
  const hoverRef = uR(false);
  const tour = TOUR(lang);
  const step = tour[stepIdx];

  // Orchestrated timeline
  uE(() => {
    if (!playing) return;
    const tick = 50;
    const dur = step.dur;
    let elapsed = 0;

    // Trigger toast 600ms in
    const toastT = step.toast ? setTimeout(() => {
      setToast(step.toast);
      setTimeout(() => setToast(null), 1600);
    }, 600) : null;
    // Trigger click 900ms in
    const clickT = step.click ? setTimeout(() => {
      setClickPulse(true);
      setTimeout(() => setClickPulse(false), 500);
    }, 900) : null;

    const iv = setInterval(() => {
      if (hoverRef.current) return;
      elapsed += tick;
      setProgress(Math.min(100, (elapsed / dur) * 100));
      if (elapsed >= dur) {
        setStepIdx((stepIdx + 1) % tour.length);
        setProgress(0);
      }
    }, tick);

    return () => { clearInterval(iv); if (toastT) clearTimeout(toastT); if (clickT) clearTimeout(clickT); };
  }, [stepIdx, playing, lang]);

  // Reset when lang changes
  uE(() => { setStepIdx(0); setProgress(0); }, [lang]);

  const onEnter = () => { hoverRef.current = true; };
  const onLeave = () => { hoverRef.current = false; };
  const manualTab = (tabId) => {
    const i = tour.findIndex(s => s.tab === tabId);
    setStepIdx(i >= 0 ? i : 0);
    setProgress(0);
  };
  const jumpStep = (i) => { setStepIdx(i); setProgress(0); };

  return (
    <div className="cockpit" onMouseEnter={onEnter} onMouseLeave={onLeave}>
      {/* Browser chrome */}
      <div className="cockpit-chrome">
        <div className="cockpit-dots"><i style={{background:'#FF5F57'}}/><i style={{background:'#FEBC2E'}}/><i style={{background:'#28C840'}}/></div>
        <div className="cockpit-url">
          <span style={{opacity:0.5}}>app.</span>obraya.mx<span style={{opacity:0.5}}>/{step.tab}</span>
        </div>
        <div className="cockpit-playbar">
          <button onClick={() => setPlaying(p => !p)} className="cockpit-play">{playing ? '❚❚' : '▶'}</button>
          <div className="cockpit-progress"><div className="cockpit-progress-bar" style={{width:`${progress}%`}}/></div>
          <span className="cockpit-pill">{playing ? (lang==='es'?'TOUR':'TOUR') : (lang==='es'?'PAUSA':'PAUSED')}</span>
        </div>
      </div>

      {/* Narrative banner — shows current step */}
      <div className="cockpit-narrator">
        <div className="cockpit-narr-steps">
          {tour.map((_, i) => (
            <button key={i} className={`cockpit-narr-dot ${i===stepIdx?'on':''} ${i<stepIdx?'done':''}`} onClick={() => jumpStep(i)}/>
          ))}
        </div>
        <div className="cockpit-narr-txt">{step.title}</div>
        <div className="cockpit-narr-count">{stepIdx+1}/{tour.length}</div>
      </div>

      <div className="cockpit-body">
        {/* Sidebar */}
        <aside className="cockpit-side">
          <div className="cockpit-brand"><span className="cockpit-brand-mark">OY</span> OBRA YA</div>
          <div className="cockpit-side-section">
            <div className="cockpit-side-label">{lang==='es'?'OPERACIÓN':'OPERATIONS'}</div>
            {screens.map(s => (
              <button key={s.id} className={`cockpit-nav ${step.tab===s.id?'on':''}`} onClick={() => manualTab(s.id)}>
                <span className="cockpit-nav-i">{s.icon}</span>{s.name}
                {s.id==='inbox' && <span className="cockpit-nav-badge">3</span>}
                {s.id==='delivery' && <span className="cockpit-nav-badge warn">1</span>}
              </button>
            ))}
          </div>
          <div className="cockpit-side-section">
            <div className="cockpit-side-label">{lang==='es'?'OBRAS':'SITES'}</div>
            <button className="cockpit-nav"><span style={{width:8,height:8,borderRadius:2,background:'#635BFF'}}/>Torre Andares</button>
            <button className="cockpit-nav"><span style={{width:8,height:8,borderRadius:2,background:'#FF7A45'}}/>Residencial GDL</button>
            <button className="cockpit-nav"><span style={{width:8,height:8,borderRadius:2,background:'#FF80B5'}}/>Bodega Tlaq.</button>
          </div>
          <div className="cockpit-user">
            <div className="cockpit-avatar">RS</div>
            <div><div style={{fontWeight:600,fontSize:12}}>Roberto S.</div><div style={{fontSize:10,color:'var(--ink-muted)'}}>Constructora del Valle</div></div>
          </div>
        </aside>

        {/* Content */}
        <main className="cockpit-main">
          <header className="cockpit-head">
            <div>
              <div className="cockpit-crumb">{lang==='es'?'Operación':'Operations'} / {screens.find(s=>s.id===step.tab).name}</div>
              <h3 className="cockpit-h1">{titleFor(step.tab, lang)}</h3>
            </div>
            <div className="cockpit-head-actions">
              <div className="cockpit-search">🔍 <span style={{opacity:0.5}}>⌘K</span></div>
              <button className="cockpit-btn-primary">+ {lang==='es'?'Nuevo pedido':'New request'}</button>
            </div>
          </header>
          <div className="cockpit-screen" key={step.tab}>
            {step.tab==='inbox' && <ScreenInbox lang={lang} focus={step.focus}/>}
            {step.tab==='compare' && <ScreenCompare lang={lang} focus={step.focus}/>}
            {step.tab==='suppliers' && <ScreenSuppliers lang={lang}/>}
            {step.tab==='delivery' && <ScreenDelivery lang={lang} focus={step.focus}/>}
            {step.tab==='invoice' && <ScreenInvoice lang={lang}/>}
          </div>

          {/* Floating cursor */}
          {playing && (
            <div className="cockpit-cursor" style={{ left: `${step.cursor.x}%`, top: `${step.cursor.y}%` }}>
              <svg width="18" height="22" viewBox="0 0 18 22" fill="none">
                <path d="M1 1L15 11L9 13L7 20L1 1Z" fill="#0A2540" stroke="white" strokeWidth="1.5" strokeLinejoin="round"/>
              </svg>
              {clickPulse && <span className="cockpit-cursor-ring"/>}
            </div>
          )}

          {/* Toast */}
          {toast && (
            <div className={`cockpit-toast ${toast.ok?'ok':''}`}>
              {toast.ok && <span style={{fontSize:14}}>✓</span>}
              {toast.txt}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}

function titleFor(t, l) {
  const es = { inbox:'Pedidos en proceso', compare:'Comparativa — Orden #4821', suppliers:'Red de proveedores', delivery:'Entregas en curso', invoice:'Facturas CFDI' };
  const en = { inbox:'Active requests', compare:'Comparison — Order #4821', suppliers:'Supplier network', delivery:'Live deliveries', invoice:'CFDI invoices' };
  return (l==='es'?es:en)[t];
}

function ScreenInbox({ lang, focus }) {
  const rows = [
    { id:'#4821', site:'Torre Andares', mat: lang==='es'?'50 × Cemento CPC 30R':'50 × CPC 30R cement', when: lang==='es'?'Mañana 7:00':'Tomorrow 7:00', st:'quoting', q:5, hot:true },
    { id:'#4820', site:'Residencial GDL', mat: lang==='es'?'2 ton · Varilla 3/8':'2 ton · 3/8 rebar', when: lang==='es'?'Jue 10:00':'Thu 10:00', st:'ready', q:8 },
    { id:'#4819', site:'Bodega Tlaq.', mat: lang==='es'?'30 m³ Premezclado':'30 m³ ready-mix', when: lang==='es'?'Vie 7:00':'Fri 7:00', st:'confirmed', q:6 },
    { id:'#4818', site:'Torre Andares', mat: lang==='es'?'1 camión · Grava 3/4':'1 truck · 3/4 gravel', when: lang==='es'?'Lun 8:00':'Mon 8:00', st:'delivered', q:4 }
  ];
  const stLabel = { es:{quoting:'Cotizando',ready:'Listo p/ elegir',confirmed:'Confirmado',delivered:'Entregado'}, en:{quoting:'Quoting',ready:'Ready to pick',confirmed:'Confirmed',delivered:'Delivered'} }[lang];
  return (
    <table className="cockpit-table">
      <thead><tr>
        <th>ID</th><th>{lang==='es'?'Obra':'Site'}</th><th>{lang==='es'?'Material':'Material'}</th><th>{lang==='es'?'Entrega':'Delivery'}</th><th>{lang==='es'?'Cotiz.':'Quotes'}</th><th>{lang==='es'?'Estado':'Status'}</th>
      </tr></thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.id} className={`${r.hot?'hot':''} ${r.hot && focus==='row-hot'?'pulse':''}`}>
            <td className="mono">{r.id}</td>
            <td>{r.site}</td>
            <td style={{color:'var(--ink-2)'}}>{r.mat}</td>
            <td className="mono" style={{color:'var(--ink-dim)'}}>{r.when}</td>
            <td className="mono">
              {r.hot && focus==='row-hot' ? <span style={{color:'var(--violet-ink)',fontWeight:600}}>{r.q}→7/8</span> : `${r.q}/8`}
            </td>
            <td><span className={`cockpit-chip ${r.st}`}>{stLabel[r.st]}</span></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ScreenCompare({ lang, focus }) {
  const offers = [
    { p:'Cemex Zapopan', km:4.2, price:246, eta: lang==='es'?'Mañana 7:00':'Tomorrow 7:00', score:98 },
    { p:'Materiales JAL', km:8.1, price:249, eta: lang==='es'?'Mañana 8:00':'Tomorrow 8:00', score:94 },
    { p:'Cruz Azul Dist.', km:11.4, price:251, eta: lang==='es'?'Mañana 9:00':'Tomorrow 9:00', score:91 }
  ];
  return (
    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12}}>
      {offers.map((o, i) => (
        <div key={i} className={`cockpit-offer ${i===0?'best':''} ${i===0 && focus==='pick'?'picked':''}`}>
          {i===0 && <div className="cockpit-offer-tag">{lang==='es'?'MEJOR OFERTA':'BEST OFFER'}</div>}
          <div className="cockpit-offer-p">{o.p}</div>
          <div className="cockpit-offer-km">{o.km} km · Zapopan</div>
          <div className="cockpit-offer-price">${o.price}<small>/{lang==='es'?'bulto':'bag'}</small></div>
          <div className="cockpit-offer-line"><span>{lang==='es'?'Entrega':'Delivery'}</span><b>{o.eta}</b></div>
          <div className="cockpit-offer-line"><span>Rating</span><b>{o.score}%</b></div>
          <div className="cockpit-offer-line"><span>{lang==='es'?'Total 50 uds':'Total 50 units'}</span><b className="mono">${(o.price*50).toLocaleString()}</b></div>
          <button className={`cockpit-offer-btn ${i===0 && focus==='pick'?'on':''}`}>
            {i===0 && focus==='pick' ? (lang==='es'?'Confirmado ✓':'Confirmed ✓') : (lang==='es'?'Elegir':'Pick')}
          </button>
        </div>
      ))}
    </div>
  );
}

function ScreenSuppliers({ lang }) {
  const sups = [
    { n:'Cemex', cat: lang==='es'?'Cemento':'Cement', ords:143, rt:98, dot:'#635BFF', delta:'+1' },
    { n:'Materiales JAL', cat: lang==='es'?'Varios':'General', ords:89, rt:94, dot:'#FF7A45' },
    { n:'Cruz Azul Dist.', cat: lang==='es'?'Cemento':'Cement', ords:76, rt:91, dot:'#FF80B5' },
    { n:'Ferretería Obregón', cat: lang==='es'?'Ferretería':'Hardware', ords:54, rt:89, dot:'#00D4FF' },
    { n:'Aceros del Norte', cat: lang==='es'?'Acero':'Steel', ords:48, rt:93, dot:'#FFB84D' },
    { n:'Distribuidora Occ.', cat: lang==='es'?'Agregados':'Aggregates', ords:41, rt:86, dot:'#635BFF' }
  ];
  return (
    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:10}}>
      {sups.map((s, i) => (
        <div key={i} className={`cockpit-sup ${i===0?'pulse':''}`}>
          <div className="cockpit-sup-top">
            <div className="cockpit-sup-logo" style={{background:s.dot}}>{s.n.charAt(0)}</div>
            <div style={{flex:1}}>
              <div style={{fontWeight:600,fontSize:13,display:'flex',gap:6,alignItems:'center'}}>{s.n}{s.delta && <span style={{fontSize:10,color:'#00D97E',fontFamily:'var(--font-mono)',fontWeight:600}}>{s.delta}</span>}</div>
              <div style={{fontSize:10,color:'var(--ink-muted)'}}>{s.cat}</div>
            </div>
          </div>
          <div className="cockpit-sup-stats">
            <div><div style={{fontSize:16,fontWeight:600}}>{s.ords}</div><div style={{fontSize:9,color:'var(--ink-muted)',textTransform:'uppercase',letterSpacing:'0.06em'}}>{lang==='es'?'órdenes':'orders'}</div></div>
            <div><div style={{fontSize:16,fontWeight:600,color: s.rt>=95?'#00D97E':s.rt>=90?'var(--violet-ink)':'var(--orange-ink)'}}>{s.rt}%</div><div style={{fontSize:9,color:'var(--ink-muted)',textTransform:'uppercase',letterSpacing:'0.06em'}}>{lang==='es'?'a tiempo':'on-time'}</div></div>
          </div>
          <div style={{height:4,background:'var(--paper-3)',borderRadius:2,overflow:'hidden'}}>
            <div style={{height:'100%',width:`${s.rt}%`,background:'linear-gradient(90deg, var(--violet), var(--pink))'}}/>
          </div>
        </div>
      ))}
    </div>
  );
}

function ScreenDelivery({ lang, focus }) {
  const list = [
    { id:'#4821', sup:'Cemex', mat: lang==='es'?'50 bultos cemento':'50 bags cement', eta:'07:00', st:focus==='live'?'transit':'scheduled', site:'Torre Andares', live: focus==='live' },
    { id:'#4819', sup:'Cemex', mat: lang==='es'?'30 m³ premezclado':'30 m³ ready-mix', eta:'09:00', st:'ok', site:'Bodega Tlaq.' },
    { id:'#4817', sup:'Mat. JAL', mat: lang==='es'?'2 ton varilla':'2 ton rebar', eta:'09:30', st:'transit', site:'Residencial GDL' },
    { id:'#4816', sup:'Cruz Azul', mat: lang==='es'?'50 bultos cemento':'50 bags cement', eta:'11:00', st:'late', site:'Bodega Tlaq.' }
  ];
  const stWord = { es:{ok:'✓ Entregado',transit:'🚚 En ruta',late:'⚠ Retraso',scheduled:'⏱ Programado'}, en:{ok:'✓ Delivered',transit:'🚚 On route',late:'⚠ Delayed',scheduled:'⏱ Scheduled'} }[lang];
  return (
    <div>
      <div style={{display:'grid', gridTemplateColumns:'repeat(4, 1fr)', gap:10, marginBottom:14}}>
        {[{k:lang==='es'?'Hoy':'Today',v:'12'},{k:lang==='es'?'En tránsito':'In transit',v:focus==='live'?'4':'3',pulse:focus==='live'},{k:lang==='es'?'A tiempo':'On time',v:'94%'},{k:lang==='es'?'Retrasos':'Late',v:'1'}].map((s,i)=>(
          <div key={i} className={`cockpit-stat-card ${s.pulse?'pulse':''}`}><div className="cockpit-stat-v">{s.v}</div><div className="cockpit-stat-k">{s.k}</div></div>
        ))}
      </div>
      <table className="cockpit-table">
        <thead><tr><th>ID</th><th>{lang==='es'?'Proveedor':'Supplier'}</th><th>{lang==='es'?'Material':'Material'}</th><th>{lang==='es'?'Obra':'Site'}</th><th>ETA</th><th>{lang==='es'?'Estado':'Status'}</th></tr></thead>
        <tbody>
          {list.map(r => (
            <tr key={r.id} className={r.live?'pulse':''}><td className="mono">{r.id}</td><td>{r.sup}</td><td style={{color:'var(--ink-2)'}}>{r.mat}</td><td style={{color:'var(--ink-dim)'}}>{r.site}</td><td className="mono">{r.eta}</td><td><span className={`cockpit-chip ${r.st}`}>{stWord[r.st]}</span></td></tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ScreenInvoice({ lang }) {
  return (
    <div style={{display:'grid', gridTemplateColumns:'1.2fr 1fr', gap:16}}>
      <table className="cockpit-table">
        <thead><tr><th>UUID</th><th>{lang==='es'?'Proveedor':'Supplier'}</th><th>Total</th><th>{lang==='es'?'Estado':'Status'}</th></tr></thead>
        <tbody>
          {[
            { u:'4B9F2-A821', s:'Cemex', t:14268, st:'ok', hot:true},
            { u:'3A8C1-A820', s:'Mat. JAL', t:48720, st:'ok'},
            { u:'9C2D4-A819', s:'Cruz Azul', t:18600, st:'pending'},
            { u:'7E1F3-A818', s:'Obregón', t:3240, st:'ok'},
            { u:'2B6A9-A817', s:'Aceros N.', t:62400, st:'ok'}
          ].map(r => (
            <tr key={r.u} className={r.hot?'hot pulse':''}><td className="mono" style={{fontSize:11}}>{r.u}</td><td>{r.s}</td><td className="mono">${r.t.toLocaleString()}</td><td><span className={`cockpit-chip ${r.st==='ok'?'ok':'pending'}`}>{r.st==='ok'?(lang==='es'?'✓ Timbrada':'✓ Stamped'):(lang==='es'?'⏱ En proceso':'⏱ Processing')}</span></td></tr>
          ))}
        </tbody>
      </table>
      <div className="cockpit-invoice">
        <div style={{fontSize:10,color:'var(--ink-muted)',fontFamily:'var(--font-mono)',letterSpacing:'0.1em',textTransform:'uppercase',fontWeight:500}}>CFDI 4.0 · {lang==='es'?'Recién timbrada':'Just stamped'}</div>
        <div style={{fontSize:20,fontWeight:600,marginTop:8,letterSpacing:'-0.02em'}}>A-4821</div>
        <div style={{fontSize:12,color:'var(--ink-dim)',marginTop:4}}>Cemex SA de CV · RFC CEM880331•••</div>
        <div style={{height:1,background:'var(--line)',margin:'14px 0'}}/>
        <div style={{display:'flex',justifyContent:'space-between',fontSize:12,marginBottom:6}}><span style={{color:'var(--ink-dim)'}}>50 × CPC 30R</span><span className="mono">$12,300.00</span></div>
        <div style={{display:'flex',justifyContent:'space-between',fontSize:12,marginBottom:6}}><span style={{color:'var(--ink-dim)'}}>IVA 16%</span><span className="mono">$1,968.00</span></div>
        <div style={{display:'flex',justifyContent:'space-between',fontSize:13,fontWeight:600,marginTop:10,paddingTop:10,borderTop:'1px solid var(--line)'}}><span>Total MXN</span><span className="mono">$14,268.00</span></div>
        <div style={{marginTop:12,padding:'8px 12px',background:'var(--violet-soft)',borderRadius:8,fontSize:10,color:'var(--violet-ink)',fontFamily:'var(--font-mono)',fontWeight:500}}>UUID: 4B9F2-A821-C4D7-••••</div>
        <button className="cockpit-btn-primary" style={{width:'100%',marginTop:12}}>{lang==='es'?'Descargar XML + PDF':'Download XML + PDF'}</button>
      </div>
    </div>
  );
}

Object.assign(window, { InteractiveCockpit });
