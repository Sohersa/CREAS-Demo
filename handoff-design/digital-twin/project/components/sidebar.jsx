const SIDEBAR_ITEMS = [
  { id:'home', icon:'home', label:'Inicio' },
  { id:'twin', icon:'cube', label:'Digital Twin', active:true },
  { id:'analytics', icon:'chart', label:'Analytics', modal:'analytics' },
  { id:'mtto', icon:'wrench', label:'Mantenimiento', modal:'maximo' },
  { id:'docs', icon:'doc', label:'Documentos', modal:'docs' },
  { id:'sim', icon:'sim', label:'Simulación', modal:'sim' },
  { id:'events', icon:'bell', label:'Eventos', modal:'events' },
  { id:'copilot', icon:'bot', label:'Copilot', modal:'copilot' },
];

const Sidebar = ({ onOpenModal, currentModal }) => {
  return (
    <aside style={{
      width:56, background:"var(--surface)", borderRight:"1px solid var(--border)",
      display:"flex", flexDirection:"column", padding:"10px 0 10px 0", gap:2, flexShrink:0,
      position:"relative", zIndex:15
    }}>
      {SIDEBAR_ITEMS.map(item => {
        const isActive = item.active || currentModal === item.modal;
        return (
          <button
            key={item.id}
            onClick={() => item.modal && onOpenModal(item.modal)}
            title={item.label}
            style={{
              display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center",
              gap:2, height:44, margin:"0 8px", borderRadius:8,
              background: isActive ? "var(--surface-2)" : "transparent",
              color: isActive ? "var(--text)" : "var(--text-3)",
              border:"none", cursor:"pointer",
              position:"relative"
            }}
            onMouseEnter={(e)=>{if(!isActive) e.currentTarget.style.background="var(--surface-2)"}}
            onMouseLeave={(e)=>{if(!isActive) e.currentTarget.style.background="transparent"}}
          >
            {isActive && <span style={{position:"absolute",left:-8,top:10,bottom:10,width:2,borderRadius:2,background:"var(--accent)"}}/>}
            <Icon name={item.icon} size={16}/>
            <span style={{fontSize:9, fontFamily:"var(--font-mono)", letterSpacing:"0.02em"}}>{item.label.slice(0,6)}</span>
          </button>
        );
      })}
      <div style={{flex:1}}/>
      <button title="Dashboard Ejecutivo" onClick={()=>onOpenModal('dashboard')} style={{
        margin:"0 8px", height:40, borderRadius:8, border:"1px dashed var(--border-strong)",
        background:"transparent", color:"var(--text-3)", cursor:"pointer",
        display:"grid", placeItems:"center"
      }}>
        <Icon name="grid" size={15}/>
      </button>
    </aside>
  );
};

Object.assign(window, { Sidebar });
