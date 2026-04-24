// Copilot panel (Claude)

const Copilot = ({ onClose }) => {
  const [q, setQ] = React.useState('');
  const [thread, setThread] = React.useState([
    { role:'axis', text:'Hola Luis. Detecté 2 anomalías en turno A. Pregúntame o usa los atajos ↓', cites:[] },
  ]);

  const shortcuts = [
    { q:'¿Por qué bajó el OEE anoche?', a:'El paro no programado de 02:14 a 03:41 en BL-B02 (sopladora PET) causó −4.8 pts de OEE. Alarma raíz: PT-402 presión aire HP baja (2.1 bar vs SP 3.8). WO-45213 abierta en Maximo. ¿Ver en 3D?', cites:['asset: BL-B02','wo: 45213','alarm: PT-402'] },
    { q:'Estado F₀ UHT 24h', a:'F₀ acumulado promedio 6.4 min · margen 28% sobre setpoint regulatorio 5.0 min. Todos los lotes Q1 cumplen NOM-243-SSA1-2010.', cites:['tag: FT-304','doc: NOM-243-SSA1-2010.pdf'] },
    { q:'Integrity test filtros', a:'Último integrity test 2026-04-17 18:22. Pre-filtros 0.45µm: OK. Filtro estéril 0.2µm: OK, ΔP 0.3 bar (límite 0.8). Próximo: 2026-04-24.', cites:['asset: F-03-STER','wo: 45089'] },
  ];

  const send = (text) => {
    if (!text.trim()) return;
    const match = shortcuts.find(s => s.q.toLowerCase() === text.toLowerCase());
    setThread(t => [...t, { role:'user', text }]);
    setTimeout(() => {
      setThread(t => [...t, {
        role:'axis',
        text: match ? match.a : 'Consultando telemetría, WOs y documentos vinculados…',
        cites: match ? match.cites : []
      }]);
    }, 400);
    setQ('');
  };

  return (
    <div style={{
      width:380, flexShrink:0,
      background:"var(--surface)", border:"1px solid var(--border)", borderRadius:10,
      display:"flex", flexDirection:"column", overflow:"hidden"
    }}>
      <div style={{padding:"10px 14px", borderBottom:"1px solid var(--border)", display:"flex", alignItems:"center", justifyContent:"space-between"}}>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          <div style={{
            width:22,height:22,borderRadius:6,
            background:"linear-gradient(135deg,#111,#333)",
            display:"grid",placeItems:"center", color:"#fff"
          }}>
            <Icon name="sparkle" size={12}/>
          </div>
          <div>
            <div style={{fontSize:12.5, fontWeight:600}}>AXIS Copilot</div>
            <div className="mono" style={{fontSize:9.5, color:"var(--text-3)"}}>Claude · RAG · tu planta</div>
          </div>
        </div>
        <Pill tone="live" dot>READY</Pill>
      </div>

      <div style={{flex:1, overflowY:"auto", padding:14, display:"flex", flexDirection:"column", gap:10}}>
        {thread.map((m,i) => (
          <div key={i} style={{display:"flex", flexDirection: m.role==='user'?"row-reverse":"row", gap:8}}>
            {m.role==='axis' && (
              <div style={{width:22,height:22,borderRadius:6,background:"var(--surface-2)", border:"1px solid var(--border)", display:"grid",placeItems:"center", flexShrink:0}}>
                <Icon name="sparkle" size={11} style={{color:"var(--text-3)"}}/>
              </div>
            )}
            <div style={{
              maxWidth:"86%",
              padding:"8px 10px",
              borderRadius:10,
              background: m.role==='user'?"var(--text)":"var(--surface-2)",
              color: m.role==='user'?"#fff":"var(--text)",
              fontSize:12.5, lineHeight:1.5
            }}>
              {m.text}
              {m.cites && m.cites.length>0 && (
                <div style={{marginTop:6, display:"flex", flexWrap:"wrap", gap:4}}>
                  {m.cites.map(c=><span key={c} className="mono" style={{fontSize:9.5, padding:"1px 6px", background:"var(--surface)", border:"1px solid var(--border)", borderRadius:999, color:"var(--text-3)"}}>{c}</span>)}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      <div style={{padding:"8px 10px", borderTop:"1px solid var(--border)"}}>
        <div style={{display:"flex", gap:4, flexWrap:"wrap", marginBottom:8}}>
          {shortcuts.slice(0,3).map(s => (
            <button key={s.q} onClick={()=>send(s.q)} style={{
              height:22, padding:"0 8px", borderRadius:999,
              background:"var(--surface)", border:"1px solid var(--border)",
              fontSize:10.5, color:"var(--text-2)", cursor:"pointer"
            }}>{s.q}</button>
          ))}
        </div>
        <form onSubmit={e=>{e.preventDefault();send(q)}} style={{
          display:"flex", alignItems:"center", gap:6,
          padding:"4px 4px 4px 10px", border:"1px solid var(--border)", borderRadius:8,
          background:"var(--surface)"
        }}>
          <input value={q} onChange={e=>setQ(e.target.value)}
            placeholder="Pregúntale a AXIS…"
            style={{flex:1, border:"none", outline:"none", fontSize:12.5, background:"transparent", fontFamily:"inherit"}}/>
          <button type="submit" className="btn primary sm" style={{width:26, padding:0}}>
            <Icon name="send" size={12}/>
          </button>
        </form>
      </div>
    </div>
  );
};

Object.assign(window, { Copilot });
