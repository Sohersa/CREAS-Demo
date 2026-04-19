/* global React */
// Playground — Capture module (WhatsApp + voice + photo + kits)

const { useState: useStateCap, useEffect: useEffectCap, useRef: useRefCap } = React;

function PgScreenCapture({ lang, onCreateOrder, setToast }) {
  const [mode, setMode] = useStateCap('chat'); // chat | voice | photo | kit
  const T = (es, en) => window.pgT(lang, es, en);

  return (
    <div className="pg-screen">
      <div className="pg-onboard">
        <div className="pg-onboard-ic">💬</div>
        <div>
          <div className="pg-onboard-t">{T('Captura un pedido — como si fueras residente de obra','Capture a request — as if you were a foreman')}</div>
          <div className="pg-onboard-d">{T('Prueba los 4 canales. Todo normalizado por Nico y enviado a cotización.','Try all 4 channels. Normalized by Nico and sent to quoting.')}</div>
        </div>
      </div>

      <div style={{ display:'flex', gap: 6, marginBottom: 18 }}>
        {[
          { k:'chat', ic:'💬', t:T('WhatsApp','WhatsApp') },
          { k:'voice', ic:'🎙️', t:T('Nota de voz','Voice note') },
          { k:'photo', ic:'📸', t:T('Foto de lista','Photo') },
          { k:'kit', ic:'🏗️', t:T('Kit de obra','Site kit') }
        ].map(m => (
          <button key={m.k} className={`pg-btn ${mode === m.k ? 'primary' : ''}`} onClick={() => setMode(m.k)}>
            <span>{m.ic}</span>{m.t}
          </button>
        ))}
      </div>

      {mode === 'chat' && <PgWAChat lang={lang} onCreateOrder={onCreateOrder} setToast={setToast}/>}
      {mode === 'voice' && <PgVoice lang={lang} onCreateOrder={onCreateOrder} setToast={setToast}/>}
      {mode === 'photo' && <PgPhoto lang={lang} onCreateOrder={onCreateOrder} setToast={setToast}/>}
      {mode === 'kit' && <PgKit lang={lang} onCreateOrder={onCreateOrder} setToast={setToast}/>}
    </div>
  );
}

