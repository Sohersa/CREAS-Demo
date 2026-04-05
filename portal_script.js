
/* ─── State ─── */
let currentUser = null;  // {rol, id, nombre, telefono}
let currentView = null;
let ordersCache = [];

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
      { id: 'ordenes-activas', label: 'Ordenes activas', icon: ICONS.orders },
      { id: 'historial', label: 'Historial', icon: ICONS.history },
      { id: 'costos', label: 'Resumen de costos', icon: ICONS.cost },
      { id: 'calificaciones', label: 'Calificaciones', icon: ICONS.ratings },
    ];
  } else {
    items = [
      { id: 'ordenes-entrantes', label: 'Ordenes entrantes', icon: ICONS.incoming },
      { id: 'historial-prov', label: 'Historial', icon: ICONS.history },
      { id: 'mis-calificaciones', label: 'Mis calificaciones', icon: ICONS.ratings },
      { id: 'ingresos', label: 'Ingresos', icon: ICONS.revenue },
      { id: 'desempeno', label: 'Desempeno', icon: ICONS.metrics },
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
      case 'ordenes-activas': await renderClienteOrdenes(main, 'activas'); break;
      case 'historial': await renderClienteOrdenes(main, 'historial'); break;
      case 'costos': await renderClienteCostos(main); break;
      case 'calificaciones': await renderClienteCalificaciones(main); break;
      case 'ordenes-entrantes': await renderProveedorOrdenes(main, 'activas'); break;
      case 'historial-prov': await renderProveedorOrdenes(main, 'historial'); break;
      case 'mis-calificaciones': await renderProveedorCalificaciones(main); break;
      case 'ingresos': await renderProveedorIngresos(main); break;
      case 'desempeno': await renderProveedorDesempeno(main); break;
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

  // Simulated payment data (no real DB field yet)
  const isPaid = order.status === 'entregada';
  const paymentStatus = isPaid ? 'Pagado' : (order.status === 'en_obra' ? 'En proceso' : 'Pendiente');
  const paymentBadgeClass = isPaid ? 'pagado' : (order.status === 'en_obra' ? 'en_proceso' : 'pendiente');

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
        ${!isPaid ? '<button class="btn-pay" onclick="alert('Funcionalidad de pago en desarrollo. Proximamente podras pagar con tarjeta.')">Pagar con tarjeta</button>' : ''}
      </div>
    </div>
  `;
}

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
