# **AXIS** — Industrial Digital Twin Platform
**Master Specification · Build-Ready v1.0**
EY CREAS · Capital Projects · Abril 2026

> Documento único: análisis del video de referencia + diseño de producto + arquitectura + UX + esqueleto de código + roadmap.
> Escrito para un equipo de ingeniería que empieza a construir mañana.

---

## 0. TL;DR ejecutivo

El video del cliente muestra **Siemens Tecnomatix Plant Simulation V14** corriendo en un laptop (modelo `DairyFab.spp`, Rev23, combina lácteos + línea PET). Es un **simulador discreto de eventos (DES) de escritorio** — buena herramienta para ingenieros industriales, pero **no es una plataforma, no es un digital twin operacional, no está en la nube, no tiene IoT real, no integra con SAP/Maximo, no es colaborativa y no corre en navegador**.

Nuestra propuesta — **AXIS** — es la siguiente generación: un digital twin operacional **cloud-native, web-first, LOD 500 funcional**, que combina visualización 3D streaming, telemetría IoT en vivo, simulación de procesos, y enlace bidireccional con SAP S/4HANA e IBM Maximo. AXIS no compite contra Plant Simulation; la **absorbe** como motor offline mientras ofrece al cliente lo que Plant Simulation no puede dar: operación diaria, mantenimiento, ejecutivos, y técnicos de piso en un solo tejido digital.

**Recomendación comercial:** vender AXIS como plataforma, con Plant Simulation posicionada como "el simulador puntual que tu gente de ingeniería sigue usando, conectado ahora a la realidad operativa". Esto neutraliza cualquier objeción de incumbencia y nos posiciona arriba.

---

## 1. ANÁLISIS DEL VIDEO — Observación, inferencia, verdad cruda

### 1.1 Identificación técnica

| Elemento | Observación directa |
|---|---|
| Título de ventana | `Consumer Product Management Plant Simulation V14 Rev23 - Tecnomatix Plant Simulation 14` |
| Software | **Siemens Tecnomatix Plant Simulation V14** (desktop, Windows) |
| Modelo cargado | `.Models.DairyFab` (+ tab `DairyLib.MaterialsTable`, extensión `.spp`) |
| Class Library activa | `Basis → MaterialFlow, Fluids, Resources, InformationFlow, UserInterface (Comment, Display, Chart, HtmlReport, Dialog, Checkbox, Button, DropDownList, Toolbar), MUs, UserObjects, Tools, Models → DairyFab, DairyLib → BasicClasses → PetBlower, DairyLine, Bottle, Bottle_old` |
| Objetos vistos | Tanques de almacenamiento, homogenizadores (`RMT1 Homogenized Milk`, `RMT2`), camión-cisterna en importador, conveyors, PET Blower (sopladora), llenadoras, etiquetadoras, empaque en cajas, estación de palletizing |
| Entorno | Laptop Dell (teclado visible), Windows 11, grabado con celular apuntando a la pantalla (hay moiré, parallax y distorsión de cámara) |
| Reporte visible | `Service Statistics - Importer Statistics` (HTML) — tablas: *Importers Waiting for Services and Parts, Waiting Times for Parts, Waiting Times for Set-up Exporters* |
| Ribbon/UI | Cinta estilo Office 2013 con pestañas: `File, Home, Debugger, Window, Edit, View, Video` |
| Interacción grabada | Pan/zoom 3D, selección de objeto (status bar: *"The object .Models.DairyFab.RMT2 has been selected"*), apertura de diálogo *Comment*, visualización de reporte estadístico HTML |

### 1.2 Lectura frame-por-frame (condensada)

| Frame | Tiempo | Qué ocurre | Qué significa |
|---|---|---|---|
| 001 | 0:05 | Vista isométrica amplia: planta con **4 zonas separadas por muros**, tanques al centro, línea de botellas al frente, camión-cisterna arriba | Es un layout de planta realista pero con assets genéricos del catálogo Tecnomatix |
| 003 | 0:15 | Zoom a zona de tanques, label *"RMT1 Homogenized Milk"* visible | La planta es **mixta lácteo + PET** — no solo botellas |
| 005–010 | 0:25–0:50 | Laptop inclinado, se ve árbol `DairyLib > BasicClasses > PetBlower, DairyLine, Bottle, Bottle_old`, línea de llenado con reloj rojo de simulación | El cliente quiere mostrar **la línea PET específicamente** |
| 012 | 1:00 | Se abre diálogo de propiedades de objeto (parece `ClassOrigin` o similar) con tabs: *Navigate, View, Edit, Help* → *Position, Rotation, Attributes/Animation* | Edición manual de atributos de objeto — trabajo de modelador, no de operador |
| 015–020 | 1:15–1:40 | Primer plano de **tubería funcional**: ducto amarillo, dos grises, uno rojo, estructura metálica, escalera | Hay detalle de **piping** — pero genérico, no conectado a P&ID real |
| 022 | 1:50 | Vista amplia con camión de **importador verde** al fondo, edificio semitransparente — se aprecia la simulación corriendo | DES activo, MUs (Movable Units = botellas/pallets) fluyendo |
| 025 | 2:05 | Diálogo `Animation` con tabs para *Self-Animation, Orientation, Classes, Position, Rotation* | Setup de animación de un objeto — UX densa, técnica |
| 028 | 2:20 | Vista amplia, label *"Throughput(PET)"* en esquina inferior izquierda | Están midiendo **throughput de la línea PET** como KPI clave |
| 030 | 2:30 | Ventana blanca con "Importer" y "Waiting Times" repetidos, parece un HTML report cargando | Los reportes estadísticos se exportan como HTML plano |
| 033 | 2:45 | Zoom al área de ingeniería de línea con llenadora, tapadora, inspector, conveyor — equipos modelados con detalle medio | Geometría OK para simulación, insuficiente para mantenimiento (no hay válvulas individuales, no hay instrumentación PID) |
| 035 | 2:55 | Vista top con camión importando + área de tanques + zona de ensacado | Demostración del flujo end-to-end: recepción → proceso → llenado → empaque |
| 038 | 3:05 | Reporte HTML pantalla completa: *Service Statistics - Importer Statistics*, tabla con `Object Total Delay`, `Reason for the Delay: Waiting for Services and Parts / Waiting for Parts / Waiting for Set-up Exporters`, filas `RMT2: 0.00%` | Salida **offline**, no live dashboards. Valor nulo = modelo en estado inicial o sin corrida completa |
| 040 | 3:15 | Diálogo *Documents > Comment*, editor vacío | Mostró cómo adjuntar comentario a un objeto — feature de documentación elemental |

