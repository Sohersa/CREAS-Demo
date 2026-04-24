// Main app — wires everything together

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "orange",
  "type": "geist",
  "density": "balanced",
  "glass": "solid"
}/*EDITMODE-END*/;

const App = () => {
  const [tweaks, setTweaks] = React.useState(TWEAK_DEFAULTS);
  const [editMode, setEditMode] = React.useState(false);
  const [modal, setModal] = React.useState(null);
  const [selected, setSelected] = React.useState('UHT-01');
  const [layers, setLayers] = React.useState({arch:true,struct:true,mech:true,pipe:true,elec:false,instr:true,iot:true,alarm:true});
  const [size3d, setSize3d] = React.useState(70);

  // Tweaks protocol
  React.useEffect(() => {
    const onMsg = (e) => {
      if (e.data?.type === '__activate_edit_mode') setEditMode(true);
      if (e.data?.type === '__deactivate_edit_mode') setEditMode(false);
    };
    window.addEventListener('message', onMsg);
    window.parent.postMessage({type:'__edit_mode_available'}, '*');
    return () => window.removeEventListener('message', onMsg);
  }, []);

  // persist selection + modal in localStorage
  React.useEffect(() => {
    const saved = localStorage.getItem('axis-state');
    if (saved) try {
      const s = JSON.parse(saved);
      if (s.selected) setSelected(s.selected);
      if (s.size3d) setSize3d(s.size3d);
    } catch {}
  }, []);
  React.useEffect(() => {
    localStorage.setItem('axis-state', JSON.stringify({selected, size3d}));
  }, [selected, size3d]);

  const ModalComp = {
    sim: SimModal,
    dashboard: DashboardModal,
    pid: PIDModal,
    maximo: MaximoModal,
    analytics: AnalyticsModal,
    docs: DocsModal,
    events: EventsModal,
    settings: SettingsModal,
    history: HistoryModal,
  }[modal];

  return (
    <div data-accent={tweaks.accent} data-type={tweaks.type} data-density={tweaks.density} data-glass={tweaks.glass}
      style={{height:"100vh", display:"flex", flexDirection:"column", background:"var(--bg)"}}>
      <TopBar onOpenModal={setModal}/>
      <div style={{flex:1, display:"flex", minHeight:0}}>
        <Sidebar onOpenModal={setModal} currentModal={modal}/>

        <main style={{flex:1, display:"flex", flexDirection:"column", padding:14, gap:10, minWidth:0}}>
          {/* 3D + Inspector row — height driven by size3d */}
          <div style={{display:"flex", gap:10, flex: size3d/20, minHeight: 280}}>
            <div style={{flex:1, minWidth:0, position:"relative"}}>
              <Viewer3D
                selected={selected}
                onSelect={setSelected}
                layers={layers}
                setLayers={setLayers}
                size={size3d}
                onResize={setSize3d}
              />
            </div>
            {selected && <Inspector assetId={selected} onClose={()=>setSelected(null)} onOpenModal={setModal}/>}
          </div>

          {/* Time scrubber */}
          <TimeScrubber onOpenModal={setModal}/>

          {/* KPIs + Copilot */}
          <div style={{display:"flex", gap:10, flex: (100-size3d)/20, minHeight: 220}}>
            <div style={{flex:1, display:"flex", flexDirection:"column", gap:10, minWidth:0}}>
              <div style={{flex:1}}><KpiBar/></div>
              {/* Active alarms bar */}
              <div className="card" style={{padding:"10px 14px", display:"flex",alignItems:"center",gap:12}}>
                <div style={{display:"flex",alignItems:"center",gap:8}}>
                  <span className="eyebrow">Alarmas activas</span>
                  <span className="mono" style={{fontSize:14, fontWeight:600, color:"var(--err)"}}>3</span>
                </div>
                <Divider vertical style={{height:24}}/>
                <div style={{flex:1, display:"flex", gap:8, overflow:"hidden"}}>
                  {[
                    { sev:'err', t:'02:14', msg:'BL-B02 · PT-402 presión HP baja' },
                    { sev:'warn', t:'09:22', msg:'FI-F03 · FT-303 flujo fuera de banda' },
                    { sev:'err', t:'16:42', msg:'PT-402 · Anomalía detectada' },
                  ].map((a,i)=>(
                    <button key={i} className="btn sm" style={{flexShrink:0, fontWeight:400}}>
                      <span style={{width:6,height:6,borderRadius:"50%",background:a.sev==='err'?"var(--err)":"var(--warn)"}}/>
                      <span className="mono" style={{fontSize:10.5, color:"var(--text-3)"}}>{a.t}</span>
                      <span style={{fontSize:11.5}}>{a.msg}</span>
                    </button>
                  ))}
                </div>
                <button className="btn sm" onClick={()=>setModal('events')}>Ver todas →</button>
              </div>
            </div>
            <Copilot/>
          </div>
        </main>
      </div>

      {/* Footer microbar */}
      <div style={{height:22, borderTop:"1px solid var(--border)", background:"var(--surface)", display:"flex",alignItems:"center",padding:"0 14px", gap:14, fontFamily:"var(--font-mono)", fontSize:10, color:"var(--text-3)"}}>
        <span>AXIS · EY CREAS · demo · datos simulados</span>
        <span>·</span>
        <span>build 4.2.1</span>
        <span>·</span>
        <span style={{display:"flex",alignItems:"center",gap:4}}><span style={{width:5,height:5,borderRadius:"50%",background:"var(--ok)"}} className="live-dot"/>kafka ok</span>
        <span>·</span>
        <span>keycloak ok</span>
        <span>·</span>
        <span>timescale ok</span>
        <div style={{flex:1}}/>
        <span>CST · {new Date().toLocaleDateString('es-MX')}</span>
      </div>

      {ModalComp && <ModalComp onClose={()=>setModal(null)}/>}
      {editMode && <TweaksPanel tweaks={tweaks} setTweaks={setTweaks} onClose={()=>setEditMode(false)}/>}
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
