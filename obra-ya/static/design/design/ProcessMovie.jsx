/* global React, Icon */
// ProcessMovie — cinematic animated simulation of the full OBRA YA pipeline
// Auto-plays through 18 stations. Each station has a mini-animation when active.
const { useState: pS, useEffect: pE, useRef: pR } = React;

const STATIONS = (lang) => [
  { id:'wa',     group:1, ic:'chat',    name: lang==='es'?'Llega un mensaje':'A message arrives',      sub: lang==='es'?'Residente escribe o manda voz':'Foreman texts or voices' },
  { id:'voice',  group:1, ic:'mic',     name: lang==='es'?'Escucha la voz':'Listens to voice',         sub: lang==='es'?'Voz → texto al instante':'Voice → text instantly' },
  { id:'gps',    group:1, ic:'pin',     name: lang==='es'?'Lee la ubicación':'Reads the location',     sub: lang==='es'?'Un pin se vuelve dirección':'Pin becomes address' },
  { id:'cat',    group:1, ic:'book',    name: lang==='es'?'Entiende el slang':'Understands slang',     sub: lang==='es'?'"Cemento gris" → SKU exacto':'"Gray cement" → exact SKU' },
  { id:'fan',    group:2, ic:'bolt',    name: lang==='es'?'Le pregunta a 20 proveedores':'Asks 20 suppliers', sub: lang==='es'?'Todos al mismo tiempo':'All at once' },
  { id:'route',  group:2, ic:'users',   name: lang==='es'?'Al vendedor más rápido':'To the fastest rep', sub: lang==='es'?'El que contesta, no el dueño':'The one who replies' },
  { id:'tpl',    group:2, ic:'send',    name: lang==='es'?'Mensaje por WhatsApp':'WhatsApp message',    sub: lang==='es'?'Plantilla aprobada por Meta':'Meta-approved template' },
  { id:'wait',   group:2, ic:'clock',   name: lang==='es'?'Les insiste si no contestan':'Nags the silent', sub: lang==='es'?'Recordatorios a 15 y 25 min':'Reminders at 15 and 25 min' },
  { id:'parse',  group:3, ic:'compare', name: lang==='es'?'Lee lo que respondieron':'Reads each reply',  sub: lang==='es'?'Texto libre → datos ordenados':'Free text → structured data' },
  { id:'norm',   group:3, ic:'scale',   name: lang==='es'?'Compara peras con peras':'Apples to apples',  sub: lang==='es'?'Mismo bulto, mismo flete, misma moneda':'Same unit, same freight, same currency' },
  { id:'hist',   group:3, ic:'chart',   name: lang==='es'?'Sabe si el precio es justo':'Knows fair price',sub: lang==='es'?'Compara con tu histórico en la zona':'Checks against your zone history' },
  { id:'alert',  group:3, ic:'alert',   name: lang==='es'?'Detecta precios raros':'Flags weird prices',  sub: lang==='es'?'Si uno cotiza muy alto, avisa':'If one quotes too high, it flags' },
  { id:'hier',   group:4, ic:'tree',    name: lang==='es'?'Al que le toca firmar':'To whoever signs',    sub: lang==='es'?'Residente → súper → director':'Foreman → super → director' },
  { id:'pol',    group:4, ic:'shield',  name: lang==='es'?'Las reglas de tu obra':'Your jobsite rules',  sub: lang==='es'?'Si cumple los límites, pasa solo':'If within limits, auto-approves' },
  { id:'pay',    group:4, ic:'card',    name: lang==='es'?'Paga con tarjeta o banco':'Pays card or bank',sub: lang==='es'?'Stripe o SPEI, tú eliges':'Stripe or SPEI, your choice' },
  { id:'truck',  group:5, ic:'truck',   name: lang==='es'?'Ubica el camión en vivo':'Tracks the truck live', sub: lang==='es'?'Sabes dónde está, siempre':'You always know where it is' },
  { id:'photo',  group:5, ic:'camera',  name: lang==='es'?'Foto y firma al entregar':'Photo & signature on delivery', sub: lang==='es'?'Evidencia con GPS y hora':'GPS + timestamp proof' },
  { id:'cfdi',   group:5, ic:'invoice', name: lang==='es'?'Factura al contador':'Invoice to accountant', sub: lang==='es'?'CFDI sale directo al correo':'CFDI goes straight to email' }
];

