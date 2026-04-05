
/* ─── State ─── */
let currentUser = null;  // {rol, id, nombre, telefono}
let currentView = null;
let ordersCache = [];
let cart = JSON.parse(localStorage.getItem('obraya_cart') || '[]');
let activePedidoId = null;
let activePresupuestoId = null;

const STATUS_LABELS = {
  confirmada: 'Confirmada',
  preparando: 'Preparando',
  en_transito: 'En transito',
  en_obra: 'En obra',
  entregada: 'Entregada',
  cancelada: 'Cancelada',
  con_incidencia: 'Con incidencia'
};

const NEXT_STATUS = {
  confirmada: 'preparando',
  preparando: 'en_transito',
  en_transito: 'en_obra',
  en_obra: 'entregada',
};

const NEXT_STATUS_LABEL = {
  confirmada: 'Iniciar preparacion',
  preparando: 'Marcar en transito',
  en_transito: 'Registrar llegada a obra',
  en_obra: 'Confirmar entrega',
};

/* ─── SVG Icons ─── */
const ICONS = {
  orders: '<svg viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>',
  history: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
  cost: '<svg viewBox="0 0 24 24"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 000 7h5a3.5 3.5 0 010 7H6"/></svg>',
  ratings: '<svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
  metrics: '<svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
  revenue: '<svg viewBox="0 0 24 24"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>',
  incoming: '<svg viewBox="0 0 24 24"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z"/></svg>',
  cart: '<svg viewBox="0 0 24 24"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/></svg>',
};

/* ─── API helper ─── */
async function api(path, opts = {}) {
  const url = '/portal' + path;
  console.log('[API]', opts.method || 'GET', url);
  const o = { headers: { 'Content-Type': 'application/json' }, ...opts };
  if (o.body && typeof o.body === 'object') {
    console.log('[API] body:', JSON.stringify(o.body));
    o.body = JSON.stringify(o.body);
  }
  const res = await fetch(url, o);
  const data = await res.json();
  console.log('[API] response:', res.status, data);
  if (!res.ok) {
    throw new Error(data.detail || data.error || ('HTTP ' + res.status));
  }
  return data;
}

/* ─── Login ─── */
function cleanPhone(raw) {
  // Strip spaces, dashes, dots, parentheses, plus signs
  let p = raw.replace(/[^0-9]/g, '');
  // Strip common country codes if user typed them in the number field
  if (p.startsWith('52') && p.length >= 12) p = p.substring(2);
  if (p.startsWith('1') && p.length >= 11) p = p.substring(1);
  console.log('[Login] cleaned phone:', raw, '->', p);
  return p;
}

async function doLogin() {
  const rawPhone = document.getElementById('login-phone').value.trim();
  const countryCode = document.getElementById('login-country-code').value;
  const nombre = document.getElementById('login-name').value.trim();
  const empresa = document.getElementById('login-empresa').value.trim();
  const errEl = document.getElementById('login-error');
  errEl.textContent = '';
  if (!rawPhone) { errEl.textContent = 'Ingresa tu numero de WhatsApp.'; return; }
  if (!nombre) { errEl.textContent = 'Ingresa tu nombre.'; return; }
  const phone = cleanPhone(rawPhone);
  if (phone.length < 10) { errEl.textContent = 'El numero debe tener al menos 10 digitos.'; return; }
  // Build full international number (e.g. 523312345678)
  const fullPhone = countryCode.replace('+', '') + phone;
  const btn = document.getElementById('login-btn');
  btn.disabled = true;
  btn.textContent = 'Entrando...';
  try {
    const data = await api('/api/login', { method: 'POST', body: { telefono: fullPhone, nombre: nombre, empresa: empresa } });
    if (!data.rol) {
      errEl.textContent = 'Error al ingresar. Intenta de nuevo.';
      btn.disabled = false;
      btn.textContent = 'Entrar al Portal';
      return;
    }
    currentUser = data;
    showApp();
  } catch (e) {
    errEl.textContent = e.message || 'Error de conexion. Intenta de nuevo.';
    btn.disabled = false;
    btn.textContent = 'Entrar al Portal';
  }
}

document.getElementById('login-phone').addEventListener('keydown', e => {
  if (e.key === 'Enter') doLogin();
});

function doLogout() {
  currentUser = null;
  currentView = null;
  ordersCache = [];
  localStorage.removeItem('obraya_token');
  localStorage.removeItem('obraya_user');
  document.getElementById('app-shell').classList.add('hidden');
  document.getElementById('login-screen').classList.remove('hidden');
  document.getElementById('login-phone').value = '';
  document.getElementById('login-error').textContent = '';
  document.getElementById('login-btn').disabled = false;
  document.getElementById('login-btn').textContent = 'Ingresar';
}

/* ─── Auto-login from OAuth token ─── */
(async function checkOAuthSession() {
  const token = localStorage.getItem('obraya_token');
  const userJson = localStorage.getItem('obraya_user');
  if (!token) { console.log('[Portal] No OAuth token found'); return; }
  console.log('[Portal] Found OAuth token, attempting auto-login...');
  try {
    // Pre-fill form from stored user data as fallback
    if (userJson) {
      try {
        const u = JSON.parse(userJson);
        if (u.nombre) document.getElementById('login-name').value = u.nombre;
        if (u.empresa) document.getElementById('login-empresa').value = u.empresa;
      } catch(e) {}
    }
    const res = await fetch('/portal/api/login-token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token,
      },
    });
    const data = await res.json();
    console.log('[Portal] login-token response:', data);
    if (data.ok) {
      currentUser = { rol: data.rol, id: data.id, nombre: data.nombre, telefono: data.telefono };
      showApp();
    }
  } catch (e) {
    console.log('[Portal] OAuth auto-login failed:', e);
  }
})();

/* ─── App init ─── */
function showApp() {
  document.getElementById('login-screen').classList.add('hidden');
  document.getElementById('app-shell').classList.remove('hidden');
  document.getElementById('sidebar-name').textContent = currentUser.nombre;
  const roleEl = document.getElementById('sidebar-role');
  roleEl.textContent = currentUser.rol === 'cliente' ? 'Cliente' : 'Proveedor';
  roleEl.className = 'user-role role-' + currentUser.rol;
  buildNav();
}

function buildNav() {
  const nav = document.getElementById('sidebar-nav');
  let items = [];
  if (currentUser.rol === 'cliente') {
    items = [
      { id: 'nuevo-pedido', label: 'Nuevo Pedido', icon: ICONS.cart },
      { id: 'mis-pedidos', label: 'Mis Pedidos', icon: ICONS.incoming },
      { id: 'ordenes-activas', label: 'Ordenes activas', icon: ICONS.orders },
      { id: 'historial', label: 'Historial', icon: ICONS.history },
      { id: 'presupuestos', label: 'Presupuestos', icon: ICONS.cost },
      { id: 'costos', label: 'Resumen de costos', icon: ICONS.metrics },
      { id: 'aprobaciones', label: 'Aprobaciones', icon: ICONS.ratings },
      { id: 'mi-cuenta', label: 'Mi cuenta', icon: ICONS.revenue },
    ];
  } else {
    items = [
      { id: 'solicitudes-cot', label: 'Solicitudes', icon: ICONS.incoming },
      { id: 'mis-productos', label: 'Mis productos', icon: ICONS.orders },
      { id: 'ordenes-entrantes', label: 'Ordenes entrantes', icon: ICONS.cost },
      { id: 'historial-prov', label: 'Historial', icon: ICONS.history },
      { id: 'mis-calificaciones', label: 'Mis calificaciones', icon: ICONS.ratings },
      { id: 'ingresos', label: 'Ingresos', icon: ICONS.revenue },
      { id: 'desempeno', label: 'Desempeno', icon: ICONS.metrics },
      { id: 'mi-perfil', label: 'Mi perfil', icon: ICONS.cart },
    ];
  }
  nav.innerHTML = items.map(i => `
    <div class="nav-item" data-view="${i.id}" onclick="navigateTo('${i.id}')">
      <span class="nav-icon">${i.icon}</span>
      <span>${i.label}</span>
    </div>
  `).join('');
  navigateTo(items[0].id);
}

function navigateTo(view) {
  currentView = view;
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.view === view);
  });
  closeSidebar();
  renderView(view);
}

/* ─── Sidebar mobile ─── */
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  const bd = document.getElementById('sidebar-backdrop');
  sb.classList.toggle('open');
  bd.classList.toggle('show');
}
function closeSidebar() {
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebar-backdrop').classList.remove('show');
}

