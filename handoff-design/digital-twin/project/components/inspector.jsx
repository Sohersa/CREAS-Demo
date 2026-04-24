const Inspector = ({ assetId, onClose, onOpenModal }) => {
  const [tab, setTab] = React.useState('ident');
  const [open, setOpen] = React.useState({ident:true, telem:true, docs:false, mtto:false, cost:false, spec:false});
  if (!assetId) return null;

  const asset = {
    id: 'UHT-01',
    tag: 'UHT-TMR-001',
    name: 'Túnel UHT Aséptico',
    cls: 'UHT · Indirect · Tubular',
    manufacturer: 'Tetra Pak · A3/Flex',
    serial: 'TP-A3F-2021-07742',
    installed: '2021-05-14',
    criticality: 'A',
    location: 'Monterrey · Nave 2 · L-02',
    telemetry: [
      { tag:'TT-114', label:'T° Esterilización', value:138.2, unit:'°C', tone:'ok', setpoint:137, spark:[136,137,138,138.2,138.1,138.3,138.2] },
      { tag:'PT-201', label:'Presión Vapor', value:4.82, unit:'bar', tone:'ok', setpoint:4.8, spark:[4.7,4.8,4.82,4.81,4.83,4.82,4.82] },
      { tag:'FT-303', label:'Flujo Leche', value:9.8, unit:'m³/h', tone:'warn', setpoint:10, spark:[10.1,10.0,9.9,9.8,9.7,9.8,9.8] },
      { tag:'FT-304', label:'F₀ acumulado', value:6.4, unit:'min', tone:'ok', setpoint:5.0, spark:[5.8,6.0,6.1,6.2,6.3,6.4,6.4] },
    ],
    docs: 7,
    wos: 2,
    cost: 184320,
  };

  const Section = ({ id, title, badge, children }) => (
    <div style={{borderBottom:"1px solid var(--border)"}}>
      <button onClick={()=>setOpen({...open, [id]:!open[id]})} style={{
        width:"100%", padding:"10px 16px", background:"transparent", border:"none", cursor:"pointer",
        display:"flex", alignItems:"center", justifyContent:"space-between", gap:8
      }}>
        <span style={{display:"flex",alignItems:"center",gap:8, fontSize:12, fontWeight:600}}>
          <Icon name={open[id]?"chevron-down":"chevron-right"} size={13} style={{color:"var(--text-3)"}}/>
          {title}
          {badge!=null && <span style={{fontFamily:"var(--font-mono)",fontSize:10,color:"var(--text-3)"}}>{badge}</span>}
        </span>
      </button>
      {open[id] && <div style={{padding:"0 16px 14px 34px"}}>{children}</div>}
    </div>
  );

  const Row = ({ label, value, mono, children }) => (
    <div style={{display:"grid",gridTemplateColumns:"110px 1fr", gap:8, padding:"4px 0", fontSize:11.5, alignItems:"baseline"}}>
      <span style={{color:"var(--text-3)"}}>{label}</span>
      <span className={mono?"mono":""} style={{color:"var(--text)", fontWeight:mono?500:400}}>{value}{children}</span>
    </div>
  );

  return (
    <aside style={{
      width:360, flexShrink:0,
      background:"var(--surface)", borderLeft:"1px solid var(--border)",
      display:"flex", flexDirection:"column", overflow:"hidden"
    }}>
      {/* Header */}
      <div style={{padding:"14px 16px", borderBottom:"1px solid var(--border)"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",gap:8, marginBottom:8}}>
          <div style={{minWidth:0}}>
            <div style={{display:"flex",alignItems:"center",gap:8, marginBottom:4}}>
              <Pill tone="accent">CRIT. A</Pill>
              <Pill tone="live" dot>OPERANDO</Pill>
            </div>
            <h3 style={{margin:0,fontSize:16,fontWeight:600,letterSpacing:"-0.015em"}}>{asset.name}</h3>
            <div className="mono" style={{fontSize:11, color:"var(--text-3)", marginTop:2}}>{asset.tag} · {asset.cls}</div>
          </div>
          <button className="btn icon sm ghost" onClick={onClose}><Icon name="x" size={14}/></button>
        </div>
        <div style={{display:"flex",gap:6, flexWrap:"wrap"}}>
          <button className="btn sm" onClick={()=>onOpenModal('pid')}><Icon name="layers" size={12}/>P&ID</button>
          <button className="btn sm" onClick={()=>onOpenModal('history')}><Icon name="history" size={12}/>Histórico</button>
          <button className="btn sm accent" onClick={()=>onOpenModal('sim')}><Icon name="sparkle" size={12}/>Simular</button>
        </div>
      </div>

      {/* Scroll content */}
      <div style={{flex:1, overflowY:"auto"}}>
        <Section id="ident" title="Identidad">
          <Row label="Tag ISA-5.1" value={asset.tag} mono/>
          <Row label="Fabricante" value={asset.manufacturer}/>
          <Row label="Serie" value={asset.serial} mono/>
          <Row label="Instalación" value={asset.installed} mono/>
          <Row label="Criticidad" value="A · Misión crítica"/>
          <Row label="Ubicación" value={asset.location}/>
        </Section>

        <Section id="telem" title="Telemetría tiempo real" badge={`· ${asset.telemetry.length} tags`}>
          <div style={{display:"flex",flexDirection:"column",gap:8}}>
            {asset.telemetry.map(t => (
              <div key={t.tag} style={{padding:"8px 10px", borderRadius:8, border:"1px solid var(--border)", background:"var(--surface-2)"}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"baseline",marginBottom:4}}>
                  <span className="mono" style={{fontSize:10.5, color:"var(--text-3)"}}>{t.tag}</span>
                  <span className="mono" style={{fontSize:10.5, color: t.tone==='warn'?"var(--warn)":"var(--ok)"}}>SP {t.setpoint}{t.unit}</span>
                </div>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",gap:10}}>
                  <div>
                    <div style={{fontSize:11, color:"var(--text-2)"}}>{t.label}</div>
                    <div className="mono" style={{fontSize:18, fontWeight:500, letterSpacing:"-0.015em", color: t.tone==='warn'?"var(--warn)":"var(--text)"}}>
                      {t.value}<span style={{fontSize:11, color:"var(--text-3)", marginLeft:4}}>{t.unit}</span>
                    </div>
                  </div>
                  <Sparkline data={t.spark} w={90} h={28} color={t.tone==='warn'?"var(--warn)":"var(--ok)"}/>
                </div>
              </div>
            ))}
          </div>
        </Section>

        <Section id="docs" title="Documentos técnicos" badge={`· ${asset.docs}`}>
          <div style={{display:"flex",flexDirection:"column",gap:4}}>
            {['Manual Tetra Pak A3/Flex (ES).pdf','P&ID-UHT-02-R4.dwg','Certificado F₀ Q1-2026.pdf','SOP CIP-Aséptico v3.2.pdf'].map(d=>(
              <button key={d} className="btn sm" style={{justifyContent:"space-between",width:"100%"}}>
                <span style={{display:"flex",alignItems:"center",gap:8,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                  <Icon name="doc" size={12} style={{color:"var(--text-3)"}}/>
                  <span style={{fontSize:11.5, fontWeight:400, color:"var(--text-2)"}}>{d}</span>
                </span>
                <Icon name="external" size={11} style={{color:"var(--text-4)"}}/>
              </button>
            ))}
            <button className="btn ghost sm" style={{justifyContent:"flex-start", color:"var(--text-3)", fontSize:11, marginTop:4}}>Ver los 7 documentos →</button>
          </div>
        </Section>

        <Section id="mtto" title="Mantenimiento · Maximo" badge={`· ${asset.wos} OT activas`}>
          <div style={{display:"flex",flexDirection:"column",gap:6}}>
            <div style={{padding:"8px 10px",border:"1px solid var(--border)",borderRadius:8}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:2}}>
                <span className="mono" style={{fontSize:11,fontWeight:600}}>WO-45213</span>
                <Pill tone="warn">PLANIFICADA</Pill>
              </div>
              <div style={{fontSize:11.5, color:"var(--text-2)"}}>PM02 · Cambio sello mecánico bomba booster</div>
              <div className="mono" style={{fontSize:10, color:"var(--text-3)", marginTop:4}}>Téc: J. Ramírez · 2026-04-22 · 4h</div>
            </div>
            <div style={{padding:"8px 10px",border:"1px solid var(--border)",borderRadius:8}}>
              <div style={{display:"flex",justifyContent:"space-between",marginBottom:2}}>
                <span className="mono" style={{fontSize:11,fontWeight:600}}>WO-45120</span>
                <Pill tone="live" dot>EN EJECUCIÓN</Pill>
              </div>
              <div style={{fontSize:11.5, color:"var(--text-2)"}}>Calibración TT-114 · anual</div>
              <div className="mono" style={{fontSize:10, color:"var(--text-3)", marginTop:4}}>Téc: M. Vega · en sitio</div>
            </div>
            <button className="btn sm" style={{justifyContent:"center"}} onClick={()=>onOpenModal('maximo')}>
              <Icon name="plus" size={12}/>Crear OT
            </button>
          </div>
        </Section>

        <Section id="cost" title="Costo YTD · SAP CO">
          <div style={{display:"flex",gap:8, marginBottom:8}}>
            <div style={{flex:1, padding:"8px 10px", border:"1px solid var(--border)", borderRadius:8}}>
              <div className="eyebrow" style={{marginBottom:4}}>OPEX YTD</div>
              <div className="mono" style={{fontSize:16, fontWeight:500}}>$184,320<span style={{fontSize:10, color:"var(--text-3)"}}> MXN</span></div>
            </div>
            <div style={{flex:1, padding:"8px 10px", border:"1px solid var(--border)", borderRadius:8}}>
              <div className="eyebrow" style={{marginBottom:4}}>vs Budget</div>
              <div className="mono" style={{fontSize:16, fontWeight:500, color:"var(--ok)"}}>−4.2%</div>
            </div>
          </div>
          <Row label="Centro costo" value="CC-4011-UHT" mono/>
          <Row label="Última compra" value="Spare sello · $12,400 · 2026-03-28"/>
        </Section>

        <Section id="spec" title="Ficha técnica · fabricante">
          <Row label="Capacidad" value="12,000 L/h" mono/>
          <Row label="T° objetivo" value="137 °C ± 1" mono/>
          <Row label="Tiempo sostenido" value="4 s" mono/>
          <Row label="Recuperación térmica" value="≥ 90%" mono/>
          <Row label="Energía" value="38 kWh/m³" mono/>
        </Section>
      </div>
    </aside>
  );
};

Object.assign(window, { Inspector });
