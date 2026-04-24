// Modals v2 — shared shell + content for each

const Modal = ({ title, kicker, subtitle, onClose, width=1180, children, footer }) => (
  <div className="mo-overlay" onClick={onClose}>
    <div className="mo-card" onClick={e=>e.stopPropagation()} style={{
      width,maxWidth:"94vw",maxHeight:"92vh",background:"var(--bg)",borderRadius:22,border:"1px solid var(--line-strong)",
      display:"flex",flexDirection:"column",overflow:"hidden",boxShadow:"0 40px 100px -20px rgba(10,10,10,.35)"
    }}>
      <div style={{padding:"22px 28px",borderBottom:"1px solid var(--line)",display:"flex",justifyContent:"space-between",alignItems:"flex-start",gap:20,background:"var(--surface)"}}>
        <div>
          {kicker && <div className="eyebrow" style={{marginBottom:6}}>{kicker}</div>}
          <h2 style={{margin:0,fontSize:26,lineHeight:1.02,letterSpacing:"-0.035em",fontWeight:600}}>{title}</h2>
          {subtitle && <div style={{fontSize:12.5,color:"var(--ink-3)",marginTop:6}}>{subtitle}</div>}
        </div>
        <button className="btn icon sm ghost" onClick={onClose}><Icon name="x" size={14}/></button>
      </div>
      <div style={{flex:1,overflowY:"auto",padding:28}}>{children}</div>
      {footer && <div style={{padding:"14px 28px",borderTop:"1px solid var(--line)",background:"var(--surface)",display:"flex",justifyContent:"flex-end",gap:8}}>{footer}</div>}
    </div>
  </div>
);

