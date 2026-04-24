const TopBar = ({ onOpenModal }) => {
  const [t, setT] = React.useState(new Date());
  React.useEffect(()=>{const i=setInterval(()=>setT(new Date()),1000);return()=>clearInterval(i)},[]);
  return (
    <header style={{display:"flex",alignItems:"center",gap:18,height:56,padding:"0 20px",background:"var(--bg)",borderBottom:"1px solid var(--line)",position:"relative",zIndex:20}}>
      <div style={{display:"flex",alignItems:"center",gap:10}}>
        <svg width="22" height="22" viewBox="0 0 22 22"><rect width="22" height="22" rx="5" fill="var(--ink)"/><path d="M6 16L11 5L16 16M7.5 12.5H14.5" stroke="var(--bg)" strokeWidth="1.6" strokeLinecap="round"/></svg>
        <span style={{fontSize:15,fontWeight:600,letterSpacing:"-0.02em"}}>AXIS</span>
        <span className="pill" style={{marginLeft:2}}>v4.2</span>
      </div>

      <Divider vertical style={{height:18}}/>

      <nav style={{display:"flex",alignItems:"center",gap:4,fontSize:13,flex:1,minWidth:0,overflow:"hidden"}}>
        <span style={{color:"var(--ink-3)"}}>Operaciones MX</span>
        <Icon name="chevron-right" size={12} style={{color:"var(--ink-4)"}}/>
        <span style={{color:"var(--ink-3)"}}>Lácteos UHT Monterrey</span>
        <Icon name="chevron-right" size={12} style={{color:"var(--ink-4)"}}/>
        <span style={{fontWeight:600}}>Línea UHT-02</span>
        <span style={{marginLeft:10,display:"flex",gap:6}}>
          <Pill tone="live" dot>LIVE</Pill>
          <Pill>LOD 500</Pill>
        </span>
      </nav>

      <div className="mono" style={{display:"flex",alignItems:"center",gap:16,fontSize:11,color:"var(--ink-3)"}}>
        <span>edge <span style={{color:"var(--ink)"}}>12ms</span></span>
        <span>iot <span style={{color:"var(--ink)"}}>8,432/s</span></span>
        <span>{t.toLocaleTimeString('es-MX',{hour12:false})}</span>
      </div>

      <button className="btn sm" style={{minWidth:220,justifyContent:"space-between",color:"var(--ink-3)",fontWeight:400,background:"var(--surface)"}}>
        <span style={{display:"flex",alignItems:"center",gap:8}}><Icon name="search" size={13}/>Buscar activo, OT, documento</span>
        <kbd>⌘K</kbd>
      </button>

      <button className="btn icon sm" onClick={()=>onOpenModal('events')}>
        <Icon name="bell" size={14}/>
        <span style={{position:"absolute",transform:"translate(8px,-8px)",width:7,height:7,borderRadius:"50%",background:"var(--accent)"}}/>
      </button>
      <button className="btn icon sm" title="Cambiar tema" onClick={()=>{
        const cur = document.documentElement.querySelector('[data-theme]')?.getAttribute('data-theme') || 'light';
        const next = cur==='dark'?'light':'dark';
        window.dispatchEvent(new CustomEvent('axis-toggle-theme',{detail:next}));
      }}><Icon name="sun" size={14}/></button>
      <button className="btn icon sm" onClick={()=>onOpenModal('settings')}><Icon name="settings" size={14}/></button>

      <button style={{display:"flex",alignItems:"center",gap:8,padding:"2px 4px 2px 12px",background:"var(--surface)",border:"1px solid var(--line)",borderRadius:999,cursor:"pointer"}}>
        <span style={{fontSize:12.5,fontWeight:500}}>Luis H.</span>
        <span data-ink-bg style={{width:26,height:26,borderRadius:"50%",background:"var(--ink)",display:"grid",placeItems:"center",color:"#fff",fontSize:11,fontWeight:500}} className="mono">LH</span>
      </button>
    </header>
  );
};

Object.assign(window, { TopBar });
