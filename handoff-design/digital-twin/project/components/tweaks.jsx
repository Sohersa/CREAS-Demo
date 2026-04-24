// Tweaks panel — exposed in the corner when __activate_edit_mode is received

const TweaksPanel = ({ tweaks, setTweaks, onClose }) => {
  const set = (k,v) => {
    const next = { ...tweaks, [k]:v };
    setTweaks(next);
    window.parent.postMessage({type:'__edit_mode_set_keys', edits:{[k]:v}}, '*');
  };

  const Label = ({ children }) => (
    <div className="eyebrow" style={{marginBottom:6}}>{children}</div>
  );

  return (
    <div style={{
      position:"fixed", right:16, bottom:16, zIndex:80, width:288,
      background:"var(--surface)", border:"1px solid var(--border)", borderRadius:14,
      boxShadow:"var(--shadow-lg)", padding:16, fontFamily:"var(--font-sans)"
    }}>
      <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
        <div style={{display:"flex",alignItems:"center",gap:8}}>
          <Icon name="sparkle" size={14}/>
          <span style={{fontWeight:600, fontSize:13}}>Tweaks</span>
        </div>
        <button className="btn icon sm ghost" onClick={onClose}><Icon name="x" size={13}/></button>
      </div>

      <div style={{display:"flex",flexDirection:"column",gap:12}}>
        <div>
          <Label>Acento</Label>
          <div style={{display:"flex",gap:6}}>
            {[
              ['orange','#FF5500','EY'],
              ['graphite','#111','Graph'],
              ['indigo','#4C4CFF','Indigo'],
              ['teal','#006B6B','Teal'],
            ].map(([k,c,l])=>(
              <button key={k} onClick={()=>set('accent',k)} style={{
                flex:1, height:32, borderRadius:6,
                border:"1px solid "+(tweaks.accent===k?"var(--text)":"var(--border)"),
                background: tweaks.accent===k?"var(--surface-2)":"var(--surface)",
                cursor:"pointer", display:"flex",flexDirection:"column",alignItems:"center",gap:2, padding:"3px 0"
              }}>
                <span style={{width:14,height:14,borderRadius:"50%",background:c}}/>
                <span style={{fontSize:9, color:"var(--text-3)", fontFamily:"var(--font-mono)"}}>{l}</span>
              </button>
            ))}
          </div>
        </div>

        <div>
          <Label>Tipografía</Label>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)", gap:6}}>
            {[['geist','Geist'],['inter','Inter'],['system','System']].map(([k,l])=>(
              <button key={k} onClick={()=>set('type',k)} style={{
                height:30, borderRadius:6,
                border:"1px solid "+(tweaks.type===k?"var(--text)":"var(--border)"),
                background:tweaks.type===k?"var(--text)":"var(--surface)",
                color:tweaks.type===k?"#fff":"var(--text-2)",
                fontSize:11, cursor:"pointer", fontWeight:500
              }}>{l}</button>
            ))}
          </div>
        </div>

        <div>
          <Label>Densidad</Label>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)", gap:6}}>
            {[['compact','Compacta'],['balanced','Balanceada'],['spacious','Amplia']].map(([k,l])=>(
              <button key={k} onClick={()=>set('density',k)} style={{
                height:30, borderRadius:6,
                border:"1px solid "+(tweaks.density===k?"var(--text)":"var(--border)"),
                background:tweaks.density===k?"var(--text)":"var(--surface)",
                color:tweaks.density===k?"#fff":"var(--text-2)",
                fontSize:11, cursor:"pointer", fontWeight:500
              }}>{l}</button>
            ))}
          </div>
        </div>

        <div>
          <Label>Overlays 3D</Label>
          <div style={{display:"grid",gridTemplateColumns:"repeat(2,1fr)", gap:6}}>
            {[['glass','Glass'],['solid','Sólido']].map(([k,l])=>(
              <button key={k} onClick={()=>set('glass',k)} style={{
                height:30, borderRadius:6,
                border:"1px solid "+(tweaks.glass===k?"var(--text)":"var(--border)"),
                background:tweaks.glass===k?"var(--text)":"var(--surface)",
                color:tweaks.glass===k?"#fff":"var(--text-2)",
                fontSize:11, cursor:"pointer", fontWeight:500
              }}>{l}</button>
            ))}
          </div>
        </div>

        <div style={{padding:10, background:"var(--surface-2)", border:"1px solid var(--border)", borderRadius:8}}>
          <Label>Presets</Label>
          <div style={{display:"flex",flexDirection:"column",gap:4}}>
            {[
              { n:'V1 · EY clean', tweaks:{accent:'orange',type:'geist',density:'balanced',glass:'solid'} },
              { n:'V2 · Stripe-ish', tweaks:{accent:'indigo',type:'inter',density:'balanced',glass:'glass'} },
              { n:'V3 · Editorial', tweaks:{accent:'graphite',type:'geist',density:'spacious',glass:'solid'} },
            ].map(p=>(
              <button key={p.n} onClick={()=>{ Object.entries(p.tweaks).forEach(([k,v])=>set(k,v)); }} style={{
                textAlign:"left", padding:"6px 10px", borderRadius:6,
                border:"1px solid var(--border)", background:"var(--surface)",
                fontSize:11.5, cursor:"pointer", color:"var(--text)"
              }}>{p.n}</button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

Object.assign(window, { TweaksPanel });
