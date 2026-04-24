const TopBar = ({ onOpenModal, compact }) => {
  const [time, setTime] = React.useState(() => new Date());
  React.useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  const fmt = (d) => d.toLocaleTimeString('es-MX', { hour12: false });

  return (
    <header style={{
      display:"flex", alignItems:"center", gap:14,
      height:48, padding:"0 14px 0 10px",
      background:"var(--surface)", borderBottom:"1px solid var(--border)",
      position:"relative", zIndex:20
    }}>
      {/* Logo */}
      <div style={{display:"flex",alignItems:"center",gap:10}}>
        <div style={{
          width:26, height:26, borderRadius:7,
          background:"var(--text)", color:"#fff",
          display:"grid", placeItems:"center",
          fontFamily:"var(--font-mono)", fontSize:13, fontWeight:600, letterSpacing:"-0.03em"
        }}>A</div>
        <span style={{fontSize:13.5, fontWeight:600, letterSpacing:"-0.015em"}}>AXIS</span>
      </div>

      <Divider vertical style={{height:20}}/>

      {/* Breadcrumbs */}
      <nav style={{display:"flex", alignItems:"center", gap:4, fontSize:12.5, color:"var(--text-3)", flex:1, minWidth:0, overflow:"hidden"}}>
        <button className="btn ghost sm" style={{fontWeight:500, color:"var(--text-3)", padding:"0 6px"}}>Operaciones MX</button>
        <Icon name="chevron-right" size={12}/>
        <button className="btn ghost sm" style={{fontWeight:500, color:"var(--text-3)", padding:"0 6px"}}>Planta Lácteos UHT Monterrey</button>
        <Icon name="chevron-right" size={12}/>
        <span style={{padding:"0 6px", color:"var(--text)", fontWeight:600}}>Línea UHT-02</span>
        <Pill tone="live" dot>LIVE</Pill>
        <Pill>LOD 500</Pill>
        <Pill>ASÉPTIC</Pill>
      </nav>

      {/* System stats */}
      <div style={{display:"flex", alignItems:"center", gap:12, fontFamily:"var(--font-mono)", fontSize:11, color:"var(--text-3)"}}>
        <span>Edge <span style={{color:"var(--text)"}}>12ms</span></span>
        <span>IoT <span style={{color:"var(--text)"}}>8,432/s</span></span>
        <span>v<span style={{color:"var(--text)"}}>4.2.1</span></span>
        <span>{fmt(time)}</span>
      </div>

      <Divider vertical style={{height:20}}/>

      {/* Search */}
      <button className="btn sm" style={{minWidth:180, justifyContent:"space-between", color:"var(--text-3)", fontWeight:400}}>
        <span style={{display:"flex",alignItems:"center",gap:6}}><Icon name="search" size={13}/>Buscar activo, WO, doc…</span>
        <kbd>⌘K</kbd>
      </button>

      {/* Actions */}
      <button className="btn icon sm" title="Notificaciones" onClick={()=>onOpenModal('events')}>
        <Icon name="bell" size={14}/>
        <span style={{position:"absolute",transform:"translate(6px,-7px)",width:6,height:6,borderRadius:"50%",background:"var(--err)"}}/>
      </button>
      <button className="btn icon sm" title="Configuración" onClick={()=>onOpenModal('settings')}>
        <Icon name="settings" size={14}/>
      </button>

      {/* User */}
      <button style={{
        display:"flex",alignItems:"center",gap:8, padding:"2px 2px 2px 10px",
        background:"var(--surface)", border:"1px solid var(--border)", borderRadius:999,
        cursor:"pointer"
      }}>
        <span style={{fontSize:12, fontWeight:500}}>Luis H.</span>
        <span style={{
          width:24, height:24, borderRadius:"50%",
          background:"linear-gradient(135deg, var(--accent), #ff884d)",
          display:"grid",placeItems:"center",
          color:"#fff", fontSize:11, fontWeight:600, fontFamily:"var(--font-mono)"
        }}>LH</span>
      </button>
    </header>
  );
};

Object.assign(window, { TopBar });