/* WhatsApp chat simulated */
function PgWAChat({ lang, onCreateOrder, setToast }) {
  const T = (es, en) => window.pgT(lang, es, en);
  const [msgs, setMsgs] = useStateCap([
    { by:'nico', t: T('¡Buen día! Soy Nico de OBRA YA. ¿Qué necesitas para la obra hoy?','Morning! I\'m Nico from OBRA YA. What do you need for the site today?'), time:'09:12' }
  ]);
  const [input, setInput] = useStateCap('');
  const [typing, setTyping] = useStateCap(false);
  const [done, setDone] = useStateCap(false);
  const scrollRef = useRefCap(null);

  useEffectCap(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [msgs, typing]);

  const samples = [
    T('50 bultos de cemento para mañana 7am, Zapopan','50 bags of cement tomorrow 7am, Zapopan'),
    T('Necesito 2 toneladas de varilla del 3/8','I need 2 tons of 3/8" rebar'),
    T('Mándame 18 m³ de grava a Puerto Alto','Send 18 m³ of gravel to Puerto Alto')
  ];

  const send = (text) => {
    if (!text.trim() || done) return;
    setMsgs(m => [...m, { by:'me', t: text, time:'09:13' }]);
    setInput('');
    setTyping(true);
    setTimeout(() => {
      setTyping(false);
      setMsgs(m => [...m, {
        by:'nico',
        t: T('Entendido ✅ Extraje:\n• Material: Cemento CPC 30R\n• Cantidad: 50 sacos de 50kg\n• Entrega: mañana 07:00 · Zapopan\n\nArranco cotización con 6 proveedores en paralelo...','Got it ✅ Extracted:\n• Material: Cement CPC 30R\n• Qty: 50 bags of 50kg\n• Delivery: tomorrow 07:00 · Zapopan\n\nKicking off parallel quotes with 6 suppliers...'),
        time:'09:13',
        card: true
      }]);
      setTimeout(() => {
        setMsgs(m => [...m, { by:'nico', t: T('Listo — tengo 6 cotizaciones. Ver comparativa →','Done — I have 6 quotes. View comparison →'), time:'09:17', cta:true }]);
        setDone(true);
      }, 1600);
    }, 900);
  };

  return (
    <div className="pg-grid-2" style={{ gridTemplateColumns: '1fr 1fr', alignItems:'start' }}>
      <div className="pg-wa">
        <div className="pg-wa-hdr">
          <div style={{ width:28, height:28, borderRadius:'50%', background:'linear-gradient(135deg, var(--orange), var(--violet))', display:'flex', alignItems:'center', justifyContent:'center', fontSize:11, fontWeight:700 }}>N</div>
          <div>
            <div style={{ fontSize:13, fontWeight:600 }}>Nico · OBRA YA</div>
            <div style={{ fontSize:10, opacity:0.8 }}>{T('en línea','online')}</div>
          </div>
        </div>
        <div className="pg-wa-body" ref={scrollRef}>
          {msgs.map((m, i) => (
            <div key={i} className={`wa-msg ${m.by === 'me' ? 'out' : 'in'}`} style={{ whiteSpace:'pre-line' }}>
              {m.t}
              {m.cta && <button onClick={() => { onCreateOrder({ item:'Cemento CPC 30R', qty:50, unit:'saco 50kg', site:'sierra' }); setToast({ msg: T('Pedido OY-8423 creado. Abriendo cotizaciones...','Order OY-8423 created. Opening quotes...'), type:'ok' }); }} style={{ display:'block', marginTop:8, padding:'6px 10px', background:'var(--violet)', color:'white', border:'none', borderRadius:6, fontWeight:600, cursor:'pointer', fontSize:12 }}>{T('Ver comparativa →','View comparison →')}</button>}
              <span className="meta">{m.time}<span className="tick">✓✓</span></span>
            </div>
          ))}
          {typing && <div className="wa-typing"><i/><i/><i/></div>}
        </div>
        <div className="pg-wa-quick">
          {samples.map((s, i) => <button key={i} onClick={() => send(s)} disabled={done}>{s}</button>)}
        </div>
        <div className="pg-wa-input">
          <input placeholder={T('Escribe lo que necesitas...','Type what you need...')} value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && send(input)}/>
          <button onClick={() => send(input)}>➤</button>
        </div>
      </div>

      <div className="pg-card">
        <div className="pg-sect-t">🧠 {T('Cómo Nico entiende esto','How Nico parses this')}</div>
        <div style={{ fontSize:11, color:'var(--ink-dim)', marginBottom:12 }}>{T('El agente normaliza el lenguaje natural a un pedido estructurado antes de cotizar.','The agent normalizes natural language to a structured request before quoting.')}</div>
        <div className="pg-kv">
          <div className="pg-kv-r"><span className="k">{T('Material detectado','Detected material')}</span><span className="v">Cemento CPC 30R · gris</span></div>
          <div className="pg-kv-r"><span className="k">SKU</span><span className="v mono">CMTO-CPC30R-50KG</span></div>
          <div className="pg-kv-r"><span className="k">{T('Cantidad','Quantity')}</span><span className="v">50 × saco 50kg = 2,500kg</span></div>
          <div className="pg-kv-r"><span className="k">{T('Obra','Site')}</span><span className="v">Torre Sierra · SRR-01</span></div>
          <div className="pg-kv-r"><span className="k">{T('Entrega','Delivery')}</span><span className="v">Mañana 07:00</span></div>
          <div className="pg-kv-r"><span className="k">{T('Destino','Destination')}</span><span className="v">Zapopan · Av. López Mateos 2210</span></div>
          <div className="pg-kv-r"><span className="k">{T('Confianza','Confidence')}</span><span className="v" style={{ color:'#00A95F' }}>98%</span></div>
        </div>
        <div style={{ marginTop:14, padding:10, background:'var(--violet-soft)', borderRadius:8, fontSize:11, color:'var(--violet-ink)' }}>
          💡 <b>{T('Nico aprendió','Nico learned')}:</b> {T('"bultos" = sacos de 50kg (slang de GDL). Se queda en el diccionario de tu obra.','"bultos" = 50kg bags (GDL slang). Stored in your site dictionary.')}
        </div>
      </div>
    </div>
  );
}

