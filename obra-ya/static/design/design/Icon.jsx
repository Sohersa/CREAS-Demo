/* global React */
// Icon system — minimal line icons, 1.5 stroke, 24x24, currentColor
window.Icon = function Icon({ name, size = 20, className = '' }) {
  const p = { width: size, height: size, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.6, strokeLinecap: 'round', strokeLinejoin: 'round', className };
  const icons = {
    chat:      <svg {...p}><path d="M21 12a9 9 0 1 1-3.6-7.2L21 3v5h-5"/><path d="M8 10h8M8 14h5"/></svg>,
    bolt:      <svg {...p}><path d="M13 2L3 14h7l-1 8 10-12h-7l1-8z"/></svg>,
    scale:     <svg {...p}><path d="M12 3v18M5 21h14M6 8l-3 6a3 3 0 0 0 6 0l-3-6zM18 8l-3 6a3 3 0 0 0 6 0l-3-6zM8 5h8"/></svg>,
    shield:    <svg {...p}><path d="M12 2L4 5v7c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V5l-8-3z"/><path d="M9 12l2 2 4-4"/></svg>,
    chart:     <svg {...p}><path d="M3 3v18h18"/><path d="M7 14l3-3 3 3 5-6"/></svg>,
    alert:     <svg {...p}><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.7L2 18a2 2 0 0 0 1.7 3h16.6a2 2 0 0 0 1.7-3L13.7 3.7a2 2 0 0 0-3.4 0z"/></svg>,
    truck:     <svg {...p}><path d="M1 7h13v10H1zM14 10h4l3 3v4h-7"/><circle cx="5.5" cy="17.5" r="2"/><circle cx="17.5" cy="17.5" r="2"/></svg>,
    camera:    <svg {...p}><path d="M3 7h4l2-3h6l2 3h4v13H3z"/><circle cx="12" cy="13" r="4"/></svg>,
    doc:       <svg {...p}><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M8 13h8M8 17h5"/></svg>,
    card:      <svg {...p}><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20M6 15h4"/></svg>,
    plug:      <svg {...p}><path d="M9 2v6M15 2v6M5 8h14v4a7 7 0 0 1-14 0zM12 19v3"/></svg>,
    pie:       <svg {...p}><path d="M21 12A9 9 0 1 1 12 3v9z"/><path d="M21 12a9 9 0 0 0-9-9v9h9z"/></svg>,
    inbox:     <svg {...p}><path d="M22 12h-6l-2 3h-4l-2-3H2"/><path d="M5 4h14l3 8v6a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-6l3-8z"/></svg>,
    compare:   <svg {...p}><path d="M4 5h6M4 12h6M4 19h6M14 5h6M14 12h6M14 19h6"/></svg>,
    factory:   <svg {...p}><path d="M2 20V10l5 3V10l5 3V10l5 3v7zM2 20h20"/><path d="M6 17h2M11 17h2M16 17h2"/></svg>,
    invoice:   <svg {...p}><path d="M4 2h12l4 4v16H4z"/><path d="M16 2v4h4M8 10h8M8 14h8M8 18h5"/></svg>,
    mic:       <svg {...p}><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>,
    pin:       <svg {...p}><path d="M12 22s7-7 7-13a7 7 0 0 0-14 0c0 6 7 13 7 13z"/><circle cx="12" cy="9" r="2.5"/></svg>,
    users:     <svg {...p}><circle cx="9" cy="8" r="3"/><path d="M3 20c0-3 3-5 6-5s6 2 6 5M17 11a3 3 0 1 0 0-6M21 20c0-2-2-4-4-4"/></svg>,
    tree:      <svg {...p}><rect x="3" y="4" width="6" height="4" rx="1"/><rect x="15" y="4" width="6" height="4" rx="1"/><rect x="15" y="16" width="6" height="4" rx="1"/><path d="M6 8v4h12M12 12v4h3M12 16v4h3"/></svg>,
    book:      <svg {...p}><path d="M4 4h10a4 4 0 0 1 4 4v12H8a4 4 0 0 1-4-4z"/><path d="M4 16a4 4 0 0 1 4-4h10"/></svg>,
    clock:     <svg {...p}><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>,
    lang:      <svg {...p}><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>,
    shieldok:  <svg {...p}><path d="M12 2L4 5v7c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V5l-8-3z"/></svg>,
    send:      <svg {...p}><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
  };
  return icons[name] || null;
};