### 1.3 Qué es real, qué es comercial

| Afirmación típica del vendor | Realidad técnica |
|---|---|
| "Es un digital twin" | **NO.** Es un modelo de simulación DES. No hay binding a datos reales de planta. |
| "Visualización 3D" | **SÍ, pero limitada.** Renderer OpenGL propietario de Tecnomatix. No es WebGL, no streamable, no colaborativo. Assets genéricos del catálogo. |
| "Análisis de cuellos de botella" | **SÍ.** Plant Simulation es excelente para esto — su *razón de ser*. |
| "Integración con sistemas" | **PARCIAL.** Conectores OPC UA, SQL, Excel. **NO hay conector SAP o Maximo nativo**, requiere middleware. |
| "IoT en tiempo real" | **NO existe nativamente.** Se puede simular inyectando datos por OPC, pero la UI no es un dashboard operacional. |
| "LOD 500" | **NO.** Es LOD 300-400 — geometría suficiente para simulación, insuficiente para mantenimiento de equipos individuales (no válvulas, no instrumentos, no ficha técnica por objeto). |
| "Simulación de procesos" | **SÍ, muy buena.** Es su núcleo. Aquí no competimos — *integramos*. |
| "Web / Cloud" | **NO.** Solo desktop Windows con licencia por nodo. |
| "Multi-usuario colaborativo" | **NO.** Archivo `.spp` monolítico, sin control de versiones nativo. |
| "Usuarios no técnicos" | **NO.** Interfaz para ingeniero industrial entrenado. |

### 1.4 Para quién fue hecho

Plant Simulation está hecho para un **ingeniero industrial / de procesos** que diseña o rediseña plantas. El ejecutivo, el operador, el supervisor de turno, el técnico de mantenimiento y el gerente financiero **no tienen una entrada natural** a esta herramienta. Eso es exactamente el hueco donde AXIS entra.

### 1.5 Brechas reales frente a enterprise-grade

1. **Sin cloud, sin sesión compartida, sin URL.**
2. **Sin RBAC ni SSO.**
3. **Sin capa de documentación técnica vinculada al objeto 3D** (P&IDs, manuales, planos mecánicos, fichas).
4. **Sin historización operativa** (time-series de sensores, eventos, OEE).
5. **Sin conectores enterprise SAP/Maximo.**
6. **Sin mobile / offline de piso.**
7. **Sin observabilidad, sin trazabilidad de auditoría, sin gobierno de datos.**
8. **Sin capa semántica** — el modelo está en un árbol propietario, no en una ontología compartida (ISO 15926, IEC 81346).

---

## 2. PRODUCTO DEFINIDO

### 2.1 Nombre y posicionamiento

**AXIS — Industrial Digital Twin Platform**
*Tagline:* "Tu planta, en vivo. Desde el navegador."

Categoría: **Operational Digital Twin Platform (ODTP)**. Rivaliza conceptualmente con AVEVA Unified Operations Center, Siemens MindSphere Digital Twin, Bentley iTwin, Hexagon HxGN SDx. Diferencial: **web-first, foundation-model-native, time-to-first-value en 8 semanas**.

### 2.2 Problema que resuelve

Las plantas industriales tienen su información fragmentada en 7–12 sistemas (ERP, EAM, CMMS, SCADA, historian, ACC/BIM360, gestores documentales, hojas de Excel, simuladores offline, CCTV). Ningún rol — ni el gerente de planta, ni el supervisor de mantenimiento, ni el operador de turno, ni el CFO — ve la planta en un solo lugar con el contexto correcto. AXIS es ese lugar.

### 2.3 Quién lo usa (5 personas reales)

| Rol | Qué viene a hacer | Qué se lleva |
|---|---|---|
| **Gerente de planta** (Laura, 45 años) | Ver estado general, pérdidas, OEE, proyecciones de cumplimiento | Dashboard ejecutivo, drill-down hasta causa raíz en <3 clicks |
| **Supervisor de mantenimiento** (Ricardo, 38) | Planear paros, ver órdenes Maximo, priorizar activos críticos | Vista 3D filtrada por criticidad + health score + próximos PMs |
| **Operador de turno** (Jesús, 29) | Ver alarmas activas, leer SOP de equipo, reportar anomalía | Vista móvil, QR de activo → ficha, chat con experto |
| **Ingeniero de procesos** (Andrea, 34) | Correr what-if, comparar escenarios, optimizar línea | Motor de simulación embebido + publicación de escenarios |
| **CFO / Capital Projects** (Luis — nuestro buyer) | Ver costo operativo, ROI de nuevas inversiones, riesgo | Módulo financiero cruzando SAP CO + desempeño de activos |

### 2.4 Capabilities — concretas, no genéricas