const GROUPS = {
  es: ['El pedido llega', 'Nico sale a cotizar', 'Compara y elige', 'Autoriza y paga', 'Llega a obra'],
  en: ['The order comes in', 'Nico quotes around', 'Compares & picks', 'Approves & pays', 'Arrives on site']
};

function ProcessMovie({ lang = 'es' }) {
  const stations = STATIONS(lang);
  const groups = GROUPS[lang];
  const [active, setActive] = pS(0);
  const [playing, setPlaying] = pS(true);
  const [progress, setProgress] = pS(0);
  const hoverRef = pR(false);

  pE(() => {
    if (!playing) return;
    const tick = 50;
    const dur = 1600;
    let e = 0;
    const iv = setInterval(() => {
      if (hoverRef.current) return;
      e += tick;
      setProgress(Math.min(100, (e/dur)*100));
      if (e >= dur) {
        e = 0;
        setProgress(0);
        setActive(a => (a + 1) % stations.length);
      }
    }, tick);
    return () => clearInterval(iv);
  }, [active, playing, lang]);

  pE(() => { setActive(0); setProgress(0); }, [lang]);

  const currentStation = stations[active];
  const currentGroup = currentStation.group;

  return (
    <div className="pmov" onMouseEnter={() => hoverRef.current = true} onMouseLeave={() => hoverRef.current = false}>
      {/* HEADER */}
      <div className="pmov-head">
        <div className="pmov-ttl">
          <div className="pmov-eyebrow">{lang==='es'?'SIMULACIÓN DEL PIPELINE':'PIPELINE SIMULATION'}</div>
          <div className="pmov-stage">{String(active+1).padStart(2,'0')} · {currentStation.name}</div>
        </div>
        <div className="pmov-controls">
          <button className="pmov-play" onClick={() => setPlaying(p => !p)}>{playing ? '❚❚' : '▶'}</button>
          <div className="pmov-bar"><div className="pmov-bar-fill" style={{width:`${(active/(stations.length-1))*100}%`}}/></div>
          <span className="pmov-count mono">{active+1}/{stations.length}</span>
        </div>
      </div>

      {/* GROUP TABS */}
      <div className="pmov-groups">
        {groups.map((g, i) => (
          <div key={i} className={`pmov-group ${currentGroup===i+1?'on':''}`}>
            <span className="pmov-group-n mono">0{i+1}</span>
            <span className="pmov-group-t">{g}</span>
          </div>
        ))}
      </div>

      {/* STAGE */}
      <div className="pmov-stage-area">
        <SceneForStation station={currentStation} lang={lang} progress={progress}/>
      </div>

      {/* STATION TIMELINE */}
      <div className="pmov-timeline">
        {stations.map((s, i) => (
          <button key={s.id} className={`pmov-node ${i===active?'on':''} ${i<active?'done':''}`} onClick={() => { setActive(i); setProgress(0); }}>
            <div className="pmov-node-dot"><Icon name={s.ic} size={14}/></div>
            <div className="pmov-node-label">{s.name}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

/* ═══ Per-station cinematic scenes ═══ */
function SceneForStation({ station, lang, progress }) {
  const scenes = {
    wa: () => (
      <div className="scene">
        <div className="scene-phone">
          <div className="scene-phone-hdr">Nico · OBRA YA</div>
          <div className="scene-bubble in" style={{animationDelay:'0ms'}}>{lang==='es'?'Necesito 50 bultos cemento CPC 30R para mañana 7am, Zapopan':'Need 50 bags CPC 30R cement tomorrow 7am, Zapopan'}</div>
          <div className="scene-bubble typing" style={{animationDelay:'600ms'}}>• • •</div>
          <div className="scene-bubble out" style={{animationDelay:'1100ms'}}>{lang==='es'?'Listo. Cotizando con 8 proveedores ahora mismo':'Got it. Quoting 8 suppliers now'}</div>
        </div>
        <div className="scene-caption">{lang==='es'?'El residente manda texto, voz o ubicación. Nada más.':'Foreman sends text, voice or pin. Nothing else.'}</div>
      </div>
    ),
    voice: () => (
      <div className="scene">
        <div className="scene-voice">
          <div className="voice-wave">
            {[...Array(32)].map((_, i) => (
              <span key={i} style={{animationDelay: `${i*40}ms`, height: `${20 + Math.sin(i*0.6)*40 + Math.random()*20}%`}}/>
            ))}
          </div>
          <div className="voice-time mono">0:04 / 0:04</div>
          <div className="voice-arrow">→</div>
          <div className="voice-txt">
            <div className="voice-txt-label">Whisper · Groq</div>
            <div className="voice-txt-body">"{lang==='es'?'necesito varilla del tres octavos dos toneladas':'need three eighths rebar two tons'}"</div>
          </div>
        </div>
        <div className="scene-caption">{lang==='es'?'Transcripción automática en 800ms. No hay que escribir.':'Auto transcription in 800ms. No typing needed.'}</div>
      </div>
    ),
    gps: () => (
      <div className="scene">
        <div className="scene-map">
          <svg viewBox="0 0 400 200" width="100%" height="100%">
            <defs><pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0L0 0 0 20" fill="none" stroke="rgba(10,37,64,0.05)" strokeWidth="1"/></pattern></defs>
            <rect width="400" height="200" fill="url(#grid)"/>
            <path d="M40 100 Q 120 60 180 100 T 360 80" stroke="#635BFF" strokeWidth="2" fill="none" strokeDasharray="4 4"/>
            <circle cx="200" cy="90" r="16" fill="#FF7A45" opacity="0.25"><animate attributeName="r" from="16" to="40" dur="1.8s" repeatCount="indefinite"/><animate attributeName="opacity" from="0.35" to="0" dur="1.8s" repeatCount="indefinite"/></circle>
            <circle cx="200" cy="90" r="8" fill="#FF7A45"/>
            <path d="M200 82 L200 98" stroke="white" strokeWidth="2"/>
          </svg>
          <div className="scene-map-label">📍 Av. Patria 1234, Zapopan JAL</div>
        </div>
        <div className="scene-caption">{lang==='es'?'Un pin en WhatsApp → dirección formal + municipio + zona.':'A WhatsApp pin → formal address + city + zone.'}</div>
      </div>
    ),
    cat: () => (
      <div className="scene">
        <div className="scene-cat">
          <div className="cat-in">"{lang==='es'?'cementito tolteca del gris':'gray tolteca cement'}"</div>
          <div className="cat-arrow">→</div>
          <div className="cat-out">
            <div className="cat-row"><span className="cat-sku mono">CEM-CPC30R-50</span><span className="cat-name">Cemento CPC 30R · Tolteca · bulto 50kg</span></div>
            <div className="cat-row"><span className="cat-sku mono">CEM-CPC40R-50</span><span className="cat-name">Cemento CPC 40R · Tolteca · bulto 50kg</span></div>
            <div className="cat-row"><span className="cat-sku mono">CEM-GRIS-25</span><span className="cat-name">Cemento gris genérico · bulto 25kg</span></div>
          </div>
        </div>
        <div className="scene-caption">{lang==='es'?'Slang de obra → SKU normalizado del catálogo maestro.':'Jobsite slang → normalized master-catalog SKU.'}</div>
      </div>
    ),
    fan: () => (
      <div className="scene">
        <div className="scene-fanout">
          <div className="fan-center"><div className="fan-center-logo">OY</div></div>
          {[...Array(12)].map((_, i) => {
            const angle = (i / 12) * Math.PI * 2 - Math.PI/2;
            const r = 130;
            const x = 50 + (Math.cos(angle)*r)/8;
            const y = 50 + (Math.sin(angle)*r)/6;
            return (
              <div key={i} className="fan-node" style={{left:`${x}%`, top:`${y}%`, animationDelay: `${i*60}ms`}}>
                <div className="fan-node-dot"/>
                <div className="fan-node-label">Prov {String(i+1).padStart(2,'0')}</div>
              </div>
            );
          })}
          <svg className="fan-lines" viewBox="0 0 400 200">
            {[...Array(12)].map((_, i) => {
              const angle = (i / 12) * Math.PI * 2 - Math.PI/2;
              const x = 200 + Math.cos(angle)*160;
              const y = 100 + Math.sin(angle)*80;
              return <line key={i} x1="200" y1="100" x2={x} y2={y} stroke="#635BFF" strokeWidth="1" strokeDasharray="3 3" opacity="0.3"/>;
            })}
          </svg>
        </div>
        <div className="scene-caption">{lang==='es'?'Un pedido explota a 20 cotizaciones paralelas. En segundos.':'One request fans out to 20 parallel quotes. In seconds.'}</div>
      </div>
    ),
    route: () => (
      <div className="scene">
        <div className="scene-route">
          <div className="route-sup">
            <div className="route-sup-name">Cemex Zapopan</div>
            <div className="route-sellers">
              <div className="route-seller"><div className="sel-ava">JM</div><div><div className="sel-n">Juan M.</div><div className="sel-s busy">Ocupado · 18 min</div></div></div>
              <div className="route-seller winner"><div className="sel-ava">MA</div><div><div className="sel-n">María A. ✓</div><div className="sel-s ok">Disponible · 2 min</div></div></div>
              <div className="route-seller"><div className="sel-ava">CR</div><div><div className="sel-n">Carlos R.</div><div className="sel-s off">Fuera de horario</div></div></div>
            </div>
          </div>
        </div>
        <div className="scene-caption">{lang==='es'?'Elige al vendedor más rápido disponible dentro del proveedor.':'Picks the fastest available seller within the supplier.'}</div>
      </div>
    ),
    tpl: () => (
      <div className="scene">
        <div className="scene-tpl">
          <div className="tpl-msg">
            <div className="tpl-tag">WHATSAPP TEMPLATE · APPROVED</div>
            <div className="tpl-body">
              Hola, soy Nico de ObraYa.<br/>
              Tengo cliente que necesita: <b>50 × Cemento CPC 30R</b><br/>
              Entrega: <b>Zapopan · Mañana 7am</b><br/>
              ¿Me pasas tu mejor precio con flete?
            </div>
            <div className="tpl-meta">
              <span>✓ Template aprobado</span>
              <span>→ {lang==='es'?'Fallback texto libre si no':'Free-text fallback if not'}</span>
            </div>
          </div>
        </div>
        <div className="scene-caption">{lang==='es'?'Template aprobado por Meta para abrir ventana 24h. Fallback automático.':'Meta-approved template opens 24h window. Auto fallback.'}</div>
      </div>
    ),
    wait: () => (
      <div className="scene">
        <div className="scene-wait">
          <div className="wait-track">
            <div className="wait-dot" style={{left:'0%'}}><div className="wait-dot-inner"/><div className="wait-dot-label">T+0<br/>{lang==='es'?'Enviado':'Sent'}</div></div>
            <div className="wait-dot" style={{left:'30%'}}><div className="wait-dot-inner warn"/><div className="wait-dot-label">T+15<br/>{lang==='es'?'Recordatorio':'Reminder'}</div></div>
            <div className="wait-dot" style={{left:'60%'}}><div className="wait-dot-inner warn"/><div className="wait-dot-label">T+25<br/>{lang==='es'?'2º recordatorio':'2nd reminder'}</div></div>
            <div className="wait-dot" style={{left:'100%'}}><div className="wait-dot-inner done"/><div className="wait-dot-label">T+30<br/>{lang==='es'?'Cierre':'Close'}</div></div>
            <div className="wait-progress" style={{width:`${progress}%`}}/>
          </div>
        </div>
        <div className="scene-caption">{lang==='es'?'Recordatorios automáticos a los que no respondieron. Timeout a los 30.':'Auto reminders to the silent. Timeout at 30.'}</div>
      </div>
    ),
    parse: () => (
      <div className="scene">
        <div className="scene-parse">
          <div className="parse-raw">
            <div className="parse-label">{lang==='es'?'RESPUESTA CRUDA DE PROVEEDOR':'RAW SUPPLIER REPLY'}</div>
            <div className="parse-txt">"{lang==='es'?'hola! te van a salir a $246 c/u, incluye flete, entrego mañana a las 7. saludos':'hi! they go at $246 each, freight included, delivery tomorrow 7am. cheers'}"</div>
          </div>
          <div className="parse-arrow">→</div>
          <div className="parse-struct">
            <div className="parse-row"><span>price_unit</span><b className="mono">246.00</b></div>
            <div className="parse-row"><span>currency</span><b className="mono">MXN</b></div>
            <div className="parse-row"><span>includes_freight</span><b className="mono">true</b></div>
            <div className="parse-row"><span>eta</span><b className="mono">2026-04-20T07:00</b></div>
            <div className="parse-row"><span>in_stock</span><b className="mono">true</b></div>
          </div>
        </div>
        <div className="scene-caption">{lang==='es'?'Claude lee el texto libre y lo convierte en JSON estructurado.':'Claude reads free text and converts it to structured JSON.'}</div>
      </div>
    ),
    norm: () => (
      <div className="scene">
        <div className="scene-norm">
          <table className="norm-tbl">
            <thead><tr><th>{lang==='es'?'Proveedor':'Supplier'}</th><th>{lang==='es'?'Unitario':'Unit'}</th><th>Flete</th><th>{lang==='es'?'Efectivo':'Effective'}</th><th>ETA</th><th>Rating</th></tr></thead>
            <tbody>
              <tr className="best"><td>Cemex</td><td className="mono">$240</td><td className="mono">$6</td><td className="mono">$246</td><td>7:00</td><td>98%</td></tr>
              <tr><td>Mat. JAL</td><td className="mono">$245</td><td className="mono">$4</td><td className="mono">$249</td><td>8:00</td><td>94%</td></tr>
              <tr><td>Cruz Azul</td><td className="mono">$238</td><td className="mono">$13</td><td className="mono">$251</td><td>9:00</td><td>91%</td></tr>
              <tr className="out"><td>Obregón</td><td className="mono">$310</td><td className="mono">$0</td><td className="mono">$310 ⚠</td><td>10:00</td><td>85%</td></tr>
            </tbody>
          </table>
        </div>
        <div className="scene-caption">{lang==='es'?'Mismo bulto, mismo flete, misma moneda. La comparativa es justa.':'Same unit, same freight, same currency. Apples to apples.'}</div>
      </div>
    ),
    hist: () => (
      <div className="scene">
        <div className="scene-hist">
          <svg viewBox="0 0 400 160" width="100%" height="100%" preserveAspectRatio="none">
            <defs>
              <linearGradient id="histg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#635BFF" stopOpacity="0.3"/><stop offset="1" stopColor="#635BFF" stopOpacity="0"/></linearGradient>
            </defs>
            <path d="M0 110 L40 100 L80 95 L120 105 L160 85 L200 80 L240 90 L280 75 L320 70 L360 72 L400 65 L400 160 L0 160 Z" fill="url(#histg)"/>
            <path d="M0 110 L40 100 L80 95 L120 105 L160 85 L200 80 L240 90 L280 75 L320 70 L360 72 L400 65" stroke="#635BFF" strokeWidth="2" fill="none"/>
            <circle cx="200" cy="80" r="4" fill="#FF7A45"/>
            <text x="205" y="75" fontSize="10" fill="#0A2540" fontFamily="JetBrains Mono">$246 · HOY</text>
            {[240, 245, 238, 249, 252, 246, 250, 241, 239, 244].map((v, i) => (
              <text key={i} x={i*40} y="130" fontSize="8" fill="#8792A2" fontFamily="JetBrains Mono">${v}</text>
            ))}
          </svg>
        </div>
        <div className="scene-caption">{lang==='es'?'Cada cotización alimenta el histórico. Zona · fecha · producto.':'Every quote feeds the history. Zone · date · SKU.'}</div>
      </div>
    ),
    alert: () => (
      <div className="scene">
        <div className="scene-alert">
          <div className="alert-row ok"><span className="alert-ic">✓</span><span className="alert-txt">Cemex · <b>$246</b></span><span className="alert-tag">{lang==='es'?'dentro de rango':'in range'}</span></div>
          <div className="alert-row ok"><span className="alert-ic">✓</span><span className="alert-txt">Cruz Azul · <b>$251</b></span><span className="alert-tag">{lang==='es'?'dentro de rango':'in range'}</span></div>
          <div className="alert-row warn"><span className="alert-ic">⚠</span><span className="alert-txt">Obregón · <b>$310</b></span><span className="alert-tag">+26% {lang==='es'?'fuera de rango':'outlier'}</span></div>
          <div className="alert-msg">{lang==='es'?'Nico avisa al director: "Este proveedor está cotizando 26% arriba del promedio de la zona. ¿Excluir?"':'Nico flags director: "This supplier is quoting 26% above zone average. Exclude?"'}</div>
        </div>
        <div className="scene-caption">{lang==='es'?'Detección automática de outliers · evita mordidas y errores.':'Auto outlier detection · stops bribes and mistakes.'}</div>
      </div>
    ),
    hier: () => (
      <div className="scene">
        <div className="scene-hier">
          <div className="hier-col"><div className="hier-role">{lang==='es'?'Residente':'Foreman'}</div><div className="hier-lim">≤ $10K</div><div className="hier-dot ok"/></div>
          <div className="hier-arrow">→</div>
          <div className="hier-col"><div className="hier-role">{lang==='es'?'Superintendente':'Superintendent'}</div><div className="hier-lim">≤ $100K</div><div className="hier-dot ok"/></div>
          <div className="hier-arrow">→</div>
          <div className="hier-col"><div className="hier-role">{lang==='es'?'Compras':'Procurement'}</div><div className="hier-lim">≤ $500K</div><div className="hier-dot pend"/></div>
          <div className="hier-arrow">→</div>
          <div className="hier-col"><div className="hier-role">{lang==='es'?'Director':'Director'}</div><div className="hier-lim">{lang==='es'?'Sin límite':'No limit'}</div><div className="hier-dot off"/></div>
        </div>
        <div className="scene-caption">{lang==='es'?'Cada monto se rutea al nivel que corresponde — sin pasar de largo.':'Each amount routes to the right level — no bypassing.'}</div>
      </div>
    ),
    pol: () => (
      <div className="scene">
        <div className="scene-pol">
          <div className="pol-card">
            <div className="pol-card-ttl">{lang==='es'?'Política Torre Andares':'Torre Andares policy'}</div>
            <div className="pol-rule"><span className="pol-key">{lang==='es'?'Cemento':'Cement'}</span><span className="pol-op">≤</span><span className="pol-val mono">$15,000</span><span className="pol-badge ok">{lang==='es'?'AUTO':'AUTO'}</span></div>
            <div className="pol-rule"><span className="pol-key">{lang==='es'?'Acero':'Steel'}</span><span className="pol-op">≤</span><span className="pol-val mono">$100,000</span><span className="pol-badge ok">{lang==='es'?'AUTO':'AUTO'}</span></div>
            <div className="pol-rule"><span className="pol-key">{lang==='es'?'Cualquiera':'Any'}</span><span className="pol-op">&gt;</span><span className="pol-val mono">$500,000</span><span className="pol-badge warn">{lang==='es'?'DIRECTOR':'DIRECTOR'}</span></div>
          </div>
        </div>
        <div className="scene-caption">{lang==='es'?'Define umbrales una vez. Nico decide por ti dentro del rango.':'Set thresholds once. Nico decides within range.'}</div>
      </div>
    ),
    pay: () => (
      <div className="scene">
        <div className="scene-pay">
          <div className="pay-card">
            <div className="pay-card-brand">STRIPE</div>
            <div className="pay-card-num mono">4242 •••• •••• 4821</div>
            <div className="pay-card-row"><div><div className="pay-card-k">HOLDER</div><div className="pay-card-v">Constructora del Valle</div></div><div><div className="pay-card-k">EXP</div><div className="pay-card-v mono">09/28</div></div></div>
          </div>
          <div className="pay-or">{lang==='es'?'o':'or'}</div>
          <div className="pay-spei">
            <div className="pay-spei-ic">SPEI</div>
            <div className="pay-spei-txt">{lang==='es'?'Transferencia bancaria programada':'Scheduled bank transfer'}</div>
            <div className="pay-spei-amt mono">$14,268.00</div>
          </div>
        </div>
        <div className="scene-caption">{lang==='es'?'Pago instantáneo con tarjeta o SPEI programado. Cero paperwork.':'Instant card payment or scheduled SPEI. Zero paperwork.'}</div>
      </div>
    ),
    truck: () => (
      <div className="scene">
        <div className="scene-truck">
          <svg viewBox="0 0 400 180" width="100%" height="100%">
            <rect width="400" height="180" fill="#F6F9FC"/>
            <path d="M30 120 Q 150 60 260 90 T 380 70" stroke="#635BFF" strokeWidth="3" fill="none" strokeDasharray="6 4" opacity="0.4"/>
            <circle cx="30" cy="120" r="6" fill="#0A2540"/>
            <text x="40" y="125" fontSize="10" fill="#0A2540" fontFamily="JetBrains Mono">Cemex</text>
            <circle cx="380" cy="70" r="6" fill="#FF7A45"/>
            <text x="320" y="65" fontSize="10" fill="#0A2540" fontFamily="JetBrains Mono">Torre Andares</text>
            <g transform={`translate(${30 + progress * 3.5}, ${120 - progress*0.5}) rotate(-12)`}>
              <rect x="-14" y="-8" width="24" height="12" rx="2" fill="#FF7A45"/>
              <rect x="-18" y="-4" width="8" height="8" fill="#FF7A45"/>
              <circle cx="-12" cy="6" r="3" fill="#0A2540"/>
              <circle cx="6" cy="6" r="3" fill="#0A2540"/>
            </g>
          </svg>
          <div className="truck-eta">ETA: <b className="mono">06:47</b> · {lang==='es'?'a 4.2 km de obra':'4.2 km from site'} · 🚚 {lang==='es'?'en ruta':'on route'}</div>
        </div>
        <div className="scene-caption">{lang==='es'?'Ubicación del camión en vivo. Si se atrasa, todos se enteran.':'Live truck location. If it\'s late, everyone knows.'}</div>
      </div>
    ),
    photo: () => (
      <div className="scene">
        <div className="scene-photo">
          <div className="photo-frame">
            <div className="photo-img">
              <svg viewBox="0 0 200 140" width="100%" height="100%">
                <rect width="200" height="140" fill="#8792A2"/>
                <rect x="20" y="60" width="40" height="50" fill="#6B7280"/>
                <rect x="65" y="65" width="40" height="45" fill="#6B7280"/>
                <rect x="110" y="55" width="40" height="55" fill="#6B7280"/>
                <rect x="155" y="62" width="35" height="48" fill="#6B7280"/>
                <text x="100" y="130" fontSize="9" fill="white" textAnchor="middle" fontFamily="JetBrains Mono" opacity="0.7">50 bultos · entregados</text>
              </svg>
            </div>
            <div className="photo-meta">
              <div className="photo-ts mono">2026-04-20 07:03 GMT-6</div>
              <div className="photo-gps mono">📍 20.6736, -103.4012</div>
              <div className="photo-sig">✓ {lang==='es'?'Firmado por Roberto S.':'Signed by Roberto S.'}</div>
            </div>
          </div>
        </div>
        <div className="scene-caption">{lang==='es'?'Foto + GPS + timestamp. Evidencia fiscalmente válida.':'Photo + GPS + timestamp. Legally valid proof.'}</div>
      </div>
    ),
    cfdi: () => (
      <div className="scene">
        <div className="scene-cfdi">
          <div className="cfdi-doc">
            <div className="cfdi-stamp">CFDI 4.0 · TIMBRADA ✓</div>
            <div className="cfdi-uuid mono">UUID: 4B9F2-A821-C4D7-••••</div>
            <div className="cfdi-row"><span>Emisor</span><b>Cemex SA de CV</b></div>
            <div className="cfdi-row"><span>Receptor</span><b>Constructora del Valle</b></div>
            <div className="cfdi-row"><span>Subtotal</span><b className="mono">$12,300.00</b></div>
            <div className="cfdi-row"><span>IVA 16%</span><b className="mono">$1,968.00</b></div>
            <div className="cfdi-row total"><span>Total MXN</span><b className="mono">$14,268.00</b></div>
            <div className="cfdi-routes">
              <div>→ {lang==='es'?'Contador':'Accountant'}</div>
              <div>→ SAP</div>
              <div>→ {lang==='es'?'Archivo':'Archive'}</div>
            </div>
          </div>
        </div>
        <div className="scene-caption">{lang==='es'?'Timbrada por el SAT, enviada al contador y al ERP automáticamente.':'SAT-stamped, sent to accountant and ERP automatically.'}</div>
      </div>
    )
  };
  const render = scenes[station.id] || (() => null);
  return <div className="scene-wrap" key={station.id}>{render()}</div>;
}

Object.assign(window, { ProcessMovie });
