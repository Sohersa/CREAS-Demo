/* global React */
// Mock data & shared state for the Playground

const PG_SITES = [
  { id:'sierra', name:'Torre Sierra · Zapopan', code:'SRR-01', budget:48_000_000, spent:31_240_000, phase:'Estructura', residente:'Luis Ramírez' },
  { id:'puerto', name:'Residencial Puerto Alto · GDL', code:'PTA-02', budget:22_500_000, spent:9_870_000, phase:'Cimentación', residente:'Carmen Vega' },
  { id:'norte', name:'Centro Logístico Norte · Tlaj', code:'CLN-03', budget:67_000_000, spent:52_100_000, phase:'Acabados', residente:'Pedro González' }
];

const PG_SUPPLIERS = [
  { id:'cmx', name:'Cemex Distribuidor', rfc:'CMX•950131•AB7', color:'#0051B5', rating:4.8, otd:94, leadH:14, cats:['Cemento','Concreto','Agregados'], city:'Monterrey', exclusive:false },
  { id:'hnk', name:'Holcim Apasco', rfc:'HOL•810412•2Z9', color:'#E40613', rating:4.7, otd:92, leadH:18, cats:['Cemento','Mortero'], city:'GDL', exclusive:false },
  { id:'fxr', name:'Ferrepro S.A.', rfc:'FPR•020815•R34', color:'#0A2540', rating:4.6, otd:88, leadH:22, cats:['Varilla','Acero','Ferretería'], city:'GDL', exclusive:false },
  { id:'acs', name:'Aceros del Occidente', rfc:'AOC•130607•M81', color:'#FF7A45', rating:4.4, otd:85, leadH:26, cats:['Varilla','Alambrón'], city:'Zapopan', exclusive:true },
  { id:'grv', name:'Grava Express', rfc:'GEX•180919•H22', color:'#8AB800', rating:4.3, otd:90, leadH:8, cats:['Agregados','Arena','Grava'], city:'Tlaj', exclusive:false },
  { id:'cnc', name:'Concretos Rápido', rfc:'CNR•990220•P45', color:'#635BFF', rating:4.9, otd:98, leadH:4, cats:['Concreto premezclado'], city:'GDL', exclusive:false },
  { id:'mtl', name:'Materiales del Sur', rfc:'MTS•070515•K19', color:'#00D4FF', rating:4.2, otd:82, leadH:30, cats:['Block','Tabique','Cerámica'], city:'Tlaquepaque', exclusive:false },
  { id:'frr', name:'Ferrecentro Jalisco', rfc:'FCJ•110302•Q88', color:'#FFB84D', rating:4.5, otd:87, leadH:20, cats:['Ferretería','Herramienta'], city:'GDL', exclusive:false }
];

const PG_INITIAL_ORDERS = [
  { id:'OY-8421', site:'sierra', item:'Cemento CPC 30R', qty:50, unit:'saco 50kg', winner:'cmx', total:14268, status:'transito', createdAt:'Hoy 09:12', eta:'Hoy 15:30', progress:62, po:'PO-8421', cfdi:null, paid:false },
  { id:'OY-8420', site:'norte', item:'Varilla del 3/8"', qty:2, unit:'ton', winner:'acs', total:54800, status:'aprobada', createdAt:'Hoy 08:47', eta:'Mañana 11:00', progress:15, po:'PO-8420', cfdi:null, paid:false },
  { id:'OY-8418', site:'puerto', item:'Grava 3/4"', qty:18, unit:'m³', winner:'grv', total:9200, status:'entregada', createdAt:'Ayer 14:30', eta:'Ayer 17:00', progress:100, po:'PO-8418', cfdi:'A-3821', paid:true },
  { id:'OY-8415', site:'sierra', item:'Concreto premezclado f\'c=250', qty:30, unit:'m³', winner:'cnc', total:98700, status:'facturada', createdAt:'Ayer 10:15', eta:'Ayer 07:00', progress:100, po:'PO-8415', cfdi:'A-3820', paid:false },
  { id:'OY-8412', site:'norte', item:'Block pesado 15x20x40', qty:800, unit:'pza', winner:'mtl', total:17600, status:'pagada', createdAt:'2 días', eta:'Lun 09:00', progress:100, po:'PO-8412', cfdi:'A-3819', paid:true },
  { id:'OY-8422', site:'puerto', item:'Alambrón recocido', qty:300, unit:'kg', winner:null, total:0, status:'cotizando', createdAt:'Ahora', eta:'—', progress:0, po:null, cfdi:null, paid:false }
];

const PG_ALERTS = [
  { id:'a1', lvl:'warn', t:'Cemento CPC 30R subió 7% esta semana', d:'Cemex, Monterrey · promedio vs. 30d: +$18/saco', ago:'hace 2h' },
  { id:'a2', lvl:'info', t:'3 proveedores respondieron a OY-8422', d:'Alambrón · mejor oferta $28/kg · 12% bajo lista', ago:'hace 8m' },
  { id:'a3', lvl:'ok', t:'Pedido OY-8418 entregado sin incidentes', d:'Foto + firma registradas · CFDI timbrado automático', ago:'ayer' },
  { id:'a4', lvl:'warn', t:'Presupuesto CLN-03 al 78% (81% de avance de obra)', d:'Desviación: -3 puntos · ritmo sano', ago:'hoy 6am' }
];

// Supplier quotes for a given item (used by quote module)
function pgGenerateQuotes(item, qty) {
  const base = {
    'Cemento CPC 30R': 285,
    'Varilla del 3/8"': 27000,
    'Grava 3/4"': 510,
    'Concreto premezclado f\'c=250': 3290,
    'Alambrón recocido': 32,
    'Block pesado 15x20x40': 22,
    'Tabique rojo': 4.2,
    'Arena fina': 320
  };
  const b = base[item] || 100;
  return PG_SUPPLIERS.slice(0, 6).map((s, i) => {
    const jitter = (Math.sin(i * 1.7 + item.length) * 0.08);
    const price = Math.round(b * (1 + jitter - 0.04) * qty);
    return { supplier: s, unitPrice: Math.round(b * (1 + jitter - 0.04)), total: price, eta: s.leadH, rating: s.rating, otd: s.otd, distance: 3 + i * 4 + Math.floor(Math.random()*3) };
  }).sort((a, b) => a.total - b.total);
}

window.PG_SITES = PG_SITES;
window.PG_SUPPLIERS = PG_SUPPLIERS;
window.PG_INITIAL_ORDERS = PG_INITIAL_ORDERS;
window.PG_ALERTS = PG_ALERTS;
window.pgGenerateQuotes = pgGenerateQuotes;

// Translation helper
window.pgT = (lang, es, en) => lang === 'es' ? es : en;

// Currency
window.pgMoney = (n) => '$' + Math.round(n).toLocaleString('en-US');
