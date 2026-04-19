/* global React */
// Playground — Finance + Dashboard + Suppliers + Admin + Reports

const { useState: useStateFin } = React;

function PgScreenFinance({ lang, orders, onPay, setToast }) {
  const T = (es, en) => window.pgT(lang, es, en);
  const [tab, setTab] = useStateFin('cfdi');
  const invoiced = orders.filter(o => o.cfdi);
  const payable = invoiced.filter(o => !o.paid);

  return (
    <div className="pg-screen">
      <div style={{ display:'flex', gap:6, marginBottom:18, flexWrap:'wrap' }}>
        {[
          { k:'cfdi', ic:'📄', t:T('CFDI 4.0','CFDI 4.0'), c:invoiced.length },
          { k:'pay', ic:'💳', t:T('Por pagar','Payable'), c:payable.length },
          { k:'credit', ic:'🏦', t:T('Crédito OBRA YA','OBRA YA Credit') },
          { k:'recon', ic:'🧾', t:T('Conciliación','Reconciliation') }
        ].map(x => (
          <button key={x.k} className={`pg-btn ${tab===x.k?'primary':''}`} onClick={()=>setTab(x.k)}>
            {x.ic} {x.t}{x.c!=null && ' · '+x.c}
          </button>
        ))}
      </div>

      {tab==='cfdi' && (
        <div className="pg-grid-2" style={{gridTemplateColumns:'1.4fr 1fr', alignItems:'start'}}>
          <div className="pg-card pad-0">
            <table className="pg-table">
              <thead><tr><th>UUID</th><th>{T('Proveedor','Supplier')}</th><th className="num">Total</th><th>{T('Estado','Status')}</th></tr></thead>
              <tbody>
                {invoiced.map(o => {
                  const sup = window.PG_SUPPLIERS.find(s=>s.id===o.winner);
                  return <tr key={o.id}>
                    <td style={{fontFamily:'var(--font-mono)', fontSize:10, color:'var(--violet-ink)'}}>{o.cfdi}</td>
                    <td>{sup?.name}</td>
                    <td className="num bold">${o.total.toLocaleString()}</td>
                    <td><span className={`pg-chip ${o.paid?'pagada':'facturada'}`}>{o.paid?T('Pagada','Paid'):T('Timbrada','Stamped')}</span></td>
                  </tr>;
                })}
              </tbody>
            </table>
          </div>
          <div className="pg-cfdi">
            <div style={{display:'flex', justifyContent:'space-between'}}>
              <div>
                <div style={{fontSize:10, fontFamily:'var(--font-mono)', color:'var(--ink-muted)', letterSpacing:'0.1em'}}>CFDI 4.0 · INGRESO</div>
                <div style={{fontSize:18, fontWeight:700, marginTop:4, letterSpacing:'-0.02em'}}>Factura A-3821</div>
              </div>
              <div className="pg-cfdi-stamp">{T('TIMBRADO SAT','SAT STAMPED')}</div>
            </div>
            <div style={{marginTop:14, fontSize:11, color:'var(--ink-dim)'}}>
              <div><b>Emisor:</b> Cemex S.A.B. de C.V.</div>
              <div><b>RFC:</b> CEM•880331•AB7</div>
              <div><b>Receptor:</b> Grupo Sohersa</div>
            </div>
            <div style={{height:1, background:'var(--line)', margin:'14px 0'}}/>
            <div className="pg-kv">
              <div className="pg-kv-r"><span className="k">50 × Cemento CPC 30R</span><span className="v mono">$12,300.00</span></div>
              <div className="pg-kv-r"><span className="k">IVA 16%</span><span className="v mono">$1,968.00</span></div>
              <div className="pg-kv-r" style={{paddingTop:10, borderTop:'1px solid var(--line)', fontWeight:700}}><span>TOTAL MXN</span><span className="mono">$14,268.00</span></div>
            </div>
            <div className="pg-cfdi-uuid">UUID: 4B9F2A82-1F7E-4C33-9D16-8A2B1C5E7F91</div>
            <div style={{display:'flex', gap:6, marginTop:14}}>
              <button className="pg-btn" style={{flex:1, justifyContent:'center'}}>⬇ XML</button>
              <button className="pg-btn" style={{flex:1, justifyContent:'center'}}>⬇ PDF</button>
            </div>
          </div>
        </div>
      )}

      {tab==='pay' && (
        <div>
          <div className="pg-grid-4" style={{marginBottom:16}}>
            <div className="pg-stat"><div className="pg-stat-k">{T('A 15 días','Due 15d')}</div><div className="pg-stat-v">$54,800</div></div>
            <div className="pg-stat"><div className="pg-stat-k">{T('A 30 días','Due 30d')}</div><div className="pg-stat-v">$98,700</div></div>
            <div className="pg-stat"><div className="pg-stat-k">{T('A 60 días','Due 60d')}</div><div className="pg-stat-v">$172,400</div></div>
            <div className="pg-stat" style={{background:'linear-gradient(135deg, var(--violet-soft), white)'}}><div className="pg-stat-k">{T('Total por pagar','Total payable')}</div><div className="pg-stat-v" style={{color:'var(--violet-ink)'}}>$325,900</div></div>
          </div>
          <div className="pg-card pad-0">
            <div className="pg-card-hdr">
              <div><div className="pg-card-t">{T('Cuentas por pagar','Accounts payable')}</div></div>
              <button className="pg-btn primary">💸 {T('Pagar vía SPEI en lote','Batch pay via SPEI')}</button>
            </div>
            <table className="pg-table">
              <thead><tr><th>{T('Proveedor','Supplier')}</th><th>CFDI</th><th className="num">{T('Monto','Amount')}</th><th></th></tr></thead>
              <tbody>
                {payable.map(o => {
                  const sup = window.PG_SUPPLIERS.find(s=>s.id===o.winner);
                  return <tr key={o.id}>
                    <td>{sup?.name}</td>
                    <td style={{fontFamily:'var(--font-mono)', fontSize:10}}>{o.cfdi}</td>
                    <td className="num bold">${o.total.toLocaleString()}</td>
                    <td><button className="pg-btn primary" onClick={()=>{onPay(o.id); setToast({msg:T('SPEI programado · Clave •••4821','SPEI scheduled · Key •••4821'), type:'ok'});}}>{T('Pagar ahora','Pay now')}</button></td>
                  </tr>;
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab==='credit' && (
        <div className="pg-card" style={{background:'linear-gradient(135deg, #0A2540, #1A365D)', color:'white', padding:28, border:'none', maxWidth:520}}>
          <div style={{fontSize:11, opacity:0.7, letterSpacing:'0.08em', fontFamily:'var(--font-mono)'}}>LÍNEA DE CRÉDITO · OBRA YA</div>
          <div style={{fontSize:40, fontWeight:700, letterSpacing:'-0.035em', marginTop:10}}>$2,000,000</div>
          <div style={{fontSize:12, opacity:0.8, marginTop:4}}>MXN · {T('tasa 14.5% anual','14.5% APR')}</div>
          <div style={{marginTop:24, height:10, borderRadius:100, background:'rgba(255,255,255,0.1)', overflow:'hidden'}}>
            <div style={{width:'42%', height:'100%', background:'linear-gradient(90deg, var(--orange), var(--pink))'}}/>
          </div>
          <div style={{display:'flex', justifyContent:'space-between', marginTop:8, fontSize:12}}>
            <span>{T('Usado','Used')} · $847,200</span>
            <span style={{opacity:0.7}}>{T('Disponible','Available')} · $1,152,800</span>
          </div>
        </div>
      )}

      {tab==='recon' && (
        <div className="pg-card pad-0">
          <table className="pg-table">
            <thead><tr><th>PO</th><th>CFDI</th><th>{T('Match','Match')}</th></tr></thead>
            <tbody>
              {orders.filter(o=>o.cfdi).map(o=>(
                <tr key={o.id}>
                  <td style={{fontFamily:'var(--font-mono)'}}>{o.po}</td>
                  <td style={{fontFamily:'var(--font-mono)'}}>{o.cfdi}</td>
                  <td><span className="pg-chip entregada">✓ 3/3</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function PgScreenDashboard({ lang, orders }) {
  const T = (es, en) => window.pgT(lang, es, en);
  const activeCount = orders.filter(o=>['cotizando','aprobada','transito'].includes(o.status)).length;

  return (
    <div className="pg-screen">
      <div className="pg-grid-4" style={{marginBottom:18}}>
        <div className="pg-stat"><div className="pg-stat-k">{T('Gasto YTD','Spend YTD')}</div><div className="pg-stat-v">$41.7M</div><div className="pg-stat-delta up">↑ 12.4% vs Q3</div></div>
        <div className="pg-stat"><div className="pg-stat-k">{T('Pedidos activos','Active orders')}</div><div className="pg-stat-v">{activeCount}</div><div className="pg-stat-delta up">↑ 3 {T('hoy','today')}</div></div>
        <div className="pg-stat"><div className="pg-stat-k">{T('Ahorro vs lista','Savings vs list')}</div><div className="pg-stat-v" style={{color:'#00A95F'}}>$3.5M</div><div className="pg-stat-delta up">↑ 8.4%</div></div>
        <div className="pg-stat"><div className="pg-stat-k">{T('Avg cotización','Avg quote')}</div><div className="pg-stat-v">4.2 min</div><div className="pg-stat-delta down">↓ 18s</div></div>
      </div>

      <div className="pg-grid-2" style={{gridTemplateColumns:'1.3fr 1fr', marginBottom:18}}>
        <div className="pg-card">
          <div className="pg-sect-t">{T('Gasto por obra — últimos 6 meses','Spend per site — last 6 months')}</div>
          <svg viewBox="0 0 600 200" style={{width:'100%', height:200}}>
            <defs><linearGradient id="dgrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#635BFF" stopOpacity="0.3"/><stop offset="100%" stopColor="#635BFF" stopOpacity="0"/></linearGradient></defs>
            {[0,50,100,150,200].map(y=><line key={y} x1="40" y1={y} x2="600" y2={y} stroke="var(--line)" strokeDasharray="2 3"/>)}
            {['Jun','Jul','Ago','Sep','Oct','Nov'].map((m,i)=><text key={m} x={70+i*95} y="195" fontSize="10" fill="var(--ink-muted)" textAnchor="middle">{m}</text>)}
            <path d="M 70 120 L 165 100 L 260 85 L 355 65 L 450 50 L 545 35 L 545 200 L 70 200 Z" fill="url(#dgrad)"/>
            <path d="M 70 120 L 165 100 L 260 85 L 355 65 L 450 50 L 545 35" stroke="#635BFF" strokeWidth="2.5" fill="none"/>
            {[120,100,85,65,50,35].map((y,i)=><circle key={i} cx={70+i*95} cy={y} r="3" fill="#635BFF"/>)}
          </svg>
        </div>
        <div className="pg-card">
          <div className="pg-sect-t">🚨 {T('Alertas','Alerts')} <span className="chip-sm" style={{background:'#FFE8E0', color:'#E85D2B'}}>{window.PG_ALERTS.length}</span></div>
          <div style={{display:'flex', flexDirection:'column', gap:10}}>
            {window.PG_ALERTS.map(a => (
              <div key={a.id} style={{padding:'10px 12px', borderRadius:8, background: a.lvl==='warn'?'#FFF4EC':a.lvl==='ok'?'#F1FAF4':'var(--paper-2)', borderLeft:'3px solid '+(a.lvl==='warn'?'var(--orange)':a.lvl==='ok'?'#00A95F':'var(--violet)')}}>
                <div style={{fontSize:12, fontWeight:600}}>{a.t}</div>
                <div style={{fontSize:11, color:'var(--ink-dim)', marginTop:2}}>{a.d}</div>
                <div style={{fontSize:10, color:'var(--ink-muted)', fontFamily:'var(--font-mono)', marginTop:4}}>{a.ago}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="pg-sect-t">{T('Obras activas','Active sites')} · {window.PG_SITES.length}</div>
      <div className="pg-grid-3">
        {window.PG_SITES.map(s => {
          const pct = Math.round(s.spent/s.budget*100);
          return (
            <div key={s.id} className="pg-card">
              <div style={{display:'flex', justifyContent:'space-between'}}>
                <div>
                  <div style={{fontSize:10, fontFamily:'var(--font-mono)', color:'var(--ink-muted)'}}>{s.code}</div>
                  <div style={{fontSize:14, fontWeight:600, marginTop:2}}>{s.name.split('·')[0]}</div>
                  <div style={{fontSize:11, color:'var(--ink-dim)', marginTop:2}}>{s.residente} · {s.phase}</div>
                </div>
                <span className="pg-chip entregada">{T('activa','active')}</span>
              </div>
              <div style={{marginTop:14}}>
                <div style={{display:'flex', justifyContent:'space-between', fontSize:11, marginBottom:4}}>
                  <span style={{color:'var(--ink-dim)'}}>{T('Presupuesto','Budget')}</span>
                  <span style={{fontFamily:'var(--font-mono)', fontWeight:600}}>${(s.spent/1e6).toFixed(1)}M / ${(s.budget/1e6).toFixed(1)}M</span>
                </div>
                <div className="pg-prog"><div className="pg-prog-bar" style={{width:pct+'%', background: pct>85?'linear-gradient(90deg, var(--orange), #E85D2B)':'linear-gradient(90deg, var(--violet), var(--pink))'}}/></div>
                <div style={{fontSize:10, color:'var(--ink-muted)', marginTop:4, fontFamily:'var(--font-mono)'}}>{pct}% {T('gastado','spent')}</div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function PgScreenSuppliers({ lang, setToast }) {
  const T = (es, en) => window.pgT(lang, es, en);
  const [query, setQuery] = useStateFin('');
  const filtered = window.PG_SUPPLIERS.filter(s => !query || s.name.toLowerCase().includes(query.toLowerCase()));

  return (
    <div className="pg-screen">
      <div className="pg-onboard">
        <div className="pg-onboard-ic">🏭</div>
        <div>
          <div className="pg-onboard-t">{T('1,247 proveedores activos en 32 ciudades','1,247 active suppliers in 32 cities')}</div>
          <div className="pg-onboard-d">{T('Vetting KYC, rating, exclusividades.','KYC vetting, rating, exclusivities.')}</div>
        </div>
        <button className="pg-btn primary" style={{marginLeft:'auto'}}>+ {T('Invitar','Invite')}</button>
      </div>
      <input value={query} onChange={e=>setQuery(e.target.value)} placeholder={T('Buscar...','Search...')} style={{width:'100%', padding:'9px 12px', border:'1px solid var(--line-2)', borderRadius:8, fontSize:13, fontFamily:'inherit', marginBottom:16}}/>
      <div className="pg-grid-4">
        {filtered.map(s => (
          <div key={s.id} className="pg-sup">
            <div className="pg-sup-top">
              <div className="pg-sup-logo" style={{background:s.color}}>{s.name[0]}</div>
              <div style={{flex:1, minWidth:0}}>
                <div className="pg-sup-name">{s.name}</div>
                <div className="pg-sup-rfc">{s.rfc}</div>
              </div>
              {s.exclusive && <span style={{fontSize:9, padding:'2px 6px', background:'linear-gradient(135deg, var(--orange), var(--violet))', color:'white', borderRadius:4, fontWeight:700, fontFamily:'var(--font-mono)'}}>EXCL</span>}
            </div>
            <div className="pg-sup-stats">
              <div><div className="pg-sup-stat-k">Rating</div><div className="pg-sup-stat-v">⭐ {s.rating}</div></div>
              <div><div className="pg-sup-stat-k">On-time</div><div className="pg-sup-stat-v">{s.otd}%</div></div>
              <div><div className="pg-sup-stat-k">Lead</div><div className="pg-sup-stat-v">{s.leadH}h</div></div>
              <div><div className="pg-sup-stat-k">{T('Ciudad','City')}</div><div className="pg-sup-stat-v" style={{fontSize:12}}>{s.city}</div></div>
            </div>
            <div className="pg-sup-tags">{s.cats.slice(0,3).map(c=><span key={c}>{c}</span>)}</div>
            <button className="pg-btn primary" style={{width:'100%', justifyContent:'center', marginTop:10, fontSize:11}} onClick={()=>setToast({msg:T('Invitado a cotizar · ','Invited · ')+s.name, type:'ok'})}>{T('Invitar a cotizar','Invite to quote')}</button>
          </div>
        ))}
      </div>
    </div>
  );
}

function PgScreenAdmin({ lang }) {
  const T = (es, en) => window.pgT(lang, es, en);
  const [tab, setTab] = useStateFin('policy');

  return (
    <div className="pg-screen">
      <div style={{display:'flex', gap:6, marginBottom:18, flexWrap:'wrap'}}>
        {[
          {k:'policy', ic:'🤖', t:T('Políticas','Policies')},
          {k:'users', ic:'👥', t:T('Usuarios','Users')},
          {k:'erp', ic:'🔌', t:T('Integraciones','Integrations')},
          {k:'compl', ic:'🔒', t:T('Compliance','Compliance')}
        ].map(x=><button key={x.k} className={`pg-btn ${tab===x.k?'primary':''}`} onClick={()=>setTab(x.k)}>{x.ic} {x.t}</button>)}
      </div>

      {tab==='policy' && (
        <div className="pg-grid-2">
          <div className="pg-card">
            <div className="pg-sect-t">{T('Auto-aprobación por monto','Auto-approval by amount')}</div>
            <div style={{fontSize:12, color:'var(--ink-dim)', marginBottom:14}}>{T('Bajo el umbral, Nico aprueba sin supervisor.','Below threshold, Nico auto-approves.')}</div>
            <input type="range" min="0" max="200000" defaultValue="50000" style={{width:'100%', margin:'10px 0'}}/>
            <div style={{display:'flex', justifyContent:'space-between', fontSize:11, color:'var(--ink-dim)'}}><span>$0</span><b style={{fontSize:18, color:'var(--violet-ink)', fontFamily:'var(--font-mono)'}}>$50,000</b><span>$200k</span></div>
          </div>
          <div className="pg-card">
            <div className="pg-sect-t">{T('Workflow de aprobación','Approval workflow')}</div>
            <div className="pg-timeline">
              <div className="pg-tl-step done"><div className="pg-tl-dot">R</div><div><div className="pg-tl-t">{T('Residente','Foreman')}</div></div></div>
              <div className="pg-tl-step done"><div className="pg-tl-dot">🤖</div><div><div className="pg-tl-t">Nico</div></div></div>
              <div className="pg-tl-step current"><div className="pg-tl-dot">S</div><div><div className="pg-tl-t">{T('Super · Carlos M.','Super · Carlos M.')}</div></div></div>
              <div className="pg-tl-step"><div className="pg-tl-dot">C</div><div><div className="pg-tl-t">{T('Contralor','Controller')}</div></div></div>
            </div>
          </div>
        </div>
      )}

      {tab==='users' && (
        <div className="pg-card pad-0">
          <table className="pg-table">
            <thead><tr><th>{T('Usuario','User')}</th><th>{T('Rol','Role')}</th><th>{T('Límite','Limit')}</th></tr></thead>
            <tbody>
              {[
                {n:'Roberto Sánchez', r:'Director', l:'$∞'},
                {n:'Silvia Ramírez', r:'Contralor', l:'$∞'},
                {n:'Carlos Mendoza', r:'Super', l:'$150k'},
                {n:'Luis Ramírez', r:'Residente', l:'$20k'},
                {n:'Carmen Vega', r:'Residente', l:'$20k'}
              ].map((u,i)=>(
                <tr key={i}>
                  <td><b>{u.n}</b></td>
                  <td>{u.r}</td>
                  <td className="num mono bold">{u.l}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab==='erp' && (
        <div className="pg-grid-3">
          {[{n:'SAP S/4HANA', c:'#0FAAFF', on:true},{n:'Contpaqi', c:'#0084D8', on:true},{n:'Aspel SAE', c:'#E8344D', on:false},{n:'Odoo', c:'#8E44AD', on:false},{n:'Dynamics', c:'#0078D4', on:false},{n:'QuickBooks', c:'#2CA01C', on:true}].map((e,i)=>(
            <div key={i} className="pg-card">
              <div style={{display:'flex', alignItems:'center', gap:10, marginBottom:10}}>
                <div style={{width:40, height:40, borderRadius:8, background:e.c, color:'white', display:'flex', alignItems:'center', justifyContent:'center', fontWeight:700}}>{e.n[0]}</div>
                <div style={{fontWeight:600, fontSize:13}}>{e.n}</div>
              </div>
              <button className={`pg-btn ${e.on?'success':''}`} style={{width:'100%', justifyContent:'center'}}>{e.on?'✓ '+T('Conectado','Connected'):T('Conectar','Connect')}</button>
            </div>
          ))}
        </div>
      )}

      {tab==='compl' && (
        <div className="pg-card">
          <div className="pg-sect-t">🔒 {T('Vetting automático','Auto vetting')}</div>
          <div className="pg-timeline">
            {[T('RFC validado con SAT','SAT RFC validated'), T('Lista negra 69-B limpia','69-B blacklist clean'), T('Buró de crédito OK','Credit bureau OK'), T('KYC completo','KYC complete')].map((t,i)=>(
              <div key={i} className="pg-tl-step done"><div className="pg-tl-dot">✓</div><div><div className="pg-tl-t">{t}</div></div></div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function PgScreenReports({ lang }) {
  const T = (es, en) => window.pgT(lang, es, en);
  return (
    <div className="pg-screen">
      <div className="pg-grid-3">
        {[
          {ic:'💰', t:T('Ahorro por obra','Savings by site'), v:'$3.5M'},
          {ic:'📊', t:T('Top proveedores','Top suppliers'), v:'8 activos'},
          {ic:'📈', t:T('Partidas más caras','Costliest items'), v:'Acero +12%'},
          {ic:'🚚', t:T('On-time delivery','On-time delivery'), v:'92%'},
          {ic:'💳', t:T('Días promedio pago','DPO'), v:'28 días'},
          {ic:'🏗️', t:T('Consumo vs presupuesto','Consumption vs budget'), v:'-3.2%'}
        ].map((r,i)=>(
          <div key={i} className="pg-card">
            <div style={{fontSize:22, marginBottom:8}}>{r.ic}</div>
            <div style={{fontWeight:600, fontSize:14}}>{r.t}</div>
            <div style={{fontSize:20, fontWeight:700, letterSpacing:'-0.02em', marginTop:10, color:'var(--violet-ink)'}}>{r.v}</div>
            <div style={{display:'flex', gap:6, marginTop:12}}>
              <button className="pg-btn" style={{flex:1, justifyContent:'center', fontSize:11}}>{T('Ver','View')}</button>
              <button className="pg-btn" style={{flex:1, justifyContent:'center', fontSize:11}}>⬇ Excel</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

window.PgScreenFinance = PgScreenFinance;
window.PgScreenDashboard = PgScreenDashboard;
window.PgScreenSuppliers = PgScreenSuppliers;
window.PgScreenAdmin = PgScreenAdmin;
window.PgScreenReports = PgScreenReports;
