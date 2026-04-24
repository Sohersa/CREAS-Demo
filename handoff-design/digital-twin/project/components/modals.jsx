// Modal shell + all 7 redesigned modals

const ModalShell = ({ title, subtitle, onClose, children, width=920, actions }) => (
  <div className="modal-overlay" onClick={onClose}>
    <div className="modal-card card" onClick={e=>e.stopPropagation()} style={{
      width, maxWidth:"95vw", maxHeight:"90vh", display:"flex", flexDirection:"column",
      borderRadius:14, boxShadow:"var(--shadow-lg)"
    }}>
      <div style={{padding:"16px 20px", borderBottom:"1px solid var(--border)", display:"flex", justifyContent:"space-between", alignItems:"flex-start", gap:12}}>
        <div>
          <h2 style={{margin:0, fontSize:16, fontWeight:600, letterSpacing:"-0.015em"}}>{title}</h2>
          {subtitle && <div style={{fontSize:12, color:"var(--text-3)", marginTop:2}}>{subtitle}</div>}
        </div>
        <button className="btn icon sm ghost" onClick={onClose}><Icon name="x" size={14}/></button>
      </div>
      <div style={{flex:1, overflowY:"auto", padding:"20px"}}>{children}</div>
      {actions && (
        <div style={{padding:"12px 20px", borderTop:"1px solid var(--border)", display:"flex", justifyContent:"flex-end", gap:8, background:"var(--surface-2)"}}>
          {actions}
        </div>
      )}
    </div>
  </div>
);