/* ─── Render views ─── */
async function renderView(view) {
  const main = document.getElementById('main-content');
  main.innerHTML = '<div class="loading-center"><span class="spinner"></span> Cargando...</div>';

  try {
    switch (view) {
      // Cliente
      case 'nuevo-pedido': await renderNuevoPedido(main); break;
      case 'mis-pedidos': await renderMisPedidos(main); break;
      case 'ordenes-activas': await renderClienteOrdenes(main, 'activas'); break;
      case 'historial': await renderClienteOrdenes(main, 'historial'); break;
      case 'presupuestos': await renderPresupuestos(main); break;
      case 'costos': await renderClienteCostos(main); break;
      case 'aprobaciones': await renderAprobaciones(main); break;
      case 'mi-cuenta': await renderMiCuenta(main); break;
      case 'carrito': await renderCarrito(main); break;
      case 'comparativa': await renderComparativa(main, activePedidoId); break;
      case 'presupuesto-detalle': await renderPresupuestoDetalle(main, activePresupuestoId); break;
      case 'crear-presupuesto': await renderCrearPresupuesto(main); break;
      // Proveedor
      case 'solicitudes-cot': await renderProveedorSolicitudes(main); break;
      case 'mis-productos': await renderProveedorProductos(main); break;
      case 'ordenes-entrantes': await renderProveedorOrdenes(main, 'activas'); break;
      case 'historial-prov': await renderProveedorOrdenes(main, 'historial'); break;
      case 'mis-calificaciones': await renderProveedorCalificaciones(main); break;
      case 'ingresos': await renderProveedorIngresos(main); break;
      case 'desempeno': await renderProveedorDesempeno(main); break;
      case 'mi-perfil': await renderProveedorPerfil(main); break;
    }
  } catch (e) {
    main.innerHTML = '<div class="empty-state"><p>Error al cargar datos. Intenta de nuevo.</p></div>';
    console.error(e);
  }
}

/* ─── Format helpers ─── */
function fmtMoney(n) { return '$' + (n || 0).toLocaleString('es-MX', { minimumFractionDigits: 2, maximumFractionDigits: 2 }); }
function fmtDate(iso) {
  if (!iso) return '---';
  const d = new Date(iso);
  return d.toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' });
}
function fmtDateTime(iso) {
  if (!iso) return '---';
  const d = new Date(iso);
  return d.toLocaleDateString('es-MX', { day: '2-digit', month: 'short' }) + ' ' +
         d.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
}
function statusBadge(s) { return `<span class="badge badge-${s}">${STATUS_LABELS[s] || s}</span>`; }
function paymentBadge(paid) {
  return paid
    ? '<span class="badge badge-pagado">Pagado</span>'
    : '<span class="badge badge-pendiente">Pendiente</span>';
}

function ratingDots(score, max = 5) {
  const filled = Math.round(score || 0);
  let html = '<span class="rating-dots">';
  for (let i = 0; i < max; i++) {
    html += `<span class="rating-dot ${i < filled ? 'filled' : ''}"></span>`;
  }
  html += '</span>';
  return html;
}

function metricBar(label, value, max, colorClass) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return `<div class="metric-bar-container">
    <div class="metric-bar-label"><span class="name">${label}</span><span class="val">${Math.round(pct)}%</span></div>
    <div class="metric-bar"><div class="metric-bar-fill ${colorClass}" style="width:${pct}%"></div></div>
  </div>`;
}

function itemsSummary(items) {
  if (!items || !items.length) return 'Sin items';
  if (items.length === 1) {
    return items[0].nombre || items[0].material || items[0].descripcion || '1 item';
  }
  const first = items[0].nombre || items[0].material || items[0].descripcion || 'item';
  return first + ' +' + (items.length - 1) + ' mas';
}

/* ─── CLIENT: Orders ─── */
async function renderClienteOrdenes(main, filter) {
  const data = await api(`/api/cliente/${currentUser.id}/ordenes?status=${filter}`);
  ordersCache = data;
  const isActive = filter === 'activas';
  const title = isActive ? 'Ordenes Activas' : 'Historial de Ordenes';
  const desc = isActive ? 'Ordenes en proceso de entrega' : 'Ordenes completadas y canceladas';

  let tableRows = '';
  if (data.length === 0) {
    tableRows = `<tr><td colspan="6"><div class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>
      <p>No hay ordenes ${isActive ? 'activas' : 'en el historial'}</p>
    </div></td></tr>`;
  } else {
    tableRows = data.map(o => `
      <tr onclick="openOrderDetail(${o.id}, 'cliente')">
        <td><strong>#${o.id}</strong></td>
        <td>${itemsSummary(o.items)}</td>
        <td>${o.proveedor_nombre}</td>
        <td>${fmtMoney(o.total)}</td>
        <td>${statusBadge(o.status)}</td>
        <td>${fmtDate(o.created_at)}</td>
      </tr>
    `).join('');
  }

  main.innerHTML = `
    <div class="page-header"><h2>${title}</h2><p class="page-desc">${desc}</p></div>
    <div class="card">
      <div class="card-header"><h3>${data.length} orden${data.length !== 1 ? 'es' : ''}</h3></div>
      <div class="card-body"><div class="table-scroll">
        <table>
          <thead><tr>
            <th>ID</th><th>Materiales</th><th>Proveedor</th><th>Total</th><th>Estado</th><th>Fecha</th>
          </tr></thead>
          <tbody>${tableRows}</tbody>
        </table>
      </div></div>
    </div>
  `;
}

/* ─── CLIENT: Costs ─── */
async function renderClienteCostos(main) {
  const data = await api(`/api/cliente/${currentUser.id}/resumen`);
  let breakdownHtml = '';
  const entries = Object.entries(data.desglose_material || {});
  if (entries.length > 0) {
    breakdownHtml = entries.map(([cat, amt]) => `
      <div class="detail-row"><span class="label">${cat}</span><span class="value">${fmtMoney(amt)}</span></div>
    `).join('');
  } else {
    breakdownHtml = '<p style="color:var(--gray-500);font-size:14px;padding:8px 0">Sin datos de desglose disponibles</p>';
  }

  main.innerHTML = `
    <div class="page-header"><h2>Resumen de Costos</h2><p class="page-desc">Tu gasto acumulado en materiales</p></div>
    <div class="stats-grid">
      <div class="stat-card accent-orange">
        <div class="stat-label">Total gastado</div>
        <div class="stat-value">${fmtMoney(data.total_gastado)}</div>
      </div>
      <div class="stat-card accent-blue">
        <div class="stat-label">Ordenes totales</div>
        <div class="stat-value">${data.total_ordenes}</div>
      </div>
      <div class="stat-card accent-green">
        <div class="stat-label">Promedio por orden</div>
        <div class="stat-value">${fmtMoney(data.promedio_por_orden)}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Activas / Completadas</div>
        <div class="stat-value">${data.ordenes_activas} / ${data.ordenes_completadas}</div>
      </div>
    </div>
    <div class="card">
      <div class="card-header"><h3>Desglose por tipo de material</h3></div>
      <div class="card-body padded">${breakdownHtml}</div>
    </div>
  `;
}

/* ─── CLIENT: Ratings ─── */
async function renderClienteCalificaciones(main) {
  const data = await api(`/api/cliente/${currentUser.id}/calificaciones`);
  let rows = '';
  if (data.length === 0) {
    rows = `<tr><td colspan="5"><div class="empty-state"><p>Aun no has calificado proveedores</p></div></td></tr>`;
  } else {
    rows = data.map(c => `
      <tr>
        <td>#${c.orden_id}</td>
        <td>${c.proveedor_nombre}</td>
        <td>${ratingDots(c.calificacion_total)} <span style="font-size:12px;color:var(--gray-500);margin-left:4px">${(c.calificacion_total || 0).toFixed(1)}</span></td>
        <td>${c.comentario_usuario || '---'}</td>
        <td>${fmtDate(c.created_at)}</td>
      </tr>
    `).join('');
  }

  main.innerHTML = `
    <div class="page-header"><h2>Calificaciones</h2><p class="page-desc">Calificaciones que has dado a proveedores</p></div>
    <div class="card">
      <div class="card-header"><h3>${data.length} calificacion${data.length !== 1 ? 'es' : ''}</h3></div>
      <div class="card-body"><div class="table-scroll">
        <table>
          <thead><tr><th>Orden</th><th>Proveedor</th><th>Calificacion</th><th>Comentario</th><th>Fecha</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div></div>
    </div>
  `;
}