1. **3D Streaming Viewer (LOD 500 funcional).** Modelo ≥500 MB cargado progresivamente en <4 s hasta first-interactive. Cull por frustum + por nivel jerárquico.
2. **Live Plant Tile.** Cada activo tiene "tile" con: último valor de sensor, estado operativo, OEE, última orden de trabajo, próximo PM, alarmas.
3. **Time Machine.** Scrub temporal desde hoy hasta -12 meses con *replay* de sensores, alarmas y órdenes de trabajo sobre el 3D.
4. **What-If Sandbox.** Clonar el estado actual, inyectar cambios (paro programado, cambio de setpoint, SKU distinto) y comparar contra producción real en tiempo real.
5. **SAP / Maximo Bridge.** Ver órdenes de trabajo, crear notificaciones, consultar costo de activo — sin salir del viewer.
6. **Document Fabric.** Cada activo 3D linkea a ficha técnica, P&ID, isométrico, manual, plano mecánico, certificado — indexado con embeddings para búsqueda semántica.
7. **Anomaly Copilot.** LLM con contexto de planta: *"¿por qué cayó el OEE de la línea 3 el martes?"* → respuesta con evidencia de telemetría + órdenes abiertas + eventos de alarma.
8. **Mobile Round.** App PWA con ronda QR, captura offline, sincronización al volver a red.
9. **Escenarios publicados.** Ingeniería corre Plant Simulation o el motor interno → publica resultado como "escenario" consumible por la planta.

### 2.5 Diferenciadores reales

- **Foundation-model-native:** copiloto entrenado sobre los documentos + series temporales del propio cliente. No es un chat genérico.
- **Deploy en 8 semanas** con plantillas sectoriales (PET, lácteos, gas, minería).
- **Ontología abierta** (ISO 15926 / CFIHOS) — el cliente no queda rehén.
- **Visualización web sin plugin** — funciona en laptop corporativa sin privilegios.
- **Precio por planta, no por usuario** — escala sin penalizar adopción.

---

## 3. UX / UI COMPLETA

### 3.1 Layout principal

```
┌────────────────────────────────────────────────────────────────────────────┐
│  [AXIS] ▸ Planta PET Monterrey ▸ Línea 2                     🔔 12 ⚙️ 👤   │ ← Top Bar (48 px)
├─────┬──────────────────────────────────────────────────────┬────────────────┤
│     │                                                      │                │
│  🏠 │                                                      │  INSPECTOR     │
│  🎲 │          CANVAS 3D (contenedor elástico)             │  (card stack)  │
│  📊 │                                                      │                │
│  🛠️ │          [floating layer controls]                  │  ▸ Identidad   │
│  📄 │                                                      │  ▸ Telemetría  │
│  🎯 │                                                      │  ▸ Docs (7)    │
│  ⚡  │          [time-scrubber]                             │  ▸ Mtto (2)    │
│  🤖 │                                                      │  ▸ Historial   │
│     │                                                      │                │
│     ├──────────────────────────────────────────────────────┤  (340 px)      │
│ 72px│  BOTTOM PANEL (KPIs, alarmas, chat copilot)          │                │
└─────┴──────────────────────────────────────────────────────┴────────────────┘
```

- **Sidebar (72 px)** — íconos: Home, 3D Twin, Analytics, Maintenance, Documents, Simulation, Events, Copilot.
- **Top bar (48 px)** — breadcrumbs de sitio, alarm bell, settings, user.
- **Canvas 3D** — dominante, nunca menos de 60% del viewport.
- **Right Inspector (340 px)** — colapsable, aparece al seleccionar un activo.
- **Bottom drawer (72 px colapsado / 240 px expandido)** — KPIs tiempo real, cola de alarmas, chat al copilot.

### 3.2 Pantallas — una por una

#### 3.2.1 Dashboard ejecutivo (`/dashboard`)
- **Objetivo:** primera pantalla que ve un director al entrar.
- **Layout:** grid 12 col. Hero tile con imagen isométrica renderizada del sitio + overlay de KPIs. Debajo: 6 tiles de OEE por línea. Derecha: timeline de alarmas críticas. Footer: cumplimiento semanal vs plan.
- **Componentes:** `<KPIHero />`, `<OEEGrid lines={6} />`, `<AlarmTimeline range="7d" />`, `<PlanVsActual />`.
- **Comportamiento:** refresh cada 30 s, click en tile → drill hacia vista 3D con filtro aplicado.
- **Estados:** loading con skeletons, empty (planta sin datos), error (badge rojo "Fuente SAP desconectada hace 4 min").

#### 3.2.2 Vista 3D del Digital Twin (`/twin`) — **pantalla principal**
- **Layout:** Canvas + Layer Controls (flotante top-left) + Mini-map (top-right) + Time Scrubber (bottom-center) + Inspector derecho on-select.
- **Layer Controls:** toggles para `Arquitectura, Estructura, Mecánico, Piping, Eléctrico, Instrumentación, IoT Overlay, Alarmas, Áreas de trabajo`.
- **Mini-map:** vista top con frustum del camera, clickable para teleport.
- **Time Scrubber:** rango `-7d … ahora`, con markers de alarmas críticas y PMs completados.
- **Interacciones:**
  - Click en activo → Inspector slide-in, highlight naranja pulsante, cámara se re-centra con ease-out 600 ms.
  - Double-click → focus mode (oculta el resto con opacidad 0.08).
  - Shift-click → multi-select, aparece toolbar flotante con "Comparar, Exportar BOM, Crear orden".
  - Hover → tooltip: nombre + ID + estado + último valor de sensor primario.
  - Scroll wheel → zoom con punto focal en el cursor (no el centro de la escena).
  - Right-click → context menu: *"Ir a ficha, Ver P&ID, Ver histórico, Simular paro, Crear orden de trabajo"*.
- **Estados del activo (color-coding):**
  - `operando` → cyan tenue
  - `alarma` → rojo pulsante
  - `paro programado` → amarillo
  - `paro no programado` → rojo sólido
  - `en mantenimiento` → naranja cuadriculado
  - `sin datos` → gris con hatching

#### 3.2.3 Panel de activos (`/assets`)
- **Objetivo:** tabla densa para supervisores que quieren barrer inventario.
- **Layout:** tabla virtual (react-window) de 50k filas sin lag. Columnas: Tag, Nombre, Ubicación, Criticidad (A/B/C), Estado, Health Score, Próximo PM, MTBF, MTTR, Costo acumulado YTD.
- **Filtros:** multi-column con facets, búsqueda full-text, guardar vistas.
- **Vínculo:** click en row → abre Vista 3D con ese activo seleccionado + zoom.