// ----- What-If Simulation -----
const SimModal = ({ onClose }) => {
  const [cap, setCap] = React.useState(5);
  const [sku, setSku] = React.useState('Leche UHT 1L');
  const [turno, setTurno] = React.useState('3x8');
  const [running, setRunning] = React.useState(false);
  const [result, setResult] = React.useState({ oee:84.9, thr:26240, bot:'FI-F03', util:97.4 });
  const run = () => {
    setRunning(true);
    setTimeout(() => { setRunning(false); setResult({
      oee: +(81.4 + cap*0.7).toFixed(1),
      thr: Math.round(24810 * (1+cap/100)),
      bot: cap>=7?'BL-B02':'FI-F03',
      util: Math.min(99.5, 92 + cap*0.9).toFixed(1)
    }); }, 900);
  };
  return (
    <ModalShell title="Simulación What-If · SimPy Engine"
      subtitle={`Escenario: baseline +${cap}% capacidad · horizonte 24h · SKU ${sku}`}
      onClose={onClose} width={980}
      actions={<><button className="btn" onClick={onClose}>Cerrar</button><button className="btn primary"><Icon name="download" size={12}/>Publicar escenario</button></>}
    >
      <div style={{display:"grid", gridTemplateColumns:"320px 1fr", gap:20}}>
        <div style={{display:"flex",flexDirection:"column",gap:14}}>
          <div>
            <div className="eyebrow" style={{marginBottom:8}}>Parámetros</div>
            <div style={{display:"flex",flexDirection:"column",gap:12}}>
              <label style={{display:"flex",flexDirection:"column",gap:4}}>
                <span style={{fontSize:11.5, color:"var(--text-2)"}}>Capacidad <span className="mono" style={{color:"var(--text)"}}>+{cap}%</span></span>
                <input type="range" className="axis-range" min="-10" max="15" value={cap} onChange={e=>setCap(+e.target.value)}/>
              </label>
              <label style={{display:"flex",flexDirection:"column",gap:4}}>
                <span style={{fontSize:11.5, color:"var(--text-2)"}}>SKU</span>
                <select value={sku} onChange={e=>setSku(e.target.value)} style={{height:30, border:"1px solid var(--border)", borderRadius:6, padding:"0 8px", fontSize:12, background:"var(--surface)"}}>
                  <option>Leche UHT 1L</option><option>Leche UHT 250ml</option><option>Leche Deslactosada 1L</option>
                </select>
              </label>
              <label style={{display:"flex",flexDirection:"column",gap:4}}>
                <span style={{fontSize:11.5, color:"var(--text-2)"}}>Turnos</span>
                <select value={turno} onChange={e=>setTurno(e.target.value)} style={{height:30, border:"1px solid var(--border)", borderRadius:6, padding:"0 8px", fontSize:12, background:"var(--surface)"}}>
                  <option>3x8</option><option>2x12</option><option>5x8</option>
                </select>
              </label>
              <div style={{padding:10, background:"var(--surface-2)", border:"1px solid var(--border)", borderRadius:8}}>
                <div className="eyebrow" style={{marginBottom:4}}>Disponibilidad equipos</div>
                {[['BL-B02',94],['FI-F03',98],['PT-01',99],['UHT-01',96]].map(([tag,v])=>(
                  <div key={tag} style={{display:"flex",justifyContent:"space-between",fontSize:11, padding:"2px 0"}}>
                    <span className="mono">{tag}</span><span className="mono">{v}%</span>
                  </div>
                ))}
              </div>
              <button className="btn primary" onClick={run}>
                {running ? <><Icon name="sim" size={12}/>Corriendo…</> : <><Icon name="play" size={12}/>Ejecutar</>}
              </button>
            </div>
          </div>
        </div>

        <div>
          <div className="eyebrow" style={{marginBottom:8}}>Resultados vs baseline</div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)", gap:10, marginBottom:14}}>
            <div className="card card-pad">
              <div className="eyebrow">OEE proyectado</div>
              <div className="mono" style={{fontSize:28, fontWeight:500, letterSpacing:"-0.02em"}}>{result.oee}<span style={{fontSize:14, color:"var(--text-3)"}}>%</span></div>
              <div className="mono" style={{fontSize:11, color:"var(--ok)"}}>+{(result.oee-81.4).toFixed(1)} pts vs baseline</div>
            </div>
            <div className="card card-pad">
              <div className="eyebrow">Throughput</div>
              <div className="mono" style={{fontSize:28, fontWeight:500, letterSpacing:"-0.02em"}}>{result.thr.toLocaleString()}</div>
              <div className="mono" style={{fontSize:11, color:"var(--ok)"}}>+{((result.thr-24810)/24810*100).toFixed(1)}% bph</div>
            </div>
            <div className="card card-pad">
              <div className="eyebrow">Bottleneck</div>
              <div className="mono" style={{fontSize:18, fontWeight:500, marginTop:6}}>{result.bot}</div>
              <div className="mono" style={{fontSize:11, color:"var(--warn)"}}>util {result.util}%</div>
            </div>
          </div>
          <div className="card card-pad" style={{padding:14}}>
            <div className="eyebrow" style={{marginBottom:8}}>Proyección 24h (OEE %)</div>
            <svg width="100%" height="140" viewBox="0 0 600 140" preserveAspectRatio="none">
              <defs><linearGradient id="gbase" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="var(--text-3)" stopOpacity="0.15"/><stop offset="1" stopColor="var(--text-3)" stopOpacity="0"/></linearGradient>
              <linearGradient id="gproj" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stopColor="var(--accent)" stopOpacity="0.18"/><stop offset="1" stopColor="var(--accent)" stopOpacity="0"/></linearGradient></defs>
              <g stroke="var(--border)" strokeDasharray="2 4">
                {[0,1,2,3].map(i=><line key={i} x1="0" x2="600" y1={20+i*30} y2={20+i*30}/>)}
              </g>
              <path d="M 0 80 Q 60 70 120 75 T 240 82 T 360 70 T 480 78 T 600 72" fill="url(#gbase)" stroke="var(--text-3)" strokeWidth="1.5"/>
              <path d={`M 0 70 Q 60 ${70-cap} 120 ${68-cap} T 240 ${62-cap} T 360 ${56-cap} T 480 ${60-cap} T 600 ${52-cap}`} fill="url(#gproj)" stroke="var(--accent)" strokeWidth="2"/>
              <g fontFamily="var(--font-mono)" fontSize="9" fill="var(--text-3)">
                {['00','06','12','18','24'].map((h,i)=><text key={h} x={i*150} y="135">{h}h</text>)}
              </g>
            </svg>
            <div style={{display:"flex",gap:14, marginTop:8, fontSize:10.5}}>
              <span style={{display:"flex",alignItems:"center",gap:5}}><span style={{width:12,height:2,background:"var(--text-3)"}}/>Baseline</span>
              <span style={{display:"flex",alignItems:"center",gap:5}}><span style={{width:12,height:2,background:"var(--accent)"}}/>Proyección</span>
            </div>
          </div>
        </div>
      </div>
    </ModalShell>
  );
};