/* ─── SUPPLIER: Orders ─── */
async function renderProveedorOrdenes(main, filter) {
  const data = await api(`/api/proveedor/${currentUser.id}/ordenes?status=${filter}`);
  ordersCache = data;
  const isActive = filter === 'activas';
  const title = isActive ? 'Ordenes Entrantes' : 'Historial de Ordenes';
  const desc = isActive ? 'Ordenes asignadas pendientes de entrega' : 'Ordenes completadas y canceladas';

  let tableRows = '';
  if (data.length === 0) {
    tableRows = `<tr><td colspan="7"><div class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 002 2h16a2 2 0 002-2v-6l-3.45-6.89A2 2 0 0016.76 4H7.24a2 2 0 00-1.79 1.11z"/></svg>
      <p>No hay ordenes ${isActive ? 'pendientes' : 'en el historial'}</p>
    </div></td></tr>`;
  } else {
    tableRows = data.map(o => {
      const nextAction = NEXT_STATUS[o.status]
        ? `<button class="btn-action btn-sm" onclick="event.stopPropagation();advanceOrder(${o.id},'${NEXT_STATUS[o.status]}',this)">${NEXT_STATUS_LABEL[o.status]}</button>`
        : '';
      return `<tr onclick="openOrderDetail(${o.id}, 'proveedor')">
        <td><strong>#${o.id}</strong></td>
        <td>${itemsSummary(o.items)}</td>
        <td>${o.cliente_nombre}</td>
        <td>${o.direccion_entrega || o.municipio_entrega || '---'}</td>
        <td>${fmtMoney(o.total)}</td>
        <td>${statusBadge(o.status)}</td>
        <td>${nextAction}</td>
      </tr>`;
    }).join('');
  }

  main.innerHTML = `
    <div class="page-header"><h2>${title}</h2><p class="page-desc">${desc}</p></div>
    <div class="card">
      <div class="card-header"><h3>${data.length} orden${data.length !== 1 ? 'es' : ''}</h3></div>
      <div class="card-body"><div class="table-scroll">
        <table>
          <thead><tr>
            <th>ID</th><th>Materiales</th><th>Cliente</th><th>Destino</th><th>Total</th><th>Estado</th><th>Accion</th>
          </tr></thead>
          <tbody>${tableRows}</tbody>
        </table>
      </div></div>
    </div>
  `;
}

/* ─── SUPPLIER: Advance order ─── */
async function advanceOrder(ordenId, newStatus, btnEl) {
  // If moving to en_transito, show transport form
  if (newStatus === 'en_transito') {
    openTransportForm(ordenId);
    return;
  }
  if (btnEl) { btnEl.disabled = true; btnEl.textContent = 'Actualizando...'; }
  const res = await api(`/api/proveedor/${currentUser.id}/ordenes/${ordenId}/status`, {
    method: 'POST',
    body: { status: newStatus }
  });
  if (res.ok) {
    renderView(currentView);
  } else {
    alert(res.error || 'Error al actualizar');
    if (btnEl) { btnEl.disabled = false; btnEl.textContent = NEXT_STATUS_LABEL[newStatus] || 'Avanzar'; }
  }
}

function openTransportForm(ordenId) {
  const overlay = document.getElementById('detail-overlay');
  const panel = document.getElementById('detail-panel');
  overlay.classList.remove('hidden');
  panel.innerHTML = `
    <div class="detail-header">
      <h3>Datos de Transporte - Orden #${ordenId}</h3>
      <button class="detail-close" onclick="closeDetail()">&times;</button>
    </div>
    <div class="detail-body">
      <div class="detail-section">
        <h4>Informacion del transporte</h4>
        <p style="font-size:14px;color:var(--gray-500);margin-bottom:16px">Ingresa los datos del vehiculo y chofer para la entrega.</p>
        <div class="transport-form">
          <div class="form-row">
            <div class="form-group"><label>Nombre del chofer</label><input id="tf-chofer" placeholder="Nombre completo"></div>
            <div class="form-group"><label>Telefono del chofer</label><input id="tf-tel" placeholder="Telefono"></div>
          </div>
          <div class="form-row">
            <div class="form-group"><label>Placas del vehiculo</label><input id="tf-placas" placeholder="ABC-123"></div>
            <div class="form-group">
              <label>Tipo de vehiculo</label>
              <select id="tf-tipo">
                <option value="">Seleccionar...</option>
                <option value="camioneta">Camioneta</option>
                <option value="torton">Torton</option>
                <option value="trailer">Trailer</option>
                <option value="olla">Olla</option>
                <option value="otro">Otro</option>
              </select>
            </div>
          </div>
          <button class="btn-action" onclick="submitTransport(${ordenId})" id="tf-submit">Confirmar y marcar en transito</button>
        </div>
      </div>
    </div>
  `;
}

async function submitTransport(ordenId) {
  const btn = document.getElementById('tf-submit');
  btn.disabled = true; btn.textContent = 'Enviando...';
  const body = {
    status: 'en_transito',
    nombre_chofer: document.getElementById('tf-chofer').value,
    telefono_chofer: document.getElementById('tf-tel').value,
    placas_vehiculo: document.getElementById('tf-placas').value,
    tipo_vehiculo: document.getElementById('tf-tipo').value,
  };
  const res = await api(`/api/proveedor/${currentUser.id}/ordenes/${ordenId}/status`, {
    method: 'POST', body
  });
  if (res.ok) {
    closeDetail();
    renderView(currentView);
  } else {
    alert(res.error || 'Error');
    btn.disabled = false; btn.textContent = 'Confirmar y marcar en transito';
  }
}

/* ─── SUPPLIER: Ratings ─── */
async function renderProveedorCalificaciones(main) {
  const data = await api(`/api/proveedor/${currentUser.id}/calificaciones`);
  let avg = 0;
  if (data.length > 0) avg = data.reduce((s, c) => s + (c.calificacion_total || 0), 0) / data.length;

  let rows = '';
  if (data.length === 0) {
    rows = `<tr><td colspan="6"><div class="empty-state"><p>Aun no tienes calificaciones</p></div></td></tr>`;
  } else {
    rows = data.map(c => `
      <tr>
        <td>#${c.orden_id}</td>
        <td>${ratingDots(c.puntualidad)} ${(c.puntualidad||0).toFixed(1)}</td>
        <td>${ratingDots(c.cantidad_correcta)} ${(c.cantidad_correcta||0).toFixed(1)}</td>
        <td>${ratingDots(c.especificacion_correcta)} ${(c.especificacion_correcta||0).toFixed(1)}</td>
        <td>${ratingDots(c.calificacion_total)} <strong>${(c.calificacion_total||0).toFixed(1)}</strong></td>
        <td>${fmtDate(c.created_at)}</td>
      </tr>
    `).join('');
  }

  main.innerHTML = `
    <div class="page-header"><h2>Mis Calificaciones</h2><p class="page-desc">Como te califican tus clientes</p></div>
    <div class="stats-grid">
      <div class="stat-card accent-orange">
        <div class="stat-label">Calificacion promedio</div>
        <div class="stat-value">${avg.toFixed(1)}</div>
        <div class="stat-sub">${ratingDots(avg)}</div>
      </div>
      <div class="stat-card accent-blue">
        <div class="stat-label">Total de calificaciones</div>
        <div class="stat-value">${data.length}</div>
      </div>
    </div>
    <div class="card">
      <div class="card-header"><h3>Detalle por orden</h3></div>
      <div class="card-body"><div class="table-scroll">
        <table>
          <thead><tr><th>Orden</th><th>Puntualidad</th><th>Cantidad</th><th>Especificacion</th><th>Total</th><th>Fecha</th></tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div></div>
    </div>
  `;
}

/* ─── SUPPLIER: Revenue ─── */
async function renderProveedorIngresos(main) {
  const data = await api(`/api/proveedor/${currentUser.id}/metricas`);
  main.innerHTML = `
    <div class="page-header"><h2>Ingresos</h2><p class="page-desc">Resumen financiero de tus ordenes</p></div>
    <div class="stats-grid">
      <div class="stat-card accent-green">
        <div class="stat-label">Ingresos totales</div>
        <div class="stat-value">${fmtMoney(data.ingresos_total)}</div>
        <div class="stat-sub">${data.ordenes_completadas} ordenes completadas</div>
      </div>
      <div class="stat-card accent-orange">
        <div class="stat-label">Pendiente de cobro</div>
        <div class="stat-value">${fmtMoney(data.ingresos_pendiente)}</div>
        <div class="stat-sub">${data.ordenes_activas} ordenes activas</div>
      </div>
      <div class="stat-card accent-blue">
        <div class="stat-label">Total ordenes</div>
        <div class="stat-value">${data.total_ordenes}</div>
      </div>
    </div>
  `;
}