#### 3.2.4 IoT en tiempo real (`/iot`)
- **Objetivo:** un operador que quiere ver sensores.
- **Layout:** split 60/40 — izquierda 3D, derecha grid de 8 mini-gráficas tiempo real (uplot, WebSocket stream).
- **Interacción:** click en sensor dentro del 3D → se resalta su gráfica y viceversa.

#### 3.2.5 Mantenimiento / Maximo view (`/maintenance`)
- **Layout:** Kanban con columnas *Pendiente, Planificada, En ejecución, Completada*. Cards mostrando WO ID (Maximo), activo, prioridad, técnico asignado.
- **Drill:** click en card → drawer derecho con detalle de orden + botón "Ver en 3D" que abre Vista 3D con ese activo.

#### 3.2.6 Integración SAP (`/sap`)
- **Layout:** 3 tabs: *Costos de activos, Órdenes de compra vinculadas, Budget vs Actual*.
- **Widget:** treemap de costo acumulado por área con zoom.

#### 3.2.7 Simulación (`/simulation`)
- **Layout:** Canvas 3D (mismo engine que `/twin` pero en modo "sandbox"), toolbar superior con *Crear escenario, Duplicar, Comparar, Publicar*.
- **Comportamiento:** al crear escenario, se clona el estado actual de la planta. Parámetros editables: ratios de producción, disponibilidad de equipos, SKU mix, turno. Al correr → barras de progreso, al terminar → dashboard de resultado comparado contra baseline.

#### 3.2.8 Documentación técnica (`/docs`)
- **Layout:** 3 columnas — *árbol jerárquico, lista de archivos, visor PDF/DWG/IFC*.
- **Features:** búsqueda semántica ("¿dónde está el manual de la sopladora Sidel?"), preview inline, copiar link con deep-link al activo 3D relacionado.

#### 3.2.9 Alertas y eventos (`/events`)
- **Layout:** feed infinito, filtros por severidad/área/tipo.
- **Card:** timestamp, activo, severidad, mensaje, botones *Reconocer, Crear WO, Ignorar, Ver en 3D*.

#### 3.2.10 Configuración (`/settings`)
- **Tabs:** *Perfil, Organización, Integraciones (SAP/Maximo/OPC), Roles y permisos, Audit log, Facturación*.

### 3.3 Interacciones clave (flujos críticos)

#### Flujo 1: "¿Por qué cayó el OEE anoche?"
1. Director entra a `/dashboard` → ve OEE L2 en rojo (73%).
2. Click en tile → llega a `/twin` con filtro "Línea 2".
3. Copilot aparece con tarjeta sugerida: *"Paro no programado 02:14–03:41 en Blower B-02. Relacionado con alarma de presión baja aire comprimido. WO #45213 creada. ¿Ver en 3D?"*
4. Click → cámara vuela a B-02, se resaltan los sensores de presión con su curva temporal en overlay, Inspector abre ficha + histórico + docs.

#### Flujo 2: Operador de turno ante alarma
1. PWA en tablet suena → notificación: *"Alarma A2 en Llenadora F-03"*.
2. Tap → se abre la ficha del activo, botón grande "Ver en 3D" y "Leer SOP".
3. Tap *Leer SOP* → PDF renderizado inline con highlight del paso actual.
4. Al final, *"Marcar como atendida"* → firma con huella + sync offline.

#### Flujo 3: Cruzar modelo 3D con dato IoT
- Sensor IoT está **siempre** representado por un nodo 3D con geometría tag (no es una capa invisible).
- Al hacer hover sobre un tag de sensor aparece un tooltip con último valor + sparkline 60 s.
- Doble click → panel derecho muestra la curva extendida con agregaciones.

### 3.4 Sistema de diseño

- **Paleta:** fondo `#060D18`, superficies `#0A1420 → #0F1D2E`, primario `#FF5500` (EY/CREAS), cyan dato `#00C8F0`, verde éxito `#10D858`, amarillo warning `#F5B300`, rojo alerta `#FF3355`.
- **Tipografía:** *Space Grotesk* (UI) + *IBM Plex Mono* (datos técnicos, tags).
- **Espaciado:** escala 4/8/12/16/24/32/48.
- **Radios:** 8 px tiles, 12 px cards, 4 px inputs.
- **Motion:** transiciones ≤300 ms, ease `cubic-bezier(0.2, 0.8, 0.2, 1)`. Nada de bounce — sensación enterprise.
- **Icons:** Lucide + set custom para activos industriales (50 íconos).

---

## 4. MOTOR 3D Y MODELO DIGITAL

### 4.1 Estructura del modelo (LOD 500 funcional)

LOD 500 no se refiere solo a geometría — nosotros lo definimos como **nivel de funcionalidad semántica**:

| Nivel | Geometría | Atributos | Comportamiento |
|---|---|---|---|
| LOD 300 | Forma simplificada | Tag, Clase | Ninguno |
| LOD 400 | Ensamblajes, componentes | + Proveedor, Nº serie | Estado binario |
| **LOD 500 funcional** | **Piezas individuales (válvulas, instrumentos, accesorios)** | **+ Specs técnicas, curvas, tolerancias, historial, documentos, sensores vinculados** | **Comportamiento simulable: caudal, pérdida de carga, consumo energético** |

### 4.2 Representación por tipo de activo

```
AssetNode (TS interface)
├─ id: UUID (estable, asignado por CMMS)
├─ tag: string (ISA-5.1 / KKS)
├─ class: "Tank" | "Pump" | "Valve" | "Pipe" | "Instrument" | "Conveyor" | "Motor" | ...
├─ geometry: { meshUri, lod: 100|200|300|400|500, bbox }
├─ parent: UUID (jerarquía funcional, p.ej. Línea → Zona → Activo → Componente)
├─ position: { x,y,z, rx,ry,rz, scale }
├─ process: {
│    fluid: "PET pellet" | "CO2" | "Air" | "Water" | ...
│    flowRate?: { nominal, min, max, unit }
│    pressure?: { nominal, rangeMin, rangeMax, unit }
│    temperature?: { ... }
│  }
├─ maintenance: { criticality: "A"|"B"|"C", MTBF, MTTR, nextPM, cmmsId }
├─ telemetry: { sensors: SensorRef[], lastValue?, unit, threshold }
├─ documents: DocRef[] (manuales, P&ID, ficha)
├─ lifecycle: { installed, warrantyEnds, expectedEOL, replacedAssets[] }
├─ costYTD: number  (cruza SAP CO)
└─ state: "operating"|"idle"|"alarm"|"maintenance"|"offline"
```

