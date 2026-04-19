/* global React */
// Platform Map — the full tool, all modules organized by phase
// Answers: "what does OBRA YA actually DO?"

const PHASES_ES = [
  {
    id: 'capture', name: 'Captura', color: '#FF7A45',
    desc: 'El residente pide. En su idioma, por el canal que quiera.',
    modules: [
      { ic:'💬', t:'WhatsApp IA', d:'Agente "Nico" en tu número. Entiende slang de obra mexicano.' },
      { ic:'🎙️', t:'Nota de voz', d:'Dicta el pedido. Transcribimos y normalizamos SKU.' },
      { ic:'📸', t:'Foto de lista', d:'Manda la foto del plano o la libreta. Extraemos partidas.' },
      { ic:'🏗️', t:'Kits por obra', d:'Plantillas de materiales por etapa (cimentación, losa, acabados).' }
    ]
  },
  {
    id: 'quote', name: 'Cotización', color: '#FF80B5',
    desc: 'Cotiza con 8 proveedores en paralelo. 4 minutos, no 4 días.',
    modules: [
      { ic:'⚡', t:'Cotización paralela', d:'Nico contacta 8 proveedores por canal preferido (WA, email, API).' },
      { ic:'🧠', t:'Normalización IA', d:'"Cemento gris" = CPC 30R / CEMEX / saco 50kg. Sin ambigüedad.' },
      { ic:'💱', t:'Negociación auto', d:'Contraoferta por volumen y lealtad. Cierra el mejor precio.' },
      { ic:'⚖️', t:'Comparativa', d:'Precio, ETA, distancia, rating histórico. 1 clic decide.' }
    ]
  },
  {
    id: 'order', name: 'Orden', color: '#635BFF',
    desc: 'Genera la PO, aprueba según política, notifica a todos.',
    modules: [
      { ic:'📋', t:'Orden de compra', d:'PO formal con términos, partidas y entrega. Firma digital.' },
      { ic:'🤖', t:'Auto-aprobación', d:'Política por monto, obra, partida. Bajo umbral → auto.' },
      { ic:'👥', t:'Workflow multi-rol', d:'Residente → Super → Contralor. Notificaciones y audit log.' },
      { ic:'🔒', t:'Vetting proveedor', d:'KYC, RFC 32-D, buró y lista negra antes de pagar.' }
    ]
  },
  {
    id: 'fulfill', name: 'Entrega', color: '#00D4FF',
    desc: 'Tracking GPS, ETA en vivo, confirmación con foto.',
    modules: [
      { ic:'🚚', t:'Tracking en vivo', d:'Ubicación del camión. ETA recalculado cada 3 min.' },
      { ic:'📷', t:'Confirmación foto', d:'Residente sube foto + firma. Queda en bitácora.' },
      { ic:'📦', t:'Recepción parcial', d:'¿Falta medio camión? Divide la orden, ajusta la factura.' },
      { ic:'🔄', t:'Devoluciones', d:'Material defectuoso: reporte con foto, reembolso en 48h.' }
    ]
  },
  {
    id: 'finance', name: 'Finanzas', color: '#FFB84D',
    desc: 'CFDI timbrada, SPEI programado, crédito cuando lo necesites.',
    modules: [
      { ic:'📄', t:'CFDI 4.0', d:'Timbrado válido, XML + PDF directo a tu contador.' },
      { ic:'💳', t:'SPEI programado', d:'Paga a 15, 30 o 60 días. Una sola transferencia al mes.' },
      { ic:'🏦', t:'Crédito OBRA YA', d:'Hasta $2M para materiales. Aprobación en 48h.' },
      { ic:'🧾', t:'Conciliación', d:'Auto-match de CFDI vs. PO vs. entrega. Bandera discrepancias.' }
    ]
  },
  {
    id: 'control', name: 'Control', color: '#0A2540',
    desc: 'Presupuesto vs. real, alertas, reportes por obra y partida.',
    modules: [
      { ic:'📊', t:'Dashboard multi-obra', d:'Gasto en vivo, desviación vs. presupuesto, proyección.' },
      { ic:'🚨', t:'Alertas de precio', d:'Si un material sube >10% vs. histórico, te avisamos.' },
      { ic:'📈', t:'Reportes', d:'Ahorro por obra / proveedor / partida. Export a Excel.' },
      { ic:'🔌', t:'ERP integrado', d:'SAP, Contpaqi, Aspel, Odoo. Webhook o API bidireccional.' }
    ]
  }
];

