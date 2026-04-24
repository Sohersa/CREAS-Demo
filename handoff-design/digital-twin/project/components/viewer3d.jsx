// Placeholder 3D viewer — isometric SVG of the line + floating controls, zoom, pan, layer toggles
// and an elegant selection state. Not real three.js; it's a representative mock.

const LAYERS = [
  { id:'arch', label:'Arquitectura', color:'#c7c2bb', on:true },
  { id:'struct', label:'Estructura', color:'#928e87', on:true },
  { id:'mech', label:'Mecánico', color:'#111', on:true },
  { id:'pipe', label:'Piping', color:'#1F6FEB', on:true },
  { id:'elec', label:'Eléctrico', color:'#B5730C', on:false },
  { id:'instr', label:'Instrumentación', color:'#2B8A3E', on:true },
  { id:'iot', label:'IoT Overlay', color:'#FF5500', on:true },
  { id:'alarm', label:'Alarmas', color:'#C23A3A', on:true },
];

const SENSORS = [
  { id:'PT-201', x:380, y:200, value:'4.82 bar', tone:'ok' },
  { id:'TT-114', x:520, y:260, value:'138.2°C', tone:'ok' },
  { id:'FT-303', x:660, y:340, value:'24,810 bph', tone:'warn' },
  { id:'PT-402', x:770, y:250, value:'2.1 bar', tone:'err' },
  { id:'VT-501', x:280, y:330, value:'72.4 rpm', tone:'ok' },
];

const ASSETS = [
  { id:'RC-01', name:'Recepción', x:90, y:300, w:70, h:90, stage:'recepcion' },
  { id:'PT-01', name:'Pasteurizador', x:190, y:260, w:90, h:130, stage:'past', alarm:false },
  { id:'HG-01', name:'Homogenizador', x:320, y:240, w:70, h:150, stage:'homo' },
  { id:'UHT-01', name:'UHT Aséptico', x:420, y:200, w:120, h:190, stage:'uht', selected:true },
  { id:'BL-B02', name:'Sopladora PET', x:580, y:270, w:100, h:120, stage:'blow', alarm:true },
  { id:'FI-F03', name:'Llenadora', x:710, y:290, w:90, h:100, stage:'fill', warn:true },
  { id:'LB-02', name:'Etiquetadora', x:820, y:310, w:70, h:80, stage:'label' },
  { id:'PK-01', name:'Empaque', x:910, y:330, w:80, h:60, stage:'pack' },
];