### 4.3 Streaming y carga progresiva

- Formato de entrega: **glTF 2.0 + Draco compression + Meshopt quantization + KTX2 textures**.
- Spatial partitioning: **BVH** construido offline + **Hierarchical LOD** (3DTiles-inspired).
- Tiler que parte la planta en *tiles 3D* (20×20×20 m cúbicos) + tile descriptors con bbox y LOD máximo.
- **Presupuesto de memoria:** 800 MB GPU máximo; cull agresivo por frustum + distancia.
- **First paint:** <1.5 s con versión LOD 100 (siluetas); **full interactive:** <4 s con LOD 400 en la zona visible.
- Usamos `three.js` + `three-mesh-bvh` + `@loaders.gl/gltf` + `meshopt_decoder`.

### 4.4 Selección y picking

- **GPU picking** vía render pass auxiliar (colores únicos por ID) para evitar raycast sobre meshes densos.
- Hover con rAF debounce 16 ms.
- Al seleccionar: halo outline (postprocessing `OutlinePass`), sonido UI suave, Inspector expand 280 ms.

### 4.5 Capas

- Cada mesh pertenece a N capas (`Layer` = bitmask 32-bit).
- Toggle de capa es O(1) — setea visibility en el scene graph por layer mask.
- Capas predefinidas: `Architecture, Structure, Mechanical, Piping, Electrical, Instrumentation, IoT_Overlay, Alarms_Overlay, Work_Areas`.

### 4.6 Sensores y overlays

- Los sensores no son meshes — son **sprites billboard** con sparkline dibujada en canvas 2D compuesto sobre WebGL.
- Valor live via WebSocket → animación de color y ping cuando hay cambio crítico.
- Al pasar de umbral, el sprite pulsa + el mesh del activo padre se tinta con alpha 0.4 rojo.

---

## 5. ARQUITECTURA TÉCNICA

### 5.1 Decisión de stack — con trade-offs

| Capa | Opción elegida | Alternativas descartadas | Razón |
|---|---|---|---|
| **3D engine** | `three.js r160` | Babylon, PlayCanvas, WebGPU puro | Comunidad masiva, ecosystem (postprocessing, drei-like), soporte de Meshopt/Draco/KTX2 maduro. Babylon pierde en ecosystem de loaders. WebGPU aún frágil en Safari Mac / corp browsers. |
| **Frontend framework** | React 18 + TanStack Router + TanStack Query | Vue, Svelte, Angular | Equipos grandes familiarizados. Ecosystem de react-three-fiber para conectar Three a estado. |
| **3D-React bridge** | `@react-three/fiber` + `@react-three/drei` | Imperative three.js puro | Componibilidad, HMR, reuso. Costo: overhead de reconciler ~5%, aceptable. |
| **State** | Zustand (global UI) + TanStack Query (server) + Valtio (3D state) | Redux, MobX | Zustand minimiza boilerplate. Valtio es proxy — ideal para mutaciones frecuentes en 3D. |
| **Backend** | Python 3.12 + **FastAPI** (síncrono) + **aiokafka** (streams) | Node.js/Nest, Go/Fiber, Java/Spring | Python domina ML/simulación. FastAPI = perf OK + OpenAPI auto. Go solo si latencia <10 ms es crítica (no lo es todavía). |
| **Arquitectura backend** | Modular monolith → microservicios por dominio | Microservicios desde día 1 | Evita over-engineering. Dominios claros: *assets, telemetry, work-orders, sim, docs, iam, copilot*. |
| **DB operacional** | **PostgreSQL 16** + PostGIS | MySQL, MongoDB | ACID, JSONB para metadatos flexibles, PostGIS para geometría, extensiones (`pgvector`, `timescaledb`). |
| **DB time-series** | **TimescaleDB** (extensión de Postgres) | InfluxDB, Prometheus, ClickHouse | Misma DB = menos ops. Compresión columnar. Ventanas agregadas nativas. Para volúmenes >1 TB/día mover a ClickHouse. |
| **DB vectorial** | `pgvector` en la misma Postgres | Pinecone, Weaviate | Ya tenemos Postgres, latencia <50 ms para <5M docs. |
| **Object store** | S3 / Azure Blob | Local FS | Modelos grandes, versionado, lifecycle. |
| **Stream / IoT** | **Apache Kafka** (Confluent Cloud en prod) + **MQTT** broker (HiveMQ) en planta | Kinesis, Pulsar, RabbitMQ | MQTT es el de facto en planta. Kafka para fan-out interno y durabilidad. |
| **Cache** | Redis | Memcached | Pub/sub para WebSockets + cache de autorización. |
| **API** | REST + **WebSocket** + **SSE** (para streams ligeros) | GraphQL puro, gRPC | REST + OpenAPI es universal. GraphQL agrega complejidad no justificada. WS para 3D sync, SSE para dashboards. |
| **Auth** | **Keycloak** (SSO SAML + OIDC) | Auth0, Okta | Open source, on-prem si cliente lo exige (bancos, gobierno). |
| **Documentos** | MinIO/S3 + indexer a `pgvector` + Apache Tika para extracción | Elastic, Algolia | Menos licencias. Tika maneja 1400 formatos. |
| **Cloud** | **Azure** como default (Luis/EY ecosystem) con **AWS** como opción cliente | GCP | Azure tiene mejor camino con clientes EY y mayor presencia en MX. AKS + Azure Service Bus + Azure Blob + Azure AD. Nota: mantener **sin dependencia dura de Azure AD del tenant del cliente** para evitar fricción. |
| **IaC** | Terraform + Helm | Pulumi, Bicep | Multi-cloud compatible. |
| **Observability** | Grafana + Loki + Tempo + Prometheus | Datadog (caro) | Self-host en AKS. Métricas + logs + traces con correlación. |
| **CI/CD** | GitHub Actions + ArgoCD | Jenkins | GitOps, deploy declarativo. |

