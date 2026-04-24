// Small reusable bits: Pill, Sparkline, MetricTile, SectionHeader, ScaleCSS class

const Pill = ({ tone = "default", children, dot = false }) => {
  const cls = "pill" + (tone !== "default" ? " " + tone : "");
  return (
    <span className={cls}>
      {dot && <span style={{width:6,height:6,borderRadius:"50%",background:"currentColor",display:"inline-block"}}/>}
      {children}
    </span>
  );
};

// Sparkline draws a tiny line from an array of numbers
const Sparkline = ({ data, w = 80, h = 22, color = "var(--accent)", fill = true }) => {
  if (!data || data.length < 2) return null;
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v,i) => {
    const x = (i/(data.length-1)) * w;
    const y = h - ((v - min)/range) * h;
    return [x,y];
  });
  const d = pts.map((p,i) => (i===0?"M":"L")+p[0].toFixed(1)+","+p[1].toFixed(1)).join(" ");
  const last = pts[pts.length-1];
  return (
    <svg width={w} height={h} style={{display:"block"}}>
      {fill && (
        <path d={d + ` L ${w},${h} L 0,${h} Z`} fill={color} opacity="0.08" />
      )}
      <path d={d} fill="none" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
      <circle cx={last[0]} cy={last[1]} r="2.2" fill={color}/>
    </svg>
  );
};

const MetricTile = ({ label, value, unit, delta, deltaTone, hint, spark, sparkColor }) => {
  return (
    <div className="card" style={{padding:"12px 14px", display:"flex", flexDirection:"column", gap:6, minWidth:0}}>
      <div style={{display:"flex", justifyContent:"space-between", alignItems:"center", gap:8}}>
        <span className="eyebrow" style={{whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{label}</span>
        {delta && (
          <span className="mono" style={{fontSize:10.5, color: deltaTone==="up"?"var(--ok)":deltaTone==="down"?"var(--err)":"var(--text-3)", whiteSpace:"nowrap"}}>
            {deltaTone==="up"?"▲":deltaTone==="down"?"▼":"·"} {delta}
          </span>
        )}
      </div>
      <div style={{display:"flex", alignItems:"baseline", gap:4}}>
        <span className="mono" style={{fontSize:22, fontWeight:500, letterSpacing:"-0.02em", color:"var(--text)"}}>{value}</span>
        {unit && <span className="mono" style={{fontSize:11, color:"var(--text-3)"}}>{unit}</span>}
      </div>
      <div style={{display:"flex", justifyContent:"space-between", alignItems:"flex-end", gap:8}}>
        <span style={{fontSize:11, color:"var(--text-3)", whiteSpace:"nowrap", overflow:"hidden", textOverflow:"ellipsis"}}>{hint}</span>
        {spark && <Sparkline data={spark} color={sparkColor || "var(--text-3)"} />}
      </div>
    </div>
  );
};

const SectionHeader = ({ title, hint, right, compact }) => (
  <div style={{display:"flex", alignItems:"center", justifyContent:"space-between", gap:12, marginBottom: compact?6:10}}>
    <div style={{display:"flex", alignItems:"baseline", gap:10, minWidth:0}}>
      <span style={{fontSize:13, fontWeight:600, color:"var(--text)", whiteSpace:"nowrap"}}>{title}</span>
      {hint && <span className="eyebrow" style={{overflow:"hidden",textOverflow:"ellipsis"}}>{hint}</span>}
    </div>
    {right}
  </div>
);

const Divider = ({ vertical, style }) => vertical
  ? <span style={{width:1, height:"100%", background:"var(--border)", ...style}} />
  : <span style={{height:1, width:"100%", background:"var(--border)", ...style}} />;

const Chip = ({ active, onClick, children, icon }) => (
  <button
    onClick={onClick}
    style={{
      display:"inline-flex", alignItems:"center", gap:5,
      height:24, padding:"0 9px", borderRadius:6,
      background: active ? "var(--text)" : "var(--surface)",
      color: active ? "#fff" : "var(--text-2)",
      border: "1px solid " + (active ? "var(--text)" : "var(--border)"),
      fontSize:11.5, fontWeight:500, cursor:"pointer",
      fontFamily:"var(--font-mono)", letterSpacing:"0.01em"
    }}
  >
    {icon}{children}
  </button>
);

Object.assign(window, { Pill, Sparkline, MetricTile, SectionHeader, Divider, Chip });
