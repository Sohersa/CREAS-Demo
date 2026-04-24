// Inspector v2 — serif headline, more editorial hierarchy

const Inspector = ({ assetId, onClose, onOpenModal }) => {
  const [tab, setTab] = React.useState('telem');
  if (!assetId) return null;
  const a = {
    tag:'UHT-TMR-001', name:'Túnel UHT Aséptico', cls:'UHT · Indirect · Tubular',
    manufacturer:'Tetra Pak · A3/Flex', serial:'TP-A3F-2021-07742', installed:'2021-05-14', crit:'A',
    loc:'Monterrey · Nave 2 · L-02',
    telemetry:[
      { tag:'TT-114', label:'T° esterilización', value:138.2, unit:'°C', tone:'ok', sp:137, spark:[136,137,138,138.2,138.1,138.3,138.2] },
      { tag:'PT-201', label:'Presión vapor', value:4.82, unit:'bar', tone:'ok', sp:4.8, spark:[4.7,4.8,4.82,4.81,4.83,4.82,4.82] },
      { tag:'FT-303', label:'Flujo leche', value:9.8, unit:'m³/h', tone:'warn', sp:10, spark:[10.1,10.0,9.9,9.8,9.7,9.8,9.8] },
      { tag:'FT-304', label:'F₀ acumulado', value:6.4, unit:'min', tone:'ok', sp:5.0, spark:[5.8,6.0,6.1,6.2,6.3,6.4,6.4] },
    ],
    docs:['Manual Tetra Pak A3/Flex (ES).pdf','P&ID-UHT-02-R4.dwg','Certificado F₀ Q1-2026.pdf','SOP CIP-Aséptico v3.2.pdf'],
    wos:[
      { id:'WO-45213', st:'PLAN', task:'PM02 sello mecánico bomba', tec:'J. Ramírez', when:'22/04 · 4h' },
      { id:'WO-45120', st:'LIVE', task:'Calibración TT-114 anual', tec:'M. Vega', when:'en sitio' },
    ],
  };

  const tabs = [
    { id:'ident', label:'Identidad' },
    { id:'telem', label:'Telemetría' },
    { id:'docs', label:'Docs' },
    { id:'mtto', label:'Mantto' },
    { id:'cost', label:'SAP CO' },
  ];

  return (
    <aside style={{width:380,flexShrink:0,background:"var(--surface)",border:"1px solid var(--line)",borderRadius:20,display:"flex",flexDirection:"column",overflow:"hidden"}}>
      <div style={{padding:"20px 22px 16px",borderBottom:"1px solid var(--line)"}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",marginBottom:10}}>
          <div style={{display:"flex",gap:6}}>
            <Pill tone="accent">CRIT A</Pill>
            <Pill tone="live" dot>OPERANDO</Pill>
          </div>
          <button className="btn icon xs ghost" onClick={onClose}><Icon name="x" size={13}/></button>
        </div>
        <div className="eyebrow" style={{marginBottom:4}}>{a.tag}</div>
        <h2 style={{margin:0,fontSize:26,lineHeight:1.02,letterSpacing:"-0.035em",fontWeight:600}}>{a.name}</h2>
        <div style={{fontSize:12,color:"var(--ink-3)",marginTop:8}}>{a.cls}</div>
        <div style={{display:"flex",gap:6,marginTop:14,flexWrap:"wrap"}}>
          <button className="btn sm" onClick={()=>onOpenModal('pid')}><Icon name="layers" size={12}/>P&ID</button>
          <button className="btn sm" onClick={()=>onOpenModal('history')}><Icon name="history" size={12}/>Histórico</button>
          <button className="btn sm accent" onClick={()=>onOpenModal('sim')}><Icon name="sparkle" size={12}/>Simular</button>
        </div>
      </div>

      <div style={{display:"flex",gap:0,padding:"0 12px",borderBottom:"1px solid var(--line)"}}>
        {tabs.map(t=>(
          <button key={t.id} onClick={()=>setTab(t.id)} style={{
            flex:1,height:40,border:"none",background:"transparent",
            borderBottom:tab===t.id?"2px solid var(--ink)":"2px solid transparent",
            color:tab===t.id?"var(--ink)":"var(--ink-3)",fontSize:12,fontWeight:500,cursor:"pointer",padding:0
          }}>{t.label}</button>
        ))}
      </div>

      <div style={{flex:1,overflowY:"auto",padding:"18px 22px"}}>
        {tab==='ident' && (
          <div style={{display:"flex",flexDirection:"column",gap:14}}>
            {[['Tag ISA-5.1',a.tag,true],['Fabricante',a.manufacturer],['Serie',a.serial,true],['Instalación',a.installed,true],['Criticidad','A · misión crítica'],['Ubicación',a.loc]].map(([k,v,mono],i)=>(
              <div key={i} style={{display:"flex",justifyContent:"space-between",alignItems:"baseline",gap:10,paddingBottom:10,borderBottom:i<5?"1px dashed var(--line)":"none"}}>
                <span className="eyebrow">{k}</span>
                <span className={mono?"mono":""} style={{fontSize:12.5,fontWeight:500,textAlign:"right"}}>{v}</span>
              </div>
            ))}
          </div>
        )}

        {tab==='telem' && (
          <div style={{display:"flex",flexDirection:"column",gap:14}}>
            {a.telemetry.map(t=>{
              const c = t.tone==='warn'?"var(--warn)":"var(--ok)";
              return (
                <div key={t.tag} style={{padding:"14px",border:"1px solid var(--line)",borderRadius:12,background:"var(--bg)"}}>
                  <div style={{display:"flex",justifyContent:"space-between",marginBottom:8}}>
                    <span className="eyebrow">{t.tag}</span>
                    <span className="mono" style={{fontSize:10,color:c}}>SP {t.sp}{t.unit}</span>
                  </div>
                  <div style={{fontSize:11.5,color:"var(--ink-3)",marginBottom:6}}>{t.label}</div>
                  <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-end",gap:10}}>
                    <div className="mega-num" style={{fontSize:32,color:c}}>
                      {t.value}<span style={{fontSize:14,color:"var(--ink-3)",marginLeft:4,fontFamily:"var(--font-mono)"}}>{t.unit}</span>
                    </div>
                    <Spark data={t.spark} w={100} h={34} color={c}/>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {tab==='docs' && (
          <div style={{display:"flex",flexDirection:"column",gap:4}}>
            <div className="eyebrow" style={{marginBottom:6}}>7 documentos vinculados</div>
            {a.docs.map(d=>(
              <button key={d} className="btn sm" style={{justifyContent:"space-between",width:"100%"}}>
                <span style={{display:"flex",alignItems:"center",gap:8,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap",fontWeight:400,color:"var(--ink-2)"}}>
                  <Icon name="doc" size={12} style={{color:"var(--ink-3)"}}/>{d}
                </span>
                <Icon name="external" size={11} style={{color:"var(--ink-4)"}}/>
              </button>
            ))}
          </div>
        )}

        {tab==='mtto' && (
          <div style={{display:"flex",flexDirection:"column",gap:10}}>
            {a.wos.map(w=>(
              <div key={w.id} style={{padding:"12px 14px",border:"1px solid var(--line)",borderRadius:12}}>
                <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:6}}>
                  <span className="mono" style={{fontSize:11,fontWeight:600}}>{w.id}</span>
                  <Pill tone={w.st==='LIVE'?'live':'warn'} dot={w.st==='LIVE'}>{w.st==='LIVE'?'EN EJECUCIÓN':'PLANIFICADA'}</Pill>
                </div>
                <div style={{fontSize:12.5,color:"var(--ink)",marginBottom:4}}>{w.task}</div>
                <div className="mono" style={{fontSize:10.5,color:"var(--ink-3)"}}>{w.tec} · {w.when}</div>
              </div>
            ))}
            <button className="btn sm" onClick={()=>onOpenModal('maximo')} style={{justifyContent:"center"}}><Icon name="plus" size={12}/>Crear OT</button>
          </div>
        )}

        {tab==='cost' && (
          <div>
            <div className="eyebrow" style={{marginBottom:8}}>OPEX YTD</div>
            <div className="mega-num" style={{fontSize:44}}>$184,320<span style={{fontSize:16,color:"var(--ink-3)",fontFamily:"var(--font-mono)",marginLeft:6}}>MXN</span></div>
            <div className="mono" style={{fontSize:11,color:"var(--ok)",marginTop:4}}>▼ −4.2% vs budget</div>
            <div style={{marginTop:22,display:"flex",flexDirection:"column",gap:12}}>
              {[['Centro costo','CC-4011-UHT'],['Última compra','Spare sello · $12,400'],['Próxima renovación','Q3-2026']].map(([k,v])=>(
                <div key={k} style={{display:"flex",justifyContent:"space-between",paddingBottom:10,borderBottom:"1px dashed var(--line)"}}>
                  <span className="eyebrow">{k}</span><span className="mono" style={{fontSize:12}}>{v}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};

Object.assign(window,{Inspector});