/* ─── SUPPLIER: Performance ─── */
async function renderProveedorDesempeno(main) {
  const data = await api(`/api/proveedor/${currentUser.id}/metricas`);
  main.innerHTML = `
    <div class="page-header"><h2>Desempeno</h2><p class="page-desc">Metricas de cumplimiento y calidad</p></div>
    <div class="stats-grid">
      <div class="stat-card accent-green">
        <div class="stat-label">Calificacion general</div>
        <div class="stat-value">${(data.calificacion || 0).toFixed(1)}</div>
        <div class="stat-sub">${ratingDots(data.calificacion)}</div>
      </div>
      <div class="stat-card accent-blue">
        <div class="stat-label">Puntualidad</div>
        <div class="stat-value">${data.puntualidad_porcentaje}%</div>
      </div>
      <div class="stat-card accent-red">
        <div class="stat-label">Incidencias totales</div>
        <div class="stat-value">${data.total_incidencias}</div>
      </div>
    </div>
    <div class="card">
      <div class="card-header"><h3>Metricas detalladas</h3></div>
      <div class="card-body padded">
        ${metricBar('Puntualidad en entregas', data.tasa_puntualidad, 1, 'green')}
        ${metricBar('Cantidad correcta', data.tasa_cantidad_correcta, 1, 'blue')}
        ${metricBar('Especificacion correcta', data.tasa_especificacion_correcta, 1, 'orange')}
      </div>
    </div>
  `;
}

/* ─── Order Detail ─── */
async function openOrderDetail(ordenId, rol) {
  const overlay = document.getElementById('detail-overlay');
  const panel = document.getElementById('detail-panel');
  overlay.classList.remove('hidden');
  panel.innerHTML = '<div class="loading-center"><span class="spinner"></span> Cargando...</div>';

  const order = ordersCache.find(o => o.id === ordenId);
  const timeline = await api(`/api/orden/${ordenId}/timeline`);

  const isPaid = order.pagado === true;
  const paymentStatus = isPaid ? 'Pagado' : 'Pendiente';
  const paymentBadgeClass = isPaid ? 'pagado' : 'pendiente';

  // Cost breakdown
  const subtotal = (order.total || 0) / 1.02;  // Remove 2% commission
  const commission = (order.total || 0) - subtotal;

  // Build items table
  let itemsHtml = '';
  if (order.items && order.items.length > 0) {
    itemsHtml = '<table style="margin-bottom:0"><thead><tr><th>Material</th><th>Cantidad</th><th>Precio</th></tr></thead><tbody>';
    for (const item of order.items) {
      const name = item.nombre || item.material || item.descripcion || '---';
      const qty = item.cantidad ? (item.cantidad + ' ' + (item.unidad || '')) : '---';
      const price = item.precio_unitario ? fmtMoney(item.precio_unitario) : (item.subtotal ? fmtMoney(item.subtotal) : '---');
      itemsHtml += `<tr style="cursor:default"><td>${name}</td><td>${qty}</td><td>${price}</td></tr>`;
    }
    itemsHtml += '</tbody></table>';
  }

  // Timeline HTML
  let timelineHtml = '<div class="timeline">';
  const statusOrder = ['confirmada', 'preparando', 'en_transito', 'en_obra', 'entregada'];
  const currentIdx = statusOrder.indexOf(order.status);
  for (const step of timeline.steps) {
    const stepIdx = statusOrder.indexOf(step.status);
    let dotClass = '';
    if (step.completed) dotClass = 'completed';
    else if (stepIdx === currentIdx + 1) dotClass = '';  // next step
    if (step.status === order.status && !step.completed) dotClass = 'current';
    if (step.status === order.status && step.completed) dotClass = 'completed';
    // If current status, mark as current (pulsing)
    if (step.status === order.status && order.status !== 'entregada') dotClass = 'current';

    const labelClass = step.completed || step.status === order.status ? '' : 'pending';
    timelineHtml += `
      <div class="timeline-step">
        <div class="timeline-dot ${dotClass}"></div>
        <div class="timeline-label ${labelClass}">${step.label}</div>
        <div class="timeline-time">${fmtDateTime(step.timestamp)}</div>
      </div>
    `;
  }
  timelineHtml += '</div>';

  // Supplier action (for supplier view)
  let actionHtml = '';
  if (rol === 'proveedor' && NEXT_STATUS[order.status]) {
    if (NEXT_STATUS[order.status] === 'en_transito') {
      actionHtml = `<div class="detail-section"><h4>Accion</h4>
        <button class="btn-action" onclick="closeDetail();openTransportForm(${order.id})">${NEXT_STATUS_LABEL[order.status]}</button>
      </div>`;
    } else {
      actionHtml = `<div class="detail-section"><h4>Accion</h4>
        <button class="btn-action" onclick="closeDetail();advanceOrder(${order.id},'${NEXT_STATUS[order.status]}',null)">${NEXT_STATUS_LABEL[order.status]}</button>
      </div>`;
    }
  }

  // Transport info
  let transportHtml = '';
  if (order.nombre_chofer || order.telefono_chofer || order.placas_vehiculo) {
    transportHtml = `<div class="detail-section"><h4>Transporte</h4>
      <div class="detail-row"><span class="label">Chofer</span><span class="value">${order.nombre_chofer || '---'}</span></div>
      <div class="detail-row"><span class="label">Tel. chofer</span><span class="value">${order.telefono_chofer || '---'}</span></div>
      <div class="detail-row"><span class="label">Placas</span><span class="value">${order.placas_vehiculo || '---'}</span></div>
      <div class="detail-row"><span class="label">Vehiculo</span><span class="value">${order.tipo_vehiculo || '---'}</span></div>
    </div>`;
  }

  panel.innerHTML = `
    <div class="detail-header">
      <h3>Orden #${order.id}</h3>
      <button class="detail-close" onclick="closeDetail()">&times;</button>
    </div>
    <div class="detail-body">
      <div class="detail-section">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px">
          ${statusBadge(order.status)}
          <span class="badge badge-${paymentBadgeClass}">${paymentStatus}</span>
        </div>
      </div>

      <div class="detail-section">
        <h4>Progreso de entrega</h4>
        ${timelineHtml}
      </div>

      ${actionHtml}

      <div class="detail-section">
        <h4>Materiales</h4>
        ${itemsHtml || '<p style="color:var(--gray-500);font-size:14px">Sin detalle de items</p>'}
      </div>

      <div class="detail-section">
        <h4>Informacion de entrega</h4>
        <div class="detail-row"><span class="label">Direccion</span><span class="value">${order.direccion_entrega || '---'}</span></div>
        <div class="detail-row"><span class="label">Municipio</span><span class="value">${order.municipio_entrega || '---'}</span></div>
        <div class="detail-row"><span class="label">Entrega prometida</span><span class="value">${fmtDateTime(order.fecha_entrega_prometida)}</span></div>
        <div class="detail-row"><span class="label">${rol === 'cliente' ? 'Proveedor' : 'Cliente'}</span><span class="value">${rol === 'cliente' ? (order.proveedor_nombre || '---') : (order.cliente_nombre || '---')}</span></div>
      </div>

      ${transportHtml}

      <div class="detail-section">
        <h4>Pago</h4>
        <div class="payment-breakdown">
          <div class="payment-line"><span>Subtotal materiales</span><span>${fmtMoney(subtotal)}</span></div>
          <div class="payment-line"><span>Comision ObraYa (2%)</span><span>${fmtMoney(commission)}</span></div>
          <div class="payment-line total"><span>Total</span><span>${fmtMoney(order.total)}</span></div>
        </div>
        ${!isPaid && rol === 'cliente' ? '<button class="btn-pay" onclick="pagarOrden(' + order.id + ')">Pagar con Stripe</button>' : ''}
        ${isPaid ? '<p style="color:var(--green);font-size:14px;margin-top:8px">&#10003; Pago completado</p>' : ''}
      </div>
    </div>
  `;
}

/* ═══ FASE 1: NUEVO PEDIDO — Catalogo + Carrito ═══ */

function saveCart() { localStorage.setItem('obraya_cart', JSON.stringify(cart)); }

function addToCart(item) {
  const existing = cart.find(c => c.catalogo_id === item.id);
  if (existing) { existing.cantidad += 1; }
  else { cart.push({ catalogo_id: item.id, nombre: item.nombre, categoria: item.categoria, unidad: item.unidad, precio_referencia: item.precio_referencia, cantidad: 1 }); }
  saveCart();
  renderView('nuevo-pedido');
}

