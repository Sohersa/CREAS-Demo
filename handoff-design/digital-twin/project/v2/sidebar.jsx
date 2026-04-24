const NAV = [
  { id:'home', icon:'home', label:'Inicio' },
  { id:'twin', icon:'cube', label:'Twin', active:true },
  { id:'analytics', icon:'chart', label:'Analytics', modal:'analytics' },
  { id:'mtto', icon:'wrench', label:'Mantto', modal:'maximo' },
  { id:'docs', icon:'doc', label:'Docs', modal:'docs' },
  { id:'sim', icon:'sim', label:'Sim', modal:'sim' },
  { id:'events', icon:'bell', label:'Eventos', modal:'events' },
];
const Sidebar = ({ onOpenModal, currentModal }) => (
  <aside style={{width:64,background:"var(--bg)",borderRight:"1px solid var(--line)",display:"flex",flexDirection:"column",alignItems:"center",gap:2,padding:"14px 0",flexShrink:0}}>
    {NAV.map(it=>{
      const active = it.active || currentModal===it.modal;
      return (
        <button key={it.id} onClick={()=>it.modal&&onOpenModal(it.modal)} title={it.label} data-ink-bg={active?"":undefined} style={{
          width:44,height:44,borderRadius:12,border:"none",cursor:"pointer",
          background: active?"var(--ink)":"transparent",
          color: active?"#fff":"var(--ink-3)",
          display:"grid",placeItems:"center",position:"relative"
        }}>
          <Icon name={it.icon} size={17}/>
        </button>
      );
    })}
    <div style={{flex:1}}/>
    <button onClick={()=>onOpenModal('dashboard')} title="Dashboard" style={{width:44,height:44,borderRadius:12,border:"1px dashed var(--line-strong)",background:"transparent",cursor:"pointer",color:"var(--ink-3)",display:"grid",placeItems:"center"}}>
      <Icon name="grid" size={15}/>
    </button>
  </aside>
);
Object.assign(window,{Sidebar});
