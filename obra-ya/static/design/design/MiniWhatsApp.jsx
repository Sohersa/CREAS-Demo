/* global React */
// Mini interactive WhatsApp demo
const { useState: useStateMW2, useRef: useRefMW2, useEffect: useEffectMW2 } = React;
function MiniWhatsApp({ lang = 'es' }) {
  const initial = lang === 'es'
    ? [{ side: 'in', text: '¡Hola! Soy Nico. ¿Qué necesitas para la obra?' }]
    : [{ side: 'in', text: 'Hey! I\'m Nico. What do you need for the site?' }];
  const [msgs, setMsgs] = useStateMW2(initial);
  const [input, setInput] = useStateMW2('');
  const [busy, setBusy] = useStateMW2(false);
  const scrollRef = useRefMW2(null);
  useEffectMW2(() => { setMsgs(initial); }, [lang]);
  useEffectMW2(() => { if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight; }, [msgs, busy]);
  const send = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput(''); setMsgs(m => [...m, { side: 'out', text }]); setBusy(true);
    const history = msgs.map(m => ({ role: m.side === 'out' ? 'user' : 'assistant', content: m.text }));
    const sys = lang === 'es'
      ? 'Eres Nico, agente IA de OBRA YA. Mexicano, directo, breve (máx 2 oraciones). Ayudas a residentes a pedir materiales. Si tienen material+cantidad+dirección+fecha, confirma y di que cotizarás con 8 proveedores. Si falta algo, pregunta SOLO eso. MXN. Nunca inventes precios.'
      : 'You are Nico, OBRA YA AI. Direct, brief (max 2 sentences). If they give material+qty+address+date, confirm and say you\'ll quote with 8 suppliers. If missing, ask ONLY that. MXN. Never invent prices.';
    try {
      const reply = await window.claude.complete({ messages: [{ role: 'user', content: sys }, ...history, { role: 'user', content: text }] });
      setMsgs(m => [...m, { side: 'in', text: reply }]);
    } catch { setMsgs(m => [...m, { side: 'in', text: lang === 'es' ? 'Tuve un problema. Reintenta.' : 'Something went wrong.' }]); }
    setBusy(false);
  };
  const hint = lang === 'es' ? '50 bultos cemento mañana Zapopan' : '50 bags cement tomorrow Zapopan';
  return (
    <div className="mini-wa">
      <div className="mini-wa-hdr">
        <div className="wa-avatar">N</div>
        <div className="wa-contact"><div className="wa-name">Nico · OBRA YA</div><div className="wa-status">{lang === 'es' ? 'en línea' : 'online'}</div></div>
        <div style={{ fontFamily: 'var(--font-mono)', fontSize: 10, color: 'rgba(255,255,255,0.7)', letterSpacing: '0.14em' }}>DEMO</div>
      </div>
      <div className="mini-wa-body" ref={scrollRef}>
        {msgs.map((m, i) => (<div key={i} className={`wa-msg ${m.side}`}>{m.text}</div>))}
        {busy && <div className="wa-typing"><i/><i/><i/></div>}
      </div>
      <form className="mini-wa-input" onSubmit={(e) => { e.preventDefault(); send(); }}>
        <input type="text" value={input} onChange={(e) => setInput(e.target.value)} placeholder={hint} disabled={busy} />
        <button type="submit" disabled={busy || !input.trim()}>➤</button>
      </form>
    </div>
  );
}
window.MiniWhatsApp = MiniWhatsApp;
