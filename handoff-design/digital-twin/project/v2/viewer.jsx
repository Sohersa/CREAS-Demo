// Viewer v2.1 — 3D MOUNT SLOT + draggable resize handle
//
// ╔══════════════════════════════════════════════════════════════════════════╗
// ║  INTEGRACIÓN DEL MODELO 3D REAL                                          ║
// ║                                                                          ║
// ║  El componente <ThreeDSlot/> es el contenedor vacío donde se debe        ║
// ║  montar el visor 3D real (Three.js / Babylon / react-three-fiber /       ║
// ║  Autodesk Forge Viewer, etc.).                                           ║
// ║                                                                          ║
// ║  Opciones de integración:                                                ║
// ║                                                                          ║
// ║  1) React-three-fiber / Three.js:                                        ║
// ║     reemplaza el contenido de <ThreeDSlot/> por:                         ║
// ║       <Canvas>                                                           ║
// ║         <YourScene selected={selected} onSelect={onSelect}/>             ║
// ║       </Canvas>                                                          ║
// ║                                                                          ║
// ║  2) iframe (Unity WebGL, Autodesk Forge, Matterport):                    ║
// ║       <iframe src="/your-3d-viewer" style={{width:'100%',height:'100%', ║
// ║                border:0}} allow="xr-spatial-tracking"/>                  ║
// ║                                                                          ║
// ║  3) Canvas/WebGL nativo:                                                 ║
// ║       <canvas ref={canvasRef} style={{width:'100%',height:'100%'}}/>     ║
// ║                                                                          ║
// ║  PROPS QUE SE DEBEN PASAR AL VISOR:                                      ║
// ║   - selected:   id del activo seleccionado (string)                      ║
// ║   - onSelect:   callback(id) al hacer click en un mesh                   ║
// ║   - layers:     objeto { arch, struct, mech, pipe, elec, instr, iot,     ║
// ║                 alarm } con booleanos de visibilidad                     ║
// ║   - viewMode:   'iso' | 'top' | 'front'                                  ║
// ║   - zoom:       número (0.4 – 2.0)                                       ║
// ║                                                                          ║
// ║  EVENTOS QUE EL VISOR DEBE EMITIR:                                       ║
// ║   - onSelect(assetId)    → al clickear un componente                     ║
// ║   - onHover(assetId)     → al hover (opcional, para tooltip)             ║
// ║   - onReady()            → cuando el modelo terminó de cargar            ║
// ╚══════════════════════════════════════════════════════════════════════════╝

const LAYER_DEFS = [
  { id:'arch', label:'Arquitectura', on:true },
  { id:'struct', label:'Estructura', on:true },
  { id:'mech', label:'Mecánico', on:true },
  { id:'pipe', label:'Piping', on:true },
  { id:'elec', label:'Eléctrico', on:false },
  { id:'instr', label:'Instrumentación', on:true },
  { id:'iot', label:'IoT overlay', on:true },
  { id:'alarm', label:'Alarmas', on:true },
];

