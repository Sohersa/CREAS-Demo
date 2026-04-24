// Tweaks panel — edit mode UI

const TweakPanel = ({ state, setState, visible, onClose }) => {
  if (!visible) return null;
  const update = (k,v) => {
    const next = { ...state, [k]: v };
    setState(next);
    window.parent.postMessage({ type:'__edit_mode_set_keys', edits:{ [k]:v } }, '*');
  };
  return (
    <div style={{position:"fixed",right:22,top:74,width:280,zIndex:80}} className="floating card" >
      <div style={{padding:"14px 16px",borderBottom:"1px solid var(--line)",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
        <div>
          <div className="eyebrow">Tweaks</div>
          <div style={{fontSize:13,fontWeight:600,marginTop:2}}>Panel de exploración</div>
        </div>
        <button className="btn icon xs ghost" onClick={onClose}><Icon name="x" size={12}/></button>
      </div>
      <div style={{padding:16,display:"flex",flexDirection:"column",gap:16}}>
        <div>
          <div className="eyebrow" style={{marginBottom:8}}>Tema</div>
          <div style={{display:"flex",gap:4}}>
            {[['light','☀ Claro'],['dark','☾ Oscuro']].map(([id,l])=>(
              <button key={id} className={"chip"+(state.theme===id?" active":"")} onClick={()=>update('theme',id)} style={{flex:1,justifyContent:"center"}}>{l}</button>
            ))}
          </div>
        </div>

        <div>
          <div className="eyebrow" style={{marginBottom:8}}>Preset</div>
          <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:4}}>
            {[
              ['v1','V1 Claro',{accent:'orange',type:'geist',density:'balanced',glass:'solid',theme:'light'}],
              ['v2','V2 Mono',{accent:'graphite',type:'geist',density:'spacious',glass:'solid',theme:'light'}],
              ['v3','V3 Oscuro',{accent:'indigo',type:'geist',density:'compact',glass:'glass',theme:'dark'}],
            ].map(([k,l,p])=>(
              <button key={k} className="btn xs" style={{justifyContent:"center"}} onClick={()=>{setState({...state,...p});Object.entries(p).forEach(([kk,vv])=>window.parent.postMessage({type:'__edit_mode_set_keys',edits:{[kk]:vv}},'*'))}}>{l}</button>
            ))}
          </div>
        </div>

        <div>
          <div className="eyebrow" style={{marginBottom:8}}>Acento</div>
          <div style={{display:"flex",gap:6}}>
            {[['orange','#FF5500'],['graphite','#0A0A0A'],['indigo','#4536FF'],['teal','#006B5F']].map(([id,c])=>(
              <button key={id} onClick={()=>update('accent',id)} style={{width:26,height:26,borderRadius:"50%",background:c,border:state.accent===id?"2px solid var(--ink)":"2px solid var(--line)",cursor:"pointer",padding:0,outlineOffset:2}}/>
            ))}
          </div>
        </div>

        <div>
          <div className="eyebrow" style={{marginBottom:8}}>Tipografía</div>
          <div style={{display:"flex",gap:4}}>
            {[['geist','Geist'],['inter','Inter'],['serif','Serif']].map(([id,l])=>(
              <button key={id} className={"chip"+(state.type===id?" active":"")} onClick={()=>update('type',id)} style={{flex:1,justifyContent:"center"}}>{l}</button>
            ))}
          </div>
        </div>

        <div>
          <div className="eyebrow" style={{marginBottom:8}}>Densidad</div>
          <div style={{display:"flex",gap:4}}>
            {[['compact','Compact'],['balanced','Bal.'],['spacious','Amplia']].map(([id,l])=>(
              <button key={id} className={"chip"+(state.density===id?" active":"")} onClick={()=>update('density',id)} style={{flex:1,justifyContent:"center"}}>{l}</button>
            ))}
          </div>
        </div>

        <div>
          <div className="eyebrow" style={{marginBottom:8}}>Overlays 3D</div>
          <div style={{display:"flex",gap:4}}>
            {[['solid','Sólido'],['glass','Glass']].map(([id,l])=>(
              <button key={id} className={"chip"+(state.glass===id?" active":"")} onClick={()=>update('glass',id)} style={{flex:1,justifyContent:"center"}}>{l}</button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

Object.assign(window,{TweakPanel});