const SimModal = ({ onClose }) => {
  const [speed,setSpeed]=React.useState(100);
  const [temp,setTemp]=React.useState(138);
  const [press,setPress]=React.useState(4.8);
  const oeeNew = 87.4 + (speed-100)*.15 + (temp-138)*.3;
  const scrapNew = 2.18 - (speed-100)*.01 + Math.abs(temp-138)*.15;
  return (
    <Modal kicker="02 · Simulación Monte Carlo" title="What-If · Escenarios operativos" subtitle="Proyecta el impacto en OEE, scrap y energía de ajustes en setpoints · 10,000 iteraciones" onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary">Guardar escenario</button><button className="btn accent">Ejecutar simulación</button></>}>
      <div style={{display:"grid",gridTemplateColumns:"380px 1fr",gap:28}}>
        <div style={{display:"flex",flexDirection:"column",gap:20}}>
          <div className="card" style={{padding:20}}>
            <SectionHeader kicker="Parámetros" title="Setpoints"/>
            {[
              ['Velocidad línea',speed,setSpeed,80,120,'%'],
              ['T° esterilización',temp,setTemp,130,145,'°C'],
              ['Presión vapor',press,v=>setPress(+v),4.0,5.5,'bar'],
            ].map(([lbl,val,setter,mn,mx,u],i)=>(
              <div key={i} style={{marginTop:i?16:0}}>
                <div style={{display:"flex",justifyContent:"space-between",marginBottom:6}}>
                  <span style={{fontSize:12}}>{lbl}</span>
                  <span className="mono" style={{fontSize:12,fontWeight:600}}>{val}<span style={{color:"var(--ink-3)",marginLeft:2}}>{u}</span></span>
                </div>
                <input type="range" className="ax" min={mn} max={mx} step={u==='bar'?.1:1} value={val} onChange={e=>setter(+e.target.value)} style={{width:"100%"}}/>
                <div className="mono" style={{display:"flex",justifyContent:"space-between",fontSize:9.5,color:"var(--ink-4)",marginTop:3}}>
                  <span>{mn}{u}</span><span>{mx}{u}</span>
                </div>
              </div>
            ))}
          </div>
          <div className="card" style={{padding:20}}>
            <SectionHeader kicker="Contexto" title="Lote actual"/>
            {[['SKU','Leche Entera 1L'],['Lote','UHT-240422-07'],['Volumen','18,000 L'],['Duración','6h 20min']].map(([k,v])=>(
              <div key={k} style={{display:"flex",justifyContent:"space-between",padding:"8px 0",borderBottom:"1px dashed var(--line)"}}>
                <span className="eyebrow">{k}</span><span className="mono" style={{fontSize:12}}>{v}</span>
              </div>
            ))}
          </div>
        </div>

        <div>
          <SectionHeader kicker="Resultado proyectado" title="Impacto estimado" hint="Intervalo de confianza 95% · n=10.000"
            right={<Pill tone="accent" dot>Simulación 2</Pill>}/>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:0,border:"1px solid var(--line)",borderRadius:14,overflow:"hidden",background:"var(--surface)",marginBottom:20}}>
            {[
              ['OEE','87.4%',oeeNew.toFixed(1)+'%',oeeNew>87.4],
              ['Scrap','2.18%',Math.max(0,scrapNew).toFixed(2)+'%',scrapNew<2.18],
              ['Energía','0.184','0.'+(180+Math.round((temp-138)*2)),false],
            ].map(([k,base,proj,good],i)=>(
              <div key={k} style={{padding:"20px 22px",borderRight:i<2?"1px solid var(--line)":"none"}}>
                <span className="eyebrow">{k}</span>
                <div style={{display:"flex",alignItems:"baseline",gap:8,marginTop:10}}>
                  <div className="mega-num" style={{fontSize:32,color:good?"var(--ok)":"var(--err)"}}>{proj}</div>
                </div>
                <div className="mono" style={{fontSize:10.5,color:"var(--ink-3)",marginTop:4}}>baseline {base}</div>
              </div>
            ))}
          </div>

          <div className="card" style={{padding:20,marginBottom:16}}>
            <SectionHeader kicker="Proyección 24h" title="OEE estimado"/>
            <svg width="100%" height="160" viewBox="0 0 700 160">
              <g stroke="var(--line)" strokeWidth="1">
                {[0,40,80,120,160].map(y=><line key={y} x1="0" x2="700" y1={y} y2={y}/>)}
              </g>
              <path d="M0 70 L60 68 L120 65 L180 62 L240 60 L300 58 L360 55 L420 52 L480 48 L540 45 L600 42 L660 40 L700 38"
                fill="none" stroke="var(--accent)" strokeWidth="2"/>
              <path d="M0 70 L60 68 L120 65 L180 62 L240 60 L300 58 L360 55 L420 52 L480 48 L540 45 L600 42 L660 40 L700 38 L700 160 L0 160 Z"
                fill="var(--accent)" opacity="0.08"/>
              <path d="M0 90 L60 90 L120 88 L180 85 L240 80 L300 78 L360 75 L420 75 L480 72 L540 70 L600 68 L660 68 L700 65"
                fill="none" stroke="var(--ink-3)" strokeWidth="1.2" strokeDasharray="3 3"/>
            </svg>
            <div className="mono" style={{display:"flex",gap:20,fontSize:11,marginTop:8,color:"var(--ink-3)"}}>
              <span><span style={{display:"inline-block",width:10,height:2,background:"var(--accent)",verticalAlign:"middle",marginRight:6}}/>Escenario simulado</span>
              <span><span style={{display:"inline-block",width:10,height:2,background:"var(--ink-3)",verticalAlign:"middle",marginRight:6}}/>Baseline</span>
            </div>
          </div>

          <div className="card" style={{padding:16,display:"flex",gap:12,alignItems:"center",background:"var(--accent-soft)",borderColor:"color-mix(in srgb, var(--accent) 30%, transparent)"}}>
            <span style={{width:30,height:30,borderRadius:"50%",background:"var(--accent)",color:"#fff",display:"grid",placeItems:"center"}}><Icon name="sparkle" size={14}/></span>
            <div style={{flex:1,fontSize:12.5,color:"var(--ink)"}}>
              <strong>Copiloto:</strong> Subir temp a 139°C incrementa OEE +1.3pts y mantiene F₀ en rango. Energía +2.1% queda compensada por reducción de scrap (−0.18pts).
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};