function removeFromCart(idx) { cart.splice(idx, 1); saveCart(); }
function updateCartQty(idx, val) { cart[idx].cantidad = Math.max(1, parseInt(val) || 1); saveCart(); }

async function renderNuevoPedido(main) {
  const cats = await api('/api/catalogo/categorias');
  const searchQ = document.getElementById('cat-search')?.value || '';
  const activeCat = window._activeCat || '';
  let url = '/api/catalogo?q=' + encodeURIComponent(searchQ);
  if (activeCat) url += '&categoria=' + encodeURIComponent(activeCat);
  const items = await api(url);

  const cartCount = cart.reduce((s, c) => s + c.cantidad, 0);

  main.innerHTML = '<div class="page-header"><h2>Nuevo Pedido</h2><p class="subtitle">Busca materiales y agrega al carrito</p></div>' +
    '<div style="display:flex;gap:12px;margin-bottom:16px;flex-wrap:wrap;align-items:center">' +
      '<input type="text" id="cat-search" placeholder="Buscar material..." value="' + searchQ.replace(/"/g, '&quot;') + '" style="flex:1;min-width:200px;padding:10px 14px;border:1.5px solid var(--gray-300);border-radius:var(--radius);font-size:14px" onkeyup="if(event.key==='Enter'){window._activeCat='';renderView('nuevo-pedido')}">' +
      '<button onclick="navigateTo('carrito')" class="btn-primary" style="width:auto;padding:10px 20px;position:relative">Carrito (' + cartCount + ')</button>' +
    '</div>' +
    '<div style="display:flex;gap:8px;margin-bottom:16px;flex-wrap:wrap">' +
      '<button class="cat-btn' + (!activeCat ? ' active' : '') + '" onclick="window._activeCat='';renderView('nuevo-pedido')">Todos</button>' +
      cats.map(c => '<button class="cat-btn' + (activeCat === c ? ' active' : '') + '" onclick="window._activeCat='' + c + '';renderView('nuevo-pedido')">' + c + '</button>').join('') +
    '</div>' +
    '<div class="product-grid">' +
      items.map(i => {
        const inCart = cart.find(c => c.catalogo_id === i.id);
        return '<div class="product-card">' +
          '<div class="product-cat">' + i.categoria + '</div>' +
          '<div class="product-name">' + i.nombre + '</div>' +
          '<div class="product-unit">' + i.unidad + '</div>' +
          (i.precio_referencia ? '<div class="product-price">Ref: ' + fmtMoney(i.precio_referencia) + '</div>' : '') +
          (inCart ? '<button class="btn-added" disabled>En carrito (' + inCart.cantidad + ')</button>' :
            '<button class="btn-add" onclick='addToCart(' + JSON.stringify(i).replace(/'/g, "\'") + ')'>+ Agregar</button>') +
        '</div>';
      }).join('') +
      (items.length === 0 ? '<div class="empty-state"><p>No se encontraron productos</p></div>' : '') +
    '</div>';
}

async function renderCarrito(main) {
  if (cart.length === 0) {
    main.innerHTML = '<div class="page-header"><h2>Carrito</h2></div><div class="empty-state"><p>Tu carrito esta vacio.</p><button class="btn-primary" style="width:auto;padding:10px 20px;margin-top:12px" onclick="navigateTo('nuevo-pedido')">Buscar materiales</button></div>';
    return;
  }
  const subtotal = cart.reduce((s, c) => s + (c.precio_referencia || 0) * c.cantidad, 0);
  main.innerHTML = '<div class="page-header"><h2>Carrito</h2><p class="subtitle">' + cart.length + ' materiales</p></div>' +
    '<div class="card"><table class="data-table"><thead><tr><th>Material</th><th>Unidad</th><th>Cantidad</th><th>Ref. Precio</th><th></th></tr></thead><tbody>' +
    cart.map((c, i) =>
      '<tr><td>' + c.nombre + '</td><td>' + c.unidad + '</td>' +
      '<td><input type="number" min="1" value="' + c.cantidad + '" style="width:70px;padding:6px;border:1px solid var(--gray-300);border-radius:4px" onchange="updateCartQty(' + i + ',this.value);renderView('carrito')"></td>' +
      '<td>' + (c.precio_referencia ? fmtMoney(c.precio_referencia * c.cantidad) : '-') + '</td>' +
      '<td><button onclick="removeFromCart(' + i + ');renderView('carrito')" style="color:var(--red);background:none;border:none;font-size:18px;cursor:pointer">X</button></td></tr>'
    ).join('') +
    '</tbody></table>' +
    (subtotal > 0 ? '<div style="text-align:right;padding:12px;font-weight:600">Estimado: ' + fmtMoney(subtotal) + ' (precio final al cotizar)</div>' : '') +
    '</div>' +
    '<div class="card" style="margin-top:16px"><h3 style="margin-bottom:12px">Datos de entrega</h3>' +
      '<div class="form-group"><label>Direccion de entrega</label><input type="text" id="cart-direccion" placeholder="Ej. Calle 5 #123, Col. Centro, Guadalajara" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
      '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>Municipio</label><input type="text" id="cart-municipio" placeholder="Ej. Zapopan" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
      '<div class="form-group" style="flex:1"><label>Fecha de entrega</label><input type="date" id="cart-fecha" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div></div>' +
      '<button class="btn-primary" style="margin-top:12px" onclick="submitPedido()">Solicitar Cotizaciones</button>' +
    '</div>';
}

async function submitPedido() {
  const dir = document.getElementById('cart-direccion')?.value || '';
  const mun = document.getElementById('cart-municipio')?.value || '';
  const fecha = document.getElementById('cart-fecha')?.value || '';
  if (!dir) { alert('Ingresa la direccion de entrega'); return; }
  const body = { usuario_id: currentUser.id, items: cart, direccion_entrega: dir, municipio_entrega: mun, fecha_entrega: fecha };
  const data = await api('/api/pedido', { method: 'POST', body: body });
  if (data.ok) {
    cart = []; saveCart();
    if (data.cotizaciones_count > 0) { activePedidoId = data.pedido_id; navigateTo('comparativa'); }
    else { navigateTo('mis-pedidos'); }
  } else { alert(data.error || 'Error al crear pedido'); }
}

async function renderMisPedidos(main) {
  const data = await api('/api/mis-pedidos/' + currentUser.id);
  let rows = '';
  if (data.length === 0) {
    rows = '<tr><td colspan="5"><div class="empty-state"><p>No tienes pedidos en proceso</p></div></td></tr>';
  } else {
    rows = data.map(p =>
      '<tr style="cursor:pointer" onclick="activePedidoId=' + p.id + ';navigateTo('comparativa')">' +
      '<td>#' + p.id + '</td><td>' + (p.items_resumen || '-') + '</td><td>' + statusBadge(p.status) + '</td>' +
      '<td>' + p.cotizaciones + ' cotizaciones</td><td>' + fmtDate(p.created_at) + '</td></tr>'
    ).join('');
  }
  main.innerHTML = '<div class="page-header"><h2>Mis Pedidos en Proceso</h2><p class="subtitle">Pedidos esperando cotizaciones o seleccion</p></div>' +
    '<div class="card"><table class="data-table"><thead><tr><th>ID</th><th>Materiales</th><th>Status</th><th>Cotizaciones</th><th>Fecha</th></tr></thead><tbody>' + rows + '</tbody></table></div>';
}

async function renderComparativa(main, pedidoId) {
  if (!pedidoId) { navigateTo('mis-pedidos'); return; }
  const cotizaciones = await api('/api/pedido/' + pedidoId + '/cotizaciones');
  if (cotizaciones.length === 0) {
    main.innerHTML = '<div class="page-header"><h2>Comparativa - Pedido #' + pedidoId + '</h2></div><div class="empty-state"><p>Aun no hay cotizaciones disponibles. Espera a que los proveedores respondan.</p><button class="btn-primary" style="width:auto;padding:10px 20px;margin-top:12px" onclick="navigateTo('mis-pedidos')">Volver</button></div>';
    return;
  }
  const cards = cotizaciones.map((c, idx) => {
    const items = (c.items || []).map(it =>
      '<div style="display:flex;justify-content:space-between;padding:4px 0;font-size:13px"><span>' + (it.producto || it.nombre || '-') + ' x' + (it.cantidad || 1) + '</span><span>' + fmtMoney(it.subtotal || it.precio_unitario || 0) + '</span></div>'
    ).join('');
    return '<div class="cot-card">' +
      '<div class="cot-header"><span class="cot-rank">#' + (idx + 1) + '</span><span class="cot-name">' + c.proveedor_nombre + '</span><span class="cot-rating">' + (c.proveedor_calificacion || 0).toFixed(1) + '/5</span></div>' +
      '<div class="cot-items">' + items + '</div>' +
      '<div class="cot-totals">' +
        '<div style="display:flex;justify-content:space-between"><span>Subtotal</span><span>' + fmtMoney(c.subtotal) + '</span></div>' +
        '<div style="display:flex;justify-content:space-between"><span>Flete</span><span>' + (c.costo_flete > 0 ? fmtMoney(c.costo_flete) : 'Incluido') + '</span></div>' +
        '<div style="display:flex;justify-content:space-between;font-weight:700;font-size:16px;border-top:1px solid var(--gray-200);padding-top:8px;margin-top:4px"><span>Total</span><span>' + fmtMoney(c.total) + '</span></div>' +
      '</div>' +
      '<div style="padding:12px;font-size:13px;color:var(--gray-500)">Entrega: ' + (c.tiempo_entrega || 'Consultar') + '</div>' +
      '<button class="btn-primary" onclick="elegirProveedor(' + pedidoId + ',' + c.cotizacion_id + ')">Elegir este proveedor</button>' +
    '</div>';
  }).join('');
  main.innerHTML = '<div class="page-header"><h2>Comparativa de Precios</h2><p class="subtitle">Pedido #' + pedidoId + ' - ' + cotizaciones.length + ' opciones</p></div><div class="cot-grid">' + cards + '</div>';
}

async function elegirProveedor(pedidoId, cotizacionId) {
  if (!confirm('Confirmas este proveedor?')) return;
  const data = await api('/api/pedido/' + pedidoId + '/elegir', { method: 'POST', body: { cotizacion_id: cotizacionId, usuario_id: currentUser.id } });
  if (data.ok) { alert('Orden #' + data.orden_id + ' creada! Total: ' + fmtMoney(data.total)); navigateTo('ordenes-activas'); }
  else { alert(data.error || 'Error al crear orden'); }
}

/* ═══ FASE 2: PAGOS ═══ */

async function pagarOrden(ordenId) {
  const data = await api('/api/pagar/' + ordenId, { method: 'POST' });
  if (data.ok) { window.location.href = data.url; }
  else { alert(data.error || 'Error al crear sesion de pago'); }
}

/* ═══ FASE 3: PRESUPUESTOS ═══ */

async function renderPresupuestos(main) {
  const data = await api('/api/presupuestos/' + currentUser.id);
  let cards = '';
  if (data.length === 0) {
    cards = '<div class="empty-state"><p>No tienes presupuestos de obra</p></div>';
  } else {
    cards = data.map(p => {
      const pct = p.porcentaje_consumido || 0;
      const color = pct >= 80 ? 'var(--red)' : pct >= 50 ? 'var(--orange)' : 'var(--green)';
      return '<div class="card" style="cursor:pointer;margin-bottom:12px" onclick="activePresupuestoId=' + p.id + ';navigateTo('presupuesto-detalle')">' +
        '<h3>' + p.nombre_obra + '</h3><p style="color:var(--gray-500);font-size:13px">' + (p.direccion || '') + '</p>' +
        '<div style="margin-top:12px"><div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px"><span>Consumido: ' + pct.toFixed(1) + '%</span><span>' + fmtMoney(p.gastado_total || 0) + ' / ' + fmtMoney(p.presupuesto_total || 0) + '</span></div>' +
        '<div style="background:var(--gray-200);border-radius:4px;height:8px;overflow:hidden"><div style="width:' + Math.min(pct, 100) + '%;height:100%;background:' + color + ';border-radius:4px"></div></div></div>' +
      '</div>';
    }).join('');
  }
  main.innerHTML = '<div class="page-header" style="display:flex;justify-content:space-between;align-items:center"><div><h2>Presupuestos de Obra</h2><p class="subtitle">Control de costos por proyecto</p></div><button class="btn-primary" style="width:auto;padding:8px 16px" onclick="navigateTo('crear-presupuesto')">+ Nuevo</button></div>' + cards;
}

async function renderPresupuestoDetalle(main, presId) {
  if (!presId) { navigateTo('presupuestos'); return; }
  const data = await api('/api/presupuesto/' + presId);
  if (!data.ok) { main.innerHTML = '<div class="empty-state"><p>Presupuesto no encontrado</p></div>'; return; }
  const p = data.presupuesto;
  const rows = data.partidas.map(pt => {
    const pct = pt.porcentaje_consumido || 0;
    const color = pt.bloqueado ? 'var(--red)' : pct >= 80 ? 'var(--orange)' : pct >= 50 ? '#f39c12' : 'var(--green)';
    return '<tr' + (pt.bloqueado ? ' style="opacity:0.6"' : '') + '><td>' + pt.nombre_material + '</td><td>' + pt.categoria + '</td><td>' + pt.unidad + '</td>' +
      '<td>' + (pt.cantidad_consumida || 0) + ' / ' + pt.cantidad_presupuestada + '</td>' +
      '<td><div style="display:flex;align-items:center;gap:8px"><div style="flex:1;background:var(--gray-200);border-radius:3px;height:6px"><div style="width:' + Math.min(pct, 100) + '%;height:100%;background:' + color + ';border-radius:3px"></div></div><span style="font-size:12px;min-width:40px">' + pct.toFixed(0) + '%</span></div></td>' +
      '<td>' + fmtMoney(pt.monto_gastado || 0) + ' / ' + fmtMoney(pt.monto_presupuestado || 0) + '</td>' +
      '<td>' + (pt.bloqueado ? '<span style="color:var(--red);font-size:12px">Bloqueado</span>' : '<button class="btn-sm" onclick="registrarConsumo(' + presId + ',' + pt.id + ')">+ Consumo</button>') + '</td></tr>';
  }).join('');
  main.innerHTML = '<div class="page-header"><button onclick="navigateTo('presupuestos')" style="background:none;border:none;color:var(--blue);cursor:pointer;font-size:14px;margin-bottom:8px">< Volver</button><h2>' + p.nombre_obra + '</h2><p class="subtitle">' + fmtMoney(p.gastado_total || 0) + ' de ' + fmtMoney(p.presupuesto_total || 0) + ' (' + (p.porcentaje_consumido || 0).toFixed(1) + '%)</p></div>' +
    '<div class="card"><table class="data-table"><thead><tr><th>Material</th><th>Categoria</th><th>Unidad</th><th>Cantidad</th><th>Progreso</th><th>Monto</th><th></th></tr></thead><tbody>' + rows + '</tbody></table></div>';
}

async function registrarConsumo(presId, partidaId) {
  const cant = prompt('Cantidad consumida:');
  if (!cant || isNaN(cant)) return;
  const data = await api('/api/presupuesto/' + presId + '/partidas/' + partidaId + '/consumo', { method: 'PUT', body: { cantidad: parseFloat(cant) } });
  if (data.ok) { renderView('presupuesto-detalle'); }
  else { alert(data.error || 'Error'); }
}

async function renderCrearPresupuesto(main) {
  main.innerHTML = '<div class="page-header"><button onclick="navigateTo('presupuestos')" style="background:none;border:none;color:var(--blue);cursor:pointer;font-size:14px;margin-bottom:8px">< Volver</button><h2>Nuevo Presupuesto</h2></div>' +
    '<div class="card"><div class="form-group"><label>Nombre de la obra</label><input type="text" id="pres-nombre" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)" placeholder="Ej. Casa habitacion Zapopan"></div>' +
    '<div class="form-group"><label>Direccion</label><input type="text" id="pres-dir" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>Fecha inicio</label><input type="date" id="pres-inicio" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div class="form-group" style="flex:1"><label>Fecha fin estimada</label><input type="date" id="pres-fin" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div></div>' +
    '<div class="form-group"><label>Presupuesto total (MXN)</label><input type="number" id="pres-total" style="width:200px;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)" placeholder="0"></div>' +
    '<button class="btn-primary" style="margin-top:12px" onclick="submitPresupuesto()">Crear Presupuesto</button></div>';
}

async function submitPresupuesto() {
  const nombre = document.getElementById('pres-nombre')?.value;
  if (!nombre) { alert('Ingresa el nombre de la obra'); return; }
  const body = {
    usuario_id: currentUser.id,
    nombre_obra: nombre,
    direccion: document.getElementById('pres-dir')?.value || '',
    fecha_inicio: document.getElementById('pres-inicio')?.value || '',
    fecha_fin_estimada: document.getElementById('pres-fin')?.value || '',
    presupuesto_total: parseFloat(document.getElementById('pres-total')?.value) || 0,
    partidas: []
  };
  const data = await api('/api/presupuestos', { method: 'POST', body: body });
  if (data.ok) { activePresupuestoId = data.presupuesto_id; navigateTo('presupuesto-detalle'); }
  else { alert('Error al crear presupuesto'); }
}

/* ═══ FASE 4: APROBACIONES ═══ */

async function renderAprobaciones(main) {
  const data = await api('/api/aprobaciones/pendientes/' + currentUser.id);
  if (!data.es_aprobador) {
    main.innerHTML = '<div class="page-header"><h2>Aprobaciones</h2></div><div class="empty-state"><p>No eres aprobador en ninguna empresa. Contacta a tu administrador para obtener permisos.</p></div>';
    return;
  }
  if (data.pendientes.length === 0) {
    main.innerHTML = '<div class="page-header"><h2>Aprobaciones</h2></div><div class="empty-state"><p>No tienes aprobaciones pendientes</p></div>';
    return;
  }
  const cards = data.pendientes.map(a => {
    const items = (a.items || []).map(it => '<div style="font-size:13px">' + (it.producto || it.nombre || '-') + ' x' + (it.cantidad || 1) + '</div>').join('');
    return '<div class="card" style="margin-bottom:12px">' +
      '<div style="display:flex;justify-content:space-between;align-items:center"><h3>Orden #' + a.orden_id + '</h3><span style="font-size:20px;font-weight:700;color:var(--orange)">' + fmtMoney(a.monto) + '</span></div>' +
      '<p style="color:var(--gray-500);font-size:13px">Solicitado por: ' + a.solicitante + ' - ' + fmtDate(a.solicitada_at) + '</p>' +
      (a.direccion ? '<p style="font-size:13px;margin-top:4px">Entrega: ' + a.direccion + '</p>' : '') +
      '<div style="margin:8px 0">' + items + '</div>' +
      '<div style="display:flex;gap:8px;margin-top:12px"><button class="btn-primary" style="flex:1" onclick="aprobarSolicitud(' + a.id + ')">Aprobar</button><button style="flex:1;padding:10px;background:var(--red);color:#fff;border:none;border-radius:var(--radius);font-weight:600;cursor:pointer" onclick="rechazarSolicitud(' + a.id + ')">Rechazar</button></div>' +
    '</div>';
  }).join('');
  main.innerHTML = '<div class="page-header"><h2>Aprobaciones Pendientes</h2><p class="subtitle">' + data.pendientes.length + ' solicitudes</p></div>' + cards;
}

async function aprobarSolicitud(id) {
  if (!confirm('Aprobar esta compra?')) return;
  const data = await api('/api/aprobaciones/' + id + '/aprobar', { method: 'POST' });
  if (data.ok) { renderView('aprobaciones'); } else { alert(data.error || 'Error'); }
}

async function rechazarSolicitud(id) {
  const motivo = prompt('Motivo del rechazo (opcional):');
  const data = await api('/api/aprobaciones/' + id + '/rechazar', { method: 'POST', body: { motivo: motivo || '' } });
  if (data.ok) { renderView('aprobaciones'); } else { alert(data.error || 'Error'); }
}

/* ═══ FASE 5: PORTAL VENDEDOR ═══ */

async function renderProveedorProductos(main) {
  const data = await api('/api/proveedor/' + currentUser.id + '/productos');
  const rows = data.map(p =>
    '<tr><td>' + p.nombre + '</td><td>' + p.categoria + '</td><td>' + p.unidad + '</td>' +
    '<td><input type="number" value="' + p.precio_unitario + '" style="width:100px;padding:6px;border:1px solid var(--gray-300);border-radius:4px" onchange="updateProductPrice(' + p.id + ',this.value)"></td>' +
    '<td>' + p.disponibilidad + '</td>' +
    '<td>' + (p.activo ? '<span style="color:var(--green)">Activo</span>' : '<span style="color:var(--red)">Inactivo</span>') + '</td>' +
    '<td><button class="btn-sm" style="color:var(--red)" onclick="deleteProduct(' + p.id + ')">Eliminar</button></td></tr>'
  ).join('');
  main.innerHTML = '<div class="page-header" style="display:flex;justify-content:space-between;align-items:center"><div><h2>Mis Productos</h2><p class="subtitle">' + data.length + ' productos en tu catalogo</p></div><button class="btn-primary" style="width:auto;padding:8px 16px" onclick="renderAgregarProducto()">+ Agregar</button></div>' +
    '<div class="card"><table class="data-table"><thead><tr><th>Producto</th><th>Categoria</th><th>Unidad</th><th>Precio (MXN)</th><th>Disponibilidad</th><th>Status</th><th></th></tr></thead><tbody>' +
    (rows || '<tr><td colspan="7"><div class="empty-state"><p>No tienes productos registrados</p></div></td></tr>') +
    '</tbody></table></div>';
}

async function updateProductPrice(prodId, newPrice) {
  await api('/api/proveedor/' + currentUser.id + '/productos/' + prodId, { method: 'PUT', body: { precio_unitario: parseFloat(newPrice) } });
}

async function deleteProduct(prodId) {
  if (!confirm('Eliminar este producto?')) return;
  await api('/api/proveedor/' + currentUser.id + '/productos/' + prodId, { method: 'DELETE' });
  renderView('mis-productos');
}

async function renderAgregarProducto() {
  const main = document.getElementById('main-content');
  const cats = await api('/api/catalogo/categorias');
  main.innerHTML = '<div class="page-header"><button onclick="navigateTo('mis-productos')" style="background:none;border:none;color:var(--blue);cursor:pointer;font-size:14px;margin-bottom:8px">< Volver</button><h2>Agregar Producto</h2></div>' +
    '<div class="card">' +
    '<div class="form-group"><label>Nombre del producto</label><input type="text" id="prod-nombre" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)" placeholder="Ej. Concreto premezclado FC 250"></div>' +
    '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>Categoria</label><select id="prod-cat" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)">' + cats.map(c => '<option value="' + c + '">' + c + '</option>').join('') + '</select></div>' +
    '<div class="form-group" style="flex:1"><label>Unidad</label><select id="prod-unidad" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"><option>m3</option><option>pieza</option><option>kg</option><option>ton</option><option>bulto</option><option>cubeta</option><option>rollo</option><option>viaje</option></select></div></div>' +
    '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>Precio unitario (MXN)</label><input type="number" id="prod-precio" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)" placeholder="0"></div>' +
    '<div class="form-group" style="flex:1"><label>Disponibilidad</label><select id="prod-disp" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"><option value="inmediata">Inmediata</option><option value="24h">24 horas</option><option value="48h">48 horas</option><option value="sobre_pedido">Sobre pedido</option></select></div></div>' +
    '<button class="btn-primary" style="margin-top:12px" onclick="submitProducto()">Guardar Producto</button></div>';
}

async function submitProducto() {
  const body = {
    nombre: document.getElementById('prod-nombre')?.value || '',
    categoria: document.getElementById('prod-cat')?.value || '',
    unidad: document.getElementById('prod-unidad')?.value || '',
    precio_unitario: parseFloat(document.getElementById('prod-precio')?.value) || 0,
    disponibilidad: document.getElementById('prod-disp')?.value || 'inmediata',
  };
  if (!body.nombre || !body.precio_unitario) { alert('Completa nombre y precio'); return; }
  const data = await api('/api/proveedor/' + currentUser.id + '/productos', { method: 'POST', body: body });
  if (data.ok) { navigateTo('mis-productos'); }
  else { alert(data.error || 'Error al guardar'); }
}

async function renderProveedorSolicitudes(main) {
  const data = await api('/api/proveedor/' + currentUser.id + '/solicitudes');
  if (data.length === 0) {
    main.innerHTML = '<div class="page-header"><h2>Solicitudes de Cotizacion</h2></div><div class="empty-state"><p>No tienes solicitudes pendientes</p></div>';
    return;
  }
  const cards = data.map(s => {
    const items = (s.items || []).map(it => '<div style="font-size:13px;padding:2px 0">' + (it.producto || '-') + ' - ' + (it.cantidad || 1) + ' ' + (it.unidad || '') + '</div>').join('');
    return '<div class="card" style="margin-bottom:12px">' +
      '<div style="display:flex;justify-content:space-between;align-items:center"><h3>Pedido #' + s.pedido_id + '</h3>' + statusBadge(s.status) + '</div>' +
      '<p style="color:var(--gray-500);font-size:13px">Recibida: ' + fmtDateTime(s.enviada_at) + (s.recordatorios > 0 ? ' (' + s.recordatorios + ' recordatorios)' : '') + '</p>' +
      (s.direccion_entrega ? '<p style="font-size:13px;margin-top:4px">Entrega: ' + s.direccion_entrega + (s.fecha_entrega ? ' - ' + s.fecha_entrega : '') + '</p>' : '') +
      '<div style="margin:8px 0;padding:8px;background:var(--gray-50);border-radius:var(--radius)">' + items + '</div>' +
      '<div style="margin-top:12px;border-top:1px solid var(--gray-200);padding-top:12px"><h4 style="font-size:14px;margin-bottom:8px">Responder cotizacion</h4>' +
      '<div style="display:flex;gap:12px;flex-wrap:wrap">' +
        '<div class="form-group" style="flex:1;min-width:120px"><label>Precio total (MXN)</label><input type="number" id="sol-precio-' + s.id + '" style="width:100%;padding:8px;border:1px solid var(--gray-300);border-radius:4px" placeholder="0"></div>' +
        '<div class="form-group" style="flex:1;min-width:120px"><label>Tiempo entrega</label><input type="text" id="sol-tiempo-' + s.id + '" style="width:100%;padding:8px;border:1px solid var(--gray-300);border-radius:4px" placeholder="Ej. manana 7am"></div>' +
        '<div class="form-group" style="flex:1;min-width:120px"><label>Costo flete</label><input type="number" id="sol-flete-' + s.id + '" style="width:100%;padding:8px;border:1px solid var(--gray-300);border-radius:4px" placeholder="0" value="0"></div>' +
      '</div>' +
      '<div class="form-group"><label>Notas</label><input type="text" id="sol-notas-' + s.id + '" style="width:100%;padding:8px;border:1px solid var(--gray-300);border-radius:4px" placeholder="Condiciones, observaciones..."></div>' +
      '<button class="btn-primary" onclick="responderSolicitud(' + s.id + ')">Enviar Cotizacion</button></div>' +
    '</div>';
  }).join('');
  main.innerHTML = '<div class="page-header"><h2>Solicitudes de Cotizacion</h2><p class="subtitle">' + data.length + ' pendientes</p></div>' + cards;
}

async function responderSolicitud(solId) {
  const precio = parseFloat(document.getElementById('sol-precio-' + solId)?.value);
  if (!precio || precio <= 0) { alert('Ingresa el precio total'); return; }
  const body = {
    precio_total: precio,
    tiempo_entrega: document.getElementById('sol-tiempo-' + solId)?.value || '24h',
    costo_flete: parseFloat(document.getElementById('sol-flete-' + solId)?.value) || 0,
    notas: document.getElementById('sol-notas-' + solId)?.value || '',
  };
  const data = await api('/api/proveedor/' + currentUser.id + '/solicitudes/' + solId + '/responder', { method: 'POST', body: body });
  if (data.ok) { alert('Cotizacion enviada!'); renderView('solicitudes-cot'); }
  else { alert(data.error || 'Error'); }
}

async function renderProveedorPerfil(main) {
  const data = await api('/api/proveedor/' + currentUser.id + '/perfil');
  if (!data.ok) { main.innerHTML = '<div class="empty-state"><p>Error al cargar perfil</p></div>'; return; }
  const p = data.perfil;
  const cats = (p.categorias || []).join(', ');
  main.innerHTML = '<div class="page-header"><h2>Mi Perfil</h2></div>' +
    '<div class="card">' +
    '<div class="form-group"><label>Nombre</label><input type="text" id="perf-nombre" value="' + (p.nombre || '').replace(/"/g, '&quot;') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>WhatsApp</label><input type="text" id="perf-tel" value="' + (p.telefono_whatsapp || '') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div class="form-group" style="flex:1"><label>Email</label><input type="email" id="perf-email" value="' + (p.email || '') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div></div>' +
    '<div class="form-group"><label>Direccion</label><input type="text" id="perf-dir" value="' + (p.direccion || '').replace(/"/g, '&quot;') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div style="display:flex;gap:12px"><div class="form-group" style="flex:1"><label>Municipio</label><input type="text" id="perf-muni" value="' + (p.municipio || '') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div>' +
    '<div class="form-group" style="flex:1"><label>Horario</label><input type="text" id="perf-horario" value="' + (p.horario_atencion || '') + '" style="width:100%;padding:10px;border:1.5px solid var(--gray-300);border-radius:var(--radius)"></div></div>' +
    '<div class="stats-grid" style="margin:16px 0"><div class="stat-card"><div class="stat-value">' + (p.calificacion || 0).toFixed(1) + '</div><div class="stat-label">Calificacion</div></div>' +
    '<div class="stat-card"><div class="stat-value">' + (p.total_pedidos || 0) + '</div><div class="stat-label">Pedidos</div></div>' +
    '<div class="stat-card"><div class="stat-value">' + (p.pedidos_cumplidos || 0) + '</div><div class="stat-label">Cumplidos</div></div></div>' +
    '<button class="btn-primary" style="margin-top:12px" onclick="guardarPerfil()">Guardar Cambios</button></div>';
}

async function guardarPerfil() {
  const body = {
    nombre: document.getElementById('perf-nombre')?.value,
    telefono_whatsapp: document.getElementById('perf-tel')?.value,
    email: document.getElementById('perf-email')?.value,
    direccion: document.getElementById('perf-dir')?.value,
    municipio: document.getElementById('perf-muni')?.value,
    horario_atencion: document.getElementById('perf-horario')?.value,
  };
  const data = await api('/api/proveedor/' + currentUser.id + '/perfil', { method: 'PUT', body: body });
  if (data.ok) { alert('Perfil actualizado'); } else { alert(data.error || 'Error'); }
}

/* ═══ FASE 6: MI CUENTA + VINCULACION ═══ */

async function renderMiCuenta(main) {
  const hasPhone = currentUser.telefono && currentUser.telefono.length >= 10;
  main.innerHTML = '<div class="page-header"><h2>Mi Cuenta</h2></div>' +
    '<div class="card"><h3>Datos de la cuenta</h3>' +
    '<div style="margin:12px 0"><div class="detail-row"><span class="label">Nombre</span><span class="value">' + currentUser.nombre + '</span></div>' +
    '<div class="detail-row"><span class="label">WhatsApp</span><span class="value">' + (hasPhone ? currentUser.telefono : '<span style="color:var(--orange)">No vinculado</span>') + '</span></div></div>' +
    (hasPhone ? '<p style="color:var(--green);font-size:14px">Tu cuenta web esta vinculada a WhatsApp. Las ordenes de ambos canales aparecen aqui.</p>' :
    '<div style="margin-top:16px;padding:16px;background:var(--gray-50);border-radius:var(--radius);border:1px solid var(--gray-200)">' +
      '<h4 style="margin-bottom:8px">Vincular WhatsApp</h4><p style="font-size:13px;color:var(--gray-500);margin-bottom:12px">Vincula tu numero para ver ordenes de WhatsApp en el portal.</p>' +
      '<div style="display:flex;gap:8px;align-items:end"><div class="form-group" style="flex:1"><label>Numero WhatsApp (10 digitos)</label><div class="phone-row"><select class="phone-country" id="link-country"><option value="52">+52</option><option value="1">+1</option></select><input type="tel" id="link-phone" class="phone-input" placeholder="33 1234 5678"></div></div>' +
      '<button class="btn-primary" style="width:auto;padding:10px 16px;margin-bottom:20px" onclick="vincularTelefono()">Vincular</button></div></div>') +
    '</div>';
}

async function vincularTelefono() {
  const code = document.getElementById('link-country')?.value || '52';
  const phone = document.getElementById('link-phone')?.value.replace(/[^0-9]/g, '');
  if (!phone || phone.length < 10) { alert('Ingresa un numero valido de 10 digitos'); return; }
  const fullPhone = code + phone;
  const data = await api('/api/vincular-telefono', { method: 'POST', body: { usuario_id: currentUser.id, telefono: fullPhone, codigo_pais: '+' + code } });
  if (data.ok) {
    currentUser.telefono = fullPhone;
    alert('Vinculado! ' + (data.ordenes_vinculadas > 0 ? data.ordenes_vinculadas + ' ordenes previas vinculadas.' : ''));
    renderView('mi-cuenta');
  } else { alert(data.error || 'Error'); }
}

/* ─── End of new views ─── */

function closeDetail() {
  document.getElementById('detail-overlay').classList.add('hidden');
}
function closeDetailIfOutside(e) {
  if (e.target === document.getElementById('detail-overlay')) closeDetail();
}

/* ─── Keyboard ─── */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeDetail();
});