### 5.2 Arquitectura de servicios (diagrama textual)

```
[Browser: AXIS Web App (React + three.js)]
        │
        ▼  HTTPS / WSS
[Azure Front Door + WAF]
        │
        ▼
[AKS Cluster]
   ├─ api-gateway (Kong/Nginx)
   ├─ auth-svc (Keycloak)
   ├─ asset-svc (FastAPI) ──► Postgres (assets) + S3 (geo/gltf)
   ├─ telemetry-svc (FastAPI+aiokafka) ──► TimescaleDB + Kafka
   ├─ wo-svc (FastAPI)  ──► Postgres (wo) + Maximo adapter
   ├─ erp-svc (FastAPI) ──► Postgres + SAP adapter
   ├─ sim-svc (Python + SimPy/OMPR) ──► Job queue (Redis/RQ) + S3 (scenarios)
   ├─ docs-svc (FastAPI) ──► pgvector + S3
   ├─ copilot-svc (Python) ──► Claude API / on-prem LLM
   ├─ event-svc (FastAPI + ws) ──► Redis pub/sub
   └─ notify-svc (FastAPI) ──► Twilio/WhatsApp/Email

[Edge (on-prem en planta)]
   ├─ MQTT broker (HiveMQ)
   ├─ OPC UA Gateway (Kepware/Ignition)
   └─ Edge-agent (Rust) → buffers + forward a Kafka cloud (compresión, store-forward)
```

### 5.3 Integraciones

#### SAP (S/4HANA)
- Canal: **SAP OData API** vía gateway + **SAP Event Mesh** para eventos async.
- Lectura: WO costos, compras, inventario, centro de costo.
- Escritura: crear notificación de mantenimiento, PM02.
- **En AXIS demo:** se simula con un **sap-mock-service** que expone los mismos endpoints OData con datos generados — un developer puede conectar al real cambiando solo la URL.

#### IBM Maximo
- Canal: **Maximo REST (MIF / Integration Framework)**.
- Lectura: órdenes de trabajo, activos, jerarquía de ubicaciones, planes PM.
- Escritura: crear/actualizar WO, subir attachments, cambiar estado.
- **En AXIS demo:** `maximo-mock` con 200 WOs generadas sobre los 180 activos demo.

#### IoT / Historian
- Canales: **OPC UA** (equipos modernos), **Modbus TCP** (legacy), **MQTT** (IIoT).
- Historiadores soportados: OSIsoft PI, GE Proficy, AVEVA PI, InfluxDB existente.
- Latencia objetivo edge→cloud→UI: **<2 s p95** en conexión estable.

#### Documentos
- Conectores: SharePoint, Google Drive, ACC (Autodesk), Bentley ProjectWise, carpetas SMB.
- Formatos: PDF, DWG, DXF, IFC, RVT (export), STEP, IGES, Excel, Word.

### 5.4 Escalabilidad

- **Modelos 3D hasta 5 GB** por planta (mesh + texturas) — servidos desde CDN con rango byte.
- **Eventos IoT hasta 100k msg/s** por tenant — Kafka particionado por tag.
- **Usuarios concurrentes por planta:** objetivo 500.
- **Multi-tenant soft isolation** (DB por cliente, namespace AKS por cliente Enterprise).

### 5.5 Seguridad

- SSO SAML/OIDC, MFA obligatorio para roles administrativos.
- RBAC granular por activo (`asset:{id}:read`, `asset:{id}:write`, `wo:create`, etc.).
- Cifrado: TLS 1.3 en tránsito, AES-256 GCM en reposo, secretos en Azure Key Vault.
- Audit log inmutable (append-only, firmado).
- Network: VPC privada, bastion, NSG restrictivo, egress whitelisted para SAP/Maximo.
- Compliance: SOC 2 Type II roadmap, ISO 27001, IEC 62443 para componente edge.

### 5.6 Performance budget

| Métrica | Target |
|---|---|
| Time to First Paint | <1.2 s |
| Time to Interactive (3D) | <4 s |
| Hover latency en 3D | <20 ms |
| Selección de activo | <100 ms |
| Dashboard refresh | <500 ms |
| IoT end-to-end (edge→pixel) | <2 s p95 |
| Simulación 1 h planta 180 activos | <90 s |

---

## 6. MODELADO Y DATOS (LOD 500 funcional operativo)

### 6.1 Ontología base

Adoptamos **CFIHOS** (Capital Facilities Information HandOver Spec) como ontología primaria, con mapeo a **ISO 15926** para interoperabilidad. Extendemos para PET/bebidas con clases:
`Preform, Blower, Filler, Capper, Labeler, CasePacker, Palletizer, Depalletizer, ConveyorBelt, AirCompressor, ChillerUnit, CIPStation, WaterTreatment, PET_Silo, ResinFeeder`.

### 6.2 Atributos obligatorios por activo

Mínimo para entrar al twin:
`tag, class, manufacturer, model, serial, installDate, location, criticality, parentAsset, primarySensorTag[], cmmsId, drawingRef[], manualRef`.

Enriquecidos (post-onboarding):
`designCapacity, actualCapacity, specSheet, MTBF, MTTR, sparePartKit, energySignature, qualityImpact, hoursRun, batchCount`.

### 6.3 Vinculación