// ----- Dashboard Ejecutivo -----
const DashboardModal = ({ onClose }) => {
  const lines = [
    { id:'L-01 PET', oee:79.2, plan:80, tone:'warn' },
    { id:'L-02 UHT', oee:81.4, plan:80, tone:'ok' },
    { id:'L-03 UHT', oee:88.1, plan:85, tone:'ok' },
    { id:'L-04 PET', oee:74.6, plan:78, tone:'err' },
    { id:'L-05 Yog', oee:85.3, plan:82, tone:'ok' },
    { id:'L-06 Cre', oee:83.0, plan:82, tone:'ok' },
  ];
  const causes = [
    { name:'Cambio SKU', hrs:14.2, pct:28 },
    { name:'Falla mecánica BL', hrs:9.8, pct:19 },
    { name:'Calidad / rechazo', hrs:7.1, pct:14 },
    { name:'CIP extendido', hrs:6.0, pct:12 },
    { name:'Paro eléctrico', hrs:4.3, pct:8 },
  ];
  return (
    <ModalShell title="Dashboard Ejecutivo · Planta Lácteos Monterrey"
      subtitle={`Semana 16 · todas las líneas · plan cumplimiento 96.2%`}
      onClose={onClose} width={1080}
      actions={<><button className="btn" onClick={onClose}>Cerrar</button><button className="btn primary"><Icon name="download" size={12}/>Descargar PDF</button></>}
    >
      <div style={{display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:10, marginBottom:16}}>
        <MetricTile label="OEE PLANTA" value="82.6" unit="%" delta="+1.4 pts" deltaTone="up" hint="meta 84%" spark={[80,81,80,82,81,82.6,82.6]} sparkColor="var(--ok)"/>
        <MetricTile label="OUTPUT SEMANA" value="1.42M" unit="L" delta="+3.1%" deltaTone="up" hint="plan 1.40M" spark={[1.38,1.39,1.40,1.41,1.41,1.42,1.42]} sparkColor="var(--ok)"/>
        <MetricTile label="SCRAP" value="0.84" unit="%" delta="−0.1 pts" deltaTone="up" hint="meta ≤1.0%" spark={[1.0,0.95,0.9,0.88,0.86,0.85,0.84]} sparkColor="var(--ok)"/>
        <MetricTile label="COSTO/L" value="$4.21" unit="" delta="−$0.08" deltaTone="up" hint="budget $4.30" spark={[4.30,4.28,4.26,4.24,4.22,4.21,4.21]} sparkColor="var(--ok)"/>
      </div>

      <div style={{display:"grid", gridTemplateColumns:"1.2fr 1fr", gap:16}}>
        <div className="card card-pad">
          <SectionHeader title="OEE por línea · últimas 24h" hint="vs plan"/>
          <div style={{display:"flex",flexDirection:"column",gap:8}}>
            {lines.map(l => (
              <div key={l.id} style={{display:"grid",gridTemplateColumns:"80px 1fr 50px", alignItems:"center", gap:10}}>
                <span className="mono" style={{fontSize:11, color:"var(--text-2)"}}>{l.id}</span>
                <div style={{height:18, background:"var(--surface-2)", border:"1px solid var(--border)", borderRadius:4, position:"relative", overflow:"hidden"}}>
                  <div style={{position:"absolute",left:0,top:0,bottom:0, width:`${l.oee}%`, background: l.tone==='err'?"var(--err)":l.tone==='warn'?"var(--warn)":"var(--ok)", opacity:0.85}}/>
                  <div style={{position:"absolute",left:`${l.plan}%`,top:-2,bottom:-2, width:2, background:"var(--text)"}}/>
                  <div style={{position:"absolute", left:8, top:1, fontSize:10.5, color:"#fff", fontFamily:"var(--font-mono)", fontWeight:600}}>{l.oee}%</div>
                </div>
                <span className="mono" style={{fontSize:10.5, color:"var(--text-3)", textAlign:"right"}}>plan {l.plan}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card card-pad">
          <SectionHeader title="Top 5 causas de paro" hint="últimos 7d"/>
          <div style={{display:"flex",flexDirection:"column",gap:6}}>
            {causes.map(c=>(
              <div key={c.name} style={{display:"flex",alignItems:"center",gap:8}}>
                <span style={{fontSize:11.5, color:"var(--text-2)", width:150}}>{c.name}</span>
                <div style={{flex:1, height:8, background:"var(--surface-2)", borderRadius:2}}>
                  <div style={{height:"100%", width:`${c.pct*3}%`, background:"var(--accent)", borderRadius:2}}/>
                </div>
                <span className="mono" style={{fontSize:10.5, color:"var(--text-3)", width:50, textAlign:"right"}}>{c.hrs}h</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card card-pad" style={{gridColumn:"1 / -1"}}>
          <SectionHeader title="Plan vs Actual · Weekly output" hint="L × 1000"/>
          <svg width="100%" height="120" viewBox="0 0 800 120">
            <g stroke="var(--border)" strokeDasharray="2 3">{[0,1,2,3].map(i=><line key={i} x1="0" x2="800" y1={20+i*25} y2={20+i*25}/>)}</g>
            {[['L',120],['M',140],['X',135],['J',145],['V',150],['S',110],['D',95]].map(([d,v],i)=>(
              <g key={d}>
                <rect x={i*110+30} y={100-v*0.5} width="24" height={v*0.5} fill="var(--surface-3)" stroke="var(--border)"/>
                <rect x={i*110+58} y={100-(v+5)*0.5} width="24" height={(v+5)*0.5} fill="var(--accent)"/>
                <text x={i*110+48} y="115" fontSize="10" fill="var(--text-3)" fontFamily="var(--font-mono)" textAnchor="middle">{d}</text>
              </g>
            ))}
          </svg>
          <div style={{display:"flex",gap:14, fontSize:10.5, marginTop:6}}>
            <span style={{display:"flex",alignItems:"center",gap:5}}><span style={{width:10,height:10,background:"var(--surface-3)",border:"1px solid var(--border)"}}/>Plan</span>
            <span style={{display:"flex",alignItems:"center",gap:5}}><span style={{width:10,height:10,background:"var(--accent)"}}/>Actual</span>
          </div>
        </div>
      </div>
    </ModalShell>
  );
};

// ----- P&ID -----
const PIDModal = ({ onClose }) => (
  <ModalShell title="P&ID · Sistema Aire HP — Sopladora BL-B02"
    subtitle="DWG · CREAS-PID-AIR-002-R4 · ISA-5.1 · ISO 10628 · sync hace 2s"
    onClose={onClose} width={1040}
    actions={<><button className="btn" onClick={onClose}>Cerrar</button><button className="btn primary"><Icon name="download" size={12}/>Exportar PDF</button></>}
  >
    <div style={{display:"flex",alignItems:"center",gap:8, marginBottom:12}}>
      <button className="btn sm"><Icon name="minus" size={12}/></button>
      <span className="mono" style={{fontSize:11, padding:"0 8px"}}>100%</span>
      <button className="btn sm"><Icon name="plus" size={12}/></button>
      <Divider vertical style={{height:20}}/>
      <div style={{display:"flex",gap:10,fontSize:11}}>
        <span style={{display:"flex",alignItems:"center",gap:4}}><span style={{width:8,height:8,borderRadius:"50%",background:"var(--ok)"}}/>en servicio</span>
        <span style={{display:"flex",alignItems:"center",gap:4}}><span style={{width:8,height:8,borderRadius:"50%",background:"var(--err)"}}/>alarma</span>
        <span style={{display:"flex",alignItems:"center",gap:4}}><span style={{width:8,height:8,borderRadius:"50%",background:"var(--text-3)"}}/>aislado</span>
      </div>
    </div>
    <div style={{border:"1px solid var(--border)", borderRadius:8, background:"#fff", padding:16}}>
      <svg width="100%" viewBox="0 0 800 360">
        <defs>
          <marker id="arr" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
            <path d="M0,0 L0,10 L10,5 z" fill="var(--text-2)"/>
          </marker>
        </defs>
        <g stroke="var(--text)" strokeWidth="1.4" fill="none">
          {/* compressor */}
          <circle cx="90" cy="180" r="32"/>
          <text x="90" y="184" fontFamily="var(--font-mono)" fontSize="11" textAnchor="middle">C-01</text>
          <text x="90" y="230" fontFamily="var(--font-mono)" fontSize="9" textAnchor="middle" fill="var(--text-3)">COMPR HP</text>

          {/* pipe */}
          <path d="M 122 180 L 200 180" markerEnd="url(#arr)"/>
          {/* valve V-101 */}
          <g transform="translate(220 180)">
            <polygon points="-12,-12 12,12 -12,12 12,-12" fill="#fff"/>
            <text y="28" fontSize="9" textAnchor="middle" fontFamily="var(--font-mono)">V-101</text>
          </g>
          <path d="M 232 180 L 320 180"/>
          {/* filter F-101 */}
          <g transform="translate(340 180)">
            <rect x="-18" y="-14" width="36" height="28" fill="#fff"/>
            <line x1="-18" y1="-14" x2="18" y2="14" strokeDasharray="2 2"/>
            <text y="30" fontSize="9" textAnchor="middle" fontFamily="var(--font-mono)">F-101</text>
          </g>
          <path d="M 358 180 L 460 180"/>
          {/* pressure transmitter PT-402 (alarm) */}
          <g transform="translate(480 180)">
            <circle r="16" fill="#FBE9E9" stroke="var(--err)" strokeWidth="2"/>
            <text fontSize="10" textAnchor="middle" dy="-2" fontFamily="var(--font-mono)" fill="var(--err)">PT</text>
            <text fontSize="9" textAnchor="middle" dy="8" fontFamily="var(--font-mono)" fill="var(--err)">402</text>
            <circle r="20" fill="none" stroke="var(--err)" strokeDasharray="2 2"><animate attributeName="r" values="20;26;20" dur="1.6s" repeatCount="indefinite"/></circle>
          </g>
          <path d="M 496 180 L 600 180 L 600 120"/>
          {/* blower */}
          <g transform="translate(640 90)">
            <rect x="-36" y="-22" width="72" height="44" fill="#FFF1EA" stroke="var(--accent)" strokeWidth="2" rx="4"/>
            <text fontSize="11" textAnchor="middle" fontFamily="var(--font-mono)" fontWeight="600" fill="var(--accent)">BL-B02</text>
            <text fontSize="9" textAnchor="middle" dy="14" fontFamily="var(--font-mono)" fill="var(--accent)">SOPLADORA</text>
          </g>
          {/* branch */}
          <path d="M 460 180 L 460 280 L 680 280"/>
          <g transform="translate(380 280)">
            <rect x="-24" y="-14" width="48" height="28" fill="#fff"/>
            <text fontSize="9" textAnchor="middle" dy="3" fontFamily="var(--font-mono)">TK-201</text>
          </g>
          <path d="M 404 280 L 460 280"/>
          <g transform="translate(700 280)">
            <circle r="14" fill="#fff"/>
            <text fontSize="9" textAnchor="middle" dy="2" fontFamily="var(--font-mono)">PI-301</text>
          </g>
        </g>
        {/* legend tags */}
        <g fontFamily="var(--font-mono)" fontSize="9" fill="var(--text-3)">
          <text x="160" y="170">Ø3" SCH40</text>
          <text x="280" y="170">Ø3" SCH40</text>
          <text x="410" y="170">Ø3" SCH40</text>
          <text x="540" y="170">Ø3" SCH40</text>
        </g>
      </svg>
    </div>
  </ModalShell>
);

// ----- Maximo -----
const MaximoModal = ({ onClose }) => {
  const cols = ['Pendiente','Planificada','En ejecución','Completada'];
  const wos = {
    'Pendiente':[
      { id:'WO-45301', asset:'FI-F03', task:'Cambio boquillas llenado', prio:'A', tec:'—' },
      { id:'WO-45298', asset:'CAP-02', task:'Torque tapadora', prio:'B', tec:'—' },
    ],
    'Planificada':[
      { id:'WO-45213', asset:'UHT-01', task:'PM02 sello bomba booster', prio:'A', tec:'J. Ramírez', when:'22/04' },
      { id:'WO-45205', asset:'BL-B02', task:'Inspección molde PET', prio:'A', tec:'L. Torres', when:'23/04' },
    ],
    'En ejecución':[
      { id:'WO-45120', asset:'UHT-01', task:'Calibración TT-114', prio:'B', tec:'M. Vega' },
      { id:'WO-45115', asset:'CIP-02', task:'Validación CIP anual', prio:'A', tec:'R. Navarro' },
    ],
    'Completada':[
      { id:'WO-45089', asset:'F-03-STER', task:'Integrity test', prio:'A', tec:'M. Vega', when:'17/04' },
    ],
  };
  return (
    <ModalShell title="Mantenimiento · IBM Maximo"
      subtitle="Órdenes activas · Línea UHT-02 · sync Maximo MIF"
      onClose={onClose} width={1100}
      actions={<><button className="btn" onClick={onClose}>Cerrar</button><button className="btn primary"><Icon name="plus" size={12}/>Nueva OT</button></>}
    >
      <div style={{display:"flex",gap:8, marginBottom:14}}>
        <Chip active>Todas</Chip><Chip>Crit. A</Chip><Chip>Esta semana</Chip><Chip>Mis OT</Chip>
        <div style={{flex:1}}/>
        <button className="btn sm"><Icon name="filter" size={12}/>Filtros</button>
      </div>
      <div style={{display:"grid", gridTemplateColumns:"repeat(4,1fr)", gap:10}}>
        {cols.map(col => (
          <div key={col} style={{background:"var(--surface-2)", borderRadius:8, padding:8, minHeight:300}}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",padding:"4px 6px 10px"}}>
              <span style={{fontSize:11.5, fontWeight:600}}>{col}</span>
              <span className="mono" style={{fontSize:10, color:"var(--text-3)"}}>{wos[col].length}</span>
            </div>
            <div style={{display:"flex",flexDirection:"column",gap:6}}>
              {wos[col].map(w => (
                <div key={w.id} className="card" style={{padding:10}}>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:4}}>
                    <span className="mono" style={{fontSize:11, fontWeight:600}}>{w.id}</span>
                    <Pill tone={w.prio==='A'?'err':'default'}>{w.prio}</Pill>
                  </div>
                  <div style={{fontSize:11.5, color:"var(--text)", marginBottom:4, lineHeight:1.35}}>{w.task}</div>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
                    <span className="mono" style={{fontSize:10, color:"var(--text-3)"}}>{w.asset}</span>
                    <span className="mono" style={{fontSize:10, color:"var(--text-3)"}}>{w.tec}{w.when?` · ${w.when}`:''}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </ModalShell>
  );
};

// ----- Analytics -----
const AnalyticsModal = ({ onClose }) => {
  const heatmap = Array.from({length:7}, (_,r)=>Array.from({length:24},(_,c)=>Math.random()));
  return (
    <ModalShell title="Analytics operacional"
      subtitle="Correlación geometría × proceso × desempeño"
      onClose={onClose} width={1100}
      actions={<button className="btn" onClick={onClose}>Cerrar</button>}
    >
      <div style={{display:"grid", gridTemplateColumns:"repeat(2,1fr)", gap:14}}>
        <div className="card card-pad">
          <SectionHeader title="MTBF / MTTR por activo" hint="últimos 90d"/>
          <table className="axis">
            <thead><tr><th>Activo</th><th>MTBF</th><th>MTTR</th><th>Crit.</th></tr></thead>
            <tbody>
              {[['BL-B02',124,42,'A'],['FI-F03',188,28,'A'],['UHT-01',340,35,'A'],['LB-02',410,22,'B'],['PK-01',520,18,'B']].map(r=>(
                <tr key={r[0]}><td className="mono">{r[0]}</td><td className="mono">{r[1]}h</td><td className="mono">{r[2]}min</td><td><Pill tone={r[3]==='A'?'err':'default'}>{r[3]}</Pill></td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card card-pad">
          <SectionHeader title="Pareto · causas de paro 30d"/>
          <svg width="100%" height="180" viewBox="0 0 400 180">
            {[60,44,30,22,14,10,6].map((v,i)=>(
              <g key={i}>
                <rect x={i*54+10} y={150-v*2} width="40" height={v*2} fill="var(--accent)" opacity={1-i*0.1}/>
                <text x={i*54+30} y="170" fontSize="9" fontFamily="var(--font-mono)" textAnchor="middle" fill="var(--text-3)">C{i+1}</text>
              </g>
            ))}
            <path d="M 30 30 L 84 60 L 138 84 L 192 102 L 246 118 L 300 128 L 354 134"
              stroke="var(--text)" strokeWidth="1.5" fill="none"/>
          </svg>
        </div>

        <div className="card card-pad">
          <SectionHeader title="Heatmap utilización · UHT-02" hint="día × hora"/>
          <svg width="100%" height="160" viewBox="0 0 480 140">
            {heatmap.map((row,ri)=>row.map((v,ci)=>(
              <rect key={`${ri}-${ci}`} x={ci*19+20} y={ri*18+10} width="17" height="16"
                fill="var(--accent)" opacity={0.1 + v*0.85}/>
            )))}
            {['L','M','X','J','V','S','D'].map((d,i)=><text key={d} x="8" y={i*18+22} fontSize="9" fontFamily="var(--font-mono)" fill="var(--text-3)">{d}</text>)}
            {[0,6,12,18,23].map(h=><text key={h} x={h*19+25} y="140" fontSize="9" fontFamily="var(--font-mono)" fill="var(--text-3)" textAnchor="middle">{h}h</text>)}
          </svg>
        </div>

        <div className="card card-pad">
          <SectionHeader title="Anomaly detection · 24h" hint="IsolationForest"/>
          <svg width="100%" height="160" viewBox="0 0 400 160">
            <g stroke="var(--border)" strokeDasharray="2 3">{[0,1,2,3].map(i=><line key={i} x1="0" x2="400" y1={25+i*35} y2={25+i*35}/>)}</g>
            <path d="M 0 90 Q 40 85 80 92 T 160 88 T 240 70 T 320 95 T 400 90" stroke="var(--text-3)" strokeWidth="1.5" fill="none"/>
            <circle cx="100" cy="50" r="5" fill="var(--err)"/>
            <circle cx="260" cy="40" r="5" fill="var(--err)"/>
            <circle cx="340" cy="60" r="4" fill="var(--warn)"/>
            <text x="108" y="47" fontSize="9" fontFamily="var(--font-mono)" fill="var(--err)">02:14 BL-B02</text>
            <text x="268" y="37" fontSize="9" fontFamily="var(--font-mono)" fill="var(--err)">16:42 PT-402</text>
          </svg>
        </div>
      </div>
    </ModalShell>
  );
};

// ----- Docs -----
const DocsModal = ({ onClose }) => (
  <ModalShell title="Documentación técnica" subtitle="142 documentos vinculados · búsqueda semántica (pgvector)"
    onClose={onClose} width={1040} actions={<button className="btn" onClick={onClose}>Cerrar</button>}
  >
    <div style={{display:"flex",gap:8, marginBottom:12}}>
      <div style={{flex:1, display:"flex",alignItems:"center",gap:8, padding:"4px 10px", border:"1px solid var(--border)", borderRadius:8, background:"var(--surface)"}}>
        <Icon name="search" size={14} style={{color:"var(--text-3)"}}/>
        <input placeholder="¿Dónde está el manual de la sopladora Sidel?" style={{flex:1, border:"none", outline:"none", fontSize:13, padding:"6px 0", background:"transparent", fontFamily:"inherit"}}/>
        <Pill tone="accent">CLAUDE</Pill>
      </div>
      <button className="btn"><Icon name="plus" size={12}/>Subir</button>
    </div>
    <div style={{display:"grid",gridTemplateColumns:"240px 1fr", gap:16}}>
      <div>
        <div className="eyebrow" style={{marginBottom:6}}>Filtros</div>
        <div style={{display:"flex",flexDirection:"column",gap:4}}>
          {['Manuales (34)','P&IDs (18)','ISOmétricos (12)','Certificados (22)','SOPs (31)','MSDS (8)','Planos mec. (17)'].map(f=>(
            <label key={f} style={{display:"flex",alignItems:"center",gap:6, fontSize:12, color:"var(--text-2)"}}>
              <input type="checkbox" defaultChecked style={{accentColor:"var(--text)"}}/>{f}
            </label>
          ))}
        </div>
      </div>
      <div>
        <table className="axis">
          <thead><tr><th>Nombre</th><th>Tipo</th><th>Activo</th><th>Versión</th><th>Actualizado</th></tr></thead>
          <tbody>
            {[
              ['Manual Tetra Pak A3/Flex (ES).pdf','MANUAL','UHT-01','R2.4','2026-01-12'],
              ['P&ID-UHT-02-R4.dwg','PID','L-02','R4','2026-03-28'],
              ['SOP CIP-Aséptico v3.2.pdf','SOP','CIP-02','v3.2','2026-02-14'],
              ['Certificado F₀ Q1-2026.pdf','CERT','UHT-01','2026-Q1','2026-04-02'],
              ['Ficha SIDEL SBO-24.pdf','SPEC','BL-B02','R1','2025-11-05'],
              ['Isométrico-AIR-HP-002.pdf','ISO','AIR-HP','R3','2026-02-02'],
              ['MSDS NaOH 2% CIP.pdf','MSDS','CIP-02','R1','2024-10-10'],
            ].map(r=>(
              <tr key={r[0]} style={{cursor:"pointer"}}>
                <td style={{display:"flex",alignItems:"center",gap:8}}><Icon name="doc" size={13} style={{color:"var(--text-3)"}}/>{r[0]}</td>
                <td><Pill>{r[1]}</Pill></td>
                <td className="mono">{r[2]}</td>
                <td className="mono">{r[3]}</td>
                <td className="mono" style={{color:"var(--text-3)"}}>{r[4]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  </ModalShell>
);

// ----- Events -----
const EventsModal = ({ onClose }) => (
  <ModalShell title="Alarmas y eventos · últimas 24h" subtitle="5 eventos · filtrable por severidad"
    onClose={onClose} width={880}
    actions={<><button className="btn" onClick={onClose}>Cerrar</button><button className="btn primary"><Icon name="check" size={12}/>Reconocer todos</button></>}
  >
    <div style={{display:"flex",gap:6, marginBottom:12}}>
      <Chip active>Todos</Chip><Chip>Crítico</Chip><Chip>Warning</Chip><Chip>Info</Chip>
    </div>
    <div style={{display:"flex",flexDirection:"column",gap:8}}>
      {[
        { t:'02:14', sev:'err', asset:'BL-B02', msg:'PT-402 presión aire HP baja · 2.1 bar (SP 3.8)', wo:'WO-45213' },
        { t:'03:41', sev:'ok', asset:'BL-B02', msg:'Reinicio automático tras restablecer presión', wo:null },
        { t:'09:22', sev:'warn', asset:'FI-F03', msg:'FT-303 flujo fuera de banda · 9.8 m³/h (banda 9.9–10.1)', wo:null },
        { t:'14:08', sev:'info', asset:'CIP-02', msg:'CIP programado completado · 42 min', wo:null },
        { t:'16:42', sev:'err', asset:'PT-402', msg:'Anomalía detectada por IsolationForest', wo:'WO-45301' },
      ].map((e,i)=>(
        <div key={i} className="card" style={{padding:"10px 14px", display:"flex",alignItems:"center",gap:12}}>
          <div style={{width:4, height:36, borderRadius:2, background: e.sev==='err'?"var(--err)":e.sev==='warn'?"var(--warn)":e.sev==='ok'?"var(--ok)":"var(--info)"}}/>
          <div style={{display:"flex",flexDirection:"column",gap:2, minWidth:90}}>
            <span className="mono" style={{fontSize:11, color:"var(--text-3)"}}>{e.t}</span>
            <Pill tone={e.sev==='err'?'err':e.sev==='warn'?'warn':e.sev==='ok'?'live':'default'}>{e.sev==='err'?'CRIT':e.sev==='warn'?'WARN':e.sev==='ok'?'OK':'INFO'}</Pill>
          </div>
          <div style={{flex:1}}>
            <div style={{display:"flex",alignItems:"center",gap:8}}>
              <span className="mono" style={{fontSize:11, fontWeight:600}}>{e.asset}</span>
              {e.wo && <span className="mono" style={{fontSize:10.5, color:"var(--accent)"}}>{e.wo}</span>}
            </div>
            <div style={{fontSize:12, color:"var(--text-2)"}}>{e.msg}</div>
          </div>
          <div style={{display:"flex",gap:4}}>
            <button className="btn sm">Reconocer</button>
            <button className="btn sm">Ver en 3D</button>
          </div>
        </div>
      ))}
    </div>
  </ModalShell>
);

// ----- Settings -----
const SettingsModal = ({ onClose }) => {
  const [tab, setTab] = React.useState('integr');
  return (
    <ModalShell title="Configuración" subtitle="Usuario · Organización · Integraciones"
      onClose={onClose} width={900}
      actions={<><button className="btn" onClick={onClose}>Cerrar</button><button className="btn primary">Guardar</button></>}
    >
      <div style={{display:"grid",gridTemplateColumns:"200px 1fr", gap:20}}>
        <div style={{display:"flex",flexDirection:"column",gap:2}}>
          {[['perfil','Perfil'],['org','Organización'],['integr','Integraciones'],['roles','Roles y permisos'],['audit','Audit log'],['bill','Facturación']].map(([id,lbl])=>(
            <button key={id} onClick={()=>setTab(id)} style={{
              textAlign:"left", padding:"8px 10px", border:"none", borderRadius:6,
              background: tab===id?"var(--surface-2)":"transparent", color:"var(--text)",
              fontSize:12.5, cursor:"pointer", fontWeight: tab===id?600:400
            }}>{lbl}</button>
          ))}
        </div>
        <div>
          {tab==='integr' && (
            <div style={{display:"flex",flexDirection:"column",gap:10}}>
              {[
                { n:'SAP S/4HANA', desc:'OData · Event Mesh · CO / PM', status:'ok' },
                { n:'IBM Maximo', desc:'MIF · MBO MXWO · readonly demo', status:'ok' },
                { n:'OPC UA (Kepware)', desc:'Plant MTY · 412 tags', status:'ok' },
                { n:'MQTT HiveMQ', desc:'Edge broker · 8,432 msg/s', status:'ok' },
                { n:'SharePoint', desc:'Docs · 142 vinculados', status:'warn' },
              ].map(x=>(
                <div key={x.n} className="card" style={{padding:"10px 14px", display:"flex",alignItems:"center",gap:10}}>
                  <div style={{width:32,height:32,borderRadius:6,background:"var(--surface-2)",display:"grid",placeItems:"center"}}>
                    <Icon name="wifi" size={14}/>
                  </div>
                  <div style={{flex:1}}>
                    <div style={{fontSize:13, fontWeight:500}}>{x.n}</div>
                    <div className="mono" style={{fontSize:10.5, color:"var(--text-3)"}}>{x.desc}</div>
                  </div>
                  <Pill tone={x.status==='ok'?'live':'warn'} dot>{x.status==='ok'?'CONECTADO':'DEGRADADO'}</Pill>
                  <button className="btn sm">Configurar</button>
                </div>
              ))}
            </div>
          )}
          {tab!=='integr' && <div style={{padding:40, textAlign:"center", color:"var(--text-3)", fontSize:13}}>Sección "{tab}" · demo placeholder</div>}
        </div>
      </div>
    </ModalShell>
  );
};

// ----- History -----
const HistoryModal = ({ onClose }) => (
  <ModalShell title="Histórico · Telemetría" subtitle="TimescaleDB · UHT-01 tags primarios"
    onClose={onClose} width={960}
    actions={<><button className="btn" onClick={onClose}>Cerrar</button><button className="btn primary"><Icon name="download" size={12}/>Exportar CSV</button></>}
  >
    <div style={{display:"flex",gap:6, marginBottom:12}}>
      {['1h','24h','7d','30d'].map((r,i)=><Chip key={r} active={i===1}>{r}</Chip>)}
    </div>
    <div className="card card-pad">
      <svg width="100%" height="260" viewBox="0 0 800 260">
        <g stroke="var(--border)" strokeDasharray="2 3">
          {[0,1,2,3,4].map(i=><line key={i} x1="0" x2="800" y1={20+i*50} y2={20+i*50}/>)}
        </g>
        <path d="M 0 130 Q 80 120 160 128 T 320 125 T 480 118 T 640 130 T 800 122" stroke="var(--accent)" strokeWidth="1.8" fill="none"/>
        <path d="M 0 160 Q 80 155 160 165 T 320 150 T 480 170 T 640 155 T 800 160" stroke="var(--info)" strokeWidth="1.8" fill="none"/>
        <path d="M 0 90 Q 80 95 160 100 T 320 92 T 480 105 T 640 98 T 800 95" stroke="var(--ok)" strokeWidth="1.8" fill="none"/>
        <g fontFamily="var(--font-mono)" fontSize="10" fill="var(--text-3)">
          {['00','04','08','12','16','20','24'].map((h,i)=><text key={h} x={i*130+10} y="250">{h}h</text>)}
        </g>
      </svg>
      <div style={{display:"flex",gap:14,fontSize:11, marginTop:8, flexWrap:"wrap"}}>
        <span style={{display:"flex",alignItems:"center",gap:5}}><span style={{width:12,height:2,background:"var(--accent)"}}/>TT-114 T°</span>
        <span style={{display:"flex",alignItems:"center",gap:5}}><span style={{width:12,height:2,background:"var(--info)"}}/>PT-201 P</span>
        <span style={{display:"flex",alignItems:"center",gap:5}}><span style={{width:12,height:2,background:"var(--ok)"}}/>FT-303 Q</span>
      </div>
    </div>
  </ModalShell>
);

Object.assign(window, { ModalShell, SimModal, DashboardModal, PIDModal, MaximoModal, AnalyticsModal, DocsModal, EventsModal, SettingsModal, HistoryModal });