const PHASES_EN = [
  { id:'capture', name:'Capture', color:'#FF7A45', desc:'The foreman asks. In their own words, on any channel.',
    modules:[{ic:'💬',t:'WhatsApp AI',d:'"Nico" agent on your number. Understands jobsite slang.'},{ic:'🎙️',t:'Voice note',d:'Dictate the request. We transcribe and normalize SKUs.'},{ic:'📸',t:'Photo of a list',d:'Send a blueprint or notebook photo. We extract line items.'},{ic:'🏗️',t:'Per-site kits',d:'Material templates per phase (foundation, slab, finishes).'}]},
  { id:'quote', name:'Quote', color:'#FF80B5', desc:'Quote 8 suppliers in parallel. 4 minutes, not 4 days.',
    modules:[{ic:'⚡',t:'Parallel quoting',d:'Nico reaches 8 suppliers on their channel (WA, email, API).'},{ic:'🧠',t:'AI normalization',d:'"Grey cement" = CPC 30R / CEMEX / 50kg bag. No ambiguity.'},{ic:'💱',t:'Auto-negotiation',d:'Volume & loyalty counter-offers. Locks best price.'},{ic:'⚖️',t:'Comparison',d:'Price, ETA, distance, rating. One click decides.'}]},
  { id:'order', name:'Order', color:'#635BFF', desc:'PO generation, policy-driven approval, notify everyone.',
    modules:[{ic:'📋',t:'Purchase order',d:'Formal PO with terms, lines, delivery. Digital sign.'},{ic:'🤖',t:'Auto-approval',d:'Policy by amount, site, line. Below threshold → auto.'},{ic:'👥',t:'Multi-role workflow',d:'Foreman → Super → Controller. Audit log.'},{ic:'🔒',t:'Supplier vetting',d:'KYC, RFC 32-D, credit bureau before paying.'}]},
  { id:'fulfill', name:'Fulfill', color:'#00D4FF', desc:'GPS tracking, live ETA, photo confirmation.',
    modules:[{ic:'🚚',t:'Live tracking',d:'Truck location. ETA recalc every 3 min.'},{ic:'📷',t:'Photo confirm',d:'Foreman uploads photo + sign. Logged.'},{ic:'📦',t:'Partial receipt',d:'Missing half a truck? Split the order, adjust invoice.'},{ic:'🔄',t:'Returns',d:'Defective material: report with photo, refund in 48h.'}]},
  { id:'finance', name:'Finance', color:'#FFB84D', desc:'Stamped CFDI, scheduled SPEI, credit when needed.',
    modules:[{ic:'📄',t:'CFDI 4.0',d:'Valid stamped invoice, XML + PDF to your accountant.'},{ic:'💳',t:'Scheduled SPEI',d:'Pay at 15/30/60 days. One transfer per month.'},{ic:'🏦',t:'OBRA YA credit',d:'Up to $2M for materials. Approval in 48h.'},{ic:'🧾',t:'Reconciliation',d:'Auto-match CFDI vs PO vs delivery. Flags discrepancies.'}]},
  { id:'control', name:'Control', color:'#0A2540', desc:'Budget vs actual, alerts, reports by site and line.',
    modules:[{ic:'📊',t:'Multi-site dashboard',d:'Live spend, variance vs budget, projection.'},{ic:'🚨',t:'Price alerts',d:'If a material spikes >10% vs history, we alert you.'},{ic:'📈',t:'Reports',d:'Savings per site / supplier / line. Excel export.'},{ic:'🔌',t:'ERP integration',d:'SAP, Contpaqi, Aspel, Odoo. Webhook or API.'}]}
];

function PlatformMap({ lang = 'es' }) {
  const phases = lang === 'es' ? PHASES_ES : PHASES_EN;
  const [active, setActive] = React.useState('capture');
  const activePhase = phases.find(p => p.id === active);

  return (
    <div className="pmap">
      {/* Phase strip */}
      <div className="pmap-strip">
        {phases.map((p, i) => (
          <React.Fragment key={p.id}>
            <button className={`pmap-phase ${active === p.id ? 'on' : ''}`} onClick={() => setActive(p.id)} style={active === p.id ? { borderColor: p.color } : {}}>
              <span className="pmap-phase-dot" style={{ background: p.color }}/>
              <span className="pmap-phase-num">{String(i + 1).padStart(2, '0')}</span>
              <span className="pmap-phase-name">{p.name}</span>
            </button>
            {i < phases.length - 1 && <span className="pmap-arrow">→</span>}
          </React.Fragment>
        ))}
      </div>

      {/* Active phase detail */}
      <div className="pmap-body">
        <div className="pmap-header">
          <div className="pmap-header-tag" style={{ color: activePhase.color }}>
            <span className="pmap-header-dot" style={{ background: activePhase.color }}/>
            {lang === 'es' ? 'FASE' : 'PHASE'} {String(phases.findIndex(p => p.id === active) + 1).padStart(2, '0')} · {activePhase.name.toUpperCase()}
          </div>
          <h3 className="pmap-header-t">{activePhase.desc}</h3>
        </div>
        <div className="pmap-modules">
          {activePhase.modules.map((m, i) => (
            <div key={i} className="pmap-mod" style={{ '--accent-phase': activePhase.color }}>
              <div className="pmap-mod-ic" style={{ background: activePhase.color + '18', color: activePhase.color }}>{m.ic}</div>
              <div>
                <div className="pmap-mod-t">{m.t}</div>
                <div className="pmap-mod-d">{m.d}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

window.PlatformMap = PlatformMap;