/* Voice note */
function PgVoice({ lang, onCreateOrder, setToast }) {
  const T = (es, en) => window.pgT(lang, es, en);
  const [recording, setRecording] = useStateCap(false);
  const [transcribed, setTranscribed] = useStateCap(false);
  const [sent, setSent] = useStateCap(false);

  return (
    <div className="pg-grid-2" style={{ gridTemplateColumns:'1fr 1fr', alignItems:'start' }}>
      <div className="pg-card" style={{ padding:24, textAlign:'center' }}>
        <div style={{ fontSize:13, fontWeight:600, marginBottom:16 }}>{T('Graba una nota de voz','Record a voice note')}</div>
        <div style={{ display:'flex', justifyContent:'center', marginBottom:16 }}>
          <button
            onClick={() => { setRecording(true); setTimeout(() => { setRecording(false); setTranscribed(true); }, 2200); }}
            disabled={recording || transcribed}
            style={{
              width:96, height:96, borderRadius:'50%',
              background: recording ? 'linear-gradient(135deg, var(--orange), var(--pink))' : 'var(--violet)',
              border:'none', color:'white', fontSize:32, cursor:'pointer',
              boxShadow: recording ? '0 0 0 12px rgba(255,122,69,0.18)' : '0 10px 24px rgba(99,91,255,0.3)',
              animation: recording ? 'pulseDot 1s infinite' : 'none'
            }}
          >🎙️</button>
        </div>
        <div style={{ fontSize:12, color:'var(--ink-dim)' }}>{recording ? T('Grabando... 00:0'+Math.floor(Math.random()*9),'Recording... 00:0'+Math.floor(Math.random()*9)) : transcribed ? T('Nota de 14s capturada','14s note captured') : T('Toca para grabar','Tap to record')}</div>

        {recording && (
          <div style={{ marginTop:20, display:'flex', justifyContent:'center', gap:3, alignItems:'flex-end', height:40 }}>
            {Array.from({length:24}).map((_,i)=><div key={i} style={{ width:3, height: 8+Math.abs(Math.sin(i*0.7+Date.now()*0.005))*28, background:'var(--violet)', borderRadius:2, animation:'typingBounce '+(0.6+i*0.05)+'s infinite' }}/>)}
          </div>
        )}
      </div>

      <div className="pg-card">
        <div className="pg-sect-t">📝 {T('Transcripción','Transcript')}</div>
        <div style={{ padding:12, background:'var(--paper-2)', borderRadius:8, fontSize:13, lineHeight:1.5, minHeight:90 }}>
          {transcribed ? <>"<i>{T('Nico, pásame unas 30 bolsas de cemento tolteca pa mañana temprano, que nos lo manden acá a Puerto Alto. Y de una vez tantéame si tienen varilla del 3/8, como media tonelada.','Hey Nico, send me like 30 bags of Tolteca cement for tomorrow early, deliver to Puerto Alto. And while you\'re at it, check if they\'ve got 3/8" rebar, like half a ton.')}</i>"</> : <span style={{ color:'var(--ink-ghost)' }}>{T('Aún no hay audio','No audio yet')}</span>}
        </div>

        {transcribed && (
          <>
            <div className="pg-sect-t" style={{ marginTop:18 }}>⚡ {T('Nico extrajo 2 pedidos','Nico extracted 2 requests')}</div>
            <div className="pg-kv" style={{ gap:10 }}>
              <div style={{ padding:10, border:'1px solid var(--line)', borderRadius:8 }}>
                <div style={{ fontSize:12, fontWeight:600 }}>1. Cemento Tolteca 50kg × 30</div>
                <div style={{ fontSize:11, color:'var(--ink-dim)', marginTop:2 }}>Mañana 07:00 · Puerto Alto · PTA-02</div>
              </div>
              <div style={{ padding:10, border:'1px solid var(--line)', borderRadius:8 }}>
                <div style={{ fontSize:12, fontWeight:600 }}>2. Varilla 3/8" × 500kg</div>
                <div style={{ fontSize:11, color:'var(--ink-dim)', marginTop:2 }}>{T('Pendiente confirmar fecha','Pending date')}</div>
              </div>
            </div>
            <button disabled={sent} onClick={() => { onCreateOrder({ item:'Cemento Tolteca', qty:30, unit:'saco 50kg', site:'puerto' }); onCreateOrder({ item:'Varilla del 3/8"', qty:0.5, unit:'ton', site:'puerto' }); setSent(true); setToast({ msg: T('2 pedidos creados desde nota de voz','2 orders created from voice note'), type:'ok' }); }} className="pg-btn primary" style={{ marginTop:14, width:'100%', justifyContent:'center' }}>
              {sent ? '✓ ' + T('Enviado','Sent') : T('Confirmar y cotizar','Confirm & quote')}
            </button>
          </>
        )}
      </div>
    </div>
  );
}

/* Photo upload */
function PgPhoto({ lang, onCreateOrder, setToast }) {
  const T = (es, en) => window.pgT(lang, es, en);
  const [uploaded, setUploaded] = useStateCap(false);
  const [processed, setProcessed] = useStateCap(false);
  const items = [
    { n:'Cemento CPC 30R', q:'50 sacos' },
    { n:'Arena fina', q:'6 m³' },
    { n:'Grava 3/4"', q:'10 m³' },
    { n:'Varilla 3/8"', q:'1.2 ton' },
    { n:'Alambre recocido', q:'25 kg' },
    { n:'Clavos 2.5"', q:'10 kg' }
  ];

  return (
    <div className="pg-grid-2" style={{ gridTemplateColumns:'1fr 1.2fr', alignItems:'start' }}>
      <div>
        {!uploaded ? (
          <div className="pg-drop" onClick={() => { setUploaded(true); setTimeout(() => setProcessed(true), 1400); }}>
            <div className="pg-drop-ic">📸</div>
            <div className="pg-drop-t">{T('Sube foto de la lista','Upload photo of the list')}</div>
            <div className="pg-drop-d">{T('Libreta, plano, papel. JPEG/HEIC. Máx 8MB.','Notebook, plan, paper. JPEG/HEIC. Max 8MB.')}</div>
            <div style={{ marginTop:12, fontSize:11, color:'var(--violet-ink)', fontWeight:500 }}>{T('O toca para usar una imagen de ejemplo →','Or tap to use a sample image →')}</div>
          </div>
        ) : (
          <div className="pg-card pad-0">
            <div style={{ aspectRatio:'3/4', background:'linear-gradient(135deg, #F5EEDC 0%, #E8DCC4 100%)', position:'relative', overflow:'hidden' }}>
              {/* Fake notebook page with handwritten list */}
              <div style={{ position:'absolute', inset:24, fontFamily:'Caveat, cursive', fontSize:18, color:'#2C3E50', lineHeight:1.8 }}>
                <div style={{ fontSize:22, textDecoration:'underline', marginBottom:12 }}>Pedido 12-nov</div>
                {items.map((it, i) => (
                  <div key={i} style={{ opacity: processed ? 1 : 0.9, transition:'all 300ms', background: processed ? 'rgba(99,91,255,0.12)' : 'transparent', padding: processed ? '2px 6px' : 0, borderRadius:4 }}>
                    • {it.n} — {it.q}
                    {processed && <span style={{ position:'absolute', right:24, color:'#00A95F', fontSize:14, fontFamily:'inherit' }}>✓</span>}
                  </div>
                ))}
              </div>
              {!processed && <div style={{ position:'absolute', inset:0, background:'linear-gradient(180deg, transparent 40%, rgba(99,91,255,0.15) 50%, transparent 60%)', animation:'scan 2s linear infinite' }}/>}
              <div style={{ position:'absolute', top:10, left:10, padding:'4px 8px', background:'rgba(0,0,0,0.7)', color:'white', fontSize:10, fontFamily:'var(--font-mono)', borderRadius:4 }}>IMG_2847.jpg · 2.4MB</div>
            </div>
          </div>
        )}
      </div>

      <div className="pg-card">
        <div className="pg-sect-t">🧠 {T('Extracción por OCR + LLM','OCR + LLM extraction')}{processed && <span className="chip-sm" style={{ background:'#E8F5E9', color:'#2E7D32' }}>100%</span>}</div>
        {!uploaded && <div style={{ fontSize:12, color:'var(--ink-dim)' }}>{T('Sube una foto para ver la extracción automática.','Upload a photo to see automatic extraction.')}</div>}
        {uploaded && !processed && (
          <>
            <div className="pg-prog"><div className="pg-prog-bar" style={{ width:'45%' }}/></div>
            <div style={{ fontSize:11, color:'var(--ink-dim)', marginTop:6 }}>{T('Analizando imagen...','Analyzing image...')}</div>
          </>
        )}
        {processed && (
          <>
            <table className="pg-table" style={{ fontSize:11 }}>
              <thead><tr><th>#</th><th>{T('Material','Material')}</th><th>{T('Cantidad','Qty')}</th><th>SKU</th></tr></thead>
              <tbody>
                {items.map((it, i) => (
                  <tr key={i}><td style={{ fontFamily:'var(--font-mono)', color:'var(--ink-muted)' }}>{i+1}</td><td style={{ fontWeight:500 }}>{it.n}</td><td>{it.q}</td><td style={{ fontFamily:'var(--font-mono)', fontSize:10 }}>{(it.n.slice(0,3)+'-'+Math.floor(Math.random()*9000+1000)).toUpperCase()}</td></tr>
                ))}
              </tbody>
            </table>
            <div style={{ display:'flex', gap:8, marginTop:14 }}>
              <button className="pg-btn">{T('Editar','Edit')}</button>
              <button className="pg-btn primary" onClick={() => { items.forEach(it => onCreateOrder({ item:it.n, qty: parseFloat(it.q), unit:it.q.split(' ')[1], site:'sierra' })); setToast({ msg: T('6 pedidos creados desde la foto','6 orders created from photo'), type:'ok' }); }}>{T('Crear 6 pedidos','Create 6 orders')}</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

/* Kit */
function PgKit({ lang, onCreateOrder, setToast }) {
  const T = (es, en) => window.pgT(lang, es, en);
  const kits = [
    { id:'cim', ic:'🏗️', t:T('Cimentación (estándar)','Foundation (standard)'), d:T('Cemento, varilla, agregados, alambre, malla','Cement, rebar, aggregates, wire, mesh'), count:8, total:'$148,400' },
    { id:'los', ic:'🧱', t:T('Losa maciza 15cm','Solid slab 15cm'), d:T('Concreto premezclado + acero de refuerzo','Ready-mix + reinforcement steel'), count:5, total:'$212,800' },
    { id:'mur', ic:'🧱', t:T('Muros de carga','Load-bearing walls'), d:T('Block pesado, cemento, mortero, castillos','Heavy block, cement, mortar, columns'), count:6, total:'$67,500' },
    { id:'ins', ic:'⚡', t:T('Instalaciones eléctricas','Electrical'), d:T('Conduit, cable, contactos, apagadores','Conduit, cable, outlets, switches'), count:12, total:'$38,200' },
    { id:'pln', ic:'🔧', t:T('Plomería hidráulica','Plumbing'), d:T('PVC, CPVC, conexiones, llaves','PVC, CPVC, fittings, valves'), count:10, total:'$24,600' },
    { id:'aca', ic:'🎨', t:T('Acabados básicos','Basic finishes'), d:T('Aplanado, pintura, cerámica, resanes','Plaster, paint, tile, patching'), count:7, total:'$89,300' }
  ];
  const [selected, setSelected] = useStateCap(null);

  return (
    <>
      <div className="pg-sect-t">{T('Plantillas por etapa de obra','Templates by construction phase')} <span className="chip-sm">{kits.length} {T('kits','kits')}</span></div>
      <div className="pg-grid-3">
        {kits.map(k => (
          <div key={k.id} className={`pg-card ${selected === k.id ? 'pg-highlight' : ''}`} style={{ cursor:'pointer', position:'relative' }} onClick={() => setSelected(k.id)}>
            <div style={{ fontSize:24, marginBottom:8 }}>{k.ic}</div>
            <div style={{ fontWeight:600, fontSize:13, marginBottom:4 }}>{k.t}</div>
            <div style={{ fontSize:11, color:'var(--ink-dim)', marginBottom:10 }}>{k.d}</div>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', paddingTop:10, borderTop:'1px solid var(--line)' }}>
              <span style={{ fontSize:11, color:'var(--ink-muted)' }}>{k.count} {T('partidas','line items')}</span>
              <span style={{ fontFamily:'var(--font-mono)', fontWeight:600, fontSize:12 }}>{k.total}</span>
            </div>
            {selected === k.id && (
              <button className="pg-btn primary" style={{ width:'100%', marginTop:12, justifyContent:'center' }} onClick={(e) => { e.stopPropagation(); for (let i = 0; i < k.count; i++) onCreateOrder({ item: k.t+' #'+(i+1), qty:1, unit:'lote', site:'sierra' }); setToast({ msg: k.count + ' ' + T('pedidos generados desde el kit','orders generated from kit'), type:'ok' }); }}>
                {T('Generar pedidos del kit','Generate kit orders')}
              </button>
            )}
          </div>
        ))}
      </div>
    </>
  );
}

window.PgScreenCapture = PgScreenCapture;
