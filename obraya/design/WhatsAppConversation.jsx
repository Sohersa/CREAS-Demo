/* global React */
const { useState: useStateWA2, useEffect: useEffectWA2 } = React;

function WhatsAppConversation({ lang = 'es' }) {
  const script = lang === 'es' ? [
    { side: 'out', text: <>Necesito <b>50 bultos CPC 30R</b> para mañana 7am en Zapopan 🚧</>, t: '08:14' },
    { side: 'in', text: <><span className="label">parsing</span> 50 · CPC 30R · Zapopan · mañana 07:00</>, t: '08:14' },
    { side: 'in', text: <>Contacto <b>8 proveedores</b> en tu zona ⚡</>, t: '08:14' },
    { side: 'in', text: <><b>3 respuestas</b> en 4 min. Mejor: <b>$246/bulto</b> 🟢</>, t: '08:18' },
    { side: 'in', text: <><b>Comparativa:</b><span className="list-line">🥇 Cemex — $246 · 7am ✅</span><span className="list-line">🥈 JAL — $249 · 8am</span><span className="list-line">🥉 Cruz Azul — $251 · 9am</span>Responde 1, 2 ó 3.</>, t: '08:26' },
    { side: 'out', text: <>1</>, t: '08:26' },
    { side: 'in', text: <>Orden <b>#4821</b> con Cemex. Total $12,300. Proveedor notificado. 👌</>, t: '08:27' }
  ] : [
    { side: 'out', text: <>Need <b>50 bags CPC 30R</b> tomorrow 7am at Zapopan 🚧</>, t: '08:14' },
    { side: 'in', text: <><span className="label">parsing</span> 50 · CPC 30R · Zapopan · tomorrow 07:00</>, t: '08:14' },
    { side: 'in', text: <>Reaching <b>8 suppliers</b> in your area ⚡</>, t: '08:14' },
    { side: 'in', text: <><b>3 replies</b> in 4 min. Best: <b>$246/bag</b> 🟢</>, t: '08:18' },
    { side: 'in', text: <><b>Comparison:</b><span className="list-line">🥇 Cemex — $246 · 7am ✅</span><span className="list-line">🥈 JAL — $249 · 8am</span><span className="list-line">🥉 Cruz Azul — $251 · 9am</span>Reply 1, 2 or 3.</>, t: '08:26' },
    { side: 'out', text: <>1</>, t: '08:26' },
    { side: 'in', text: <>Order <b>#4821</b> with Cemex. Total $12,300. Supplier notified. 👌</>, t: '08:27' }
  ];
  const [shown, setShown] = useStateWA2(1);
  const [typing, setTyping] = useStateWA2(false);
  useEffectWA2(() => {
    if (shown >= script.length) { const r = setTimeout(() => setShown(1), 5000); return () => clearTimeout(r); }
    const delay = shown === 1 ? 900 : (script[shown - 1].side === 'out' ? 600 : 1400);
    setTyping(script[shown] && script[shown].side === 'in');
    const t = setTimeout(() => { setShown(s => s + 1); setTyping(false); }, delay + (script[shown] && script[shown].side === 'in' ? 800 : 0));
    return () => clearTimeout(t);
  }, [shown, lang]);
  return (
    <div className="wa-phone">
      <div className="wa-screen">
        <div className="wa-topbar">
          <div className="wa-avatar">N</div>
          <div className="wa-contact"><div className="wa-name">Nico · OBRA YA</div><div className="wa-status">{lang === 'es' ? 'en línea' : 'online'}</div></div>
          <div className="wa-icons">📞 ⋮</div>
        </div>
        <div className="wa-messages">
          {script.slice(0, shown).map((m, i) => (
            <div key={i} className={`wa-msg ${m.side}`} style={{ animationDelay: `${i * 40}ms` }}>
              {m.text}
              <span className="meta">{m.t}{m.side === 'out' && <span className="tick">✓✓</span>}</span>
            </div>
          ))}
          {typing && <div className="wa-typing"><i/><i/><i/></div>}
        </div>
        <div className="wa-input">
          <div className="wa-input-box">{lang === 'es' ? 'Mensaje' : 'Message'}</div>
          <div className="wa-input-mic">🎤</div>
        </div>
      </div>
    </div>
  );
}
window.WhatsAppConversation = WhatsAppConversation;