// ═══════════════════════════════════════════════════════════════════════════
//  THREE-D SLOT — mount point for real 3D viewer
// ═══════════════════════════════════════════════════════════════════════════
const ThreeDSlot = ({ selected, onSelect, layers, viewMode, zoom }) => {
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  //  ⬇⬇⬇  AQUÍ VA EL MODELO 3D REAL  ⬇⬇⬇
  //
  //  Reemplaza todo el contenido del return() por el montaje de tu visor.
  //  Ejemplo react-three-fiber:
  //
  //    return (
  //      <Canvas camera={{position:[10,8,10]}} style={{width:'100%',height:'100%'}}>
  //        <PlantScene
  //          selected={selected}
  //          onSelect={onSelect}
  //          layers={layers}
  //          viewMode={viewMode}
  //          zoom={zoom}
  //        />
  //      </Canvas>
  //    );
  //
  //  Ejemplo iframe (Forge / Unity WebGL):
  //
  //    return (
  //      <iframe
  //        src={`/viewer3d?asset=${selected}&mode=${viewMode}`}
  //        style={{width:'100%',height:'100%',border:0,borderRadius:20}}
  //        title="AXIS 3D Viewer"
  //      />
  //    );
  //
  //  Por ahora: placeholder informativo.
  // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  return (
    <div style={{width:"100%",height:"100%",position:"relative",overflow:"hidden",
      background:"var(--surface)",borderRadius:20,
      display:"flex",alignItems:"center",justifyContent:"center"}} data-role="viewer-3d-bg">

      {/* dotgrid + axis lines — puramente estético, se reemplaza al montar el visor */}
      <div className="dotgrid" style={{position:"absolute",inset:0,opacity:0.6}}/>
      <svg style={{position:"absolute",inset:0,width:"100%",height:"100%"}} viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid meet">
        <g stroke="var(--line-strong)" strokeWidth="1" fill="none" opacity="0.35">
          <path d="M 100 500 L 900 500 M 100 500 L 100 100 M 100 500 L 500 300"/>
          <text x="905" y="504" fontSize="10" fontFamily="var(--font-mono)" fill="var(--ink-3)">X</text>
          <text x="100" y="92" fontSize="10" fontFamily="var(--font-mono)" fill="var(--ink-3)">Z</text>
          <text x="510" y="296" fontSize="10" fontFamily="var(--font-mono)" fill="var(--ink-3)">Y</text>
        </g>
      </svg>

      {/* Mount point card */}
      <div style={{textAlign:"center",padding:"40px 48px",maxWidth:520,position:"relative",zIndex:1}}>
        <div data-ink-bg style={{display:"inline-flex",width:68,height:68,borderRadius:0,background:"var(--accent)",
          color:"#fff",alignItems:"center",justifyContent:"center",marginBottom:22,
          boxShadow:"0 0 40px -8px var(--accent), 0 0 0 1px var(--accent), inset 0 0 0 1px rgba(255,255,255,.15)",
          transform:"rotate(45deg)"}}>
          <div style={{transform:"rotate(-45deg)"}}><Icon name="cube" size={30}/></div>
        </div>
        <div className="eyebrow" style={{marginBottom:8}}>Slot de montaje</div>
        <h3 style={{margin:0,fontSize:26,lineHeight:1.05,letterSpacing:"-0.035em",fontWeight:600}}>
          Aquí se monta el<br/>modelo 3D real
        </h3>
        <p style={{fontSize:13,color:"var(--ink-3)",lineHeight:1.55,marginTop:14,marginBottom:22}}>
          Componente <span className="mono" style={{background:"var(--bg-2)",padding:"1px 6px",borderRadius:4,fontSize:11.5}}>&lt;ThreeDSlot/&gt;</span> en <span className="mono" style={{background:"var(--bg-2)",padding:"1px 6px",borderRadius:4,fontSize:11.5}}>v2/viewer.jsx</span>.
          Reemplazar el contenido por el visor real (three.js, react-three-fiber, Forge, Unity WebGL, iframe, etc.).
          Las props <span className="mono" style={{fontSize:11.5}}>selected · onSelect · layers · viewMode · zoom</span> ya están conectadas.
        </p>
        <div style={{display:"flex",gap:8,justifyContent:"center",flexWrap:"wrap"}}>
          <Pill>selected: <span className="mono" style={{marginLeft:4}}>{selected||'—'}</span></Pill>
          <Pill>view: <span className="mono" style={{marginLeft:4}}>{viewMode}</span></Pill>
          <Pill>zoom: <span className="mono" style={{marginLeft:4}}>{Math.round(zoom*100)}%</span></Pill>
          <Pill>layers on: <span className="mono" style={{marginLeft:4}}>{Object.values(layers).filter(Boolean).length}</span></Pill>
        </div>
      </div>

      {/* Dashed frame — solo para marcar el área reservada */}
      <div style={{position:"absolute",top:18,left:18,right:18,bottom:18,border:"1.5px dashed var(--line-strong)",borderRadius:14,pointerEvents:"none"}}/>
      <div style={{position:"absolute",top:26,left:28,fontFamily:"var(--font-mono)",fontSize:10,color:"var(--ink-4)",letterSpacing:".08em",textTransform:"uppercase"}}>
        ◊ 3d mount area
      </div>
    </div>
  );
};

