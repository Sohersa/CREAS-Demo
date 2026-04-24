// KPI bar sits under the 3D viewer. Also includes the time scrubber.

const KpiBar = () => {
  const kpis = [
    { label:"OEE Línea 2", value:"81.4", unit:"%", delta:"+2.1 pts", deltaTone:"up", hint:"vs plan · -7d",
      spark:[76,78,79,81,80,82,81.4], sparkColor:"var(--ok)" },
    { label:"Throughput", value:"24,810", unit:"bph", delta:"−4.6%", deltaTone:"down", hint:"meta 26,000",
      spark:[25800,25500,25200,24900,24700,24800,24810], sparkColor:"var(--warn)" },
    { label:"Calidad", value:"99.2", unit:"%", delta:"estable", deltaTone:"flat", hint:"rechazo 0.8%",
      spark:[99.1,99.2,99.2,99.3,99.2,99.2,99.2], sparkColor:"var(--ok)" },
    { label:"Disponibilidad", value:"92.7", unit:"%", delta:"MTBF 184h", deltaTone:"flat", hint:"MTTR 28 min",
      spark:[93,92.5,92,92.8,92.9,92.6,92.7], sparkColor:"var(--text-3)" },
    { label:"Energía kWh/L", value:"0.088", unit:"", delta:"−1.8%", deltaTone:"up", hint:"baseline 0.090",
      spark:[0.092,0.091,0.09,0.089,0.088,0.088,0.088], sparkColor:"var(--ok)" },
    { label:"F₀ UHT", value:"6.4", unit:"min", delta:"setpoint 5.0", deltaTone:"flat", hint:"margen 28%",
      spark:[5.8,6.0,6.1,6.2,6.3,6.4,6.4], sparkColor:"var(--ok)" },
  ];
  return (
    <div style={{display:"grid", gridTemplateColumns:"repeat(6, 1fr)", gap:8}}>
      {kpis.map((k,i) => <MetricTile key={i} {...k}/>)}
    </div>
  );
};

const TimeScrubber = ({ onOpenModal }) => {
  const [at, setAt] = React.useState(100);
  const markers = [
    { pos: 18, tone:'err', label:'Paro BL-B02 02:14' },
    { pos: 42, tone:'warn', label:'SKU change' },
    { pos: 68, tone:'ok', label:'PM WO-45120' },
    { pos: 84, tone:'err', label:'Alarma PT-402' },
  ];
  return (
    <div style={{display:"flex", alignItems:"center", gap:14, padding:"10px 14px",
      background:"var(--surface)", border:"1px solid var(--border)", borderRadius:10}}>
      <button className="btn sm" style={{gap:6}}>
        <span style={{width:6,height:6,borderRadius:"50%",background:at>=100?"var(--ok)":"var(--warn)"}} className={at>=100?"live-dot":""}/>
        {at>=100 ? "LIVE" : "REPLAY"}
      </button>
      <div className="mono" style={{fontSize:11, color:"var(--text-3)", whiteSpace:"nowrap"}}>
        2026-04-18 · 23:47:12 CST
      </div>
      <div style={{flex:1, position:"relative", height:24}}>
        <div style={{position:"absolute",left:0,right:0,top:11,height:2,background:"var(--surface-3)",borderRadius:2}}/>
        <div style={{position:"absolute",left:0,width:`${at}%`,top:11,height:2,background:"var(--text)",borderRadius:2}}/>
        {markers.map((m,i)=>(
          <div key={i} title={m.label} style={{
            position:"absolute", left:`${m.pos}%`, top:8,
            width:8, height:8, borderRadius:"50%",
            background: m.tone==='err'?"var(--err)":m.tone==='warn'?"var(--warn)":"var(--ok)",
            transform:"translateX(-4px)", border:"2px solid #fff", cursor:"pointer"
          }}/>
        ))}
        <input type="range" className="axis-range" min="0" max="100" value={at} onChange={e=>setAt(+e.target.value)}
          style={{position:"absolute",left:0,right:0,top:9, width:"100%", background:"transparent"}}/>
      </div>
      <div style={{display:"flex",gap:2}}>
        {['-7d','-3d','-1d','-1h','AHORA'].map((lbl,i)=>(
          <button key={lbl} onClick={()=>setAt([5,30,60,90,100][i])} style={{
            height:24, padding:"0 8px", border:"1px solid var(--border)", borderRadius:5,
            background: at===[5,30,60,90,100][i]?"var(--text)":"var(--surface)",
            color: at===[5,30,60,90,100][i]?"#fff":"var(--text-2)",
            fontFamily:"var(--font-mono)", fontSize:10.5, cursor:"pointer"
          }}>{lbl}</button>
        ))}
      </div>
    </div>
  );
};

Object.assign(window, { KpiBar, TimeScrubber });