- **Geometría ↔ Atributos:** se linkean por `asset.id`. El mesh en glTF lleva `extensions.EXT_mesh_features` con la propiedad `assetId`.
- **Atributos ↔ Telemetría:** `asset.telemetry.sensors[]` apunta a tags del historian.
- **Atributos ↔ Documentos:** `asset.documents[]` con tipo semántico (`MANUAL, PID, ISO, SPEC, CERT, MSDS, SOP, PHOTO`).
- **Atributos ↔ Mantenimiento:** `asset.cmmsId` es la llave en Maximo.
- **Atributos ↔ Costo:** `asset.costCenter` cruza a SAP CO.

### 6.4 Metadatos y trazabilidad

- Cada cambio en un atributo genera un evento en la tabla `asset_events` (append-only).
- Origen de cada dato etiquetado: `source: "manual"|"sap"|"maximo"|"opc"|"import-step"|"copilot-extract"` + `confidence` 0-1 para datos inferidos por el LLM desde docs.
- Versionado del modelo: cada release del twin es inmutable y referenciable por SHA.

### 6.5 Capa semántica

Sobre la tabla plana de activos construimos un **graph layer** con Apache AGE (Postgres) para queries como:
- "dame todo lo downstream del tanque T-03"
- "qué activos comparten el loop de control PC-201"
- "qué WO afectaron a la línea 2 en los últimos 30 días"

Esta capa es lo que consume el copilot como retrieval estructurado.

---

## 7. SIMULACIÓN Y CAPA DE INTELIGENCIA OPERACIONAL

### 7.1 Motor de simulación interno

Implementación en 3 niveles:

| Nivel | Motor | Qué hace | Cuándo |
|---|---|---|---|
| **Rápido** | **SimPy** (Python) | Flujo discreto de eventos líneal — throughput, tiempos de espera | What-if interactivo (<60 s) |
| **Medio** | **OMPR + CPLEX/COIN-OR** | Optimización de turnos, mix SKU, planificación | Nightly batch |
| **Avanzado** | **Bridge a Plant Simulation / AnyLogic** | Escenarios con lógica muy compleja | Bajo demanda de ingeniería, corre en VM dedicada y publica resultados |

**Posicionamiento:** Plant Simulation queda integrado — no peleamos contra la inversión del cliente.

### 7.2 Escenarios what-if

- UI en `/simulation`: el usuario selecciona un "snapshot" del twin (ahora, o un histórico).
- Parámetros editables en panel derecho: disponibilidad por equipo, SKU mix, duración, turnos.
- Se enqueue en RQ, corre container simpy con timeout 90 s.
- Salida: KPI delta vs baseline + heatmap de utilización sobre el 3D.

### 7.3 Cuellos de botella y rendimiento

- Al terminar simulación, algoritmo `theory-of-constraints` identifica el activo con mayor utilización sostenida.
- Se resalta en 3D con halo rojo + recomendación: "si subes throughput de F-03 5%, OEE planta +1.8 pts".

### 7.4 Mantenimiento predictivo (fase 2)

- Features derivadas de TimescaleDB: RMS vibración, kurtosis corriente, tendencia de delta-P.
- Modelos por clase de activo: IsolationForest baseline + LSTM para señal compleja.
- Umbrales adaptativos con EWMA.
- Acción: al cruzar umbral → evento → copilot sugiere WO predictiva en Maximo.

### 7.5 Copilot (Claude)

- **Retrieval augmented generation** sobre: `docs (pgvector), activos (graph), telemetry (agregados por hora), WOs (Maximo), eventos`.
- Prompt system: *"Eres un ingeniero de planta senior. Respondes con evidencia o dices 'no tengo dato'. Cita fuentes como `[asset: F-03]` `[wo: 45213]` `[doc: manual-sidel-sbo-24.pdf#p42]`"*.
- Tools: `queryTelemetry(tag, range)`, `getWOs(filter)`, `get3DScreenshot(assetId)`, `runMiniSim(params)`.
- **Guardrails:** no ejecuta acciones de escritura sin confirmación explícita del usuario.

### 7.6 Realismo por fase

| Fase | Qué sí | Qué no todavía |
|---|---|---|
| 1 | Flujo DES, what-if simple, KPIs | Predictivo real, ejecución autónoma |
| 2 | Predictivo por clase de activo, copilot con escritura controlada | Cierre de loop de control |
| 3 | Digital twin de control loop (co-simulación con PLCs) | Autonomía de decisión sin humano |

---

## 8. BENCHMARK Y VISIÓN COMPETITIVA

### 8.1 Nivel donde está el video

El video está en el nivel **"simulación offline para ingeniería industrial"** — un nicho maduro y pequeño. Es valor real pero NO es lo que piden las plantas hoy.

### 8.2 Dónde está el mercado líder

| Plataforma | Fortaleza | Debilidad explotable |
|---|---|---|
| **AVEVA Unified Operations Center** | Historian + UI muy pulido, adopción en Oil&Gas | Pesado, licenciamiento complejo, curva brutal |
| **Siemens MindSphere / Xcelerator** | Integración nativa con hardware Siemens | Lock-in, adopción fuera de Siemens floja |
| **Bentley iTwin** | Excelente 3D streaming, iModel | Muy ingeniería/BIM, débil en operación diaria |
| **Hexagon HxGN SDx / SmartPlant** | Información de activo profunda (O&G) | UI años 2010, no es moderno |
| **GE Digital Predix (lo que queda)** | Analytics APM sólido | Producto en declive |

### 8.3 Cómo nos posicionamos arriba

- **Ligero, web puro, sin plugin** — diferencia brutal contra AVEVA/Hexagon.
- **Deploy 8 semanas, not 12 meses.**
- **Copilot nativo** — solo Bentley está empezando a mostrar algo.
- **Precio lineal, no-escalera** — la escalera es lo que mata adopción.
- **Open ontology + data portability** — el cliente no queda rehén.

### 8.4 Qué hace que se sienta "premium"

1. **Rendimiento visual impecable** (3D silencioso, 60 fps sin gastar batería).
2. **Tipografía y espaciado que respiran.**
3. **Respuestas del copilot citadas con evidencia.**
4. **Sin loaders falsos ni toasts excesivos.**
5. **Motion design sutil — nada "se rebota".**
6. **Errores con lenguaje humano, no "500 Internal Server Error".**