// ═══════════════════════════════════════════════════════════════════════════
//  VIEWER shell — controls + draggable resize handle
// ═══════════════════════════════════════════════════════════════════════════
const Viewer = ({ selected, onSelect, layers, setLayers, onResizeStart }) => {
  const [zoom,setZoom] = React.useState(1);
  const [mode,setMode] = React.useState('iso');

  return (
    <div className="noise" style={{position:"relative",width:"100%",height:"100%",overflow:"hidden",
      background:"var(--surface)",borderRadius:20,border:"1px solid var(--line)"}}>

      {/* 3D mount */}
      <div style={{position:"absolute",inset:0,transform:`scale(${zoom})`,transformOrigin:"center",transition:"transform .22s"}}>
        <ThreeDSlot selected={selected} onSelect={onSelect} layers={layers} viewMode={mode} zoom={zoom}/>
      </div>

      {/* Corner marks */}
      {[[14,14,"tl"],[14,"b","bl"],["r",14,"tr"],["r","b","br"]].map((p)=>{
        const s = {position:"absolute",width:10,height:10,pointerEvents:"none"};
        if(p[0]==="r") s.right=14; else s.left=p[0];
        if(p[1]==="b") s.bottom=14; else s.top=p[1];
        s.borderTop = p[1]!=="b" ? "1px solid var(--ink)" : "none";
        s.borderBottom = p[1]==="b" ? "1px solid var(--ink)" : "none";
        s.borderLeft = p[0]!=="r" ? "1px solid var(--ink)" : "none";
        s.borderRight = p[0]==="r" ? "1px solid var(--ink)" : "none";
        return <div key={p[2]} style={s}/>;
      })}

      {/* Title caption — top-left */}
      <div style={{position:"absolute",top:26,left:40,pointerEvents:"none"}}>
        <div className="eyebrow" style={{color:"var(--ink-3)"}}>FIG. 01 · LÍNEA UHT-02</div>
        <div className="mono" style={{fontSize:10,color:"var(--ink-4)",marginTop:2,letterSpacing:".08em"}}>ISO · ESC 1:120 · LOD 500</div>
      </div>

      {/* Coordinates — bottom-right */}
      <div style={{position:"absolute",bottom:26,right:40,fontFamily:"var(--font-mono)",fontSize:10,color:"var(--ink-4)",textAlign:"right",pointerEvents:"none"}}>
        <div>N 25°41'18" · W 100°18'42"</div>
        <div>ELEV 538 m · NAVE 2</div>
      </div>

      {/* LAYERS — bottom-left */}
      <div className="floating" style={{position:"absolute",left:20,bottom:20,padding:14,borderRadius:14,width:218,zIndex:4}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"baseline",marginBottom:10}}>
          <span className="eyebrow">Capas</span>
          <button className="btn xs ghost" style={{padding:"0 6px",height:16,fontSize:10}}>reset</button>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:6}}>
          {LAYER_DEFS.map(l=>{
            const on = layers[l.id] ?? l.on;
            return (
              <button key={l.id} onClick={()=>setLayers({...layers,[l.id]:!on})} style={{
                display:"flex",alignItems:"center",gap:10,background:"transparent",border:"none",padding:0,cursor:"pointer",textAlign:"left"
              }}>
                <span style={{width:22,height:12,borderRadius:999,background:on?"var(--ink)":"var(--line-strong)",position:"relative",transition:".15s",flexShrink:0}}>
                  <span style={{position:"absolute",top:1,left:on?11:1,width:10,height:10,borderRadius:"50%",background:"#fff",transition:".15s"}}/>
                </span>
                <span style={{fontSize:12,color:on?"var(--ink)":"var(--ink-3)",flex:1}}>{l.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* View mode — top right */}
      <div className="floating" style={{position:"absolute",top:20,right:20,padding:4,borderRadius:999,display:"flex",gap:2,zIndex:4}}>
        {['iso','top','front'].map(m=>(
          <button key={m} onClick={()=>setMode(m)} data-ink-bg={mode===m?"":undefined} style={{
            height:28,padding:"0 12px",borderRadius:999,
            background:mode===m?"var(--ink)":"transparent",
            color:mode===m?"#fff":"var(--ink-3)",
            border:"none",cursor:"pointer",
            fontFamily:"var(--font-mono)",fontSize:10.5,letterSpacing:".08em",textTransform:"uppercase",fontWeight:500
          }}>{m}</button>
        ))}
      </div>

      {/* Zoom — right bottom */}
      <div className="floating" style={{position:"absolute",right:20,bottom:20,padding:12,borderRadius:14,display:"flex",flexDirection:"column",gap:8,width:180,zIndex:4}}>
        <div style={{display:"flex",justifyContent:"space-between",marginBottom:2}}>
          <span className="eyebrow">Zoom</span>
          <span className="num" style={{fontSize:10,color:"var(--ink-3)"}}>{Math.round(zoom*100)}%</span>
        </div>
        <div style={{display:"flex",alignItems:"center",gap:4}}>
          <button className="btn icon xs" onClick={()=>setZoom(z=>Math.max(.4,z-.15))}><Icon name="minus" size={11}/></button>
          <input type="range" className="ax" min="40" max="200" step="5" value={Math.round(zoom*100)} onChange={e=>setZoom(+e.target.value/100)} style={{flex:1}}/>
          <button className="btn icon xs" onClick={()=>setZoom(z=>Math.min(2,z+.15))}><Icon name="plus" size={11}/></button>
        </div>
      </div>

      {/* ═══ RESIZE HANDLE — right edge, drag left/right to resize 3D panel ═══ */}
      <div
        onMouseDown={onResizeStart}
        title="Arrastra para ajustar el tamaño del panel 3D"
        style={{
          position:"absolute",top:0,right:-5,width:10,height:"100%",
          cursor:"col-resize",zIndex:5,
          display:"flex",alignItems:"center",justifyContent:"center"
        }}>
        <div style={{
          width:4,height:64,borderRadius:999,background:"var(--line-strong)",
          transition:"background .15s"
        }}
        onMouseEnter={e=>e.currentTarget.style.background="var(--ink)"}
        onMouseLeave={e=>e.currentTarget.style.background="var(--line-strong)"}
        />
      </div>
    </div>
  );
};

Object.assign(window,{Viewer});