const DashboardModal = ({ onClose }) => (
  <Modal kicker="03 · Dashboard Ejecutivo" title="Panorama operacional" subtitle="Visión consolidada 6 plantas · mes en curso"
    onClose={onClose} width={1280}>
    <div style={{display:"grid",gridTemplateColumns:"repeat(4,1fr)",gap:14,marginBottom:22}}>
      {[
        ['Ingreso mes','$142.4M','+8.2% YoY','ok'],
        ['OEE global','84.2%','+3.1pts','ok'],
        ['Scrap','2.41%','−0.4pts','ok'],
        ['CO₂ intensidad','0.82','+2.1%','warn'],
      ].map(([k,v,d,t])=>(
        <div key={k} className="card" style={{padding:18}}>
          <span className="eyebrow">{k}</span>
          <div className="mega-num" style={{fontSize:38,marginTop:10,letterSpacing:"-0.04em"}}>{v}</div>
          <div className="mono" style={{fontSize:11,color:t==='ok'?"var(--ok)":"var(--warn)",marginTop:4}}>{d}</div>
        </div>
      ))}
    </div>

    <div style={{display:"grid",gridTemplateColumns:"1.3fr 1fr",gap:14}}>
      <div className="card" style={{padding:20}}>
        <SectionHeader kicker="Plantas" title="Ranking OEE"/>
        {[['Monterrey · Lácteos',92.1,94],['CDMX · Bebidas',88.4,90],['Guadalajara · Yogur',85.2,90],['Tijuana · Queso',82.8,85],['Puebla · Leche',79.4,85],['Mérida · Jugos',74.2,85]].map(([n,v,t],i)=>(
          <div key={n} style={{display:"grid",gridTemplateColumns:"24px 1fr 120px 60px",gap:12,padding:"10px 0",borderBottom:i<5?"1px dashed var(--line)":"none",alignItems:"center"}}>
            <span className="mono" style={{fontSize:11,color:"var(--ink-3)"}}>0{i+1}</span>
            <span style={{fontSize:13}}>{n}</span>
            <div className="bar-bg" style={{height:6,borderRadius:999,background:"var(--bg-2)",border:"none"}}>
              <div style={{width:`${v}%`,height:"100%",background:v>=t?"var(--ok)":"var(--warn)",borderRadius:999}}/>
              <div style={{position:"absolute",left:`${t}%`,top:-2,width:2,height:10,background:"var(--ink)"}}/>
            </div>
            <span className="mono" style={{fontSize:12,fontWeight:600,textAlign:"right"}}>{v}%</span>
          </div>
        ))}
      </div>
      <div className="card" style={{padding:20}}>
        <SectionHeader kicker="Agenda" title="Top 3 riesgos"/>
        {[
          ['err','Mérida','Pérdida productiva 12% Q2 por paradas UHT'],
          ['warn','Puebla','CAPEX sopladora pospuesto — riesgo MTBF'],
          ['warn','Global','Contrato energía vence 30/06 · −14% opción'],
        ].map(([tone,plant,msg],i)=>(
          <div key={i} style={{padding:"12px 0",borderBottom:i<2?"1px dashed var(--line)":"none",display:"flex",gap:10}}>
            <span style={{width:6,height:6,borderRadius:"50%",background:tone==='err'?"var(--err)":"var(--warn)",marginTop:6,flexShrink:0}}/>
            <div>
              <div className="eyebrow" style={{marginBottom:2}}>{plant}</div>
              <div style={{fontSize:12.5,color:"var(--ink)"}}>{msg}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  </Modal>
);

const PIDModal = ({ onClose }) => (
  <Modal kicker="04 · Diagrama P&ID" title="UHT-02 · Red de proceso" subtitle="Revisión R4 · válido desde 2024-03-15" onClose={onClose}>
    <div className="ruled" style={{height:520,background:"var(--surface)",border:"1px solid var(--line)",borderRadius:12,position:"relative",overflow:"hidden"}}>
      <svg width="100%" height="100%" viewBox="0 0 1100 520">
        <g stroke="var(--ink)" strokeWidth="1.3" fill="none">
          {/* Tanks */}
          <circle cx="90" cy="120" r="36"/><text x="90" y="125" textAnchor="middle" fontSize="10" fontFamily="var(--font-mono)">T-101</text>
          <circle cx="90" cy="260" r="36"/><text x="90" y="265" textAnchor="middle" fontSize="10" fontFamily="var(--font-mono)">T-102</text>
          {/* Pumps */}
          <circle cx="240" cy="190" r="22"/><text x="240" y="194" textAnchor="middle" fontSize="9" fontFamily="var(--font-mono)">P-201</text>
          {/* Heat exchanger */}
          <rect x="340" y="150" width="120" height="80"/>
          <path d="M 340 170 Q 400 130 460 170 Q 400 210 460 210" strokeWidth="1"/>
          <text x="400" y="240" textAnchor="middle" fontSize="10" fontFamily="var(--font-mono)">HX-301 UHT</text>
          {/* Hold tube */}
          <path d="M 460 190 L 560 190 L 560 280 L 660 280" strokeWidth="2" stroke="var(--accent)"/>
          <text x="510" y="178" fontSize="9" fontFamily="var(--font-mono)" fill="var(--accent-ink)">HOLD 4s</text>
          {/* Homogenizer */}
          <rect x="660" y="260" width="100" height="40"/>
          <text x="710" y="285" textAnchor="middle" fontSize="10" fontFamily="var(--font-mono)">HG-401</text>
          {/* Filler */}
          <rect x="820" y="180" width="160" height="160"/>
          <path d="M 840 200 L 960 200 M 840 240 L 960 240 M 840 280 L 960 280 M 840 320 L 960 320"/>
          <text x="900" y="365" textAnchor="middle" fontSize="10" fontFamily="var(--font-mono)">FI-F03 LLENADORA</text>

          {/* Process lines */}
          <path d="M 126 120 L 218 180 M 126 260 L 218 200 M 262 190 L 340 190 M 760 280 L 820 260"/>

          {/* Instruments */}
          {[[200,130,'TT','114'],[320,130,'PT','201'],[500,120,'FT','303'],[700,220,'PT','402'],[800,350,'LT','505']].map(([x,y,k,n])=>(
            <g key={n}>
              <circle cx={x} cy={y} r="14" fill="#fff"/>
              <line x1={x-14} x2={x+14} y1={y} y2={y}/>
              <text x={x} y={y-2} textAnchor="middle" fontSize="8" fontFamily="var(--font-mono)" fontWeight="600">{k}</text>
              <text x={x} y={y+9} textAnchor="middle" fontSize="8" fontFamily="var(--font-mono)">{n}</text>
            </g>
          ))}
        </g>
      </svg>
      <div className="floating" style={{position:"absolute",bottom:14,right:14,padding:"8px 12px",borderRadius:10,fontFamily:"var(--font-mono)",fontSize:10,color:"var(--ink-3)"}}>
        ISA-5.1 · R4 · 19 instrumentos
      </div>
    </div>
  </Modal>
);

const MaximoModal = ({ onClose }) => {
  const cols = [
    { t:'Planificadas', items:[['WO-45213','PM02 sello bomba','J. Ramírez','22/04 · 4h','accent'],['WO-45225','Inspección anual F₀','M. Vega','24/04 · 8h']] },
    { t:'En ejecución', items:[['WO-45120','Calibración TT-114','M. Vega','en sitio','ok'],['WO-45199','Ajuste PT-201','L. Hernández','en sitio','ok']] },
    { t:'Cerradas 7d', items:[['WO-45098','Limpieza CIP manual','Equipo CIP','20/04'],['WO-45087','Reemplazo sensor','J. Ramírez','19/04']] },
  ];
  return (
    <Modal kicker="05 · Maximo IBM" title="Mantenimiento UHT-02" subtitle="8 órdenes activas · sincronizado hace 1min" onClose={onClose} width={1240}
      footer={<><button className="btn">Export CSV</button><button className="btn accent"><Icon name="plus" size={12}/>Crear OT</button></>}>
      <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:16}}>
        {cols.map(c=>(
          <div key={c.t}>
            <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:10}}>
              <h4 style={{margin:0,fontSize:15,fontWeight:600,letterSpacing:"-0.02em"}}>{c.t}</h4>
              <span className="mono" style={{fontSize:10,color:"var(--ink-3)"}}>{c.items.length}</span>
            </div>
            <div style={{display:"flex",flexDirection:"column",gap:8}}>
              {c.items.map(([id,task,tec,when,tone],i)=>(
                <div key={i} className="card" style={{padding:14,borderLeft:tone?`3px solid var(--${tone==='accent'?'accent':'ok'})`:"1px solid var(--line)"}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:4}}>
                    <span className="mono" style={{fontSize:11,fontWeight:600}}>{id}</span>
                    {tone==='ok' && <Pill tone="live" dot>LIVE</Pill>}
                  </div>
                  <div style={{fontSize:12.5,marginBottom:4}}>{task}</div>
                  <div className="mono" style={{fontSize:10.5,color:"var(--ink-3)"}}>{tec} · {when}</div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Modal>
  );
};

const AnalyticsModal = ({ onClose }) => (
  <Modal kicker="06 · Analytics" title="Analítica operacional" subtitle="MTBF · Pareto paros · Heatmap · Anomalías" onClose={onClose} width={1280}>
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16,marginBottom:16}}>
      <div className="card" style={{padding:20}}>
        <SectionHeader kicker="Fiabilidad" title="MTBF por activo" hint="Últimas 8 semanas"/>
        {[['UHT-01',142,85],['BL-B02',68,85],['FI-F03',112,85],['HG-01',201,85],['PT-01',178,85]].map(([n,v],i)=>(
          <div key={n} style={{display:"grid",gridTemplateColumns:"90px 1fr 60px",gap:12,padding:"8px 0",alignItems:"center"}}>
            <span className="mono" style={{fontSize:11}}>{n}</span>
            <div style={{height:4,background:"var(--bg-2)",borderRadius:999,overflow:"hidden"}}>
              <div style={{width:`${Math.min(100,v/2.5)}%`,height:"100%",background:v<85?"var(--err)":"var(--ok)"}}/>
            </div>
            <span className="mono" style={{fontSize:11,fontWeight:600,textAlign:"right"}}>{v}h</span>
          </div>
        ))}
      </div>
      <div className="card" style={{padding:20}}>
        <SectionHeader kicker="Pareto" title="Causas de paros"/>
        <svg width="100%" height="180" viewBox="0 0 400 180">
          {[['Mecánico',72,'#0A0A0A'],['Eléctrico',48,'#444'],['Instr.',32,'#888'],['Calidad',20,'#aaa'],['Otros',12,'#ccc']].map(([l,v,c],i)=>(
            <g key={l}>
              <rect x={20+i*72} y={160-v*1.8} width="56" height={v*1.8} fill={c}/>
              <text x={48+i*72} y={175} textAnchor="middle" fontSize="10" fontFamily="var(--font-mono)" fill="var(--ink-3)">{l}</text>
              <text x={48+i*72} y={155-v*1.8} textAnchor="middle" fontSize="10" fontFamily="var(--font-mono)" fontWeight="600">{v}</text>
            </g>
          ))}
          <path d="M 48 100 L 120 60 L 192 40 L 264 30 L 336 26" fill="none" stroke="var(--accent)" strokeWidth="2"/>
        </svg>
      </div>
    </div>
    <div className="card" style={{padding:20}}>
      <SectionHeader kicker="Heatmap" title="Eventos por turno × día" hint="Rojo = anomalías detectadas"/>
      <div style={{display:"grid",gridTemplateColumns:"80px repeat(14,1fr)",gap:2}}>
        <div/>
        {Array.from({length:14}).map((_,i)=><div key={i} className="mono" style={{fontSize:9,color:"var(--ink-4)",textAlign:"center"}}>D{i+1}</div>)}
        {['Matutino','Vespertino','Nocturno'].map((t,r)=>(
          <React.Fragment key={t}>
            <div className="mono" style={{fontSize:10,color:"var(--ink-3)",paddingRight:8,textAlign:"right",lineHeight:"26px"}}>{t}</div>
            {Array.from({length:14}).map((_,c)=>{
              const v = Math.random();
              const col = v>.8?"var(--err)":v>.6?"var(--warn)":v>.3?"var(--accent-soft)":"var(--bg-2)";
              return <div key={c} style={{height:26,background:col,borderRadius:3}}/>;
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  </Modal>
);

const EventsModal = ({ onClose }) => (
  <Modal kicker="07 · Bitácora" title="Eventos y alarmas" subtitle="28 eventos activos · 4 críticos" onClose={onClose} width={1000}>
    <table className="ax">
      <thead><tr><th>Hora</th><th>Severidad</th><th>Activo</th><th>Mensaje</th><th>Estado</th></tr></thead>
      <tbody>
        {[
          ['14:42:18','err','BL-B02','Vibración > 8mm/s · patrón desalineación','Abierto'],
          ['14:28:03','warn','FT-303','Flujo 2% bajo setpoint sostenido','En revisión'],
          ['13:55:41','warn','PT-402','Presión llenado fluctuante','En revisión'],
          ['13:12:02','info','UHT-01','Cambio de lote UHT-240422-07','OK'],
          ['12:45:10','ok','HG-01','CIP completado · F₀ en rango','Cerrado'],
          ['11:30:22','err','BL-B02','Sensor temperatura drift','Mitigado'],
        ].map((r,i)=>(
          <tr key={i}>
            <td className="mono" style={{fontSize:11}}>{r[0]}</td>
            <td><Pill tone={r[1]} dot={r[1]!=='info'}>{r[1].toUpperCase()}</Pill></td>
            <td className="mono" style={{fontSize:11.5}}>{r[2]}</td>
            <td>{r[3]}</td>
            <td style={{fontSize:12,color:"var(--ink-3)"}}>{r[4]}</td>
          </tr>
        ))}
      </tbody>
    </table>
  </Modal>
);

const DocsModal = ({ onClose }) => (
  <Modal kicker="08 · Docs" title="Documentación técnica" onClose={onClose} width={1000}>
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:12}}>
      {['Manual Tetra Pak A3/Flex','P&ID UHT-02 R4','Certificado F₀ Q1','SOP CIP Aséptico','Lista de repuestos 2026','Hoja seguridad NaOH','Procedimiento arranque','Registro lote UHT-240422','Diagrama eléctrico'].map((d,i)=>(
        <button key={d} className="card" style={{padding:16,textAlign:"left",cursor:"pointer",background:"var(--surface)"}}>
          <div style={{width:44,height:56,background:"var(--bg-2)",border:"1px solid var(--line)",borderRadius:4,marginBottom:12,display:"grid",placeItems:"center",color:"var(--ink-3)"}}>
            <Icon name="doc" size={18}/>
          </div>
          <div style={{fontSize:12.5,fontWeight:500,marginBottom:3}}>{d}</div>
          <div className="mono" style={{fontSize:10.5,color:"var(--ink-3)"}}>PDF · {(Math.random()*5+1).toFixed(1)}MB</div>
        </button>
      ))}
    </div>
  </Modal>
);

const SettingsModal = ({ onClose }) => (
  <Modal kicker="⚙" title="Configuración" subtitle="Preferencias de cuenta · integraciones · unidades" onClose={onClose} width={880}>
    <div style={{display:"flex",flexDirection:"column",gap:16}}>
      {[['Integraciones','SAP S/4HANA · Maximo · Tetra Pak Cloud · AVEVA PI'],['Unidades','SI · °C · bar · m³/h'],['Notificaciones','Email · Teams · SMS crítico'],['Sesión','luis.h@gruposohersa.com · MFA activo']].map(([k,v])=>(
        <div key={k} className="card" style={{padding:18,display:"flex",justifyContent:"space-between",alignItems:"center"}}>
          <div><div className="eyebrow" style={{marginBottom:4}}>{k}</div><div style={{fontSize:13}}>{v}</div></div>
          <button className="btn sm">Editar</button>
        </div>
      ))}
    </div>
  </Modal>
);

const HistoryModal = ({ onClose }) => (
  <Modal kicker="09 · Histórico" title="Timeline UHT-02" subtitle="Últimos 30 días · 142 eventos" onClose={onClose} width={1080}>
    <div style={{display:"flex",flexDirection:"column",gap:0,position:"relative"}}>
      <div style={{position:"absolute",left:120,top:8,bottom:8,width:1,background:"var(--line)"}}/>
      {[
        ['22/04 14:42','err','Alarma BL-B02','Vibración fuera de rango'],
        ['22/04 08:32','info','Cambio lote','UHT-240422-07 · 18,000L'],
        ['21/04 22:10','ok','CIP completado','4h 20min · F₀ ok'],
        ['20/04 11:04','warn','PM preventivo','Sustitución de sellos mecánicos'],
        ['18/04 06:00','ok','Arranque turno','OEE 89.2% promedio'],
        ['15/04 14:22','info','Calibración TT-114','Desviación 0.3°C corregida'],
      ].map((e,i)=>(
        <div key={i} style={{display:"grid",gridTemplateColumns:"120px 40px 1fr",gap:20,padding:"14px 0",alignItems:"flex-start"}}>
          <span className="mono" style={{fontSize:11,color:"var(--ink-3)"}}>{e[0]}</span>
          <span style={{width:10,height:10,borderRadius:"50%",background:`var(--${e[1]==='info'?'info':e[1]})`,border:"3px solid var(--bg)",marginLeft:5,marginTop:3,position:"relative",zIndex:2}}/>
          <div>
            <div style={{fontSize:13,fontWeight:500}}>{e[2]}</div>
            <div style={{fontSize:12,color:"var(--ink-3)",marginTop:2}}>{e[3]}</div>
          </div>
        </div>
      ))}
    </div>
  </Modal>
);

const Modals = ({ open, onClose }) => {
  if (!open) return null;
  const props = { onClose };
  return (
    <>
      {open==='sim' && <SimModal {...props}/>}
      {open==='dashboard' && <DashboardModal {...props}/>}
      {open==='pid' && <PIDModal {...props}/>}
      {open==='maximo' && <MaximoModal {...props}/>}
      {open==='analytics' && <AnalyticsModal {...props}/>}
      {open==='events' && <EventsModal {...props}/>}
      {open==='docs' && <DocsModal {...props}/>}
      {open==='settings' && <SettingsModal {...props}/>}
      {open==='history' && <HistoryModal {...props}/>}
    </>
  );
};

Object.assign(window,{Modals});