const Viewer3D = ({ selected, onSelect, layers, setLayers, size, onResize }) => {
  const [zoom, setZoom] = React.useState(1);
  const [mode, setMode] = React.useState('iso'); // iso | top | front

  return (
    <div style={{position:"relative", width:"100%", height:"100%", overflow:"hidden",
      background:"linear-gradient(180deg, #fafaf9 0%, #f3f2ef 100%)",
      borderRadius:10, border:"1px solid var(--border)"
    }} className="dotgrid">

      {/* Canvas area */}
      <svg width="100%" height="100%" viewBox="0 0 1000 560" preserveAspectRatio="xMidYMid meet"
        style={{position:"absolute", inset:0, transform:`scale(${zoom})`, transformOrigin:"center", transition:"transform .2s"}}
      >
        {/* floor grid */}
        <defs>
          <pattern id="floor" width="40" height="40" patternUnits="userSpaceOnUse" patternTransform="skewX(-30)">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e5e2dd" strokeWidth="0.8"/>
          </pattern>
          <linearGradient id="metal" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor="#f5f4f1"/>
            <stop offset="1" stopColor="#d6d3cd"/>
          </linearGradient>
          <linearGradient id="accentMetal" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor="#FFF1EA"/>
            <stop offset="1" stopColor="#FFD4BD"/>
          </linearGradient>
          <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="2" floodOpacity="0.08"/>
          </filter>
        </defs>

        <rect x="50" y="380" width="920" height="140" fill="url(#floor)"/>
        <rect x="50" y="380" width="920" height="140" fill="none" stroke="#d6d3cd" strokeDasharray="3 4" strokeWidth="0.8"/>

        {/* piping layer */}
        {layers.pipe && (
          <g stroke="#1F6FEB" strokeWidth="2" fill="none" opacity="0.55" strokeLinecap="round">
            <path d="M 160 340 L 190 320 L 320 320 L 420 280"/>
            <path d="M 420 280 L 580 310"/>
            <path d="M 580 310 L 710 330 L 820 340 L 910 350"/>
            <path d="M 420 220 Q 470 160 540 200" strokeWidth="1.5"/>
          </g>
        )}

        {/* assets */}
        {ASSETS.map(a => {
          const isSel = selected === a.id;
          const isAlarm = a.alarm && layers.alarm;
          const isWarn = a.warn;
          return (
            <g key={a.id} style={{cursor:"pointer"}} onClick={()=>onSelect(a.id)} filter="url(#soft)">
              {/* shadow base */}
              <ellipse cx={a.x + a.w/2} cy={a.y + a.h + 4} rx={a.w/2} ry="4" fill="rgba(0,0,0,.07)"/>
              {/* body */}
              <rect x={a.x} y={a.y} width={a.w} height={a.h} rx="3"
                fill={isSel ? "url(#accentMetal)" : "url(#metal)"}
                stroke={isSel ? "var(--accent)" : isAlarm ? "var(--err)" : isWarn ? "var(--warn)" : "#a3a09a"}
                strokeWidth={isSel ? 2 : 1}
              />
              {/* top face skewed */}
              <polygon
                points={`${a.x},${a.y} ${a.x+a.w},${a.y} ${a.x+a.w-14},${a.y-10} ${a.x-14},${a.y-10}`}
                fill={isSel ? "#FFD4BD" : "#e7e4df"}
                stroke={isSel ? "var(--accent)" : "#a3a09a"}
                strokeWidth={isSel ? 1.5 : 1}
              />
              {/* tag */}
              <g transform={`translate(${a.x + a.w/2}, ${a.y - 18})`}>
                <rect x="-32" y="-10" width="64" height="18" rx="4" fill="#fff" stroke={isSel?"var(--accent)":"#d6d3cd"}/>
                <text textAnchor="middle" y="3" fontSize="10" fontFamily="var(--font-mono)" fill={isSel?"var(--accent)":"#454545"} fontWeight="600">{a.id}</text>
              </g>
              {isAlarm && (
                <circle cx={a.x + a.w - 10} cy={a.y + 10} r="4" fill="var(--err)">
                  <animate attributeName="opacity" values="1;0.3;1" dur="1.2s" repeatCount="indefinite"/>
                </circle>
              )}
              {isSel && (
                <rect x={a.x-4} y={a.y-4} width={a.w+8} height={a.h+8} rx="5"
                  fill="none" stroke="var(--accent)" strokeWidth="1" strokeDasharray="3 3" opacity="0.7"/>
              )}
            </g>
          );
        })}

        {/* sensor sprites */}
        {layers.iot && SENSORS.map(s => (
          <g key={s.id} style={{cursor:"pointer"}}>
            <circle cx={s.x} cy={s.y} r="14" fill="#fff" stroke={
              s.tone==='err'?'var(--err)':s.tone==='warn'?'var(--warn)':'var(--ok)'
            } strokeWidth="1.5"/>
            <circle cx={s.x} cy={s.y} r="4" fill={
              s.tone==='err'?'var(--err)':s.tone==='warn'?'var(--warn)':'var(--ok)'
            }/>
            <g transform={`translate(${s.x+20}, ${s.y-12})`}>
              <rect x="0" y="0" width="74" height="24" rx="4" fill="#fff" stroke="var(--border)"/>
              <text x="6" y="10" fontSize="8" fontFamily="var(--font-mono)" fill="var(--text-3)">{s.id}</text>
              <text x="6" y="20" fontSize="10" fontFamily="var(--font-mono)" fontWeight="600" fill="var(--text)">{s.value}</text>
            </g>
          </g>
        ))}

        {/* stage labels */}
        <g fontFamily="var(--font-mono)" fontSize="9" fill="var(--text-4)" letterSpacing="0.08em">
          <text x="125" y="505" textAnchor="middle">RECEPCIÓN</text>
          <text x="235" y="505" textAnchor="middle">PASTEUR.</text>
          <text x="355" y="505" textAnchor="middle">HOMOGEN.</text>
          <text x="480" y="505" textAnchor="middle">UHT ASÉPTICO</text>
          <text x="630" y="505" textAnchor="middle">SOPLADO PET</text>
          <text x="755" y="505" textAnchor="middle">LLENADO</text>
          <text x="855" y="505" textAnchor="middle">ETIQUETA</text>
          <text x="950" y="505" textAnchor="middle">EMPAQUE</text>
        </g>
      </svg>

      {/* TOP-LEFT: Layer controls */}
      <div className="pane-floating" style={{
        position:"absolute", top:12, left:12, padding:10, borderRadius:10, width:220
      }}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:8}}>
          <span className="eyebrow">Capas del modelo</span>
          <button className="btn ghost sm" style={{padding:"0 4px",height:18,fontSize:10}}>Todas</button>
        </div>
        <div style={{display:"flex",flexDirection:"column",gap:4}}>
          {LAYERS.map(l => (
            <label key={l.id} style={{display:"flex",alignItems:"center",gap:8,fontSize:11.5,cursor:"pointer",padding:"2px 0"}}>
              <input type="checkbox" checked={layers[l.id] ?? l.on} onChange={e=>setLayers({...layers, [l.id]:e.target.checked})}
                style={{accentColor:"var(--text)", width:13, height:13, margin:0}}/>
              <span style={{width:8,height:8,borderRadius:2,background:l.color}}/>
              <span style={{flex:1, color:"var(--text-2)"}}>{l.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* TOP-RIGHT: View controls */}
      <div className="pane-floating" style={{position:"absolute", top:12, right:12, padding:6, borderRadius:10, display:"flex", flexDirection:"column", gap:4}}>
        <div className="tabs" style={{flexDirection:"column",padding:2}}>
          <button data-active={mode==='iso'} onClick={()=>setMode('iso')} style={{height:24,padding:"0 8px",fontFamily:"var(--font-mono)",fontSize:10}}>ISO</button>
          <button data-active={mode==='top'} onClick={()=>setMode('top')} style={{height:24,padding:"0 8px",fontFamily:"var(--font-mono)",fontSize:10}}>TOP</button>
          <button data-active={mode==='front'} onClick={()=>setMode('front')} style={{height:24,padding:"0 8px",fontFamily:"var(--font-mono)",fontSize:10}}>FRT</button>
        </div>
      </div>

      {/* BOTTOM-RIGHT: Zoom / resize controls */}
      <div className="pane-floating" style={{position:"absolute", bottom:12, right:12, padding:4, borderRadius:10, display:"flex", flexDirection:"column", gap:2}}>
        <button className="btn icon sm" style={{border:"none",background:"transparent"}} title="Zoom in" onClick={()=>setZoom(z=>Math.min(2, z+0.15))}>
          <Icon name="plus" size={14}/>
        </button>
        <div style={{fontFamily:"var(--font-mono)",fontSize:9,textAlign:"center",color:"var(--text-3)"}}>{Math.round(zoom*100)}%</div>
        <button className="btn icon sm" style={{border:"none",background:"transparent"}} title="Zoom out" onClick={()=>setZoom(z=>Math.max(0.4, z-0.15))}>
          <Icon name="minus" size={14}/>
        </button>
        <Divider/>
        <button className="btn icon sm" style={{border:"none",background:"transparent"}} title="Ajustar" onClick={()=>setZoom(1)}>
          <Icon name="maximize" size={13}/>
        </button>
      </div>

      {/* BOTTOM-LEFT: Resize 3D panel */}
      <div className="pane-floating" style={{position:"absolute", bottom:12, left:12, padding:"6px 10px", borderRadius:10, display:"flex", alignItems:"center", gap:10}}>
        <Icon name="cube" size={14} style={{color:"var(--text-3)"}}/>
        <span className="eyebrow">Tamaño modelo</span>
        <input type="range" className="axis-range" min="40" max="95" step="5" value={size}
          onChange={e=>onResize(+e.target.value)}
          style={{width:120}}
        />
        <span className="mono" style={{fontSize:11, color:"var(--text-2)", minWidth:30}}>{size}%</span>
      </div>
    </div>
  );
};

Object.assign(window, { Viewer3D, LAYERS });
