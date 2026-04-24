// Hero KPI strip + masthead

const KPIS = [
  { k:'OEE', v:87.4, u:'%', trend:+2.1, spark:[82,83,84,85,86,87,87.4], tone:'ok' },
  { k:'Disponibilidad', v:94.2, u:'%', trend:+0.4, spark:[92,93,93,94,94,94.2,94.2], tone:'ok' },
  { k:'Scrap', v:2.18, u:'%', trend:-0.3, spark:[2.6,2.5,2.4,2.3,2.2,2.18,2.18], tone:'ok' },
  { k:'Producción', v:'24.8k', u:'bph', trend:-1.2, spark:[25.5,25.2,25,24.9,24.8,24.8,24.8], tone:'warn' },
  { k:'MTBF', v:142, u:'h', trend:+8, spark:[132,135,138,140,141,142,142], tone:'ok' },
  { k:'Energía', v:0.184, u:'kWh/L', trend:+1.4, spark:[.178,.180,.181,.183,.184,.184,.184], tone:'warn' },
];

const Hero = ({ onOpenModal }) => (
  <div style={{padding:"22px 24px 20px",background:"var(--bg)",borderBottom:"1px solid var(--line)"}}>
    <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-end",marginBottom:20}}>
      <div>
        <div className="eyebrow" style={{marginBottom:6}}>01 · Gemelo Digital · Turno Matutino</div>
        <h1 style={{margin:0,fontSize:40,lineHeight:.98,letterSpacing:"-0.04em",fontWeight:600}}>
          Línea UHT-02 <span style={{color:"var(--ink-3)",fontWeight:400}}>· operando</span>
        </h1>
        <div style={{fontSize:13,color:"var(--ink-3)",marginTop:8}}>
          <span className="mono">07:00 → 15:00</span> · 3,412 botellas · última sincronía hace 2s
        </div>
      </div>
      <div style={{display:"flex",gap:8}}>
        <button className="btn" onClick={()=>onOpenModal('sim')}><Icon name="sparkle" size={13}/>What-If</button>
        <button className="btn" onClick={()=>onOpenModal('analytics')}><Icon name="chart" size={13}/>Analytics</button>
        <button className="btn primary" onClick={()=>onOpenModal('dashboard')}><Icon name="grid" size={13}/>Dashboard</button>
      </div>
    </div>

    <div style={{display:"grid",gridTemplateColumns:"repeat(6,1fr)",gap:0,border:"1px solid var(--line)",borderRadius:14,overflow:"hidden",background:"var(--surface)"}}>
      {KPIS.map((k,i)=>{
        const c = k.tone==='warn'?"var(--warn)":"var(--ok)";
        const up = k.trend>0;
        return (
          <div key={k.k} style={{padding:"16px 18px",borderRight:i<5?"1px solid var(--line)":"none",position:"relative"}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10}}>
              <span className="eyebrow">{k.k}</span>
              <span className="mono" style={{fontSize:10,color:k.tone==='warn'?"var(--warn)":(up?"var(--ok)":"var(--err)")}}>
                {up?'▲':'▼'} {Math.abs(k.trend)}{k.k==='MTBF'?'h':'%'}
              </span>
            </div>
            <div style={{display:"flex",alignItems:"flex-end",justifyContent:"space-between",gap:8}}>
              <div className="mega-num" style={{fontSize:30}}>
                {k.v}<span style={{fontSize:12,color:"var(--ink-3)",fontFamily:"var(--font-mono)",marginLeft:3,fontWeight:400}}>{k.u}</span>
              </div>
              <Spark data={k.spark} w={64} h={22} color={c} strokeW={1.2}/>
            </div>
          </div>
        );
      })}
    </div>
  </div>
);

Object.assign(window,{Hero});
