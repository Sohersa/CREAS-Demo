// Copilot — editorial chat panel

const MSGS = [
  { role:'user', t:'¿Por qué bajó la producción hoy?' },
  { role:'ai', t:'La línea UHT-02 produce **24,800 bph** vs target 26,000 (−4.6%). Identifico 2 causas concurrentes:',
    citations:[
      { icon:'warn', label:'BL-B02 Sopladora', detail:'Alarma vibración 4h 12min · patrón compatible con desalineación' },
      { icon:'info', label:'FT-303 Flujo leche', detail:'Operando 2% bajo setpoint desde cambio de lote 08:32' },
    ],
    actions:[
      { label:'Generar OT preventiva BL-B02', primary:true },
      { label:'Simular ajuste FT-303' },
    ]
  },
];

const Copilot = ({ onClose }) => {
  const [input, setInput] = React.useState('');
  return (
    <aside className="floating" style={{position:"fixed",right:22,bottom:22,width:400,maxHeight:"72vh",display:"flex",flexDirection:"column",borderRadius:18,overflow:"hidden",zIndex:60}}>
      <div style={{padding:"14px 18px",borderBottom:"1px solid var(--line)",display:"flex",alignItems:"center",justifyContent:"space-between"}}>
        <div style={{display:"flex",alignItems:"center",gap:10}}>
          <div data-ink-bg style={{width:28,height:28,borderRadius:"50%",background:"var(--ink)",display:"grid",placeItems:"center",color:"#fff"}}>
            <Icon name="sparkle" size={14}/>
          </div>
          <div>
            <div style={{fontSize:13,fontWeight:600}}>Copiloto AXIS</div>
            <div className="mono" style={{fontSize:9.5,color:"var(--ink-3)",letterSpacing:".08em"}}>CLAUDE SONNET · LIVE</div>
          </div>
        </div>
        <button className="btn icon xs ghost" onClick={onClose}><Icon name="x" size={13}/></button>
      </div>

      <div style={{flex:1,overflowY:"auto",padding:"16px 18px",display:"flex",flexDirection:"column",gap:16}}>
        {MSGS.map((m,i)=>(
          m.role==='user' ? (
            <div data-ink-bg key={i} style={{alignSelf:"flex-end",maxWidth:"82%",padding:"10px 14px",background:"var(--ink)",color:"#fff",borderRadius:"14px 14px 2px 14px",fontSize:12.5}}>{m.t}</div>
          ) : (
            <div key={i} style={{display:"flex",flexDirection:"column",gap:10}}>
              <div style={{fontSize:13,lineHeight:1.55,color:"var(--ink)"}} dangerouslySetInnerHTML={{__html:m.t.replace(/\*\*(.+?)\*\*/g,'<strong>$1</strong>')}}/>
              {m.citations && (
                <div style={{display:"flex",flexDirection:"column",gap:6}}>
                  {m.citations.map((c,j)=>(
                    <div key={j} style={{padding:"10px 12px",border:"1px solid var(--line)",borderRadius:10,display:"flex",gap:10,alignItems:"flex-start",background:"var(--bg)"}}>
                      <span style={{width:22,height:22,borderRadius:"50%",background:c.icon==='warn'?"var(--err-soft)":"var(--info-soft)",color:c.icon==='warn'?"var(--err)":"var(--info)",display:"grid",placeItems:"center",flexShrink:0}}>
                        <Icon name={c.icon==='warn'?'alert':'info'} size={11}/>
                      </span>
                      <div style={{flex:1,minWidth:0}}>
                        <div style={{fontSize:11.5,fontWeight:600,marginBottom:2}}>{c.label}</div>
                        <div style={{fontSize:11,color:"var(--ink-3)",lineHeight:1.4}}>{c.detail}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {m.actions && (
                <div style={{display:"flex",gap:6,flexWrap:"wrap",marginTop:4}}>
                  {m.actions.map((a,j)=>(
                    <button key={j} className={"btn sm"+(a.primary?" accent":"")}>{a.label}</button>
                  ))}
                </div>
              )}
            </div>
          )
        ))}
      </div>

      <div style={{padding:12,borderTop:"1px solid var(--line)",display:"flex",gap:6,alignItems:"center"}}>
        <input
          value={input}
          onChange={e=>setInput(e.target.value)}
          placeholder="Pregunta al copiloto…"
          style={{flex:1,height:34,border:"1px solid var(--line)",borderRadius:999,padding:"0 14px",fontFamily:"var(--font-sans)",fontSize:12.5,background:"var(--bg)"}}
        />
        <button data-ink-bg className="btn icon" style={{background:"var(--ink)",color:"#fff",borderColor:"var(--ink)"}}><Icon name="arrow-right" size={13}/></button>
      </div>
    </aside>
  );
};

Object.assign(window,{Copilot});
