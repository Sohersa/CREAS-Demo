// v2 atoms — reshaped for editorial feel

const Pill = ({ tone="default", children, dot=false }) => {
  const cls = "pill" + (tone!=="default"?" "+tone:"");
  return <span className={cls}>{dot&&<span style={{width:5,height:5,borderRadius:"50%",background:"currentColor",display:"inline-block"}}/>}{children}</span>;
};

const Spark = ({ data, w=90, h=26, color="var(--ink)", fill=true, strokeW=1.3 }) => {
  if (!data||data.length<2) return null;
  const mn=Math.min(...data), mx=Math.max(...data), r=mx-mn||1;
  const pts = data.map((v,i)=>[(i/(data.length-1))*w, h - ((v-mn)/r)*(h-2) - 1]);
  const d = pts.map((p,i)=>(i?"L":"M")+p[0].toFixed(1)+","+p[1].toFixed(1)).join(" ");
  const last = pts[pts.length-1];
  return <svg width={w} height={h} style={{display:"block",overflow:"visible"}}>
    {fill && <path d={d+` L ${w},${h} L 0,${h} Z`} fill={color} opacity="0.1"/>}
    <path d={d} fill="none" stroke={color} strokeWidth={strokeW} strokeLinecap="round" strokeLinejoin="round"/>
    <circle cx={last[0]} cy={last[1]} r="2.2" fill={color}/>
  </svg>;
};

const Divider = ({ vertical, style }) => vertical
  ? <span style={{width:1,height:"100%",background:"var(--line)",...style}}/>
  : <span style={{height:1,width:"100%",background:"var(--line)",...style}}/>;

const Chip = ({ active, onClick, children }) => (
  <button className={"chip"+(active?" active":"")} onClick={onClick}>{children}</button>
);

const SectionHeader = ({ kicker, title, hint, right }) => (
  <div style={{display:"flex",alignItems:"flex-end",justifyContent:"space-between",gap:16,marginBottom:16}}>
    <div>
      {kicker && <div className="eyebrow" style={{marginBottom:6}}>{kicker}</div>}
      <h3 style={{margin:0,fontSize:22,lineHeight:1.05,letterSpacing:"-0.03em",fontWeight:600}}>{title}</h3>
      {hint && <div style={{fontSize:12.5,color:"var(--ink-3)",marginTop:4}}>{hint}</div>}
    </div>
    {right}
  </div>
);

Object.assign(window, { Pill, Spark, Divider, Chip, SectionHeader });
