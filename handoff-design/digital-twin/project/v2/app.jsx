const DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "graphite",
  "type": "geist",
  "density": "spacious",
  "glass": "solid",
  "theme": "dark"
}/*EDITMODE-END*/;

function App(){
  const [tweaks,setTweaks] = React.useState(DEFAULTS);
  const [tweakVisible,setTweakVisible] = React.useState(false);
  const [selected,setSelected] = React.useState('UHT-01');
  const [modal,setModal] = React.useState(null);
  const [copilot,setCopilot] = React.useState(true);
  const [layers,setLayers] = React.useState({arch:true,struct:true,mech:true,pipe:true,elec:false,instr:true,iot:true,alarm:true});
  const containerRef = React.useRef(null);
  const [viewerWidth,setViewerWidth] = React.useState(0); // px; 0 = auto (use flex default)
  const dragStateRef = React.useRef(null);

  // ── Drag to resize 3D panel ─────────────────────────────────────────────
  const handleResizeStart = (e) => {
    e.preventDefault();
    const startX = e.clientX;
    const container = containerRef.current;
    if (!container) return;
    const containerRect = container.getBoundingClientRect();
    const viewerEl = container.querySelector('[data-role="viewer-slot"]');
    const startWidth = viewerEl ? viewerEl.getBoundingClientRect().width : containerRect.width * 0.7;
    dragStateRef.current = { startX, startWidth, maxW: containerRect.width - 396 /* inspector + gap */, minW: 360 };
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
    const onMove = (ev) => {
      const st = dragStateRef.current; if (!st) return;
      const dx = ev.clientX - st.startX;
      const nw = Math.max(st.minW, Math.min(st.maxW, st.startWidth + dx));
      setViewerWidth(nw);
    };
    const onUp = () => {
      dragStateRef.current = null;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };

  React.useEffect(()=>{
    const onMsg = e => {
      const d = e.data || {};
      if (d.type==='__activate_edit_mode') setTweakVisible(true);
      if (d.type==='__deactivate_edit_mode') setTweakVisible(false);
    };
    const onToggle = e => {
      const next = e.detail || (tweaks.theme==='dark'?'light':'dark');
      setTweaks(t=>({...t,theme:next}));
      window.parent.postMessage({type:'__edit_mode_set_keys',edits:{theme:next}},'*');
    };
    window.addEventListener('message', onMsg);
    window.addEventListener('axis-toggle-theme', onToggle);
    window.parent.postMessage({type:'__edit_mode_available'},'*');
    return ()=>{window.removeEventListener('message',onMsg);window.removeEventListener('axis-toggle-theme',onToggle)};
  },[tweaks.theme]);

  return (
    <div data-accent={tweaks.accent} data-type={tweaks.type} data-density={tweaks.density} data-glass={tweaks.glass} data-theme={tweaks.theme}
      style={{minHeight:"100vh",display:"flex",flexDirection:"column",background:"var(--bg)",color:"var(--ink)"}}>
      <TopBar onOpenModal={setModal}/>
      <div style={{display:"flex",flex:1,minHeight:0}}>
        <Sidebar onOpenModal={setModal} currentModal={modal}/>
        <div style={{flex:1,display:"flex",flexDirection:"column",minWidth:0,overflow:"hidden"}}>
          <Hero onOpenModal={setModal}/>
          <div ref={containerRef} style={{flex:1,padding:"20px 24px",display:"flex",gap:16,minHeight:0,overflow:"hidden"}}>
            <div data-role="viewer-slot" style={{
              width: viewerWidth ? viewerWidth+"px" : "auto",
              flex: viewerWidth ? "0 0 auto" : "1 1 0%",
              minWidth:360,display:"flex",position:"relative"
            }}>
              <Viewer selected={selected} onSelect={setSelected} layers={layers} setLayers={setLayers} onResizeStart={handleResizeStart}/>
            </div>
            <Inspector assetId={selected} onClose={()=>setSelected(null)} onOpenModal={setModal}/>
          </div>
        </div>
      </div>
      {copilot && <Copilot onClose={()=>setCopilot(false)}/>}
      {!copilot && (
        <button className="btn accent" onClick={()=>setCopilot(true)} style={{position:"fixed",right:22,bottom:22,height:44,borderRadius:999,padding:"0 18px",zIndex:50,boxShadow:"0 10px 30px -6px rgba(10,10,10,.25)"}}>
          <Icon name="sparkle" size={14}/>Copiloto
        </button>
      )}
      <Modals open={modal} onClose={()=>setModal(null)}/>
      <TweakPanel state={tweaks} setState={setTweaks} visible={tweakVisible} onClose={()=>setTweakVisible(false)}/>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App/>);