---

## 9. ROADMAP DE CONSTRUCCIÓN (realista, brutalmente honesto)

### Fase 1 — MVP (semanas 1–8)

**Qué incluye EXACTAMENTE:**
- Tenant único, 1 planta PET demo con 180 activos modelados LOD 400.
- Vista 3D streaming (glTF + Draco), capas, picking, inspector.
- Dashboard ejecutivo con 6 KPIs mockeados + 1 real (OEE) desde MQTT.
- Panel de activos (tabla virtual).
- **SAP mock** y **Maximo mock** con datos realistas (200 WOs, 50 POs).
- Documento viewer (PDF, IFC lite).
- Alertas básicas desde reglas simples (umbral).
- Autenticación básica (Keycloak con login local).

**Tiempo:** 8 semanas con equipo de 6: 1 tech lead, 1 UX, 2 frontend (1 experto 3D), 2 backend.
**Complejidad:** media-alta. El streaming 3D es el riesgo #1.
**Dependencias:** modelo 3D del cliente (si no existe, fotogrametría + libros CAD, +3 semanas).
**Valor para el cliente:** demo vendible, showcase en dirección, onboarding de usuarios finales.

### Fase 2 — Integración enterprise (semanas 9–20)

**Entregables:**
- Conectores **SAP real** y **Maximo real** (reemplaza mocks).
- Bridge **OPC UA** + **MQTT** real con edge agent en planta piloto.
- Time Machine (replay histórico).
- RBAC granular + audit log.
- PWA móvil para ronda QR.
- Observabilidad (Grafana + Loki).

**Tiempo:** 12 semanas. **Complejidad:** alta — conectores enterprise son el mayor riesgo de schedule.
**Riesgos:** acceso a sistemas del cliente, sandbox SAP disponible, permisos Maximo MIF.

### Fase 3 — Simulación e inteligencia (semanas 21–32)

**Entregables:**
- Sandbox what-if con SimPy + UI de escenarios.
- Copilot v1 (RAG sobre docs + activos + últimas 24 h de telemetría).
- Predictivo clase A (motores, compresores, bombas) — modelo base.
- Bridge opcional a Plant Simulation.

### Fase 4 — Escala y productización (semanas 33–52)

- Multi-tenant, multi-planta.
- Plantillas sectoriales (PET, lácteos, gas, cemento).
- Marketplace de connectors.
- Certificación SOC 2.

### Riesgos transversales

1. **Calidad del modelo CAD del cliente** — 60% de los proyectos se demoran aquí.
2. **Permisos SAP/Maximo** — política corporativa puede tomar 4–8 semanas.
3. **Performance del 3D en equipos corp** — GPUs integradas baratas.
4. **Adopción usuario** — 30% del presupuesto debe ir a UX + change management.

---

## 10. RECOMENDACIÓN FINAL EJECUTIVA

### 10.1 Qué SÍ prometer al cliente hoy

- "En 8 semanas tienes un twin web operativo de tu línea PET con 180 activos, IoT live simulado, dashboard ejecutivo, y visor 3D streaming."
- "Al final de la fase 2 estás integrado con tu SAP y Maximo reales, con edge agent en planta."
- "Copilot con RAG sobre tus documentos y datos en fase 3."
- "Open data, sin lock-in: puedes exportar todo en formatos estándar."

### 10.2 Qué NO prometer todavía

- Predictivo ultra-preciso: decir *"modelo base fase 3, ajuste por clase de activo con 6 meses de histórico mínimo"*.
- Cerrar loop de control (escribir setpoints): **NO hasta fase 4**, y con IEC 62443 verificado.
- Simulaciones de resolución CFD: **no está en scope**, redirigir a ANSYS/Simcenter.
- LOD 500 completo con piezas de repuesto modeladas individualmente: **esto toma 3–6 meses por zona**, se hace por fases.

### 10.3 Mejor versión posible con tiempo y presupuesto realista

**Con US$850k – US$1.3M y 9 meses:** plataforma que se ve al nivel de Bentley iTwin en la parte web, con operación diaria al nivel de AVEVA UOC, con copilot que Bentley todavía no tiene. Diferencial real y defendible.

### 10.4 Estrategia comercial (sin overpromising)

- **Pilot paid 8 semanas** — precio fijo, un producto que se ve y se toca. 60% se convierte.
- **Pricing transparente por planta** — no por usuario, no por módulo. Destruye objeciones.
- **Data portability declarada en contrato.**
- **Roadmap público trimestral** — la competencia enterprise no lo hace.
- **Demo live en el pitch** — el deck mata; el producto vende.

### 10.5 Balance final

| Eje | Nuestra jugada |
|---|---|
| Ambición | Alta en visión, disciplinada en fases |
| Factibilidad | 100% fase 1-2 con stack conocido; fase 3 requiere iteración |
| Tiempo | First value en 8 semanas, full-stack en 52 |
| Riesgo técnico | Medio — 3D streaming + conectores enterprise |
| Riesgo comercial | Bajo — pilot paid blinda cash |
| Ventaja defendible | Copilot + UX + time-to-value |

---

## 11. ANEXOS DE CÓDIGO — ESQUELETO REAL

Ver carpeta `pet-platform/frontend/` y `pet-platform/backend/` (en este repositorio) con:
- Estructura de proyecto lista para arrancar.
- Viewer 3D (React Three Fiber) con streaming, capas, inspector.
- Endpoint FastAPI para assets + telemetría.
- Modelo de datos Pydantic + esquema SQL.
- Stream WebSocket de telemetría mock.

Y la **demo interactiva completa** en `pet-platform/pet-DT.html` — una sola página HTML que el vendedor puede abrir en cualquier laptop, sin instalar nada, para mostrar al cliente en una reunión. Ésa es la pieza comercial.

---

*CREAS · EY · DIGITAL TWIN PRINCIPAL ARCHITECT PACK · v1.0*
