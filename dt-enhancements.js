/* ================================================================
   DT ENHANCEMENTS - Mobile, SAP Fiori, ACC
   Shared across all Digital Twin files
   ================================================================ */
(function(){
'use strict';

/* ----------------------------------------------------------------
   DETECT PLANT TYPE from page title / URL
   ---------------------------------------------------------------- */
var title = document.title.toLowerCase();
var PLANT = 'generic';
if(title.indexOf('tas')>-1 || title.indexOf('terminal gas lp')>-1) PLANT='tas';
else if(title.indexOf('gnc')>-1 || title.indexOf('gas natural comp')>-1) PLANT='gnc';
else if(title.indexOf('lng')>-1 || title.indexOf('regasif')>-1) PLANT='lng';
else if(title.indexOf('ducto')>-1 || title.indexOf('compresion ducto')>-1) PLANT='ductos';
else if(title.indexOf('fv')>-1 || title.indexOf('solar')>-1) PLANT='fv';

/* ----------------------------------------------------------------
   ISSUE 1: MOBILE RESPONSIVE CSS
   ---------------------------------------------------------------- */
var mobileCSS = document.createElement('style');
mobileCSS.id = 'dt-mobile-enhancements';
mobileCSS.textContent = [
'/* Prevent body scroll when touching 3D canvas */',
'canvas{touch-action:none!important}',
'#canvas-container,#canvasWrap,#view-3d,.center,[class*="canvas-wrap"]{touch-action:none!important;-webkit-overflow-scrolling:auto!important}',
'@media(max-width:768px){',
'  /* Mobile layout: hide sidebar, full-width canvas */',
'  .left,.sidebar,.sl-sidebar,[class*="sidebar"]{width:220px!important;position:fixed!important;left:-220px!important;z-index:300!important;transition:left .3s!important;height:calc(100vh - 52px)!important;top:52px!important}',
'  .left.open,.sidebar.open,.sl-sidebar.open{left:0!important}',
'  .center,#view-3d,#canvas-container,#canvasWrap,[class*="canvas"]{flex:1!important;width:100%!important;min-width:0!important}',
'  .right,.right-panel,[class*="right-panel"]{position:fixed!important;right:-100%!important;z-index:300!important;transition:right .3s!important;width:100%!important;max-width:360px!important;top:52px!important;height:calc(100vh - 52px)!important}',
'  .right.open,.right-panel.open{right:0!important}',
'  #app{flex-direction:column!important}',
'  #header{flex-wrap:wrap!important;height:auto!important;min-height:44px!important;padding:8px 12px!important;gap:6px!important}',
'  .h-plant{font-size:10px!important}',
'  .h-status{font-size:10px!important}',
'  .h-time{display:none!important}',
'  .demo-badge{font-size:8px!important}',
'  .sap-fullscreen .sap-fs-nav,.sap-fs-nav,[class*="sap"][class*="nav"]:not(.sap-fs-nav-item):not([class*="nav-icon"]){',
'    width:100%!important;height:auto!important;',
'    flex-direction:row!important;overflow-x:auto!important;',
'    position:relative!important;flex-shrink:0!important;',
'    white-space:nowrap!important;',
'  }',
'  .sap-fullscreen .sap-fs-content,.sap-fs-content,.sap-fs-main,.fs-sap-content,.fs-content{',
'    width:100%!important;margin-left:0!important;',
'  }',
'  .sap-fullscreen,.sap-fs,[class*="sap"][class*="fullscreen"],',
'  [id*="sapOverlay"],[id*="sap-overlay"],[id*="sapFullscreen"],',
'  .fs-overlay.fs-sap,.sap-overlay{',
'    flex-direction:column!important;',
'  }',
'  .sap-fs-body,.fs-sap-body,.fs-body{',
'    flex-direction:column!important;',
'  }',
'  .sap-fs-nav-item,.fs-nav-item,.fs-sap-nav-item{',
'    white-space:nowrap!important;padding:10px 14px!important;font-size:11px!important;',
'    min-height:44px!important;display:flex!important;align-items:center!important;',
'  }',
'  .acc-fullscreen,.acc-fs,[id*="accOverlay"],[id*="acc-overlay"],[id*="accFullscreen"],',
'  .fs-overlay.fs-acc,.acc-overlay{',
'    flex-direction:column!important;',
'  }',
'  .acc-fs-body,.fs-acc-body{flex-direction:column!important}',
'  .acc-fullscreen .acc-fs-tree,.acc-fs-tree,[class*="acc"][class*="tree"]{',
'    width:100%!important;max-height:200px!important;',
'    overflow-y:auto!important;',
'  }',
'  .acc-fs-nav,.fs-acc-nav,[class*="acc"][class*="nav"]:not(.acc-fs-nav-item){',
'    width:100%!important;height:auto!important;',
'    flex-direction:row!important;overflow-x:auto!important;',
'    position:relative!important;flex-shrink:0!important;',
'  }',
'  .acc-fs-nav-item,.fs-acc-nav-item{',
'    white-space:nowrap!important;min-height:44px!important;',
'    display:flex!important;align-items:center!important;',
'  }',
'  .acc-fs-main,.acc-fs-viewer,.fs-acc-content,.acc-fs-content{',
'    width:100%!important;',
'  }',
'  .acc-fs-viewer-body{flex-direction:column!important}',
'  .acc-fs-doc-preview{min-height:200px!important}',
'  .acc-fs-doc-meta-panel{width:100%!important;max-height:200px!important;border-left:none!important;border-top:1px solid rgba(255,255,255,.08)!important}',
'  [id*="tandemOverlay"],[id*="tandem-overlay"],[id*="tandemFullscreen"],',
'  .tandem-fs,.tandem-overlay,.fs-overlay.fs-tandem{',
'    flex-direction:column!important;',
'  }',
'  .tandem-fs-body,.fs-tandem-body{flex-direction:column!important}',
'  .tandem-fs-tree,.tandem-tree,.fs-tandem-left{width:100%!important;max-height:200px!important;overflow-y:auto!important}',
'  .tandem-fs-main,.tandem-fs-props,.tandem-content,.fs-tandem-right{width:100%!important}',
'  table{display:block!important;overflow-x:auto!important;-webkit-overflow-scrolling:touch!important}',
'  thead,tbody,tr{display:table;width:100%;table-layout:auto}',
'  .sap-lp-tiles,.fiori-tiles,.sap-fs-tiles{grid-template-columns:repeat(2,1fr)!important;gap:10px!important;padding:12px!important}',
'  .sap-apm-grid,.apm-grid{grid-template-columns:1fr!important}',
'  .sap-wo-detail{width:100%!important;max-width:100%!important}',
'  .pid-drawing{width:100%!important;min-width:500px!important;overflow-x:auto!important}',
'  .ep-btn,.sl-launch-btn,.h-btn,.h-back,.h-alert-btn,.tb-alert-btn,.tb-back{min-height:44px!important}',
'  .fs-overlay{overflow-y:auto!important}',
'  .fs-close,.sap-fs-close,.acc-fs-close,.tandem-fs-close,.td-close,.sap-close,.acc-close{min-width:44px!important;min-height:44px!important;display:flex!important;align-items:center!important;justify-content:center!important}',
'}',
'@media(max-width:480px){',
'  .sap-lp-tiles,.fiori-tiles,.sap-fs-tiles{grid-template-columns:1fr!important}',
'  .fiori-tile,.sap-lp-tile,.sap-fs-tile{min-height:80px!important}',
'  .acc-fs-tree,.acc-fs-nav{max-height:150px!important}',
'}'
].join('\n');
document.head.appendChild(mobileCSS);

/* ----------------------------------------------------------------
   ISSUE 2: SAP FIORI REALISTIC ENHANCEMENTS
   ---------------------------------------------------------------- */
var sapCSS = document.createElement('style');
sapCSS.id = 'dt-sap-enhancements';
sapCSS.textContent = [
'/* Fiori Shell Header */',
'.sap-fiori-shell{height:44px!important;background:#354A5F!important;display:flex!important;align-items:center!important;padding:0 16px!important;gap:12px!important;flex-shrink:0!important}',
'.sap-fiori-shell .sap-logo-text{font-size:16px;font-weight:800;color:#fff;font-family:Arial,sans-serif;letter-spacing:1px}',
'.sap-fiori-shell .sap-shell-spacer{flex:1}',
'.sap-fiori-shell .sap-shell-icon{width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,.7);font-size:14px;cursor:pointer;transition:background .2s}',
'.sap-fiori-shell .sap-shell-icon:hover{background:rgba(255,255,255,.1)}',
'.sap-fiori-shell .sap-shell-avatar{width:32px;height:32px;border-radius:50%;background:#6C8EBF;display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;font-weight:700}',
'/* Fiori Breadcrumb Bar */',
'.sap-fiori-breadcrumb{height:36px;background:#fff;border-bottom:1px solid #d9d9d9;display:flex;align-items:center;padding:0 16px;gap:0;flex-shrink:0;overflow-x:auto}',
'.sap-fiori-breadcrumb .sap-bc-tab{padding:8px 16px;font-size:12px;font-weight:600;color:#32363A;cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;white-space:nowrap;font-family:"72",Arial,sans-serif}',
'.sap-fiori-breadcrumb .sap-bc-tab:hover{color:#0854A0;border-bottom-color:#0854A0}',
'.sap-fiori-breadcrumb .sap-bc-tab.active{color:#0854A0;border-bottom-color:#0854A0}',
'/* Fiori Tiles - realistic */',
'.fiori-tile-real{background:#fff;border-radius:4px;padding:16px;cursor:pointer;transition:box-shadow .15s;min-height:120px;display:flex;flex-direction:column;justify-content:space-between;border:1px solid #e5e5e5;border-left:4px solid #0854A0;position:relative}',
'.fiori-tile-real:hover{box-shadow:0 2px 12px rgba(0,0,0,.12)}',
'.fiori-tile-real .ft-icon{font-family:"IBM Plex Mono",monospace;font-size:12px;font-weight:800;color:#354A5F;background:#f0f2f5;width:36px;height:36px;border-radius:4px;display:flex;align-items:center;justify-content:center;margin-bottom:8px}',
'.fiori-tile-real .ft-title{font-size:13px;font-weight:600;color:#32363A;line-height:1.3}',
'.fiori-tile-real .ft-count{font-size:28px;font-weight:300;color:#32363A;font-family:"72",Arial,sans-serif;margin-top:8px}',
'.fiori-tile-real .ft-sub{font-size:11px;color:#6a6d70;margin-top:4px}',
'.fiori-tile-real.accent-re{border-left-color:#BB0000}',
'.fiori-tile-real.accent-or{border-left-color:#E78C07}',
'.fiori-tile-real.accent-gr{border-left-color:#2B7D2B}',
'.fiori-tile-real.accent-cy{border-left-color:#0854A0}',
'.fiori-tile-real.accent-ye{border-left-color:#D4790B}',
'.fiori-tile-real.accent-pu{border-left-color:#8C3D95}',
'/* Gemelo Digital section in SAP */',
'.sap-gemelo-section{padding:24px;background:#F0F2F5}',
'.sap-gemelo-3d-area{background:#1a1a2e;border-radius:8px;padding:40px;text-align:center;margin-bottom:16px;border:1px solid #e0e0e0}',
'.sap-gemelo-3d-area h3{color:#fff;font-size:18px;margin-bottom:8px}',
'.sap-gemelo-3d-area p{color:rgba(255,255,255,.6);font-size:12px;margin-bottom:16px}',
'.sap-gemelo-btn-open{padding:10px 24px;background:#0854A0;color:#fff;border:none;border-radius:4px;font-size:13px;font-weight:600;cursor:pointer;transition:background .2s}',
'.sap-gemelo-btn-open:hover{background:#064079}',
'.sap-gemelo-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;margin-top:16px}',
'.sap-gemelo-card{background:#fff;border:1px solid #e5e5e5;border-radius:4px;padding:12px;cursor:pointer;transition:box-shadow .2s}',
'.sap-gemelo-card:hover{box-shadow:0 2px 8px rgba(0,0,0,.1)}',
'.sap-gemelo-card-tag{font-family:"IBM Plex Mono",monospace;font-size:11px;font-weight:700;color:#354A5F}',
'.sap-gemelo-card-name{font-size:12px;color:#666;margin-top:2px}',
'.sap-gemelo-card-status{font-size:10px;margin-top:6px;font-weight:600}',
'.sap-gemelo-card-status.ok{color:#2B7D2B}',
'.sap-gemelo-card-status.warn{color:#E78C07}',
'.sap-gemelo-card-status.crit{color:#BB0000}',
'/* SAP table improvements */',
'.sap-fiori-table{width:100%;border-collapse:collapse;font-size:12px;background:#fff;border:1px solid #e5e5e5}',
'.sap-fiori-table th{background:#F0F2F5;color:#32363A;padding:10px 12px;text-align:left;font-size:11px;font-weight:600;border-bottom:1px solid #d9d9d9;white-space:nowrap;position:relative}',
'.sap-fiori-table th::after{content:" ^";font-size:8px;color:#bbb}',
'.sap-fiori-table td{padding:10px 12px;border-bottom:1px solid #ededed;color:#32363A;vertical-align:middle}',
'.sap-fiori-table tr:nth-child(even){background:#f7f7f7}',
'.sap-fiori-table tr:hover{background:#E8F0FE;cursor:pointer}',
'.sap-fiori-status{font-size:10px;padding:3px 10px;border-radius:12px;font-weight:600;white-space:nowrap;display:inline-block}',
'.sap-fiori-status.st-re{background:#FDECEA;color:#BB0000}',
'.sap-fiori-status.st-or{background:#FFF3E0;color:#E78C07}',
'.sap-fiori-status.st-gr{background:#E8F5E9;color:#2B7D2B}',
'.sap-fiori-status.st-bl{background:#E3F2FD;color:#0854A0}',
'.sap-fiori-status.st-gy{background:#F5F5F5;color:#666}',
'.sap-fiori-btn-vis{padding:4px 12px;border:1px solid #0854A0;background:transparent;color:#0854A0;border-radius:4px;font-size:10px;font-weight:600;cursor:pointer;transition:all .15s}',
'.sap-fiori-btn-vis:hover{background:#0854A0;color:#fff}',
].join('\n');
document.head.appendChild(sapCSS);

/* ----------------------------------------------------------------
   ISSUE 3: ACC AUTODESK CONSTRUCTION CLOUD CSS
   ---------------------------------------------------------------- */
var accCSS = document.createElement('style');
accCSS.id = 'dt-acc-enhancements';
accCSS.textContent = [
'/* ACC Header */',
'.acc-autodesk-header{height:48px!important;background:#1C1C1C!important;display:flex!important;align-items:center!important;padding:0 16px!important;gap:12px!important;flex-shrink:0!important;border-bottom:1px solid #333!important}',
'.acc-autodesk-header .acc-a-logo{width:28px;height:28px;background:#fff;border-radius:2px;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:800;color:#1C1C1C;font-family:Arial,sans-serif}',
'.acc-autodesk-header .acc-project-name{font-size:13px;font-weight:600;color:#fff;font-family:"Space Grotesk",sans-serif}',
'.acc-autodesk-header .acc-header-spacer{flex:1}',
'.acc-autodesk-header .acc-user-info{font-size:10px;color:rgba(255,255,255,.5)}',
'/* ACC File Tree */',
'.acc-file-tree{padding:8px 0;width:240px;background:#262626;border-right:1px solid #333;overflow-y:auto;flex-shrink:0}',
'.acc-tree-folder{padding:6px 12px 6px 16px;font-size:12px;color:#e0e0e0;cursor:pointer;display:flex;align-items:center;gap:6px;transition:background .15s;font-weight:600;user-select:none}',
'.acc-tree-folder:hover{background:rgba(255,255,255,.05)}',
'.acc-tree-folder .acc-fold-arrow{font-size:8px;color:#888;transition:transform .2s;width:12px;text-align:center}',
'.acc-tree-folder.open .acc-fold-arrow{transform:rotate(90deg)}',
'.acc-tree-folder .acc-fold-icon{color:#F0A000}',
'.acc-tree-docs{display:none;padding-left:16px}',
'.acc-tree-folder.open + .acc-tree-docs{display:block}',
'.acc-tree-doc{padding:5px 12px 5px 20px;font-size:11px;color:#aaa;cursor:pointer;transition:all .15s;border-left:2px solid transparent}',
'.acc-tree-doc:hover{background:rgba(255,255,255,.05);color:#fff}',
'.acc-tree-doc.sel{background:rgba(0,133,255,.15);color:#4DA3FF;border-left-color:#4DA3FF}',
'/* ACC Doc List Table */',
'.acc-doc-list-table{width:100%;border-collapse:collapse;font-size:12px;background:#fff}',
'.acc-doc-list-table th{background:#f0f0f0;color:#333;padding:8px 12px;text-align:left;font-size:11px;font-weight:600;border-bottom:1px solid #ddd;white-space:nowrap}',
'.acc-doc-list-table td{padding:8px 12px;border-bottom:1px solid #eee;color:#333}',
'.acc-doc-list-table tr:hover{background:#f5f8ff;cursor:pointer}',
'.acc-doc-status{font-size:10px;padding:2px 8px;border-radius:10px;font-weight:600;display:inline-block}',
'.acc-doc-status.approved{background:#E8F5E9;color:#2E7D32}',
'.acc-doc-status.review{background:#FFF8E1;color:#F57F17}',
'.acc-doc-status.draft{background:#F5F5F5;color:#757575}',
'/* ACC Doc Viewer */',
'.acc-doc-viewer-wrap{flex:1;display:flex;flex-direction:column;overflow:hidden;background:#F5F5F5}',
'.acc-doc-viewer-toolbar{height:40px;background:#fff;border-bottom:1px solid #e0e0e0;display:flex;align-items:center;padding:0 16px;gap:8px;flex-shrink:0}',
'.acc-doc-viewer-toolbar .acc-vt-btn{padding:4px 12px;border:1px solid #ccc;background:#fff;color:#333;border-radius:4px;font-size:11px;cursor:pointer;transition:all .15s}',
'.acc-doc-viewer-toolbar .acc-vt-btn:hover{background:#f0f0f0;border-color:#999}',
'.acc-doc-viewer-toolbar .acc-vt-btn.primary{background:#0696D7;color:#fff;border-color:#0696D7}',
'.acc-doc-viewer-toolbar .acc-vt-btn.primary:hover{background:#0580B8}',
'.acc-doc-viewer-main{flex:1;display:flex;overflow:hidden}',
'.acc-doc-canvas{flex:1;display:flex;align-items:center;justify-content:center;overflow:auto;padding:20px}',
'.acc-doc-meta-right{width:260px;background:#fff;border-left:1px solid #e0e0e0;padding:16px;overflow-y:auto;flex-shrink:0}',
'.acc-doc-meta-right .acc-mr-section{font-size:10px;font-weight:700;letter-spacing:.08em;color:#888;text-transform:uppercase;margin:14px 0 6px;padding-bottom:4px;border-bottom:1px solid #eee}',
'.acc-doc-meta-right .acc-mr-section:first-child{margin-top:0}',
'.acc-doc-meta-right .acc-mr-row{display:flex;justify-content:space-between;padding:3px 0;font-size:11px}',
'.acc-doc-meta-right .acc-mr-row .mrk{color:#888}.acc-doc-meta-right .acc-mr-row .mrv{color:#333;font-weight:500}',
'/* P&ID Drawing Enhanced */',
'.acc-pid-enhanced{width:100%;min-width:600px;height:420px;background:#1E2838;border-radius:8px;position:relative;overflow:hidden;border:1px solid #333}',
'.acc-pid-enhanced .pid-equip{position:absolute;border:2px solid;border-radius:4px;display:flex;flex-direction:column;align-items:center;justify-content:center;font-family:"IBM Plex Mono",monospace;font-size:9px;padding:2px 4px;text-align:center;line-height:1.2}',
'.acc-pid-enhanced .pid-pipe{position:absolute;background:#5AC8FA;opacity:.5}',
'.acc-pid-enhanced .pid-vlv{position:absolute;width:10px;height:10px;border:2px solid #E94560;border-radius:50%;background:rgba(233,69,96,.2)}',
'.acc-pid-enhanced .pid-stamp{position:absolute;bottom:8px;right:8px;font-family:"IBM Plex Mono",monospace;font-size:8px;color:rgba(255,255,255,.25)}',
'/* Datasheet view */',
'.acc-datasheet{background:#fff;border:1px solid #ddd;border-radius:4px;padding:20px;width:100%;max-width:600px}',
'.acc-datasheet h3{font-size:14px;color:#333;margin-bottom:12px;border-bottom:2px solid #0696D7;padding-bottom:6px}',
'.acc-datasheet .ds-row{display:flex;border-bottom:1px solid #eee;padding:6px 0;font-size:12px}',
'.acc-datasheet .ds-row .ds-k{width:160px;color:#666;font-weight:500;flex-shrink:0}.acc-datasheet .ds-row .ds-v{color:#333;font-weight:600}',
'@media(max-width:768px){',
'  .acc-file-tree{width:100%!important;max-height:180px!important}',
'  .acc-doc-meta-right{width:100%!important;max-height:200px!important;border-left:none!important;border-top:1px solid #e0e0e0!important}',
'  .acc-doc-viewer-main{flex-direction:column!important}',
'  .acc-pid-enhanced{min-width:400px!important;height:300px!important}',
'}'
].join('\n');
document.head.appendChild(accCSS);


/* ================================================================
   PLANT-SPECIFIC DATA for SAP and ACC
   ================================================================ */

var PLANT_DATA = {
  tas: {
    name: 'Terminal Gas LP TAS-AGS-01',
    code: 'TAS-AGS-01',
    sapTiles: [
      {icon:'PM',title:'Ordenes de Trabajo',count:'8',sub:'PM - Plant Maintenance',accent:'accent-re',nav:'pm'},
      {icon:'NT',title:'Notificaciones',count:'3',sub:'Pendientes de revision',accent:'accent-or',nav:'pm'},
      {icon:'AH',title:'Asset Health',count:'17',sub:'APM - Salud de Activos',accent:'accent-cy',nav:'apm'},
      {icon:'MM',title:'Stock Refacciones',count:'6',sub:'MM - Materials Mgmt',accent:'accent-gr',nav:'mm'},
      {icon:'CO',title:'Costos Mantenimiento',count:'$1.2M',sub:'YTD 2026',accent:'accent-pu',nav:''},
      {icon:'RP',title:'Reportes',count:'12',sub:'Analytics & BI',accent:'',nav:''}
    ],
    accFolders: {
      'P&ID Gas LP': [
        {name:'PID-TAS-001 Sistema General',tipo:'DWG',ver:'REV.05',fecha:'2025-11-15',estado:'Aprobado',tam:'3.2 MB'},
        {name:'PID-TAS-002 Almacenamiento',tipo:'DWG',ver:'REV.04',fecha:'2025-10-20',estado:'Aprobado',tam:'2.8 MB'},
        {name:'PID-TAS-003 Bombeo',tipo:'DWG',ver:'REV.03',fecha:'2025-09-10',estado:'En revision',tam:'2.1 MB'},
        {name:'PID-TAS-004 Despacho',tipo:'DWG',ver:'REV.05',fecha:'2025-11-01',estado:'Aprobado',tam:'1.9 MB'}
      ],
      'PFD': [
        {name:'PFD-TAS-001 Proceso General',tipo:'PDF',ver:'REV.03',fecha:'2025-08-20',estado:'Aprobado',tam:'1.8 MB'},
        {name:'PFD-TAS-002 Balance Masa',tipo:'PDF',ver:'REV.02',fecha:'2025-06-15',estado:'Aprobado',tam:'1.2 MB'},
        {name:'PFD-TAS-003 Utilidades',tipo:'PDF',ver:'REV.01',fecha:'2025-04-10',estado:'Borrador',tam:'0.9 MB'}
      ],
      'Plot Plan': [
        {name:'PLT-TAS-001 Layout General',tipo:'DWG',ver:'REV.04',fecha:'2025-10-10',estado:'Aprobado',tam:'5.1 MB'},
        {name:'PLT-TAS-002 Areas Clasificadas',tipo:'DWG',ver:'REV.03',fecha:'2025-09-05',estado:'Aprobado',tam:'3.4 MB'},
        {name:'PLT-TAS-003 Rutas Evacuacion',tipo:'PDF',ver:'REV.02',fecha:'2025-07-22',estado:'Aprobado',tam:'2.2 MB'}
      ],
      'Isometricos': [
        {name:'ISO-TAS-001 Header Principal',tipo:'DWG',ver:'REV.03',fecha:'2025-08-15',estado:'Aprobado',tam:'4.5 MB'},
        {name:'ISO-TAS-002 Lineas Esferas',tipo:'DWG',ver:'REV.02',fecha:'2025-07-01',estado:'Aprobado',tam:'3.8 MB'},
        {name:'ISO-TAS-003 Descarga Bombas',tipo:'DWG',ver:'REV.02',fecha:'2025-06-20',estado:'En revision',tam:'3.2 MB'}
      ],
      'SCI': [
        {name:'SCI-TAS-001 Red Contra Incendio',tipo:'DWG',ver:'REV.03',fecha:'2025-09-15',estado:'Aprobado',tam:'2.9 MB'},
        {name:'SCI-TAS-002 Rociadores',tipo:'DWG',ver:'REV.02',fecha:'2025-08-01',estado:'Aprobado',tam:'2.1 MB'},
        {name:'SCI-TAS-003 Hidrantes',tipo:'PDF',ver:'REV.01',fecha:'2025-05-20',estado:'Borrador',tam:'1.5 MB'}
      ],
      'Electricos': [
        {name:'ELE-TAS-001 Unifilar',tipo:'DWG',ver:'REV.03',fecha:'2025-07-08',estado:'Aprobado',tam:'3.8 MB'},
        {name:'ELE-TAS-002 Fuerza y Control',tipo:'DWG',ver:'REV.02',fecha:'2025-05-15',estado:'Aprobado',tam:'2.6 MB'},
        {name:'ELE-TAS-003 Alumbrado',tipo:'DWG',ver:'REV.01',fecha:'2025-04-10',estado:'En revision',tam:'1.8 MB'}
      ],
      'Instrumentacion': [
        {name:'INS-TAS-001 Loop Diagrams',tipo:'DWG',ver:'REV.02',fecha:'2025-09-15',estado:'Aprobado',tam:'2.9 MB'},
        {name:'INS-TAS-002 Logica SIS',tipo:'DWG',ver:'REV.03',fecha:'2025-10-01',estado:'Aprobado',tam:'3.4 MB'},
        {name:'INS-TAS-003 Indice Instrumentos',tipo:'PDF',ver:'REV.04',fecha:'2025-11-05',estado:'Aprobado',tam:'1.1 MB'}
      ],
      'Civil': [
        {name:'CIV-TAS-001 Cimentaciones',tipo:'DWG',ver:'REV.01',fecha:'2024-12-20',estado:'Aprobado',tam:'6.1 MB'},
        {name:'CIV-TAS-002 Muros',tipo:'DWG',ver:'REV.01',fecha:'2024-11-15',estado:'Aprobado',tam:'4.2 MB'},
        {name:'CIV-TAS-003 Drenajes',tipo:'DWG',ver:'REV.02',fecha:'2025-03-10',estado:'Aprobado',tam:'2.8 MB'}
      ],
      'Datasheets': [
        {name:'DS-SPH-001 Esferas Almacenamiento',tipo:'PDF',ver:'REV.02',fecha:'2024-06-15',estado:'Aprobado',tam:'2.4 MB'},
        {name:'DS-PMP-001 Bomba Centrifuga',tipo:'PDF',ver:'REV.01',fecha:'2024-05-10',estado:'Aprobado',tam:'1.8 MB'},
        {name:'DS-CMP-001 Compresor',tipo:'PDF',ver:'REV.02',fecha:'2024-07-20',estado:'Aprobado',tam:'2.1 MB'}
      ]
    },
    pidEquips: [
      {tag:'SPH-01',x:20,y:40,w:80,h:40,color:'#5AC8FA'},
      {tag:'SPH-02',x:20,y:120,w:80,h:40,color:'#5AC8FA'},
      {tag:'SPH-03',x:20,y:200,w:80,h:40,color:'#5AC8FA'},
      {tag:'MANIFOLD',x:220,y:120,w:80,h:40,color:'#5AC8FA'},
      {tag:'PMP-01',x:350,y:80,w:70,h:40,color:'#5AC8FA'},
      {tag:'PMP-02',x:350,y:160,w:70,h:40,color:'#5AC8FA'},
      {tag:'CMP-01',x:470,y:60,w:80,h:40,color:'#FF5500'},
      {tag:'LOADING',x:470,y:180,w:80,h:40,color:'#5AC8FA'},
      {tag:'SCI RING',x:220,y:300,w:100,h:40,color:'#E94560'}
    ]
  },
  gnc: {
    name: 'Estacion GNC MTY-01',
    code: 'GNC-MTY-01',
    sapTiles: [
      {icon:'OT',title:'Ordenes de Trabajo',count:'6',sub:'Activas en planta',accent:'accent-re',nav:'pm'},
      {icon:'NT',title:'Notificaciones',count:'12',sub:'Pendientes revision',accent:'accent-or',nav:'pm'},
      {icon:'AH',title:'Asset Health',count:'92%',sub:'Health score promedio',accent:'accent-cy',nav:'apm'},
      {icon:'ST',title:'Stock Refacciones',count:'24',sub:'Items en inventario',accent:'accent-gr',nav:'mm'},
      {icon:'CO',title:'Costos Mtto',count:'$42K',sub:'Mes actual MXN',accent:'accent-ye',nav:''},
      {icon:'RP',title:'Reportes',count:'8',sub:'Reportes disponibles',accent:'',nav:''}
    ],
    accFolders: {
      'P&ID Compresion': [
        {name:'PID-GNC-001 Sistema General',tipo:'DWG',ver:'REV.05',fecha:'2026-02-15',estado:'Aprobado',tam:'3.8 MB'},
        {name:'PID-GNC-002 Compresion',tipo:'DWG',ver:'REV.04',fecha:'2026-01-10',estado:'Aprobado',tam:'2.9 MB'},
        {name:'PID-GNC-003 Cascadas',tipo:'DWG',ver:'REV.03',fecha:'2025-12-05',estado:'En revision',tam:'2.4 MB'},
        {name:'PID-GNC-004 Dispensadores',tipo:'DWG',ver:'REV.03',fecha:'2025-11-20',estado:'Aprobado',tam:'1.8 MB'}
      ],
      'PFD': [
        {name:'PFD-GNC-001 Diagrama Flujo',tipo:'PDF',ver:'REV.03',fecha:'2025-10-15',estado:'Aprobado',tam:'1.6 MB'},
        {name:'PFD-GNC-002 Balance',tipo:'PDF',ver:'REV.02',fecha:'2025-08-20',estado:'Aprobado',tam:'1.1 MB'},
        {name:'PFD-GNC-003 Utilidades',tipo:'PDF',ver:'REV.01',fecha:'2025-06-10',estado:'Borrador',tam:'0.8 MB'}
      ],
      'Estacion Layout': [
        {name:'LAY-GNC-001 Plot Plan',tipo:'DWG',ver:'REV.04',fecha:'2026-01-05',estado:'Aprobado',tam:'4.2 MB'},
        {name:'LAY-GNC-002 Areas Peligrosas',tipo:'DWG',ver:'REV.03',fecha:'2025-11-15',estado:'Aprobado',tam:'3.1 MB'},
        {name:'LAY-GNC-003 Rutas Acceso',tipo:'PDF',ver:'REV.02',fecha:'2025-09-20',estado:'Aprobado',tam:'1.9 MB'}
      ],
      'Electricos': [
        {name:'ELE-GNC-001 Diagrama Unifilar',tipo:'DWG',ver:'REV.03',fecha:'2025-12-10',estado:'Aprobado',tam:'3.2 MB'},
        {name:'ELE-GNC-002 Fuerza y Control',tipo:'DWG',ver:'REV.02',fecha:'2025-10-05',estado:'Aprobado',tam:'2.4 MB'},
        {name:'ELE-GNC-003 Tableros MCC',tipo:'DWG',ver:'REV.02',fecha:'2025-09-15',estado:'En revision',tam:'1.8 MB'}
      ],
      'Instrumentacion': [
        {name:'INS-GNC-001 Loop Diagrams',tipo:'DWG',ver:'REV.03',fecha:'2025-11-20',estado:'Aprobado',tam:'2.6 MB'},
        {name:'INS-GNC-002 Logica SIS',tipo:'DWG',ver:'REV.02',fecha:'2025-10-01',estado:'Aprobado',tam:'3.1 MB'},
        {name:'INS-GNC-003 Hook-Up Details',tipo:'DWG',ver:'REV.01',fecha:'2025-08-15',estado:'Borrador',tam:'1.4 MB'}
      ]
    },
    pidEquips: [
      {tag:'FE-001\\nMedicion',x:10,y:130,w:80,h:40,color:'#5AC8FA'},
      {tag:'PCV-001\\nRegulador',x:150,y:130,w:80,h:40,color:'#5AC8FA'},
      {tag:'FL-001\\nFiltro',x:280,y:100,w:70,h:40,color:'#5AC8FA'},
      {tag:'K-001/002\\nCompresores',x:400,y:120,w:90,h:45,color:'#FF5500'},
      {tag:'CSC-H\\n250 bar',x:530,y:60,w:80,h:35,color:'#CC3322'},
      {tag:'CSC-M\\n200 bar',x:530,y:130,w:80,h:35,color:'#DDAA00'},
      {tag:'CSC-L\\n150 bar',x:530,y:200,w:80,h:35,color:'#22AA44'},
      {tag:'DSP-01..04\\nDispensadores',x:660,y:130,w:90,h:40,color:'#5AC8FA'}
    ]
  },
  lng: {
    name: 'Planta LNG Regasificacion MTY-01',
    code: 'LNG-MTY-01',
    sapTiles: [
      {icon:'PM',title:'Ordenes Abiertas',count:'3',sub:'PM - Mantenimiento',accent:'accent-re',nav:'pm'},
      {icon:'WO',title:'Total Work Orders',count:'8',sub:'PM-LNG-6001 ... 6008',accent:'accent-or',nav:'pm'},
      {icon:'AH',title:'Health Score Prom.',count:'88%',sub:'APM - Asset Performance',accent:'accent-gr',nav:'apm'},
      {icon:'MM',title:'Materiales Criogenicos',count:'5',sub:'MM - Stock Disponible',accent:'accent-ye',nav:'mm'},
      {icon:'BT',title:'Uptime Integracion',count:'99.8%',sub:'BTP - Cloud Integration',accent:'accent-cy',nav:'btp'},
      {icon:'HR',title:'Hrs Operacion',count:'24,120',sub:'Equipos Criogenicos',accent:'',nav:''}
    ],
    accFolders: {
      'P&ID Criogenicos': [
        {name:'PID-LNG-001 Regasificacion',tipo:'DWG',ver:'REV.04',fecha:'2026-01-15',estado:'Aprobado',tam:'4.2 MB'},
        {name:'PID-LNG-002 Almacenamiento GNL',tipo:'DWG',ver:'REV.03',fecha:'2025-12-10',estado:'Aprobado',tam:'3.6 MB'},
        {name:'PID-LNG-003 Vaporizadores',tipo:'DWG',ver:'REV.03',fecha:'2025-11-20',estado:'En revision',tam:'2.8 MB'},
        {name:'PID-LNG-004 Odorizacion',tipo:'DWG',ver:'REV.02',fecha:'2025-10-05',estado:'Aprobado',tam:'1.5 MB'}
      ],
      'PFD': [
        {name:'PFD-LNG-001 Proceso Regasificacion',tipo:'PDF',ver:'REV.03',fecha:'2025-09-15',estado:'Aprobado',tam:'2.1 MB'},
        {name:'PFD-LNG-002 Balance Termico',tipo:'PDF',ver:'REV.02',fecha:'2025-07-20',estado:'Aprobado',tam:'1.4 MB'},
        {name:'PFD-LNG-003 Servicios Auxiliares',tipo:'PDF',ver:'REV.01',fecha:'2025-05-10',estado:'Borrador',tam:'0.9 MB'}
      ],
      'GA Drawings': [
        {name:'GA-LNG-001 Layout General',tipo:'DWG',ver:'REV.04',fecha:'2026-02-01',estado:'Aprobado',tam:'5.8 MB'},
        {name:'GA-LNG-002 Rack Tuberias',tipo:'DWG',ver:'REV.03',fecha:'2025-11-15',estado:'Aprobado',tam:'4.1 MB'},
        {name:'GA-LNG-003 Tanque Criogenico',tipo:'DWG',ver:'REV.02',fecha:'2025-09-20',estado:'Aprobado',tam:'3.5 MB'}
      ],
      'Datasheets Criogenicos': [
        {name:'DS-LNG-001 Tanque Criogenico',tipo:'PDF',ver:'REV.02',fecha:'2025-06-15',estado:'Aprobado',tam:'2.8 MB'},
        {name:'DS-LNG-002 Vaporizador AAV',tipo:'PDF',ver:'REV.01',fecha:'2025-04-20',estado:'Aprobado',tam:'2.1 MB'},
        {name:'DS-LNG-003 Bomba Criogenica',tipo:'PDF',ver:'REV.02',fecha:'2025-07-10',estado:'Aprobado',tam:'1.9 MB'}
      ],
      'HAZOP': [
        {name:'HAZ-LNG-001 Nodos Criogenicos',tipo:'PDF',ver:'REV.02',fecha:'2025-12-05',estado:'Aprobado',tam:'4.5 MB'},
        {name:'HAZ-LNG-002 Nodos Regasificacion',tipo:'PDF',ver:'REV.01',fecha:'2025-10-15',estado:'En revision',tam:'3.8 MB'},
        {name:'HAZ-LNG-003 Acciones Pendientes',tipo:'PDF',ver:'REV.01',fecha:'2025-11-20',estado:'Borrador',tam:'1.2 MB'}
      ],
      'SOPs': [
        {name:'SOP-LNG-001 Arranque Planta',tipo:'PDF',ver:'REV.03',fecha:'2025-09-05',estado:'Aprobado',tam:'1.5 MB'},
        {name:'SOP-LNG-002 Paro Emergencia',tipo:'PDF',ver:'REV.02',fecha:'2025-08-01',estado:'Aprobado',tam:'1.1 MB'},
        {name:'SOP-LNG-003 Carga Cisterna',tipo:'PDF',ver:'REV.02',fecha:'2025-07-15',estado:'Aprobado',tam:'0.9 MB'},
        {name:'SOP-LNG-004 Purga Criogenica',tipo:'PDF',ver:'REV.01',fecha:'2025-06-20',estado:'En revision',tam:'0.7 MB'}
      ]
    },
    pidEquips: [
      {tag:'TK-001\\nTanque GNL',x:20,y:60,w:90,h:60,color:'#00C8F0'},
      {tag:'P-001\\nBomba Crio',x:160,y:120,w:80,h:40,color:'#5AC8FA'},
      {tag:'V-001\\nVaporizador',x:300,y:60,w:80,h:50,color:'#FF5500'},
      {tag:'V-002\\nVap. Agua',x:300,y:160,w:80,h:50,color:'#FF5500'},
      {tag:'ODR-001\\nOdorizador',x:440,y:110,w:80,h:40,color:'#10D858'},
      {tag:'MET-001\\nMedicion',x:560,y:110,w:80,h:40,color:'#5AC8FA'}
    ]
  },
  ductos: {
    name: 'Estacion Compresion Ductos DUC-CEN-01',
    code: 'DUC-CEN-01',
    sapTiles: [
      {icon:'PM',title:'Ordenes Urgentes',count:'2',sub:'PM - Prioridad 1',accent:'accent-re',nav:'pm'},
      {icon:'OT',title:'Ordenes Totales',count:'10',sub:'PM - Abiertas + Prog.',accent:'accent-or',nav:'pm'},
      {icon:'AH',title:'Salud Compresores',count:'87%',sub:'APM - Health Index',accent:'accent-cy',nav:'apm'},
      {icon:'MM',title:'Items en Stock',count:'238',sub:'MM - $1.24M MXN',accent:'accent-gr',nav:'mm'},
      {icon:'BT',title:'Integraciones BTP',count:'5',sub:'BTP - Todas activas',accent:'accent-ye',nav:'btp'},
      {icon:'UP',title:'Disponibilidad',count:'99.5%',sub:'KPI - Ultimo mes',accent:'',nav:''}
    ],
    accFolders: {
      'P&ID Pipeline': [
        {name:'PID-DUC-001 Header Compresion',tipo:'DWG',ver:'REV.04',fecha:'2026-02-15',estado:'Aprobado',tam:'4.5 MB'},
        {name:'PID-DUC-002 Slug Catcher',tipo:'DWG',ver:'REV.03',fecha:'2026-01-20',estado:'Aprobado',tam:'3.2 MB'},
        {name:'PID-DUC-003 Scrubber',tipo:'DWG',ver:'REV.03',fecha:'2025-12-10',estado:'En revision',tam:'2.8 MB'},
        {name:'PID-DUC-004 Aeroenfriadores',tipo:'DWG',ver:'REV.02',fecha:'2025-11-05',estado:'Aprobado',tam:'2.1 MB'}
      ],
      'PFD': [
        {name:'PFD-DUC-001 Proceso General',tipo:'PDF',ver:'REV.03',fecha:'2025-10-15',estado:'Aprobado',tam:'2.4 MB'},
        {name:'PFD-DUC-002 Compresion',tipo:'PDF',ver:'REV.02',fecha:'2025-08-20',estado:'Aprobado',tam:'1.8 MB'},
        {name:'PFD-DUC-003 Deshidratacion',tipo:'PDF',ver:'REV.01',fecha:'2025-06-15',estado:'Borrador',tam:'1.1 MB'}
      ],
      'Isometricos': [
        {name:'ISO-DUC-001 Linea 30" Entrada',tipo:'DWG',ver:'REV.03',fecha:'2025-12-05',estado:'Aprobado',tam:'5.2 MB'},
        {name:'ISO-DUC-002 Headers Alta',tipo:'DWG',ver:'REV.02',fecha:'2025-10-20',estado:'Aprobado',tam:'4.1 MB'},
        {name:'ISO-DUC-003 Descarga Compresores',tipo:'DWG',ver:'REV.02',fecha:'2025-09-15',estado:'En revision',tam:'3.6 MB'}
      ],
      'HAZOP': [
        {name:'HAZ-DUC-001 Nodos Compresion',tipo:'PDF',ver:'REV.02',fecha:'2025-12-01',estado:'Aprobado',tam:'4.8 MB'},
        {name:'HAZ-DUC-002 Nodos Pipeline',tipo:'PDF',ver:'REV.01',fecha:'2025-10-15',estado:'Aprobado',tam:'3.5 MB'},
        {name:'HAZ-DUC-003 Acciones Pendientes',tipo:'PDF',ver:'REV.01',fecha:'2025-11-20',estado:'En revision',tam:'1.5 MB'}
      ],
      'SIF': [
        {name:'SIF-DUC-001 Lazos ESD',tipo:'PDF',ver:'REV.02',fecha:'2026-01-15',estado:'Aprobado',tam:'3.2 MB'},
        {name:'SIF-DUC-002 Lazos F&G',tipo:'PDF',ver:'REV.02',fecha:'2025-12-20',estado:'Aprobado',tam:'2.8 MB'},
        {name:'SIF-DUC-003 Verificacion SIL',tipo:'PDF',ver:'REV.01',fecha:'2025-11-05',estado:'En revision',tam:'2.1 MB'}
      ],
      'Cause-Effect': [
        {name:'CE-DUC-001 Matriz ESD',tipo:'PDF',ver:'REV.03',fecha:'2026-02-20',estado:'Aprobado',tam:'2.4 MB'},
        {name:'CE-DUC-002 Matriz F&G',tipo:'PDF',ver:'REV.02',fecha:'2026-01-10',estado:'Aprobado',tam:'1.9 MB'},
        {name:'CE-DUC-003 Interlocks',tipo:'PDF',ver:'REV.01',fecha:'2025-12-05',estado:'Borrador',tam:'1.2 MB'}
      ]
    },
    pidEquips: [
      {tag:'PL-001\\nPipeline',x:10,y:140,w:80,h:40,color:'#5AC8FA'},
      {tag:'XV-001\\nESD Vlv',x:120,y:140,w:70,h:40,color:'#E94560'},
      {tag:'V-100\\nSlug Cat.',x:230,y:100,w:80,h:45,color:'#5AC8FA'},
      {tag:'V-101\\nScrubber',x:230,y:200,w:80,h:40,color:'#5AC8FA'},
      {tag:'CMP-01/02\\nCompresores',x:380,y:120,w:100,h:50,color:'#FF5500'},
      {tag:'ACL-01\\nAeroenfr.',x:380,y:230,w:80,h:40,color:'#5AC8FA'},
      {tag:'MET-01\\nMedicion',x:520,y:140,w:80,h:40,color:'#10D858'}
    ]
  },
  fv: {
    name: 'Planta Solar FV-SON-01',
    code: 'FV-SON-01',
    sapTiles: [
      {icon:'PM',title:'Ordenes Abiertas',count:'4',sub:'PM - Mantenimiento',accent:'accent-re',nav:'pm'},
      {icon:'WO',title:'Total Work Orders',count:'12',sub:'PM-FV-001 ... 012',accent:'accent-or',nav:'pm'},
      {icon:'AH',title:'Health Score',count:'94%',sub:'APM - Inversores/Trackers',accent:'accent-gr',nav:'apm'},
      {icon:'MM',title:'Stock Paneles',count:'150',sub:'MM - Repuestos',accent:'accent-ye',nav:'mm'},
      {icon:'BT',title:'Generacion',count:'42.8 MW',sub:'Produccion actual',accent:'accent-cy',nav:''},
      {icon:'PR',title:'PR Ratio',count:'81.2%',sub:'Performance Ratio',accent:'',nav:''}
    ],
    accFolders: {
      'Single Line Diagrams': [
        {name:'SLD-FV-001 Diagrama Unifilar MT',tipo:'DWG',ver:'REV.04',fecha:'2026-01-15',estado:'Aprobado',tam:'3.8 MB'},
        {name:'SLD-FV-002 Unifilar BT Inversores',tipo:'DWG',ver:'REV.03',fecha:'2025-12-10',estado:'Aprobado',tam:'2.9 MB'},
        {name:'SLD-FV-003 Protecciones',tipo:'DWG',ver:'REV.02',fecha:'2025-11-05',estado:'En revision',tam:'2.2 MB'},
        {name:'SLD-FV-004 Sistema SCADA',tipo:'DWG',ver:'REV.02',fecha:'2025-10-20',estado:'Aprobado',tam:'1.8 MB'}
      ],
      'Cable Routing': [
        {name:'CAB-FV-001 Ruta Cables MT',tipo:'DWG',ver:'REV.03',fecha:'2025-11-20',estado:'Aprobado',tam:'4.5 MB'},
        {name:'CAB-FV-002 Ruta Cables BT',tipo:'DWG',ver:'REV.02',fecha:'2025-10-15',estado:'Aprobado',tam:'3.8 MB'},
        {name:'CAB-FV-003 Canalizaciones',tipo:'DWG',ver:'REV.02',fecha:'2025-09-10',estado:'En revision',tam:'2.6 MB'}
      ],
      'Array Layout': [
        {name:'ARR-FV-001 Layout Arrays 1-10',tipo:'DWG',ver:'REV.04',fecha:'2026-02-01',estado:'Aprobado',tam:'6.2 MB'},
        {name:'ARR-FV-002 Layout Arrays 11-20',tipo:'DWG',ver:'REV.03',fecha:'2025-12-15',estado:'Aprobado',tam:'5.8 MB'},
        {name:'ARR-FV-003 Orientacion Paneles',tipo:'PDF',ver:'REV.02',fecha:'2025-10-20',estado:'Aprobado',tam:'2.1 MB'}
      ],
      'Tracker Specs': [
        {name:'TRK-FV-001 Spec Tracker 1-eje',tipo:'PDF',ver:'REV.02',fecha:'2025-08-15',estado:'Aprobado',tam:'2.4 MB'},
        {name:'TRK-FV-002 Algoritmo Seguimiento',tipo:'PDF',ver:'REV.01',fecha:'2025-06-20',estado:'Aprobado',tam:'1.6 MB'},
        {name:'TRK-FV-003 Manuales Mantenimiento',tipo:'PDF',ver:'REV.01',fecha:'2025-05-10',estado:'Borrador',tam:'3.2 MB'}
      ],
      'Civil': [
        {name:'CIV-FV-001 Hincado Pilotes',tipo:'DWG',ver:'REV.03',fecha:'2025-11-05',estado:'Aprobado',tam:'4.8 MB'},
        {name:'CIV-FV-002 Caminos Internos',tipo:'DWG',ver:'REV.02',fecha:'2025-09-20',estado:'Aprobado',tam:'3.5 MB'},
        {name:'CIV-FV-003 Drenaje Pluvial',tipo:'DWG',ver:'REV.01',fecha:'2025-07-15',estado:'En revision',tam:'2.2 MB'},
        {name:'CIV-FV-004 Cerca Perimetral',tipo:'DWG',ver:'REV.02',fecha:'2025-08-10',estado:'Aprobado',tam:'1.8 MB'}
      ]
    },
    pidEquips: [
      {tag:'ARRAY 1-10\\nPaneles 550W',x:10,y:40,w:100,h:60,color:'#F0A000'},
      {tag:'ARRAY 11-20\\nPaneles 550W',x:10,y:140,w:100,h:60,color:'#F0A000'},
      {tag:'INV-01..05\\nInversores',x:170,y:80,w:90,h:50,color:'#FF5500'},
      {tag:'TR-01\\nTransformador',x:310,y:100,w:90,h:50,color:'#5AC8FA'},
      {tag:'SUB-01\\nSubestacion',x:450,y:80,w:100,h:60,color:'#10D858'},
      {tag:'PTO INT\\nInterconexion',x:590,y:100,w:80,h:50,color:'#5AC8FA'}
    ]
  }
};

var PD = PLANT_DATA[PLANT] || PLANT_DATA.tas;

/* ================================================================
   SAP ENHANCEMENT: Override SAP header and add Gemelo Digital
   ================================================================ */
function enhanceSAP(){
  /* Find all possible SAP overlay elements */
  var sapEl = document.getElementById('sapFullscreen') || document.getElementById('sapOverlay');
  if(!sapEl) return;

  /* Find and enhance the header */
  var header = sapEl.querySelector('.sap-fs-header, .fs-sap-header, .fs-header:first-child');
  if(header){
    /* Rebuild as Fiori shell */
    header.className = 'sap-fiori-shell';
    header.innerHTML =
      '<span class="sap-logo-text">SAP</span>' +
      '<span style="font-size:11px;color:rgba(255,255,255,.6);font-family:\'IBM Plex Mono\',monospace;margin-left:4px">S/4HANA 2023</span>' +
      '<span style="font-size:11px;color:rgba(255,255,255,.5);margin-left:8px">| ' + PD.name + '</span>' +
      '<span class="sap-shell-spacer"></span>' +
      '<span class="sap-shell-icon" title="Buscar">[S]</span>' +
      '<span class="sap-shell-icon" title="Notificaciones">[N]</span>' +
      '<span class="sap-shell-avatar">IG</span>' +
      '<button class="sap-fs-close" style="background:none;border:1px solid rgba(255,255,255,.3);color:#fff;font-size:12px;cursor:pointer;padding:4px 12px;border-radius:4px;font-weight:600;transition:all .2s;min-height:32px" onclick="' + getSapCloseFn() + '">X Cerrar</button>';
  }

  /* Add breadcrumb bar if body area exists */
  var body = sapEl.querySelector('.sap-fs-body, .fs-sap-body, .fs-body');
  if(body){
    var existingBC = body.querySelector('.sap-fiori-breadcrumb');
    if(!existingBC){
      var bc = document.createElement('div');
      bc.className = 'sap-fiori-breadcrumb';
      bc.innerHTML =
        '<span class="sap-bc-tab active" data-sapbc="launchpad">Launchpad</span>' +
        '<span class="sap-bc-tab" data-sapbc="pm">PM</span>' +
        '<span class="sap-bc-tab" data-sapbc="apm">APM</span>' +
        '<span class="sap-bc-tab" data-sapbc="mm">MM</span>' +
        '<span class="sap-bc-tab" data-sapbc="btp">BTP</span>' +
        '<span class="sap-bc-tab" data-sapbc="gemelo">Gemelo Digital</span>';
      body.insertBefore(bc, body.firstChild);

      /* Wire breadcrumb tabs to existing nav */
      bc.querySelectorAll('.sap-bc-tab').forEach(function(tab){
        tab.addEventListener('click', function(){
          bc.querySelectorAll('.sap-bc-tab').forEach(function(t){t.classList.remove('active')});
          tab.classList.add('active');
          var view = tab.dataset.sapbc;
          if(view === 'gemelo'){
            showGemeloDigitalInSAP(sapEl);
          } else {
            triggerSapNav(sapEl, view);
          }
          /* Sync left nav active state */
          var navItems = sapEl.querySelectorAll('.sap-fs-nav-item, .fs-nav-item, .fs-sap-nav-item');
          navItems.forEach(function(ni){ ni.classList.remove('active'); });
        });
      });
    }
  }

  /* Enhance Launchpad tiles if they exist - replace colored tiles with Fiori-style */
  enhanceLaunchpadTiles(sapEl);
}

function getSapCloseFn(){
  if(document.getElementById('sapFullscreen')){
    if(typeof window.closeSapFS === 'function') return 'closeSapFS()';
  }
  if(typeof window.closeSAPOverlay === 'function') return 'closeSAPOverlay()';
  if(typeof window.closeFsOverlay === 'function') return "closeFsOverlay('sapOverlay')";
  return "this.closest('.fs-overlay').classList.remove('show','open','active')";
}

function triggerSapNav(sapEl, view){
  /* Try various nav approaches */
  if(PLANT === 'tas' && typeof window.sapFsNav === 'function'){
    sapFsNav(view === 'launchpad' ? 'launchpad' : view);
    return;
  }
  if(PLANT === 'lng' && typeof window.renderSAPView === 'function'){
    renderSAPView(view === 'launchpad' ? 'launchpad' : view);
    return;
  }
  if(PLANT === 'fv' && typeof window.switchSapFsTab === 'function'){
    switchSapFsTab(view === 'launchpad' ? 'launchpad' : view);
    return;
  }
  /* For GNC and Ductos which use static panels */
  var panelIds = {
    gnc: {launchpad:'sap-fs-launch',pm:'sap-fs-pm',apm:'sap-fs-apm',mm:'sap-fs-mm',btp:'sap-fs-btp'},
    ductos: {launchpad:'sap-fs-launchpad',pm:'sap-fs-pm',apm:'sap-fs-apm',mm:'sap-fs-mm',btp:'sap-fs-btp'}
  };
  var ids = panelIds[PLANT];
  if(ids){
    sapEl.querySelectorAll('.fs-section, .sap-fs-panel').forEach(function(p){p.classList.remove('active')});
    var targetPanel = document.getElementById(ids[view]);
    if(targetPanel){targetPanel.classList.add('active');}
  }
  /* Also update the left nav */
  var navItems = sapEl.querySelectorAll('.sap-fs-nav-item, .fs-nav-item, .fs-sap-nav-item');
  var viewOrder = ['launchpad','pm','apm','mm','btp'];
  var idx = viewOrder.indexOf(view);
  navItems.forEach(function(ni,i){
    ni.classList.toggle('active', i === idx);
  });
}

function showGemeloDigitalInSAP(sapEl){
  var content = sapEl.querySelector('.sap-fs-main, .sap-fs-content, .fs-sap-content, .fs-content');
  if(!content) return;

  /* Hide all panels first (for static HTML approach) */
  content.querySelectorAll('.fs-section, .sap-fs-panel').forEach(function(p){
    p.classList.remove('active');p.style.display='none';
  });

  /* Build equipment sidebar cards */
  var equipCards = '';
  var assets = window.ASSETS || [];
  var showAssets = assets.slice(0, 12);
  showAssets.forEach(function(a){
    var stClass = a.status === 'ok' ? 'ok' : a.status === 'warn' ? 'warn' : 'crit';
    var stText = a.status === 'ok' ? 'Normal' : a.status === 'warn' ? 'Alerta' : 'Critico';
    equipCards += '<div class="sap-gemelo-card" style="cursor:pointer" onclick="if(typeof selectAsset===\'function\')selectAsset(\''+a.id+'\')">' +
      '<div class="sap-gemelo-card-tag">' + a.id + '</div>' +
      '<div class="sap-gemelo-card-name">' + (a.name||a.id) + '</div>' +
      '<div class="sap-gemelo-card-status ' + stClass + '">' + stText + '</div>' +
      '</div>';
  });
  if(equipCards === ''){
    equipCards = '<div class="sap-gemelo-card"><div class="sap-gemelo-card-tag">--</div><div class="sap-gemelo-card-name">Cargando activos...</div></div>';
  }

  /* Build asset tree */
  var treeHtml = '';
  var systems = {};
  assets.forEach(function(a){
    var sys = a.system || 'General';
    if(!systems[sys]) systems[sys] = [];
    systems[sys].push(a);
  });
  Object.keys(systems).forEach(function(sys){
    treeHtml += '<div style="padding-left:8px;margin:3px 0"><span style="color:#354A5F;font-weight:600;font-size:11px">|- ' + sys + ' (' + systems[sys].length + ')</span></div>';
    systems[sys].forEach(function(a){
      treeHtml += '<div style="padding-left:24px;color:#666;font-size:10px;margin:1px 0;cursor:pointer" onmouseover="this.style.color=\'#0854A0\'" onmouseout="this.style.color=\'#666\'" onclick="if(typeof selectAsset===\'function\')selectAsset(\''+a.id+'\')">|- ' + a.id + '</div>';
    });
  });

  /* Main layout: 3D canvas on left (embedded), equipment list on right */
  var gemHtml = '<div style="display:flex;flex:1;overflow:hidden;height:100%">' +
    /* Left side: Embedded 3D canvas */
    '<div style="flex:1;display:flex;flex-direction:column;overflow:hidden">' +
      '<div style="padding:8px 16px;background:#fff;border-bottom:1px solid #e5e5e5;display:flex;align-items:center;gap:8px;flex-shrink:0">' +
        '<span style="font-size:13px;font-weight:600;color:#32363A">Gemelo Digital 3D</span>' +
        '<span style="font-size:11px;color:#888">|</span>' +
        '<span style="font-size:11px;color:#888">' + PD.name + '</span>' +
        '<span style="flex:1"></span>' +
        '<span style="font-size:10px;padding:3px 8px;background:#E8F5E9;color:#2B7D2B;border-radius:10px;font-weight:600">EN VIVO</span>' +
      '</div>' +
      '<div id="sapGemelo3DArea" style="flex:1;background:#060D18;position:relative;overflow:hidden">' +
        '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;color:rgba(255,255,255,.4);font-size:13px">Cargando modelo 3D...</div>' +
      '</div>' +
    '</div>' +
    /* Right side: Equipment panel */
    '<div style="width:280px;background:#F7F8FA;border-left:1px solid #e5e5e5;overflow-y:auto;flex-shrink:0;display:flex;flex-direction:column">' +
      '<div style="padding:12px 16px;background:#fff;border-bottom:1px solid #e5e5e5;font-size:12px;font-weight:700;color:#354A5F">Equipos del Modelo</div>' +
      '<div style="padding:8px;display:grid;grid-template-columns:1fr;gap:6px">' + equipCards + '</div>' +
      '<div style="padding:8px 16px;background:#fff;border-top:1px solid #e5e5e5;border-bottom:1px solid #e5e5e5;font-size:11px;font-weight:700;color:#354A5F;margin-top:8px">Jerarquia SAP</div>' +
      '<div style="padding:8px 12px;font-size:11px;color:#333">' +
        '<div style="font-weight:700;margin-bottom:4px">' + PD.code + '</div>' +
        treeHtml +
      '</div>' +
    '</div>' +
  '</div>';

  /* Check if content uses static panels or JS-driven */
  var existingGemelo = content.querySelector('#sap-gemelo-panel');
  if(existingGemelo){
    existingGemelo.style.display = 'block';
    existingGemelo.classList.add('active');
    existingGemelo.innerHTML = gemHtml;
  } else if(content.querySelector('.sap-fs-panel, .fs-section')){
    var gemPanel = document.createElement('div');
    gemPanel.id = 'sap-gemelo-panel';
    gemPanel.className = 'sap-fs-panel fs-section active';
    gemPanel.style.display = 'block';
    gemPanel.style.cssText = 'display:flex;flex:1;overflow:hidden;';
    gemPanel.innerHTML = gemHtml;
    content.appendChild(gemPanel);
  } else {
    content.innerHTML = gemHtml;
  }

  /* Now MOVE the actual Three.js canvas into the SAP 3D area */
  setTimeout(function(){
    var target = document.getElementById('sapGemelo3DArea');
    if(!target) return;
    var canvas = document.getElementById('threejs-canvas') || document.querySelector('#canvas-container canvas, #canvasWrap canvas, .center canvas, canvas[data-engine]');
    if(!canvas) {
      /* Try to find any WebGL canvas */
      var allCanvas = document.querySelectorAll('canvas');
      for(var ci=0;ci<allCanvas.length;ci++){
        try { if(allCanvas[ci].getContext('webgl') || allCanvas[ci].getContext('webgl2') || allCanvas[ci].width > 100) { canvas = allCanvas[ci]; break; } } catch(e){}
      }
    }
    if(canvas){
      /* Store original parent for restoration */
      if(!window._sapOrigCanvasParent) window._sapOrigCanvasParent = canvas.parentElement;
      target.innerHTML = '';
      target.appendChild(canvas);
      canvas.style.width = '100%';
      canvas.style.height = '100%';
      /* Also move CSS2D renderer if present */
      var css2d = document.querySelector('.css2d-renderer, [style*="pointer-events: none"]');
      if(css2d && css2d.tagName === 'DIV' && css2d.childElementCount > 0){
        if(!window._sapOrigCss2dParent) window._sapOrigCss2dParent = css2d.parentElement;
        target.appendChild(css2d);
      }
      /* Trigger resize */
      if(typeof window.onResize === 'function') window.onResize();
      window.dispatchEvent(new Event('resize'));
    }
  }, 150);
}

function enhanceLaunchpadTiles(sapEl){
  /* We'll modify launchpad rendering by overriding tile appearance via observer */
  var observer = new MutationObserver(function(mutations){
    mutations.forEach(function(m){
      if(m.type === 'childList'){
        replaceTilesWithFiori(sapEl);
      }
    });
  });
  var content = sapEl.querySelector('.sap-fs-main, .sap-fs-content, .fs-sap-content, .fs-content');
  if(content){
    observer.observe(content, {childList:true, subtree:false});
    /* Initial replacement */
    setTimeout(function(){ replaceTilesWithFiori(sapEl); }, 100);
  }
}

function replaceTilesWithFiori(sapEl){
  /* Find old-style colored tiles and replace with Fiori-style */
  var tiles = sapEl.querySelectorAll('.sap-lp-tile, .fiori-tile:not(.fiori-tile-real), .sap-fs-tile');
  if(tiles.length === 0) return;

  tiles.forEach(function(tile, i){
    if(tile.classList.contains('fiori-tile-real')) return; /* Already enhanced */
    if(tile.dataset.enhanced) return;
    tile.dataset.enhanced = 'true';

    /* Extract data from old tile */
    var count = '';
    var label = '';
    var sub = '';
    var countEl = tile.querySelector('.tile-count, .fiori-tile-val, .fiori-tile-count, .sap-fs-tile-count');
    var labelEl = tile.querySelector('.tile-label, .fiori-tile-lbl, .fiori-tile-title, .sap-fs-tile-title');
    var subEl = tile.querySelector('.tile-sub, .fiori-tile-sub, .sap-fs-tile-sub');
    if(countEl) count = countEl.textContent;
    if(labelEl) label = labelEl.textContent;
    if(subEl) sub = subEl.textContent;

    /* Use plant data if available */
    var pd = PD.sapTiles[i];
    if(pd){
      count = count || pd.count;
      label = label || pd.title;
      sub = sub || pd.sub;
    }

    /* Determine accent from existing style/class */
    var accent = '';
    if(pd) accent = pd.accent;
    if(!accent){
      var bg = tile.style.background || tile.style.backgroundColor || '';
      if(bg.indexOf('E74C3C')>-1 || bg.indexOf('BB0000')>-1) accent='accent-re';
      else if(bg.indexOf('E67E22')>-1 || bg.indexOf('E78C07')>-1) accent='accent-or';
      else if(bg.indexOf('27AE60')>-1 || bg.indexOf('2B7D2B')>-1) accent='accent-gr';
      else if(bg.indexOf('2E86C1')>-1 || bg.indexOf('0854A0')>-1) accent='accent-cy';
      else if(bg.indexOf('8E44AD')>-1) accent='accent-pu';
      else if(bg.indexOf('F0A000')>-1) accent='accent-ye';
    }

    var iconText = pd ? pd.icon : (label.substring(0,2).toUpperCase());

    /* Replace content */
    tile.className = 'fiori-tile-real ' + accent;
    tile.style.cssText = '';
    tile.innerHTML =
      '<div class="ft-icon">' + iconText + '</div>' +
      '<div class="ft-title">' + label + '</div>' +
      '<div class="ft-count">' + count + '</div>' +
      '<div class="ft-sub">' + sub + '</div>';
  });

  /* Also fix the tile container grid */
  var tileContainers = sapEl.querySelectorAll('.sap-lp-tiles, .fiori-tiles, .sap-fs-tiles');
  tileContainers.forEach(function(tc){
    tc.style.display = 'grid';
    tc.style.gridTemplateColumns = 'repeat(3, 1fr)';
    tc.style.gap = '16px';
    tc.style.padding = '24px';
    tc.style.maxWidth = '960px';
  });
}


/* ================================================================
   ACC ENHANCEMENT: Build realistic Autodesk Construction Cloud
   ================================================================ */
var accCurrentFolder = null;
var accCurrentDocIdx = 0;
var accViewMode = 'list'; /* 'list' or 'viewer' */

function enhanceACC(){
  var accEl = document.getElementById('accFullscreen') || document.getElementById('accOverlay');
  if(!accEl) return;

  /* Enhance header */
  var header = accEl.querySelector('.acc-fs-header, .fs-acc-header, .fs-header.acc-header, .fs-header:first-child');
  if(header){
    header.className = 'acc-autodesk-header';
    header.style.cssText = '';
    header.innerHTML =
      '<span class="acc-a-logo">A</span>' +
      '<span class="acc-project-name">Autodesk Construction Cloud</span>' +
      '<span style="font-size:11px;color:rgba(255,255,255,.4);margin-left:8px">| ' + PD.code + ' - ' + PD.name + '</span>' +
      '<span class="acc-header-spacer"></span>' +
      '<span class="acc-user-info">Ing. Admin | ' + PD.code + '</span>' +
      '<button style="background:none;border:1px solid rgba(255,255,255,.3);color:#fff;font-size:12px;cursor:pointer;padding:4px 12px;border-radius:4px;font-weight:600;min-height:32px;margin-left:8px" onclick="' + getAccCloseFn() + '">X Cerrar</button>';
  }

  /* Replace body with new structure */
  var body = accEl.querySelector('.acc-fs-body, .fs-acc-body, .fs-body');
  if(!body){
    /* For FV which uses inline div styles */
    body = header ? header.nextElementSibling : null;
  }
  if(!body) return;

  /* Set folder keys */
  var folderKeys = Object.keys(PD.accFolders);
  accCurrentFolder = folderKeys[0];
  accCurrentDocIdx = -1;
  accViewMode = 'list';

  body.style.cssText = 'display:flex;flex:1;overflow:hidden;';
  body.innerHTML = buildACCBody(folderKeys);

  /* Wire up folder clicks */
  wireACCInteractions(body, folderKeys);
}

function getAccCloseFn(){
  if(document.getElementById('accFullscreen')){
    if(typeof window.closeAccFS === 'function') return 'closeAccFS()';
  }
  if(typeof window.closeACCOverlay === 'function') return 'closeACCOverlay()';
  if(typeof window.closeFsOverlay === 'function') return "closeFsOverlay('accOverlay')";
  return "this.closest('.fs-overlay').classList.remove('show','open','active')";
}

function buildACCBody(folderKeys){
  /* Build folder tree */
  var treeHtml = '<div class="acc-file-tree" id="accEnhTree">';
  treeHtml += '<div style="padding:8px 16px;font-size:9px;font-weight:700;letter-spacing:.1em;color:#888;text-transform:uppercase;margin-bottom:4px">Archivos del Proyecto</div>';
  folderKeys.forEach(function(fk, fi){
    var docs = PD.accFolders[fk];
    treeHtml += '<div class="acc-tree-folder' + (fi===0?' open':'') + '" data-folder="'+fk+'">' +
      '<span class="acc-fold-arrow">&gt;</span>' +
      '<span class="acc-fold-icon">[F]</span> ' + fk +
    '</div>';
    treeHtml += '<div class="acc-tree-docs" data-foldergroup="'+fk+'">';
    docs.forEach(function(d, di){
      treeHtml += '<div class="acc-tree-doc" data-folder="'+fk+'" data-docidx="'+di+'">[DOC] ' + d.name.split(' ')[0] + '</div>';
    });
    treeHtml += '</div>';
  });
  treeHtml += '</div>';

  /* Build content area */
  var contentHtml = '<div class="acc-doc-viewer-wrap" id="accEnhContent">' +
    '<div class="acc-doc-viewer-toolbar">' +
      '<span style="font-size:13px;font-weight:600;color:#333;margin-right:auto" id="accEnhTitle">' + folderKeys[0] + '</span>' +
      '<button class="acc-vt-btn" id="accBtnBack" style="display:none" onclick="window._accBackToList()">Volver a lista</button>' +
      '<button class="acc-vt-btn">Descargar</button>' +
      '<button class="acc-vt-btn">Compartir</button>' +
      '<button class="acc-vt-btn primary">Marcar revision</button>' +
    '</div>' +
    '<div class="acc-doc-viewer-main" id="accEnhMain">' +
      buildACCDocList(PD.accFolders[folderKeys[0]], folderKeys[0]) +
    '</div>' +
  '</div>';

  return treeHtml + contentHtml;
}

function buildACCDocList(docs, folderName){
  var html = '<div class="acc-doc-canvas" style="align-items:flex-start;padding:16px">' +
    '<div style="width:100%;overflow-x:auto">' +
    '<table class="acc-doc-list-table">' +
    '<thead><tr><th>Nombre</th><th>Tipo</th><th>Version</th><th>Fecha</th><th>Estado</th><th>Tamano</th></tr></thead>' +
    '<tbody>';
  docs.forEach(function(d, i){
    var stClass = d.estado === 'Aprobado' ? 'approved' : d.estado === 'En revision' ? 'review' : 'draft';
    html += '<tr class="acc-doc-row" data-folder="'+folderName+'" data-docidx="'+i+'" style="cursor:pointer">' +
      '<td style="font-weight:600;color:#0696D7">' + d.name + '</td>' +
      '<td>' + d.tipo + '</td>' +
      '<td>' + d.ver + '</td>' +
      '<td>' + d.fecha + '</td>' +
      '<td><span class="acc-doc-status ' + stClass + '">' + d.estado + '</span></td>' +
      '<td>' + d.tam + '</td>' +
    '</tr>';
  });
  html += '</tbody></table></div></div>';
  return html;
}

function buildACCDocViewer(doc, folderName, docIdx){
  /* Determine view type */
  var isPID = folderName.toLowerCase().indexOf('p&id')>-1 || folderName.toLowerCase().indexOf('pid')>-1;
  var isDatasheet = folderName.toLowerCase().indexOf('datasheet')>-1 || folderName.toLowerCase().indexOf('spec')>-1;

  var previewHtml = '';
  if(isPID){
    previewHtml = buildPIDDrawing();
  } else if(isDatasheet){
    previewHtml = buildDatasheetView(doc);
  } else {
    /* Generic document preview */
    previewHtml = '<div style="background:#1E2838;border-radius:8px;padding:40px;text-align:center;width:100%;max-width:600px;border:1px solid #333">' +
      '<div style="font-size:48px;color:rgba(255,255,255,.2);margin-bottom:16px">[DOC]</div>' +
      '<div style="color:#fff;font-size:16px;font-weight:600;margin-bottom:8px">' + doc.name + '</div>' +
      '<div style="color:rgba(255,255,255,.5);font-size:12px;margin-bottom:4px">' + doc.ver + ' | ' + doc.fecha + '</div>' +
      '<div style="color:rgba(255,255,255,.4);font-size:11px">' + doc.tipo + ' | ' + doc.tam + '</div>' +
    '</div>';
  }

  var stClass = doc.estado === 'Aprobado' ? 'approved' : doc.estado === 'En revision' ? 'review' : 'draft';

  var html = '<div class="acc-doc-canvas">' + previewHtml + '</div>' +
    '<div class="acc-doc-meta-right">' +
      '<div class="acc-mr-section">Informacion del Documento</div>' +
      '<div class="acc-mr-row"><span class="mrk">Nombre</span><span class="mrv">' + doc.name + '</span></div>' +
      '<div class="acc-mr-row"><span class="mrk">Version</span><span class="mrv">' + doc.ver + '</span></div>' +
      '<div class="acc-mr-row"><span class="mrk">Formato</span><span class="mrv">' + doc.tipo + '</span></div>' +
      '<div class="acc-mr-row"><span class="mrk">Tamano</span><span class="mrv">' + doc.tam + '</span></div>' +
      '<div class="acc-mr-section">Autor y Aprobacion</div>' +
      '<div class="acc-mr-row"><span class="mrk">Autor</span><span class="mrv">Ing. Rodriguez</span></div>' +
      '<div class="acc-mr-row"><span class="mrk">Fecha</span><span class="mrv">' + doc.fecha + '</span></div>' +
      '<div class="acc-mr-row"><span class="mrk">Revisor</span><span class="mrv">Ing. Director Tecnico</span></div>' +
      '<div class="acc-mr-row"><span class="mrk">Estado</span><span class="mrv"><span class="acc-doc-status ' + stClass + '">' + doc.estado + '</span></span></div>' +
      '<div class="acc-mr-section">Proyecto</div>' +
      '<div class="acc-mr-row"><span class="mrk">Planta</span><span class="mrv">' + PD.code + '</span></div>' +
      '<div class="acc-mr-row"><span class="mrk">Disciplina</span><span class="mrv">' + guessDiscipline(folderName) + '</span></div>' +
    '</div>';
  return html;
}

function guessDiscipline(folder){
  var f = folder.toLowerCase();
  if(f.indexOf('pid')>-1 || f.indexOf('p&id')>-1) return 'Proceso';
  if(f.indexOf('pfd')>-1) return 'Proceso';
  if(f.indexOf('elec')>-1 || f.indexOf('single')>-1 || f.indexOf('cable')>-1) return 'Electrico';
  if(f.indexOf('inst')>-1 || f.indexOf('loop')>-1) return 'Instrumentacion';
  if(f.indexOf('civil')>-1 || f.indexOf('hincado')>-1) return 'Civil';
  if(f.indexOf('data')>-1 || f.indexOf('spec')>-1) return 'Equipos';
  if(f.indexOf('hazop')>-1 || f.indexOf('sif')>-1 || f.indexOf('cause')>-1) return 'Seguridad';
  if(f.indexOf('sop')>-1) return 'Operaciones';
  if(f.indexOf('iso')>-1) return 'Piping';
  if(f.indexOf('sci')>-1) return 'Proteccion';
  if(f.indexOf('plot')>-1 || f.indexOf('layout')>-1 || f.indexOf('array')>-1) return 'General';
  if(f.indexOf('tracker')>-1) return 'Mecanico';
  return 'Multi';
}

function buildPIDDrawing(){
  var html = '<div class="acc-pid-enhanced">';
  var equips = PD.pidEquips || [];

  /* Title block */
  html += '<div style="position:absolute;top:8px;left:12px;font-family:\'IBM Plex Mono\',monospace;font-size:10px;color:rgba(255,255,255,.4)">P&ID - ' + PD.name + '</div>';
  html += '<div style="position:absolute;top:22px;left:12px;font-family:\'IBM Plex Mono\',monospace;font-size:8px;color:rgba(255,255,255,.2)">SCALE: NTS | SHEET 1 OF 3</div>';

  /* Grid lines for engineering look */
  for(var gi=0;gi<8;gi++){
    html += '<div style="position:absolute;left:0;right:0;top:'+(gi*55+35)+'px;height:1px;background:rgba(255,255,255,.03)"></div>';
  }
  for(var gj=0;gj<12;gj++){
    html += '<div style="position:absolute;top:0;bottom:0;left:'+(gj*65+10)+'px;width:1px;background:rgba(255,255,255,.03)"></div>';
  }

  equips.forEach(function(e){
    var tag = (e.tag||'').replace(/\\n/g,'<br>');
    html += '<div class="pid-equip" style="left:'+e.x+'px;top:'+e.y+'px;width:'+e.w+'px;height:'+e.h+'px;border-color:'+e.color+';color:'+e.color+';background:rgba(' + hexToRgb(e.color) + ',.08)">'+tag+'</div>';
  });

  /* Connect with pipes, valves, and instruments */
  if(equips.length > 1){
    for(var i=0;i<equips.length-1;i++){
      var e1 = equips[i];
      var e2 = equips[i+1];
      var x1 = e1.x + e1.w;
      var y1 = e1.y + e1.h/2;
      var x2 = e2.x;
      var y2 = e2.y + e2.h/2;
      var lineW = Math.max(1, x2 - x1);

      if(lineW > 5 && lineW < 300){
        /* Horizontal pipe */
        if(Math.abs(y1-y2) < 20){
          html += '<div class="pid-pipe" style="left:'+x1+'px;top:'+y1+'px;width:'+lineW+'px;height:2px"></div>';
          /* Flow arrow */
          var arrowX = x1 + lineW/2;
          html += '<div style="position:absolute;left:'+(arrowX-3)+'px;top:'+(y1-4)+'px;width:0;height:0;border-left:6px solid #5AC8FA;border-top:4px solid transparent;border-bottom:4px solid transparent;opacity:.6"></div>';
        } else {
          /* L-shaped connection */
          var midX = x1 + lineW/2;
          html += '<div class="pid-pipe" style="left:'+x1+'px;top:'+y1+'px;width:'+(midX-x1)+'px;height:2px"></div>';
          var vTop = Math.min(y1,y2);
          var vH = Math.abs(y2-y1);
          html += '<div class="pid-pipe" style="left:'+midX+'px;top:'+vTop+'px;width:2px;height:'+vH+'px"></div>';
          html += '<div class="pid-pipe" style="left:'+midX+'px;top:'+y2+'px;width:'+(x2-midX)+'px;height:2px"></div>';
        }

        /* Add valve symbol between equipment */
        var vlvX = x1 + lineW * 0.35;
        var vlvY = y1 - 5;
        html += '<div class="pid-vlv" style="left:'+vlvX+'px;top:'+vlvY+'px" title="XV-'+(100+i)+'"></div>';
        html += '<div style="position:absolute;left:'+(vlvX-8)+'px;top:'+(vlvY+14)+'px;font-family:\'IBM Plex Mono\',monospace;font-size:7px;color:rgba(255,255,255,.35)">XV-'+(100+i)+'</div>';

        /* Add instrument circle */
        var instX = x1 + lineW * 0.65;
        var instY = y1 - 16;
        var instTypes = ['PT','TT','FT','LT','AT'];
        var instType = instTypes[i % instTypes.length];
        html += '<div style="position:absolute;left:'+instX+'px;top:'+instY+'px;width:18px;height:18px;border:1.5px solid #F0A000;border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:\'IBM Plex Mono\',monospace;font-size:6px;color:#F0A000;background:rgba(240,160,0,.08)">' + instType + '</div>';
        html += '<div style="position:absolute;left:'+(instX+2)+'px;top:'+(instY-10)+'px;font-family:\'IBM Plex Mono\',monospace;font-size:6px;color:rgba(240,160,0,.4)">' + instType + '-' + (200+i) + '</div>';
      }
    }
  }

  /* Title block bottom-right */
  html += '<div style="position:absolute;bottom:0;right:0;width:200px;height:60px;border:1px solid rgba(255,255,255,.15);border-right:none;border-bottom:none">';
  html += '<div style="padding:4px 8px;font-family:\'IBM Plex Mono\',monospace;font-size:7px;color:rgba(255,255,255,.3);line-height:1.6">';
  html += 'DWG: PID-' + PD.code.replace('-','') + '-001<br>';
  html += 'REV: 05 | ' + PD.code + '<br>';
  html += 'APROBADO: Ing. Director Tecnico';
  html += '</div></div>';

  /* Legend */
  html += '<div style="position:absolute;bottom:8px;left:12px;display:flex;gap:12px;font-family:\'IBM Plex Mono\',monospace;font-size:7px;color:rgba(255,255,255,.25)">';
  html += '<span>[O] Instrumento</span><span>[X] Valvula</span><span>--- Tuberia</span>';
  html += '</div>';

  html += '</div>';
  return html;
}

function buildDatasheetView(doc){
  var tagNum = doc.name.split(' ')[0];
  var dsData = getDatasheetData(tagNum);
  var html = '<div class="acc-datasheet">' +
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;border-bottom:2px solid #0696D7;padding-bottom:8px">' +
      '<h3 style="margin:0;border:none;padding:0">' + doc.name + '</h3>' +
      '<span style="font-size:10px;color:#888;font-family:\'IBM Plex Mono\',monospace">' + doc.ver + '</span>' +
    '</div>';
  dsData.forEach(function(section){
    html += '<div style="font-size:10px;font-weight:700;color:#0696D7;letter-spacing:.08em;text-transform:uppercase;margin:12px 0 6px;padding-top:8px;border-top:1px solid #eee">' + section.title + '</div>';
    section.rows.forEach(function(r){
      html += '<div class="ds-row"><span class="ds-k">'+r.k+'</span><span class="ds-v">'+r.v+'</span></div>';
    });
  });
  html += '</div>';
  return html;
}

function getDatasheetData(tagNum){
  var base = [
    {title:'Identificacion', rows:[
      {k:'Tag Number', v:tagNum},
      {k:'Servicio', v:PD.name},
      {k:'Ubicacion', v:PD.code},
      {k:'Revision', v:'REV.02'}
    ]}
  ];
  if(PLANT === 'tas'){
    base.push({title:'Datos de Diseno', rows:[
      {k:'Presion de Diseno', v:'17.58 kg/cm2'},
      {k:'Temperatura de Diseno', v:'-40 / +55 C'},
      {k:'Presion de Operacion', v:'12.0 kg/cm2'},
      {k:'Capacidad', v:'1,000 m3'},
      {k:'Producto', v:'Gas LP (Propano/Butano)'},
      {k:'Densidad', v:'0.51 kg/L @ 15C'}
    ]});
    base.push({title:'Construccion', rows:[
      {k:'Material Cuerpo', v:'SA-516 Gr.70'},
      {k:'Espesor', v:'25.4 mm'},
      {k:'Codigo', v:'ASME VIII Div.1'},
      {k:'Fabricante', v:'Industrias META'},
      {k:'Ano Fabricacion', v:'2018'},
      {k:'Peso Vacio', v:'42,500 kg'}
    ]});
  } else if(PLANT === 'lng'){
    base.push({title:'Datos de Diseno', rows:[
      {k:'Presion de Diseno', v:'8.5 bar'},
      {k:'Temperatura de Diseno', v:'-196 / +50 C'},
      {k:'Capacidad', v:'60 m3 (GNL)'},
      {k:'Producto', v:'Gas Natural Licuado'},
      {k:'Punto Ebullicion', v:'-162 C'},
      {k:'Aislamiento', v:'Perlita al vacio'}
    ]});
    base.push({title:'Construccion', rows:[
      {k:'Material Interior', v:'AISI 304L'},
      {k:'Material Exterior', v:'SA-516 Gr.70'},
      {k:'Tipo', v:'Doble pared, vacio'},
      {k:'Fabricante', v:'Chart Industries'},
      {k:'Codigo', v:'ASME VIII Div.1 + EN13458'}
    ]});
  } else if(PLANT === 'gnc'){
    base.push({title:'Datos de Diseno', rows:[
      {k:'Presion de Diseno', v:'250 bar'},
      {k:'Temperatura de Operacion', v:'Ambiente'},
      {k:'Capacidad', v:'4,200 Nm3'},
      {k:'Producto', v:'Gas Natural Comprimido'},
      {k:'Tipo Compresor', v:'Reciprocante 4 etapas'}
    ]});
    base.push({title:'Motor', rows:[
      {k:'Potencia', v:'150 kW'},
      {k:'Voltaje', v:'440V / 3F / 60Hz'},
      {k:'RPM', v:'1,780'},
      {k:'Fabricante', v:'BAUER Compressors'}
    ]});
  } else if(PLANT === 'ductos'){
    base.push({title:'Datos de Diseno', rows:[
      {k:'Presion Succion', v:'40 bar'},
      {k:'Presion Descarga', v:'65 bar'},
      {k:'Flujo', v:'80 MMSCFD'},
      {k:'Gas', v:'Gas Natural (CH4 92%)'},
      {k:'Tipo', v:'Centrifugo'},
      {k:'Accionamiento', v:'Turbina de Gas'}
    ]});
    base.push({title:'Turbina', rows:[
      {k:'Potencia', v:'12,500 HP'},
      {k:'Modelo', v:'Solar Centaur 50'},
      {k:'RPM', v:'11,000'},
      {k:'Eficiencia', v:'28.5%'},
      {k:'Fabricante', v:'Solar Turbines / Caterpillar'}
    ]});
  } else if(PLANT === 'fv'){
    base.push({title:'Datos Electricos', rows:[
      {k:'Potencia Nominal', v:'550 Wp'},
      {k:'Voc', v:'49.5 V'},
      {k:'Isc', v:'14.0 A'},
      {k:'Vmpp', v:'41.7 V'},
      {k:'Impp', v:'13.2 A'},
      {k:'Eficiencia Modulo', v:'21.3%'}
    ]});
    base.push({title:'Mecanico', rows:[
      {k:'Tipo Celda', v:'Mono PERC Bifacial'},
      {k:'No. Celdas', v:'144 (6x24)'},
      {k:'Dimensiones', v:'2278 x 1134 x 35 mm'},
      {k:'Peso', v:'28.6 kg'},
      {k:'Fabricante', v:'LONGi Solar'},
      {k:'Modelo', v:'LR5-72HBD-550M'}
    ]});
  }
  base.push({title:'Mantenimiento', rows:[
    {k:'Ultimo Mtto.', v:'2026-02-15'},
    {k:'Proximo Mtto.', v:'2026-06-15'},
    {k:'Frecuencia', v:'Trimestral'},
    {k:'OT SAP', v:'PM-' + PD.code.replace('-','') + '-001'}
  ]});
  return base;
}

function hexToRgb(hex){
  hex = hex.replace('#','');
  if(hex.length === 3) hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
  var r = parseInt(hex.substring(0,2),16);
  var g = parseInt(hex.substring(2,4),16);
  var b = parseInt(hex.substring(4,6),16);
  return r+','+g+','+b;
}

function wireACCInteractions(body, folderKeys){
  /* Folder toggle */
  body.addEventListener('click', function(e){
    var folder = e.target.closest('.acc-tree-folder');
    if(folder){
      folder.classList.toggle('open');
      var fk = folder.dataset.folder;
      /* If opening, show docs for this folder */
      if(folder.classList.contains('open')){
        accCurrentFolder = fk;
        accViewMode = 'list';
        accCurrentDocIdx = -1;
        updateACCContent(body, fk);
      }
      return;
    }

    var doc = e.target.closest('.acc-tree-doc');
    if(doc){
      /* Select doc in tree */
      body.querySelectorAll('.acc-tree-doc').forEach(function(d){d.classList.remove('sel')});
      doc.classList.add('sel');
      var fk2 = doc.dataset.folder;
      var di = parseInt(doc.dataset.docidx);
      accCurrentFolder = fk2;
      accCurrentDocIdx = di;
      accViewMode = 'viewer';
      showACCDocViewer(body, fk2, di);
      return;
    }

    var row = e.target.closest('.acc-doc-row');
    if(row){
      var fk3 = row.dataset.folder;
      var di2 = parseInt(row.dataset.docidx);
      accCurrentFolder = fk3;
      accCurrentDocIdx = di2;
      accViewMode = 'viewer';
      showACCDocViewer(body, fk3, di2);
      /* Also select in tree */
      body.querySelectorAll('.acc-tree-doc').forEach(function(d){d.classList.remove('sel')});
      var treeDocs = body.querySelectorAll('.acc-tree-doc[data-folder="'+fk3+'"]');
      if(treeDocs[di2]) treeDocs[di2].classList.add('sel');
      return;
    }
  });

  /* Back to list function */
  window._accBackToList = function(){
    accViewMode = 'list';
    accCurrentDocIdx = -1;
    updateACCContent(body, accCurrentFolder);
    body.querySelectorAll('.acc-tree-doc').forEach(function(d){d.classList.remove('sel')});
  };
}

function updateACCContent(body, folderName){
  var main = body.querySelector('#accEnhMain');
  var title = body.querySelector('#accEnhTitle');
  var backBtn = body.querySelector('#accBtnBack');
  if(!main) return;
  if(title) title.textContent = folderName;
  if(backBtn) backBtn.style.display = 'none';
  var docs = PD.accFolders[folderName] || [];
  main.innerHTML = buildACCDocList(docs, folderName);
}

function showACCDocViewer(body, folderName, docIdx){
  var main = body.querySelector('#accEnhMain');
  var title = body.querySelector('#accEnhTitle');
  var backBtn = body.querySelector('#accBtnBack');
  if(!main) return;
  var docs = PD.accFolders[folderName] || [];
  var doc = docs[docIdx];
  if(!doc) return;
  if(title) title.textContent = doc.name;
  if(backBtn) backBtn.style.display = '';
  main.innerHTML = buildACCDocViewer(doc, folderName, docIdx);
}


/* ================================================================
   INIT: Run enhancements after DOM is ready
   ================================================================ */
function init(){
  /* Wait a bit for the page JS to finish setting up */
  setTimeout(function(){
    replaceEYLogo();
    enhanceSAP();
    enhanceACC();
    hookEquipmentClicks();
    addMobileControls();
  }, 500);
}

/* Replace text EY logos with real EY SVG logo */
function replaceEYLogo(){
  var logos = document.querySelectorAll('.h-logo, .logo, .tb-ey, .top-logo, .logo-box');
  logos.forEach(function(el){
    if(el.dataset.eyReplaced) return;
    el.dataset.eyReplaced = 'true';
    var isSmall = el.classList.contains('h-logo') || el.classList.contains('tb-ey') || el.classList.contains('top-logo') || el.classList.contains('logo-box');
    var w = isSmall ? 64 : 90;
    var h = isSmall ? 38 : 52;
    el.style.cssText = 'display:flex;align-items:center;justify-content:center;flex-shrink:0;background:none;border-radius:0;width:auto;height:auto';
    el.innerHTML = '<img src="ey-logo.svg" alt="EY" width="'+w+'" height="'+h+'" style="display:block">';
  });
}

/* Add mobile toggle buttons */
function addMobileControls(){
  if(window.innerWidth > 768) return;
  var header = document.getElementById('header');
  if(!header) return;
  /* Add menu toggle for sidebar */
  if(!document.getElementById('mobileMenuBtn')){
    var menuBtn = document.createElement('button');
    menuBtn.id = 'mobileMenuBtn';
    menuBtn.innerHTML = '&#9776;';
    menuBtn.style.cssText = 'background:var(--s2,#111D2B);border:1px solid rgba(255,255,255,.15);color:var(--t0,#E8F4FF);width:36px;height:36px;border-radius:6px;font-size:18px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;order:-1';
    menuBtn.onclick = function(){
      var sidebar = document.querySelector('.left,.sidebar,.sl-sidebar');
      if(sidebar) sidebar.classList.toggle('open');
    };
    header.insertBefore(menuBtn, header.firstChild);
  }

  /* Close sidebar when clicking canvas area */
  var canvasArea = document.querySelector('#canvas-container,#canvasWrap,#view-3d,.center');
  if(canvasArea){
    canvasArea.addEventListener('touchstart', function(){
      var sidebar = document.querySelector('.left.open,.sidebar.open,.sl-sidebar.open');
      if(sidebar) sidebar.classList.remove('open');
    }, {passive:true});
  }
}

/* Hook into existing equipment selection to show enhanced panel */
function hookEquipmentClicks(){
  /* Wrap selectAsset for TAS, LNG, Ductos, FV */
  if(typeof window.selectAsset === 'function'){
    var origSelectAsset = window.selectAsset;
    window.selectAsset = function(id){
      origSelectAsset.apply(this, arguments);
      setTimeout(function(){ showEnhancedPanelForAsset(id); }, 50);
    };
  }
  /* Wrap selectEquipment for GNC */
  if(typeof window.selectEquipment === 'function'){
    var origSelectEquip = window.selectEquipment;
    window.selectEquipment = function(key){
      origSelectEquip.apply(this, arguments);
      setTimeout(function(){ showEnhancedPanelForGNC(key); }, 50);
    };
  }
}

function showEnhancedPanelForAsset(id){
  /* Find asset in various data structures */
  var asset = null;
  var sensors = [];

  if(window.ASSETS && Array.isArray(window.ASSETS)){
    asset = window.ASSETS.find(function(a){ return a.id === id; });
  }
  if(!asset && window.ASSET_DATA && window.ASSET_DATA[id]){
    var ad = window.ASSET_DATA[id];
    asset = {id: id, name: ad.title || ad.tag || id, tag: ad.tag || id};
    /* Convert FV sensor format [name, value, status] */
    if(ad.sensors){
      ad.sensors.forEach(function(s){
        if(Array.isArray(s)){
          sensors.push({variable: s[0], value: parseFloat(s[1]) || 0, unit: '', range: [0, 100], status: s[2] || 'ok'});
        }
      });
    }
    if(ad.config){
      asset.specs = {};
      ad.config.forEach(function(c){
        if(Array.isArray(c) && c.length >= 2) asset.specs = asset.specs || {};
      });
    }
  }
  if(!asset) return;

  /* Normalize sensors */
  if(asset.sensors && sensors.length === 0){
    asset.sensors.forEach(function(s){
      if(Array.isArray(s)){
        /* [name, value, status] format */
        sensors.push({variable: s[0] || s.n, value: parseFloat(s[1] || s.v) || 0, unit: s.u || '', range: [0, 100], status: s[2] || s.s || 'ok'});
      } else if(s.n || s.variable){
        sensors.push({
          variable: s.n || s.variable,
          value: parseFloat(s.v || s.value) || 0,
          unit: s.u || s.unit || '',
          range: s.range || [0, 100],
          status: s.s || s.status || 'ok'
        });
      }
    });
  }

  /* Get related docs */
  var docs = asset.docs || [];

  window.showEnhancedEquipPanel(
    asset.id || asset.tag || id,
    asset.name || asset.title || id,
    sensors,
    docs
  );
}

function showEnhancedPanelForGNC(key){
  if(!window.EQUIP_DATA || !window.EQUIP_DATA[key]) return;
  var eq = window.EQUIP_DATA[key];
  var sensors = [];
  if(eq.sensors){
    eq.sensors.forEach(function(s){
      if(Array.isArray(s)){
        sensors.push({variable: s[0], value: parseFloat(s[1]) || 0, unit: '', range: [0, 100], status: s[2] || 'ok'});
      }
    });
  }
  window.showEnhancedEquipPanel(
    eq.tag || key,
    eq.title || eq.name || key,
    sensors,
    eq.docs || []
  );
}

if(document.readyState === 'loading'){
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}

/* Restore canvas when SAP is closed */
function restoreCanvasFromSAP(){
  var canvas = document.getElementById('threejs-canvas') || document.querySelector('#sapGemelo3DArea canvas');
  if(canvas && window._sapOrigCanvasParent){
    window._sapOrigCanvasParent.appendChild(canvas);
    canvas.style.width = '';
    canvas.style.height = '';
    window._sapOrigCanvasParent = null;
  }
  var css2d = document.querySelector('#sapGemelo3DArea [style*="pointer-events"]');
  if(css2d && window._sapOrigCss2dParent){
    window._sapOrigCss2dParent.appendChild(css2d);
    window._sapOrigCss2dParent = null;
  }
  window.dispatchEvent(new Event('resize'));
}

/* Hook into existing close functions to restore canvas */
var _origCloseSapFS = window.closeSapFS;
var _origCloseSAPOverlay = window.closeSAPOverlay;
var _origCloseFsOverlay = window.closeFsOverlay;

if(typeof _origCloseSapFS === 'function'){
  window.closeSapFS = function(){
    restoreCanvasFromSAP();
    _origCloseSapFS.apply(this, arguments);
  };
}
if(typeof _origCloseSAPOverlay === 'function'){
  window.closeSAPOverlay = function(){
    restoreCanvasFromSAP();
    _origCloseSAPOverlay.apply(this, arguments);
  };
}
if(typeof _origCloseFsOverlay === 'function'){
  window.closeFsOverlay = function(id){
    if(id && id.toLowerCase().indexOf('sap') > -1) restoreCanvasFromSAP();
    _origCloseFsOverlay.apply(this, arguments);
  };
}

/* Also re-run SAP enhancement when overlay becomes visible */
var sapOverlayId = document.getElementById('sapFullscreen') ? 'sapFullscreen' : 'sapOverlay';
var accOverlayId = document.getElementById('accFullscreen') ? 'accFullscreen' : 'accOverlay';

/* Observe overlay visibility changes */
var overlayObserver = new MutationObserver(function(mutations){
  mutations.forEach(function(m){
    if(m.type === 'attributes' && m.attributeName === 'class'){
      var el = m.target;
      if(el.id === sapOverlayId){
        if(el.classList.contains('show') || el.classList.contains('open') || el.classList.contains('active')){
          setTimeout(function(){ enhanceSAP(); }, 100);
        }
      }
      if(el.id === accOverlayId){
        if(el.classList.contains('show') || el.classList.contains('open') || el.classList.contains('active')){
          setTimeout(function(){ enhanceACC(); }, 100);
        }
      }
    }
  });
});

var sapOvEl = document.getElementById(sapOverlayId);
var accOvEl = document.getElementById(accOverlayId);
if(sapOvEl) overlayObserver.observe(sapOvEl, {attributes:true, attributeFilter:['class']});
if(accOvEl) overlayObserver.observe(accOvEl, {attributes:true, attributeFilter:['class']});


/* ================================================================
   EQUIPMENT DETAIL PANEL - Rich ficha tecnica with animated charts
   ================================================================ */
var eqpCSS = document.createElement('style');
eqpCSS.id = 'dt-equipment-enhancements';
eqpCSS.textContent = [
'/* Equipment Detail Panel Enhanced */',
'.ep-enhanced{position:fixed;right:0;top:52px;width:380px;height:calc(100vh - 52px);background:#0A1420;border-left:1px solid rgba(255,255,255,.1);z-index:200;display:none;flex-direction:column;overflow:hidden;box-shadow:-4px 0 20px rgba(0,0,0,.4)}',
'.ep-enhanced.show{display:flex}',
'.ep-enhanced .ep-hdr{padding:16px 20px;border-bottom:1px solid rgba(255,255,255,.08);display:flex;align-items:center;gap:10px;flex-shrink:0}',
'.ep-enhanced .ep-tag{font-family:"IBM Plex Mono",monospace;font-size:14px;font-weight:700;color:#FF5500}',
'.ep-enhanced .ep-name{font-size:12px;color:#7AAAC8}',
'.ep-enhanced .ep-close{margin-left:auto;background:none;border:1px solid rgba(255,255,255,.15);color:#7AAAC8;width:28px;height:28px;border-radius:4px;cursor:pointer;font-size:14px;display:flex;align-items:center;justify-content:center}',
'.ep-enhanced .ep-close:hover{color:#FF5500;border-color:#FF5500}',
'.ep-enhanced .ep-tabs{display:flex;border-bottom:1px solid rgba(255,255,255,.08);flex-shrink:0}',
'.ep-enhanced .ep-tab{flex:1;padding:10px;text-align:center;font-size:11px;font-weight:600;color:#7AAAC8;cursor:pointer;border-bottom:2px solid transparent;transition:all .15s}',
'.ep-enhanced .ep-tab:hover{color:#E8F4FF}',
'.ep-enhanced .ep-tab.active{color:#FF5500;border-bottom-color:#FF5500}',
'.ep-enhanced .ep-body{flex:1;overflow-y:auto;padding:16px 20px}',
'.ep-enhanced .ep-section-title{font-size:10px;font-weight:700;letter-spacing:.1em;color:#3A607A;text-transform:uppercase;margin:16px 0 8px;padding-bottom:4px;border-bottom:1px solid rgba(255,255,255,.06)}',
'.ep-enhanced .ep-section-title:first-child{margin-top:0}',
'.ep-enhanced .ep-kv{display:flex;justify-content:space-between;padding:4px 0;font-size:12px}',
'.ep-enhanced .ep-kv .ek{color:#7AAAC8}.ep-enhanced .ep-kv .ev{color:#E8F4FF;font-weight:500;font-family:"IBM Plex Mono",monospace}',
'.ep-enhanced .ep-status-bar{height:4px;border-radius:2px;margin-top:2px}',
'.ep-enhanced .ep-chart-wrap{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:12px;margin:8px 0}',
'.ep-enhanced .ep-chart-title{font-size:11px;font-weight:600;color:#E8F4FF;margin-bottom:8px;display:flex;justify-content:space-between}',
'.ep-enhanced .ep-chart-title .ep-val-live{font-family:"IBM Plex Mono",monospace;color:#10D858}',
'.ep-enhanced .ep-sparkline{width:100%;height:50px}',
'.ep-enhanced .ep-sparkline path{fill:none;stroke-width:1.5}',
'.ep-enhanced .ep-sparkline .area{stroke:none;opacity:.15}',
'.ep-enhanced .ep-qr-wrap{text-align:center;padding:16px;background:rgba(255,255,255,.03);border-radius:8px;margin:8px 0}',
'.ep-enhanced .ep-qr-wrap canvas{margin:0 auto}',
'.ep-enhanced .ep-doc-list{margin:8px 0}',
'.ep-enhanced .ep-doc-item{padding:8px 12px;background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.06);border-radius:6px;margin:4px 0;font-size:11px;color:#7AAAC8;cursor:pointer;display:flex;align-items:center;gap:8px;transition:all .15s}',
'.ep-enhanced .ep-doc-item:hover{background:rgba(255,85,0,.08);border-color:rgba(255,85,0,.2);color:#FF5500}',
'.ep-enhanced .ep-doc-icon{font-family:"IBM Plex Mono",monospace;font-size:9px;font-weight:700;color:#F0A000;background:rgba(240,160,0,.1);padding:2px 6px;border-radius:3px}',
'.ep-enhanced .ep-maint-item{padding:8px 12px;background:rgba(255,255,255,.03);border-left:3px solid;border-radius:0 6px 6px 0;margin:6px 0;font-size:11px}',
'.ep-enhanced .ep-maint-item.m-prev{border-left-color:#10D858}',
'.ep-enhanced .ep-maint-item.m-corr{border-left-color:#E02020}',
'.ep-enhanced .ep-maint-item.m-pred{border-left-color:#00C8F0}',
'@media(max-width:768px){.ep-enhanced{width:100%!important;left:0!important}}'
].join('\n');
document.head.appendChild(eqpCSS);

/* Animated sparkline data */
var sparklineData = {};
var sparklineInterval = null;

function createAnimatedSparkline(containerId, color, minVal, maxVal, currentVal){
  var container = document.getElementById(containerId);
  if(!container) return;
  var w = container.clientWidth || 200;
  var h = 50;

  /* Generate initial data points */
  var points = [];
  var numPts = 40;
  for(var i=0;i<numPts;i++){
    var range = maxVal - minVal;
    var noise = (Math.random() - 0.5) * range * 0.3;
    points.push(Math.max(minVal, Math.min(maxVal, currentVal + noise)));
  }
  sparklineData[containerId] = {points:points, color:color, min:minVal, max:maxVal, current:currentVal};

  renderSparkline(containerId, w, h);
}

function renderSparkline(id, w, h){
  var data = sparklineData[id];
  if(!data) return;
  var container = document.getElementById(id);
  if(!container) return;
  var pts = data.points;
  var min = data.min;
  var max = data.max;
  var range = max - min || 1;

  var pathD = '';
  var areaD = '';
  var step = w / (pts.length - 1);
  pts.forEach(function(v, i){
    var x = i * step;
    var y = h - ((v - min) / range) * (h - 4) - 2;
    if(i === 0){ pathD = 'M'+x+','+y; areaD = 'M'+x+','+h+' L'+x+','+y; }
    else { pathD += ' L'+x+','+y; areaD += ' L'+x+','+y; }
  });
  areaD += ' L'+w+','+h+' Z';

  container.innerHTML = '<svg class="ep-sparkline" viewBox="0 0 '+w+' '+h+'" preserveAspectRatio="none">' +
    '<path class="area" d="'+areaD+'" fill="'+data.color+'"/>' +
    '<path d="'+pathD+'" stroke="'+data.color+'"/>' +
    '<circle cx="'+w+'" cy="'+(h-((pts[pts.length-1]-min)/range)*(h-4)-2)+'" r="3" fill="'+data.color+'"/>' +
  '</svg>';
}

function updateAllSparklines(){
  Object.keys(sparklineData).forEach(function(id){
    var data = sparklineData[id];
    var range = data.max - data.min || 1;
    var noise = (Math.random() - 0.5) * range * 0.15;
    var newVal = Math.max(data.min, Math.min(data.max, data.current + noise));
    data.current = newVal;
    data.points.push(newVal);
    if(data.points.length > 40) data.points.shift();
    var container = document.getElementById(id);
    if(container){
      renderSparkline(id, container.clientWidth || 200, 50);
    }
    /* Update live value display */
    var valEl = document.querySelector('[data-liveval="'+id+'"]');
    if(valEl) valEl.textContent = newVal.toFixed(1);
  });
}

/* Start sparkline animation */
if(!sparklineInterval){
  sparklineInterval = setInterval(updateAllSparklines, 1500);
}

/* Expose equipment panel builder for use by DT files */
window.showEnhancedEquipPanel = function(equipId, equipName, sensors, docs){
  var panel = document.getElementById('epEnhanced');
  if(!panel){
    panel = document.createElement('div');
    panel.id = 'epEnhanced';
    panel.className = 'ep-enhanced';
    document.body.appendChild(panel);
  }

  sensors = sensors || [];
  docs = docs || [];

  /* Build tabs content */
  var fichaRows = '';
  sensors.forEach(function(s){
    var pct = ((s.value - s.range[0]) / (s.range[1] - s.range[0])) * 100;
    var barColor = pct > 80 ? '#E02020' : pct > 60 ? '#F0A000' : '#10D858';
    fichaRows += '<div class="ep-kv"><span class="ek">' + s.variable + '</span><span class="ev">' + s.value.toFixed(1) + ' ' + s.unit + '</span></div>' +
      '<div class="ep-status-bar" style="background:rgba(255,255,255,.06)"><div style="width:'+pct+'%;height:100%;background:'+barColor+';border-radius:2px;transition:width .5s"></div></div>';
  });

  /* Build charts */
  var chartsHtml = '';
  sensors.slice(0,4).forEach(function(s, idx){
    var chartId = 'spk-' + equipId.replace(/[^a-z0-9]/gi,'') + '-' + idx;
    var color = idx===0?'#00C8F0':idx===1?'#10D858':idx===2?'#F0A000':'#FF5500';
    chartsHtml += '<div class="ep-chart-wrap">' +
      '<div class="ep-chart-title"><span>' + s.variable + ' (' + s.unit + ')</span><span class="ep-val-live" data-liveval="'+chartId+'">' + s.value.toFixed(1) + '</span></div>' +
      '<div id="'+chartId+'" style="width:100%;height:50px"></div>' +
    '</div>';
    setTimeout(function(){ createAnimatedSparkline(chartId, color, s.range[0], s.range[1], s.value); }, 100);
  });

  /* Build docs list */
  var docsHtml = '';
  docs.forEach(function(d){
    docsHtml += '<div class="ep-doc-item" onclick="if(typeof openAccFS===\'function\')openAccFS();else if(typeof openACCOverlay===\'function\')openACCOverlay();else if(typeof closeFsOverlay===\'function\')openFsOverlay(\'accOverlay\')">' +
      '<span class="ep-doc-icon">' + (d.tipo || 'PDF') + '</span>' +
      '<span style="flex:1">' + d.name + '</span>' +
      '<span style="font-size:9px;color:#3A607A">' + (d.ver || '') + '</span>' +
    '</div>';
  });
  if(docsHtml === ''){
    var folderKeys = Object.keys(PD.accFolders);
    folderKeys.slice(0,2).forEach(function(fk){
      PD.accFolders[fk].slice(0,2).forEach(function(d){
        docsHtml += '<div class="ep-doc-item"><span class="ep-doc-icon">' + d.tipo + '</span><span style="flex:1">' + d.name + '</span><span style="font-size:9px;color:#3A607A">' + d.ver + '</span></div>';
      });
    });
  }

  /* Maintenance history */
  var maintHtml =
    '<div class="ep-maint-item m-prev"><div style="display:flex;justify-content:space-between"><span style="color:#10D858;font-weight:600">Preventivo</span><span style="color:#3A607A">2026-02-15</span></div><div style="color:#7AAAC8;margin-top:2px">Inspeccion y calibracion de instrumentos</div></div>' +
    '<div class="ep-maint-item m-corr"><div style="display:flex;justify-content:space-between"><span style="color:#E02020;font-weight:600">Correctivo</span><span style="color:#3A607A">2026-01-22</span></div><div style="color:#7AAAC8;margin-top:2px">Reemplazo de empaque en sello mecanico</div></div>' +
    '<div class="ep-maint-item m-pred"><div style="display:flex;justify-content:space-between"><span style="color:#00C8F0;font-weight:600">Predictivo</span><span style="color:#3A607A">2025-12-10</span></div><div style="color:#7AAAC8;margin-top:2px">Analisis de vibracion - valores normales</div></div>' +
    '<div class="ep-maint-item m-prev"><div style="display:flex;justify-content:space-between"><span style="color:#10D858;font-weight:600">Preventivo</span><span style="color:#3A607A">2025-11-15</span></div><div style="color:#7AAAC8;margin-top:2px">Mantenimiento mayor programado</div></div>';

  /* QR section */
  var qrHtml = '<div class="ep-qr-wrap"><div id="epQrCode"></div><div style="font-size:10px;color:#3A607A;margin-top:8px">Escanear para ficha tecnica movil</div></div>';

  panel.innerHTML =
    '<div class="ep-hdr">' +
      '<span class="ep-tag">' + equipId + '</span>' +
      '<span class="ep-name">' + equipName + '</span>' +
      '<button class="ep-close" onclick="document.getElementById(\'epEnhanced\').classList.remove(\'show\')">&times;</button>' +
    '</div>' +
    '<div class="ep-tabs">' +
      '<div class="ep-tab active" data-eptab="ficha">Ficha</div>' +
      '<div class="ep-tab" data-eptab="charts">Tendencias</div>' +
      '<div class="ep-tab" data-eptab="docs">Documentos</div>' +
      '<div class="ep-tab" data-eptab="maint">Historial</div>' +
    '</div>' +
    '<div class="ep-body">' +
      '<div id="epTabFicha">' +
        '<div class="ep-section-title">Datos en Tiempo Real</div>' +
        fichaRows +
        '<div class="ep-section-title">Codigo QR del Activo</div>' +
        qrHtml +
      '</div>' +
      '<div id="epTabCharts" style="display:none">' +
        '<div class="ep-section-title">Tendencias en Vivo</div>' +
        chartsHtml +
      '</div>' +
      '<div id="epTabDocs" style="display:none">' +
        '<div class="ep-section-title">Documentos Asociados</div>' +
        '<div class="ep-doc-list">' + docsHtml + '</div>' +
      '</div>' +
      '<div id="epTabMaint" style="display:none">' +
        '<div class="ep-section-title">Historial de Mantenimiento</div>' +
        maintHtml +
      '</div>' +
    '</div>';

  panel.classList.add('show');

  /* Wire tabs */
  panel.querySelectorAll('.ep-tab').forEach(function(tab){
    tab.addEventListener('click', function(){
      panel.querySelectorAll('.ep-tab').forEach(function(t){t.classList.remove('active')});
      tab.classList.add('active');
      var tabId = tab.dataset.eptab;
      document.getElementById('epTabFicha').style.display = tabId==='ficha'?'':'none';
      document.getElementById('epTabCharts').style.display = tabId==='charts'?'':'none';
      document.getElementById('epTabDocs').style.display = tabId==='docs'?'':'none';
      document.getElementById('epTabMaint').style.display = tabId==='maint'?'':'none';
    });
  });

  /* Generate QR code if library available */
  setTimeout(function(){
    if(typeof qrcode !== 'undefined'){
      var qr = qrcode(0, 'M');
      qr.addData(PD.code + '/' + equipId);
      qr.make();
      var qrEl = document.getElementById('epQrCode');
      if(qrEl) qrEl.innerHTML = qr.createImgTag(4, 8);
    }
  }, 200);
};

})();
