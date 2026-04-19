/* global React */
// Playground — Quote (live) + Orders (list/detail) + Tracking

const { useState: useStateQO, useEffect: useEffectQO } = React;

/* ════ QUOTE (live, per-order) ═════ */
function PgScreenQuote({ lang, orders, onApprove, setToast }) {
  const T = (es, en) => window.pgT(lang, es, en);
  const quotingOrders = orders.filter(o => o.status === 'cotizando');
  const [activeId, setActiveId] = useStateQO(quotingOrders[0]?.id || orders[0]?.id);
  const active = orders.find(o => o.id === activeId) || orders[0];

  const [progress, setProgress] = useStateQO(0);
  const [offers, setOffers] = useStateQO([]);
  const [picked, setPicked] = useStateQO(null);

  useEffectQO(() => {
    setProgress(0); setOffers([]); setPicked(null);
    if (!active) return;
    const q = window.pgGenerateQuotes(active.item, active.qty || 1);
    let i = 0;
    const t = setInterval(() => {
      i++;
      setProgress(Math.min(100, i * 17));
      setOffers(q.slice(0, Math.min(q.length, i)));
      if (i >= q.length) clearInterval(t);
    }, 480);
    return () => clearInterval(t);
  }, [activeId]);

  if (!active) return <div style={{ padding:40, textAlign:'center', color:'var(--ink-dim)' }}>{T('No hay cotizaciones activas. Crea un pedido en Captura.','No active quotes. Create a request in Capture.')}</div>;

  return (
    <div className="pg-screen">
      <div className="pg-onboard">
        <div className="pg-onboard-ic">⚡</div>
        <div>
          <div className="pg-onboard-t">{T('Cotización en paralelo con la red','Parallel quoting across the network')}</div>
          <div className="pg-onboard-d">{T('6 proveedores reciben el pedido al mismo tiempo. Llegan respuestas en tiempo real.','6 suppliers receive the request simultaneously. Responses arrive live.')}</div>
        </div>
        <div style={{ marginLeft:'auto', display:'flex', gap:6 }}>
          {orders.slice(0,4).map(o => (
            <button key={o.id} className={`pg-btn ${activeId === o.id ? 'primary' : ''}`} onClick={() => setActiveId(o.id)}>{o.id}</button>
          ))}
        </div>
      </div>

      {/* Header for this quote */}
      <div className="pg-card" style={{ marginBottom:14 }}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'flex-start', gap:16 }}>
          <div>
            <div style={{ fontSize:11, color:'var(--ink-muted)', fontFamily:'var(--font-mono)', letterSpacing:'0.06em' }}>{active.id} · {active.site.toUpperCase()}</div>
            <div style={{ fontSize:18, fontWeight:600, marginTop:4, letterSpacing:'-0.02em' }}>{active.item}</div>
            <div style={{ fontSize:13, color:'var(--ink-dim)', marginTop:2 }}>{active.qty} {active.unit} · {T('entrega','deliver')} {active.eta || T('por definir','TBD')}</div>
          </div>
          <div style={{ flex:1, maxWidth:300 }}>
            <div style={{ fontSize:10, color:'var(--ink-muted)', marginBottom:4, letterSpacing:'0.06em', textTransform:'uppercase', fontWeight:600 }}>{T('Cotizando...','Quoting...')}</div>
            <div className="pg-prog"><div className="pg-prog-bar" style={{ width: progress + '%' }}/></div>
            <div style={{ fontSize:11, color:'var(--ink-dim)', marginTop:6, fontFamily:'var(--font-mono)' }}>{offers.length}/6 {T('proveedores respondieron','suppliers responded')}</div>
          </div>
        </div>
      </div>

      {/* Live supplier status grid */}
      <div className="pg-sect-t">{T('Estado por proveedor','Per-supplier status')}</div>
      <div className="pg-grid-3" style={{ marginBottom:20 }}>
        {window.PG_SUPPLIERS.slice(0, 6).map((s, i) => {
          const responded = offers.find(o => o.supplier.id === s.id);
          return (
            <div key={s.id} className="pg-card" style={{ padding:12, borderColor: responded ? 'var(--violet)' : 'var(--line)', transition:'all 200ms' }}>
              <div style={{ display:'flex', gap:10, alignItems:'center' }}>
                <div className="pg-sup-logo" style={{ background:s.color, width:28, height:28, fontSize:11 }}>{s.name[0]}</div>
                <div style={{ flex:1, minWidth:0 }}>
                  <div style={{ fontSize:12, fontWeight:600, whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis' }}>{s.name}</div>
                  <div style={{ fontSize:10, color:'var(--ink-muted)', fontFamily:'var(--font-mono)' }}>{s.city} · ⭐ {s.rating}</div>
                </div>
                {responded ? (
                  <span className="pg-chip entregada" style={{ fontSize:9 }}>✓ {T('lista','ready')}</span>
                ) : (
                  <span className="pg-chip cotizando" style={{ fontSize:9 }}>• • •</span>
                )}
              </div>
              {responded && (
                <div style={{ marginTop:8, display:'flex', justifyContent:'space-between', fontSize:11 }}>
                  <span style={{ color:'var(--ink-dim)' }}>{responded.eta}h · {responded.distance}km</span>
                  <span className="mono" style={{ fontWeight:600 }}>${responded.total.toLocaleString()}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Comparison */}
      {offers.length > 0 && (
        <>
          <div className="pg-sect-t">{T('Comparativa','Comparison')} <span className="chip-sm">{T('ordenado por precio + ETA','sorted by price + ETA')}</span></div>
          <div className="pg-offers">
            {offers.map((o, i) => (
              <div key={o.supplier.id} className={`pg-offer ${i === 0 ? 'best' : ''} ${picked === o.supplier.id ? 'on' : ''}`} onClick={() => setPicked(o.supplier.id)}>
                {i === 0 && <div className="pg-offer-tag">★ {T('MEJOR','BEST')}</div>}
                <div className="pg-offer-top">
                  <div>
                    <div className="pg-offer-name">{o.supplier.name}</div>
                    <div className="pg-offer-rfc">{o.supplier.rfc}</div>
                  </div>
                  <div className="pg-offer-star">⭐ {o.rating}</div>
                </div>
                <div className="pg-offer-price">${o.total.toLocaleString()}</div>
                <div className={`pg-offer-delta ${i===0?'down':'up'}`}>{i === 0 ? '↓ '+T('mejor','lowest') : '+$'+(o.total-offers[0].total).toLocaleString()+' vs '+T('mejor','best')}</div>
                <div className="pg-offer-meta">
                  <div className="pg-offer-meta-r"><span>{T('Unitario','Unit')}</span><b className="mono">${o.unitPrice}/{active.unit}</b></div>
                  <div className="pg-offer-meta-r"><span>ETA</span><b>{o.eta}h</b></div>
                  <div className="pg-offer-meta-r"><span>{T('Distancia','Distance')}</span><b>{o.distance}km</b></div>
                  <div className="pg-offer-meta-r"><span>{T('On-time','On-time')}</span><b>{o.otd}%</b></div>
                </div>
                {picked === o.supplier.id && (
                  <button className="pg-btn primary" style={{ width:'100%', justifyContent:'center' }} onClick={(e) => { e.stopPropagation(); onApprove(active.id, o); setToast({ msg: T('Aprobado · PO generada · Notificando a '+o.supplier.name,'Approved · PO generated · Notifying '+o.supplier.name), type:'ok' }); }}>{T('Aprobar y emitir PO','Approve & issue PO')}</button>
                )}
              </div>
            ))}
          </div>

          {progress >= 100 && !picked && (
            <div style={{ marginTop:16, padding:14, background:'var(--violet-soft)', borderRadius:8, fontSize:12, color:'var(--violet-ink)', display:'flex', justifyContent:'space-between', alignItems:'center' }}>
              <span>💡 <b>{T('Política de auto-aprobación:','Auto-approval policy:')}</b> {T('esta orden entra bajo el umbral de $50k — Nico puede aprobar y emitir la PO automáticamente.','this order falls under the $50k threshold — Nico can auto-approve and issue the PO.')}</span>
              <button className="pg-btn primary" onClick={() => { onApprove(active.id, offers[0]); setToast({ msg: T('Auto-aprobado por política · PO '+active.id+' emitida','Auto-approved by policy · PO '+active.id+' issued'), type:'ok' }); }}>{T('Aplicar auto-aprobación','Apply auto-approval')}</button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ════ ORDERS table ═════ */
function PgScreenOrders({ lang, orders, onSelect, onNew }) {
  const T = (es, en) => window.pgT(lang, es, en);
  const [filter, setFilter] = useStateQO('all');
  const filtered = filter === 'all' ? orders : orders.filter(o => o.status === filter);
  const counts = orders.reduce((a, o) => { a[o.status] = (a[o.status]||0)+1; return a; }, {});

  const STATUS_LABEL = {
    cotizando: T('Cotizando','Quoting'), lista: T('Lista','Ready'),
    aprobada: T('Aprobada','Approved'), transito: T('En tránsito','In transit'),
    entregada: T('Entregada','Delivered'), facturada: T('Facturada','Invoiced'),
    pagada: T('Pagada','Paid')
  };

  return (
    <div className="pg-screen">
      <div style={{ display:'flex', gap:6, marginBottom:18, flexWrap:'wrap' }}>
        <button className={`pg-btn ${filter==='all'?'primary':''}`} onClick={() => setFilter('all')}>{T('Todas','All')} · {orders.length}</button>
        {['cotizando','aprobada','transito','entregada','facturada','pagada'].map(s => counts[s] ? (
          <button key={s} className={`pg-btn ${filter===s?'primary':''}`} onClick={() => setFilter(s)}>
            <span className={`pg-chip ${s}`} style={{ padding:'1px 5px', fontSize:9 }}>•</span>
            {STATUS_LABEL[s]} · {counts[s]}
          </button>
        ) : null)}
      </div>

      <div className="pg-card pad-0">
        <table className="pg-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>{T('Pedido','Item')}</th>
              <th>{T('Obra','Site')}</th>
              <th>{T('Proveedor','Supplier')}</th>
              <th className="num">{T('Total','Total')}</th>
              <th>{T('Estado','Status')}</th>
              <th>{T('Creada','Created')}</th>
              <th>ETA</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(o => {
              const sup = window.PG_SUPPLIERS.find(s => s.id === o.winner);
              const site = window.PG_SITES.find(s => s.id === o.site);
              return (
                <tr key={o.id} onClick={() => onSelect(o.id)} className={o.status === 'cotizando' ? 'hot' : ''}>
                  <td style={{ fontFamily:'var(--font-mono)', fontWeight:600, color:'var(--violet-ink)' }}>{o.id}</td>
                  <td style={{ fontWeight:500 }}>{o.item}<div style={{ fontSize:10, color:'var(--ink-muted)' }}>{o.qty} {o.unit}</div></td>
                  <td style={{ fontSize:11, color:'var(--ink-dim)' }}>{site?.code}<div style={{ fontSize:10, color:'var(--ink-muted)' }}>{site?.name.split('·')[0]}</div></td>
                  <td>{sup ? <span style={{ display:'inline-flex', alignItems:'center', gap:6 }}><span style={{ width:16, height:16, borderRadius:4, background:sup.color, color:'white', display:'inline-flex', alignItems:'center', justifyContent:'center', fontSize:8, fontWeight:700 }}>{sup.name[0]}</span>{sup.name}</span> : <span style={{ color:'var(--ink-ghost)' }}>—</span>}</td>
                  <td className="num bold">{o.total ? '$'+o.total.toLocaleString() : '—'}</td>
                  <td><span className={`pg-chip ${o.status}`}>{STATUS_LABEL[o.status]}</span></td>
                  <td style={{ fontSize:11, color:'var(--ink-dim)' }}>{o.createdAt}</td>
                  <td style={{ fontSize:11, color:'var(--ink-dim)' }}>{o.eta}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

/* ════ TRACKING (map + timeline + photo confirm) ═════ */
function PgScreenTracking({ lang, orders, onReceive, setToast }) {
  const T = (es, en) => window.pgT(lang, es, en);
  const trackable = orders.filter(o => ['transito','aprobada','entregada'].includes(o.status));
  const [activeId, setActiveId] = useStateQO(trackable.find(o => o.status === 'transito')?.id || trackable[0]?.id);
  const active = trackable.find(o => o.id === activeId);
  const [truckPos, setTruckPos] = useStateQO(0.4);
  const [delivered, setDelivered] = useStateQO(false);
  const [photoTaken, setPhotoTaken] = useStateQO(false);
  const [signed, setSigned] = useStateQO(false);

  useEffectQO(() => {
    if (!active || active.status !== 'transito') return;
    const t = setInterval(() => {
      setTruckPos(p => {
        const n = Math.min(0.95, p + 0.015);
        return n;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [active]);

  useEffectQO(() => {
    setDelivered(false); setPhotoTaken(false); setSigned(false);
    setTruckPos(active?.progress ? active.progress / 100 * 0.9 : 0.4);
  }, [activeId]);

  if (!active) return <div style={{ padding:40, textAlign:'center', color:'var(--ink-dim)' }}>{T('No hay entregas en curso.','No deliveries in progress.')}</div>;

  const sup = window.PG_SUPPLIERS.find(s => s.id === active.winner);
  const site = window.PG_SITES.find(s => s.id === active.site);

  // bezier route from origin to destination
  const originX = 15, originY = 72;
  const destX = 82, destY = 28;
  const curX = originX + (destX - originX) * truckPos;
  const curY = originY + (destY - originY) * truckPos - Math.sin(truckPos * Math.PI) * 18;

  return (
    <div className="pg-screen">
      <div style={{ display:'flex', gap:6, marginBottom:18, flexWrap:'wrap' }}>
        {trackable.map(o => (
          <button key={o.id} className={`pg-btn ${activeId === o.id ? 'primary' : ''}`} onClick={() => setActiveId(o.id)}>
            {o.id} · {o.item.slice(0,18)}
          </button>
        ))}
      </div>

      <div className="pg-grid-2" style={{ gridTemplateColumns:'1.4fr 1fr', alignItems:'start' }}>
        {/* Map */}
        <div>
          <div className="pg-map">
            <div className="pg-map-grid"/>
            {/* Fake roads */}
            <div className="pg-map-road" style={{ top:'68%', left:'10%', width:'75%', transform:'rotate(-20deg)' }}/>
            <div className="pg-map-road" style={{ top:'35%', left:'20%', width:'60%', transform:'rotate(5deg)' }}/>
            <div className="pg-map-road" style={{ top:'52%', left:'40%', width:'40%', height:'80px', background:'transparent', borderTop:'3px dashed rgba(255,255,255,0.6)' }}/>

            <svg className="pg-map-route" viewBox="0 0 100 100" preserveAspectRatio="none">
              <path d={`M ${originX} ${originY} Q 50 15, ${destX} ${destY}`} stroke="var(--violet)" strokeWidth="0.6" fill="none" strokeDasharray="1 1" opacity="0.6"/>
              <path d={`M ${originX} ${originY} Q 50 15, ${curX} ${curY}`} stroke="var(--violet)" strokeWidth="0.9" fill="none"/>
            </svg>

            <div className="pg-map-pin origin" style={{ left:originX+'%', top:originY+'%' }}>
              <div className="pg-map-pin-dot"/>
              <div className="pg-map-pin-label">🏭 {sup?.name}</div>
            </div>
            <div className="pg-map-pin dest" style={{ left:destX+'%', top:destY+'%' }}>
              <div className="pg-map-pin-dot"/>
              <div className="pg-map-pin-label">📍 {site?.code}</div>
            </div>

            <div className="pg-truck" style={{ left:curX+'%', top:curY+'%' }}>🚚</div>

            <div className="pg-eta-badge">
              <div className="k">ETA</div>
              <div className="v">{active.status === 'entregada' || delivered ? T('entregada','delivered') : Math.max(5, Math.round((1-truckPos) * 45)) + ' min'}</div>
            </div>
          </div>

          {/* Driver card */}
          <div className="pg-card" style={{ marginTop:14, padding:14 }}>
            <div style={{ display:'flex', gap:12, alignItems:'center' }}>
              <div style={{ width:44, height:44, borderRadius:'50%', background:'linear-gradient(135deg, #FFB84D, #FF7A45)', display:'flex', alignItems:'center', justifyContent:'center', color:'white', fontSize:16, fontWeight:700 }}>JM</div>
              <div style={{ flex:1 }}>
                <div style={{ fontWeight:600, fontSize:13 }}>Juan Mendoza · {T('Operador','Driver')}</div>
                <div style={{ fontSize:11, color:'var(--ink-dim)' }}>Kenworth T880 · Placas GDL-4821 · ⭐ 4.9</div>
              </div>
              <button className="pg-btn">💬 {T('Mensaje','Message')}</button>
              <button className="pg-btn">📞 {T('Llamar','Call')}</button>
            </div>
          </div>
        </div>

        {/* Timeline + receive */}
        <div>
          <div className="pg-card" style={{ marginBottom:14 }}>
            <div className="pg-sect-t">{T('Línea de tiempo','Timeline')}</div>
            <div className="pg-timeline">
              <div className="pg-tl-step done"><div className="pg-tl-dot">✓</div><div><div className="pg-tl-t">{T('PO emitida','PO issued')}</div><div className="pg-tl-d">{T('Enviada a','Sent to')} {sup?.name}</div></div><div className="pg-tl-time">09:12</div></div>
              <div className="pg-tl-step done"><div className="pg-tl-dot">✓</div><div><div className="pg-tl-t">{T('Proveedor confirmó','Supplier confirmed')}</div><div className="pg-tl-d">{T('ETA acordado','ETA agreed')}: {active.eta}</div></div><div className="pg-tl-time">09:15</div></div>
              <div className="pg-tl-step done"><div className="pg-tl-dot">✓</div><div><div className="pg-tl-t">{T('Cargado en almacén','Loaded at warehouse')}</div><div className="pg-tl-d">{T('Foto de carga registrada','Load photo logged')}</div></div><div className="pg-tl-time">10:48</div></div>
              <div className={`pg-tl-step ${delivered ? 'done' : 'current'}`}><div className="pg-tl-dot">{delivered ? '✓' : '🚚'}</div><div><div className="pg-tl-t">{T('En tránsito','In transit')}</div><div className="pg-tl-d">{Math.round(truckPos*100)}% {T('del recorrido','of route')} · {Math.round(truckPos*22)}km / 24km</div></div><div className="pg-tl-time">11:02</div></div>
              <div className={`pg-tl-step ${delivered ? 'current' : ''}`}><div className="pg-tl-dot">{delivered ? '📍' : '○'}</div><div><div className="pg-tl-t">{T('Entrega en obra','On-site delivery')}</div><div className="pg-tl-d">{T('Esperando confirmación con foto + firma','Awaiting photo + signature')}</div></div><div className="pg-tl-time">—</div></div>
              <div className="pg-tl-step"><div className="pg-tl-dot">○</div><div><div className="pg-tl-t">{T('CFDI timbrado','CFDI stamped')}</div><div className="pg-tl-d">{T('Automático tras confirmación','Automatic after confirmation')}</div></div><div className="pg-tl-time">—</div></div>
            </div>
          </div>

          {truckPos >= 0.9 && !delivered && (
            <button className="pg-btn primary" style={{ width:'100%', justifyContent:'center' }} onClick={() => setDelivered(true)}>📍 {T('El camión llegó — Recibir material','Truck arrived — Receive')}</button>
          )}

          {delivered && (
            <div className="pg-card">
              <div className="pg-sect-t">📷 {T('Confirmar recepción','Confirm receipt')}</div>
              {!photoTaken ? (
                <div className="pg-drop" onClick={() => setPhotoTaken(true)}>
                  <div className="pg-drop-ic">📷</div>
                  <div className="pg-drop-t">{T('Tomar foto del material','Photo the material')}</div>
                  <div className="pg-drop-d">{T('Queda en bitácora + geotag','Logged with geotag')}</div>
                </div>
              ) : (
                <div style={{ aspectRatio:'16/10', background:'linear-gradient(135deg, #B8C5D1, #8FA3B5)', borderRadius:8, display:'flex', alignItems:'center', justifyContent:'center', color:'white', fontSize:28, position:'relative' }}>
                  📦
                  <div style={{ position:'absolute', bottom:8, left:8, background:'rgba(0,0,0,0.6)', padding:'4px 8px', borderRadius:4, fontSize:10, color:'white', fontFamily:'var(--font-mono)' }}>IMG · 20.67°N 103.39°W · 12:47</div>
                </div>
              )}

              {photoTaken && !signed && (
                <>
                  <div style={{ fontSize:11, color:'var(--ink-muted)', margin:'14px 0 6px', textTransform:'uppercase', letterSpacing:'0.06em', fontWeight:600 }}>{T('Firma del residente','Foreman signature')}</div>
                  <div className="pg-sig" onMouseMove={(e) => {
                    const c = e.currentTarget;
                    const r = c.getBoundingClientRect();
                    const x = e.clientX - r.left, y = e.clientY - r.top;
                    const d = document.createElement('div');
                    d.style.cssText = `position:absolute;left:${x}px;top:${y}px;width:3px;height:3px;background:#0A2540;border-radius:50%;`;
                    c.appendChild(d);
                  }}/>
                  <div style={{ display:'flex', gap:8, marginTop:12 }}>
                    <button className="pg-btn" onClick={() => setSigned(false)}>{T('Limpiar','Clear')}</button>
                    <button className="pg-btn primary" style={{ flex:1, justifyContent:'center' }} onClick={() => setSigned(true)}>{T('Confirmar firma','Confirm signature')}</button>
                  </div>
                </>
              )}

              {signed && (
                <button className="pg-btn success" style={{ width:'100%', marginTop:14, justifyContent:'center' }} onClick={() => { onReceive(active.id); setToast({ msg: T('Recepción confirmada · CFDI timbrando...','Receipt confirmed · CFDI stamping...'), type:'ok' }); }}>
                  ✓ {T('Finalizar recepción','Complete receipt')}
                </button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

window.PgScreenQuote = PgScreenQuote;
window.PgScreenOrders = PgScreenOrders;
window.PgScreenTracking = PgScreenTracking;
