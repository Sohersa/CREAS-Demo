const fs = require('fs');
const path = require('path');

const BASE = 'C:/Users/geren/Downloads/CREAS';

// ===============================================================
// PLANT-SPECIFIC CONFIGURATIONS
// ===============================================================
const PLANT_CONFIG = {
  'tas-DT.html': {
    name: 'Terminal Gas LP TAS',
    code: 'TAS-AGS-01',
    hubHref: 'gas-hub.html',
    accFolders: `
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 01-Planos Generales</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Plot Plan Rev.3</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-15</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">GA Drawing - Terminal</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-20</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 02-P&amp;ID</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">P&amp;ID-001 Sistema Almacenamiento</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-01</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">P&amp;ID-002 Sistema Despacho</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-12</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">P&amp;ID-003 Sistema SCI</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-05-18</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 03-Ingenieria Civil</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Cimentaciones Esferas</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-03-10</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Layout Vialidades</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-03-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 04-Ingenieria Mecanica</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Isometricos Piping LP</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-20</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Arreglo de Equipos</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-15</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 05-Ingenieria Electrica</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Diagrama Unifilar</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-05-22</span></div>
          <div class="acc-file"><span class="acc-ficon xlsx">XLSX</span><span class="acc-fname">Cuadro de Cargas Electrico</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-05-22</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 06-Instrumentacion</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon xlsx">XLSX</span><span class="acc-fname">Lista de Instrumentos</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-05</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Lazos de Control</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-30</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 07-Fichas Tecnicas</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Datasheet Esfera SPH-01</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-15</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Datasheet Bomba Centrifuga P-01</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-03-22</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Certificado PSV - Valvulas Seguridad</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 08-Manuales O&amp;M</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Manual Operacion Terminal</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-01-10</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Procedimientos Emergencia</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-01-10</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Procedimiento Carga Autotanques</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-04-05</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 09-Modelos BIM</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon rvt">RVT</span><span class="acc-fname">Modelo Federado Terminal</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-10</span></div>
          <div class="acc-file"><span class="acc-ficon rvt">RVT</span><span class="acc-fname">Modelo Civil Cimentaciones</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-01</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 10-Inspecciones</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Reporte Inspeccion API 510 Esferas</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-15</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Termografia Electrica</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-01</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Prueba hidrostatica Bullets</span><span class="acc-fbadge superseded">Superseded</span><span class="acc-fdate">2023-11-20</span></div>
        </div>
      </div>`,
    accSubmittals: [
      ['SUB-TAS-042','Certificado PSV Esfera SPH-03','Aprobado','approved'],
      ['SUB-TAS-041','Datasheet Bomba P-03','Pendiente','pending'],
      ['SUB-TAS-040','Informe inspeccion API 653','Aprobado','approved'],
      ['SUB-TAS-039','Plano as-built brazo carga #4','Rechazado','rejected']
    ],
    accRfis: [
      ['RFI-TAS-018','Discrepancia cota cimentacion SPH-03','Respondido','approved'],
      ['RFI-TAS-017','Clarificacion routing tuberias zona bombeo','Abierto','pending'],
      ['RFI-TAS-016','Detalle conexion brazo carga','Respondido','approved']
    ],
    tandemAssets: `
      <div class="td-tree-root" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Terminal TAS-AGS-01</div>
      <div class="td-tree-children">
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Almacenamiento</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> SPH-01 - Esfera 4200m3 <span class="td-tag-sm">10-SPH-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> SPH-02 - Esfera 4200m3 <span class="td-tag-sm">10-SPH-002</span></div>
          <div class="td-tree-leaf"><span class="td-dot warn"></span> SPH-03 - Esfera 4200m3 <span class="td-tag-sm">10-SPH-003</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> BT-01 - Bullet 650m3 <span class="td-tag-sm">10-BT-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> BT-02 - Bullet 650m3 <span class="td-tag-sm">10-BT-002</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Bombeo</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> P-01 - Bomba Centrifuga <span class="td-tag-sm">20-PMP-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> P-02 - Bomba Centrifuga <span class="td-tag-sm">20-PMP-002</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Compresion</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> COMP-01 - Compresor Reciprocante <span class="td-tag-sm">20-CMP-001</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Despacho</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> LR-01 - Llenadora Pos.1 <span class="td-tag-sm">30-LR-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot warn"></span> LR-02 - Llenadora Pos.2 <span class="td-tag-sm">30-LR-002</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> LR-03 - Llenadora Pos.3 <span class="td-tag-sm">30-LR-003</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Proteccion / SCI</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> FW-01 - Tanque Agua SCI <span class="td-tag-sm">40-FW-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> FP-01 - Bomba Contra Incendio <span class="td-tag-sm">40-FP-001</span></div>
        </div>
      </div>`,
    tandemProps: {name:'Esfera SPH-01',tag:'SPH-01',sap:'10-SPH-001',category:'Recipiente a Presion',system:'Almacenamiento',subsystem:'Esferas Gas LP',criticality:'ALTA',dimensions:'D=16.5m',capacity:'4,200 m3',material:'SA-516 Gr.70',status:'Operativo',lastInsp:'2024-06-15',nextPM:'2026-05-20',props:[['Presion Diseno','17.6 kg/cm2'],['MAWP','15.2 kg/cm2'],['Corrosion Rate','0.08 mm/yr'],['Espesor minimo','28.5 mm']]},
    tandemStreams: [
      ['LT-SPH-01','Nivel Esfera 1','OPC-UA','2s','74.2 %','ok'],
      ['PT-SPH-01','Presion Esfera 1','OPC-UA','2s','12.5 kg/cm2','ok'],
      ['TT-SPH-01','Temperatura Esfera 1','MQTT','5s','27.3 C','ok'],
      ['FT-MET-01','Flujo Medidor Fiscal','OPC-UA','1s','178 m3/h','ok'],
      ['GT-GD-01','Detector Gas Zona Esferas','MQTT','5s','0 %LEL','ok'],
      ['VT-P-01','Vibracion Bomba P-01','MQTT','10s','2.8 mm/s','delayed']
    ],
    tandemSync: {lastSync:'hace 3 min',propsSynced:312,streamsActive:86,dataQuality:'98.7'},
    tandemActivity: [
      'Property TEMPERATURE SPH-01 updated via MQTT - 5s ago',
      'Asset SPH-01 properties synced from SAP - 2 min ago',
      'New stream connected: PT-SPH-01 (OPC-UA) - 15 min ago',
      'Alarm SPH-03 NIVEL ALTO acknowledged - 28 min ago',
      'OT PM-TAS-4521 created for P-01 vibracion check - 1 hr ago',
      'Model sync completed: 312 properties updated - 2 hr ago'
    ]
  },
  'gnc-DT.html': {
    name: 'Estacion GNC Monterrey',
    code: 'GNC-MTY-01',
    hubHref: 'gas-hub.html',
    accFolders: `
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 01-Planos Generales</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Plot Plan Estacion GNC</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-15</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">GA Drawing Estacion</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-20</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 02-P&amp;ID</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">P&amp;ID-001 Sistema Compresion</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-01</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">P&amp;ID-002 Cascada Almacenamiento</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-12</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">P&amp;ID-003 Dispensadores</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-05-18</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 03-Ingenieria Civil</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Cimentaciones Compresores</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-03-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 04-Ingenieria Mecanica</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Isometricos Piping Alta Presion</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-20</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Arreglo Mecanico Compresores</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-15</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 05-Ingenieria Electrica</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Diagrama Unifilar</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-05-22</span></div>
          <div class="acc-file"><span class="acc-ficon xlsx">XLSX</span><span class="acc-fname">Cuadro de Cargas</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-05-22</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 06-Instrumentacion</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon xlsx">XLSX</span><span class="acc-fname">Lista de Instrumentos GNC</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-05</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 07-Fichas Tecnicas</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Datasheet Compresor Ariel JGK/4</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-04-12</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Certificacion Cilindros Cascada DOT</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-10</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Datasheet Dispensador Wayne</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-02-28</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 08-Manuales O&amp;M</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Manual Operacion Compresores</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-01-10</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Manual Dispensadores GNC</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-01-10</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Protocolo ESD Estacion</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-03-15</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 09-Modelos BIM</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon rvt">RVT</span><span class="acc-fname">Modelo Federado Estacion</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 10-Inspecciones</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Retest Cilindros Cascada 2024</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-15</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Calibracion Dispensadores Mar-2026</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2026-03-01</span></div>
        </div>
      </div>`,
    accSubmittals: [
      ['SUB-GNC-031','Certificacion cilindros cascada DOT','Aprobado','approved'],
      ['SUB-GNC-030','Calibracion dispensadores Q1-2026','Pendiente','pending'],
      ['SUB-GNC-029','Manual operacion compresor K-002','Aprobado','approved'],
      ['SUB-GNC-028','HAZOP actualizacion 2025','Rechazado','rejected']
    ],
    accRfis: [
      ['RFI-GNC-012','Presion setpoint regulador entrada','Respondido','approved'],
      ['RFI-GNC-011','Especificacion mangueras despacho','Abierto','pending'],
      ['RFI-GNC-010','Proteccion catodica ducto entrada','Respondido','approved']
    ],
    tandemAssets: `
      <div class="td-tree-root" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Estacion GNC-MTY-01</div>
      <div class="td-tree-children">
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Sistema de Entrada</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> FE-001 - Estacion Medicion <span class="td-tag-sm">FE-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> PCV-001 - Regulador Presion <span class="td-tag-sm">PCV-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> FL-001 - Filtro Coalescente <span class="td-tag-sm">FL-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> DR-001 - Secador Desecante <span class="td-tag-sm">DR-001</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Compresion</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> K-001 - Compresor 4 Etapas <span class="td-tag-sm">K-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> K-002 - Compresor 4 Etapas <span class="td-tag-sm">K-002</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Almacenamiento Cascada</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> Cascada Alta 250 bar <span class="td-tag-sm">CAS-H</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> Cascada Media 200 bar <span class="td-tag-sm">CAS-M</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> Cascada Baja 150 bar <span class="td-tag-sm">CAS-L</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Dispensadores</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> D-001 - Dispensador <span class="td-tag-sm">D-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> D-002 - Dispensador <span class="td-tag-sm">D-002</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> D-003 - Dispensador <span class="td-tag-sm">D-003</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> D-004 - Dispensador <span class="td-tag-sm">D-004</span></div>
        </div>
      </div>`,
    tandemProps: {name:'Compresor K-001',tag:'K-001',sap:'20-CMP-001',category:'Compresor Reciprocante',system:'Compresion',subsystem:'Compresion GNC',criticality:'ALTA',dimensions:'3.2x1.8x2.1m',capacity:'250 bar / 400 Nm3/h',material:'Acero Forjado',status:'Operativo',lastInsp:'2024-11-20',nextPM:'2026-04-15',props:[['Etapas','4'],['Motor','200 HP / 1800 RPM'],['Aceite','Mobil Rarus SHC 1026'],['Horas operacion','4,218 h']]},
    tandemStreams: [
      ['PT-K001-S','P.Succion K-001','OPC-UA','2s','4.0 bar','ok'],
      ['PT-K001-D','P.Descarga K-001','OPC-UA','2s','242 bar','ok'],
      ['TT-K001-4','Temp Desc 4ta Etapa','MQTT','5s','78 C','delayed'],
      ['VT-K001','Vibracion K-001','MQTT','10s','2.8 mm/s','ok'],
      ['CT-K001','Corriente K-001','OPC-UA','2s','142 A','ok'],
      ['FT-001','Flujo Gas Entrada','OPC-UA','1s','1280 Nm3/h','ok']
    ],
    tandemSync: {lastSync:'hace 2 min',propsSynced:245,streamsActive:68,dataQuality:'99.1'},
    tandemActivity: [
      'Property PRESION_DESCARGA K-001 updated via OPC-UA - 3s ago',
      'Asset K-001 properties synced from SAP - 1 min ago',
      'Alarm TT-K001-4 TEMP ALTA 4ta etapa triggered - 12 min ago',
      'OT PM-GNC-3201 completed for D-001 calibracion - 45 min ago',
      'Stream VT-K001 reconnected after timeout - 1 hr ago',
      'Model sync completed: 245 properties updated - 3 hr ago'
    ]
  },
  'lng-DT.html': {
    name: 'Planta LNG Monterrey',
    code: 'LNG-MTY-01',
    hubHref: 'gas-hub.html',
    accFolders: `
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 01-Planos Generales</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Plot Plan Planta LNG</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-15</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">GA Drawing Planta</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-20</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 02-P&amp;ID</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">P&amp;ID-001 Tren Licuefaccion</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-01</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">P&amp;ID-002 Almacenamiento Criogenico</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-12</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">P&amp;ID-003 Vaporizadores</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-05-18</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 03-Ingenieria Civil</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Cimentaciones Tanque Criogenico</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-03-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 04-Ingenieria Mecanica</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Isometricos Piping Criogenico</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-20</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Arreglo Vaporizadores</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-15</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 05-Ingenieria Electrica</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Diagrama Unifilar</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-05-22</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 06-Instrumentacion</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon xlsx">XLSX</span><span class="acc-fname">Lista Instrumentos Criogenicos</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-05</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 07-Fichas Tecnicas</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Spec Tanque Criogenico Vacuum Jacket</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-04-12</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Datasheet Vaporizador Ambiente</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-02-28</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Datasheet Bomba Criogenica</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 08-Manuales O&amp;M</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Manual Operacion Planta LNG</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-01-10</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Procedimiento Carga Criogenica</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-03-15</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Plan Emergencia Criogenica</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-01-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 09-Modelos BIM</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon rvt">RVT</span><span class="acc-fname">Modelo Federado LNG</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 10-Inspecciones</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Vacuum Jacket Integrity Report</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-15</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Reporte NDT Piping Criogenico</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-01</span></div>
        </div>
      </div>`,
    accSubmittals: [
      ['SUB-LNG-025','Vacuum jacket integrity test report','Aprobado','approved'],
      ['SUB-LNG-024','Datasheet bomba criogenica CP-02','Pendiente','pending'],
      ['SUB-LNG-023','Certificado vaporizador VAP-03','Aprobado','approved']
    ],
    accRfis: [
      ['RFI-LNG-009','Espesor aislamiento piping criogenico','Respondido','approved'],
      ['RFI-LNG-008','Material pernos baja temperatura','Abierto','pending']
    ],
    tandemAssets: `
      <div class="td-tree-root" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Planta LNG-MTY-01</div>
      <div class="td-tree-children">
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Almacenamiento Criogenico</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> TK-01 - Tanque Criogenico <span class="td-tag-sm">TK-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> TK-02 - Tanque Criogenico <span class="td-tag-sm">TK-002</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Vaporizacion</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> VAP-01 - Vaporizador Ambiente <span class="td-tag-sm">VAP-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> VAP-02 - Vaporizador Ambiente <span class="td-tag-sm">VAP-002</span></div>
          <div class="td-tree-leaf"><span class="td-dot warn"></span> VAP-03 - Vaporizador Agua Caliente <span class="td-tag-sm">VAP-003</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Bombeo Criogenico</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> CP-01 - Bomba Criogenica <span class="td-tag-sm">CP-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> CP-02 - Bomba Criogenica <span class="td-tag-sm">CP-002</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Despacho</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> BA-01 - Brazo Carga LNG <span class="td-tag-sm">BA-001</span></div>
        </div>
      </div>`,
    tandemProps: {name:'Tanque Criogenico TK-01',tag:'TK-01',sap:'10-TK-001',category:'Tanque Criogenico',system:'Almacenamiento',subsystem:'LNG Storage',criticality:'ALTA',dimensions:'D=12m H=18m',capacity:'2,500 m3',material:'9% Ni Steel / Perlita',status:'Operativo',lastInsp:'2024-06-15',nextPM:'2026-06-01',props:[['Temp Operacion','-162 C'],['P.Diseno','1.5 barg'],['Vacuum Level','< 1 mbar'],['Boil-off rate','0.08 %/dia']]},
    tandemStreams: [
      ['LT-TK01','Nivel TK-01','OPC-UA','2s','72.4 %','ok'],
      ['PT-TK01','Presion TK-01','OPC-UA','2s','0.85 barg','ok'],
      ['TT-TK01','Temp LNG TK-01','MQTT','5s','-161.8 C','ok'],
      ['FT-VAP01','Flujo Vaporizador 1','OPC-UA','1s','2,400 Nm3/h','ok'],
      ['TT-VAP03','Temp salida VAP-03','MQTT','5s','12 C','delayed'],
      ['PT-CP01','P.Descarga Bomba Crio','OPC-UA','2s','8.5 bar','ok']
    ],
    tandemSync: {lastSync:'hace 1 min',propsSynced:198,streamsActive:52,dataQuality:'99.4'},
    tandemActivity: [
      'Property NIVEL TK-01 updated via OPC-UA - 2s ago',
      'Asset VAP-03 alarm TEMP BAJA cleared - 8 min ago',
      'Stream TT-VAP03 latency warning - 20 min ago',
      'OT PM-LNG-1105 created for CP-02 mantenimiento - 1 hr ago',
      'Boil-off rate calculation updated - 2 hr ago',
      'Model sync completed: 198 properties updated - 4 hr ago'
    ]
  },
  'ductos-DT.html': {
    name: 'Estacion Compresion Ductos',
    code: 'DUC-CEN-01',
    hubHref: 'gas-hub.html',
    accFolders: `
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 01-Planos Generales</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Plot Plan Estacion Compresion</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-15</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 02-P&amp;ID</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">P&amp;ID-001 Tren Compresion</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-01</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">P&amp;ID-002 Sistema Gas Combustible</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-12</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 04-Ingenieria Mecanica</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Isometricos Piping Alta Presion</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-20</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Arreglo Turbinas y Compresores</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-15</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 05-Ingenieria Electrica</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Diagrama Unifilar Estacion</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-05-22</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 07-Fichas Tecnicas</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Datasheet Turbina Gas Solar Taurus 60</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-04-12</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Datasheet Compresor Centrifugo</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-02-28</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Reporte Pigging Inspeccion ILI</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 08-Manuales O&amp;M</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Manual Operacion Turbinas</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-01-10</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Procedimiento Pigging</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-03-15</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Pipeline Integrity Management Plan</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-01-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 09-Modelos BIM</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon rvt">RVT</span><span class="acc-fname">Modelo Federado Estacion</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 10-Inspecciones</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Inspeccion ILI Pipeline 2024</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-15</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Boroscopia Turbinas Q2-2024</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-01</span></div>
        </div>
      </div>`,
    accSubmittals: [
      ['SUB-DUC-055','Reporte ILI pipeline tramo norte','Aprobado','approved'],
      ['SUB-DUC-054','Boroscopia turbina GT-001','Pendiente','pending'],
      ['SUB-DUC-053','Manual procedimiento pigging','Aprobado','approved'],
      ['SUB-DUC-052','HAZOP estacion rev.2025','Rechazado','rejected']
    ],
    accRfis: [
      ['RFI-DUC-022','Espesor minimo pipeline km 42','Respondido','approved'],
      ['RFI-DUC-021','Especificacion gas combustible turbina','Abierto','pending'],
      ['RFI-DUC-020','Proteccion catodica cruce rio','Respondido','approved']
    ],
    tandemAssets: `
      <div class="td-tree-root" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Estacion DUC-CEN-01</div>
      <div class="td-tree-children">
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Turbocompresores</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> GT-001 - Turbina Gas + Compresor <span class="td-tag-sm">GT-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> GT-002 - Turbina Gas + Compresor <span class="td-tag-sm">GT-002</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Recipientes</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> V-001 - Separador Succion <span class="td-tag-sm">V-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> V-002 - Scrubber Gas Comb. <span class="td-tag-sm">V-002</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Enfriamiento</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> AC-001 - Aeroenfriador <span class="td-tag-sm">AC-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> AC-002 - Aeroenfriador <span class="td-tag-sm">AC-002</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Medicion / Lanzadores</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> MET-001 - Medidor Ultrasonico <span class="td-tag-sm">MET-001</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> PIG-L - Lanzador Diablo <span class="td-tag-sm">PIG-L</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> PIG-R - Receptor Diablo <span class="td-tag-sm">PIG-R</span></div>
        </div>
      </div>`,
    tandemProps: {name:'Turbocompresor GT-001',tag:'GT-001',sap:'20-GT-001',category:'Turbocompresor Gas',system:'Compresion',subsystem:'Tren 1',criticality:'ALTA',dimensions:'8.5x3.2x3.0m',capacity:'98 MMSCFD',material:'Inconel 718 / SS316',status:'Operativo',lastInsp:'2024-08-01',nextPM:'2026-05-15',props:[['Modelo','Solar Taurus 60'],['RPM Turbina','11,200'],['RPM Compresor','10,800'],['Ratio Compresion','1.60']]},
    tandemStreams: [
      ['PT-GT001-S','P.Succion GT-001','OPC-UA','1s','42 bar','ok'],
      ['PT-GT001-D','P.Descarga GT-001','OPC-UA','1s','67 bar','ok'],
      ['TT-GT001-EX','Temp Escape Turbina','MQTT','2s','485 C','ok'],
      ['VT-GT001-R','Vibracion Radial GT-001','MQTT','5s','12.8 um','ok'],
      ['ST-GT001','Velocidad GT-001','OPC-UA','1s','11,200 rpm','ok'],
      ['FT-MET01','Flujo Pipeline','OPC-UA','1s','98 MMSCFD','ok']
    ],
    tandemSync: {lastSync:'hace 30 seg',propsSynced:384,streamsActive:124,dataQuality:'99.8'},
    tandemActivity: [
      'Property RPM GT-001 updated via OPC-UA - 1s ago',
      'Vibration trending GT-001 within limits - 5 min ago',
      'Gas composition analysis updated - 15 min ago',
      'OT PM-DUC-8820 boroscopia GT-002 scheduled - 30 min ago',
      'Pipeline pressure profile updated (86 km) - 1 hr ago',
      'Model sync completed: 384 properties updated - 2 hr ago'
    ]
  },
  'fv-DT.html': {
    name: 'Planta Solar FV Sonora',
    code: 'FV-SON-01',
    hubHref: 'gas-hub.html',
    accFolders: `
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 01-Planos Generales</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Plot Plan Planta Solar 50 MWp</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-15</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Panel Layout &amp; String Plan</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-20</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 02-Ingenieria Electrica</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Diagrama Unifilar General</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-01</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Single Line MV Collection</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-12</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Cable Routing DC/MV</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-05-18</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Subestacion GA &amp; Sections</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-04-22</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 03-Ingenieria Civil</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Grading &amp; Drainage Plan</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-03-10</span></div>
          <div class="acc-file"><span class="acc-ficon dwg">DWG</span><span class="acc-fname">Tracker Foundation Details</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-03-10</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 07-Fichas Tecnicas</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Datasheet Modulo 550W Bifacial</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-04-12</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Datasheet Inversor String 5 MW</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-02-28</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Datasheet Trafo 25 MVA</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-10</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">String Test Report Bloque 1-6</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-15</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 08-Manuales O&amp;M</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Manual O&amp;M Planta Solar</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-01-10</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Manual Inversor String</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-01-10</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Emergency Response Plan</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-03-15</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 09-Modelos BIM</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon rvt">RVT</span><span class="acc-fname">Modelo Campo Solar</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-09-10</span></div>
          <div class="acc-file"><span class="acc-ficon rvt">RVT</span><span class="acc-fname">Modelo Subestacion 115 kV</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-01</span></div>
        </div>
      </div>
      <div class="acc-folder" onclick="this.classList.toggle('open')">
        <div class="acc-folder-hdr"><span class="acc-arrow">&#9654;</span> 10-Inspecciones</div>
        <div class="acc-folder-body">
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Termografia Paneles Bloque 1-3</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-06-15</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">Electroluminiscencia Modulos</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-08-01</span></div>
          <div class="acc-file"><span class="acc-ficon pdf">PDF</span><span class="acc-fname">IV Curve Testing Report</span><span class="acc-fbadge current">Current</span><span class="acc-fdate">2024-07-20</span></div>
        </div>
      </div>`,
    accSubmittals: [
      ['SUB-FV-038','String test report bloque 6','Aprobado','approved'],
      ['SUB-FV-037','Datasheet inversor central IC-01','Pendiente','pending'],
      ['SUB-FV-036','Termografia paneles bloque 4-6','Aprobado','approved'],
      ['SUB-FV-035','Certificado trafo TRAFO-02','Rechazado','rejected']
    ],
    accRfis: [
      ['RFI-FV-015','Distancia entre filas trackers','Respondido','approved'],
      ['RFI-FV-014','Calibre cable DC para string 1100V','Abierto','pending'],
      ['RFI-FV-013','Fundacion tracker en zona rocky','Respondido','approved']
    ],
    tandemAssets: `
      <div class="td-tree-root" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Planta FV-SON-01</div>
      <div class="td-tree-children">
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Campo Solar</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> BLQ-01..06 - Bloques Solares <span class="td-tag-sm">FL-010..060</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> TRK-xxx - Trackers (48) <span class="td-tag-sm">FL-1xx</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> STR-xxx - Strings PV (288) <span class="td-tag-sm">FL-2xx</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Conversion</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> INV-S01..06 - Inversores String <span class="td-tag-sm">FL-300..350</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> INV-C01 - Inversor Central <span class="td-tag-sm">FL-400</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> CB-01..24 - Combiner Boxes <span class="td-tag-sm">FL-5xx</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Transformacion</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> TRAFO-01 - Trafo MV 25 MVA <span class="td-tag-sm">FL-600</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> TRAFO-02 - Trafo MV 25 MVA <span class="td-tag-sm">FL-610</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Subestacion</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> SE-01 - Subestacion 115 kV <span class="td-tag-sm">FL-700</span></div>
        </div>
        <div class="td-tree-branch" onclick="this.classList.toggle('open')"><span class="td-arrow">&#9654;</span> Auxiliares</div>
        <div class="td-tree-children">
          <div class="td-tree-leaf"><span class="td-dot ok"></span> WS-01 - Estacion Meteorologica <span class="td-tag-sm">FL-800</span></div>
          <div class="td-tree-leaf"><span class="td-dot ok"></span> SCADA-01 - Sistema SCADA <span class="td-tag-sm">FL-900</span></div>
        </div>
      </div>`,
    tandemProps: {name:'Inversor String INV-S01',tag:'INV-S01',sap:'FL-300',category:'Inversor String',system:'Conversion',subsystem:'DC-AC Conversion',criticality:'ALTA',dimensions:'2.6x1.1x0.8m',capacity:'5 MW / 1100 Vdc',material:'IP65 / Aluminio',status:'Operativo',lastInsp:'2024-08-15',nextPM:'2026-04-20',props:[['Eficiencia','98.6%'],['MPPT Channels','12'],['THD','< 3%'],['Potencia Nominal','5,000 kW']]},
    tandemStreams: [
      ['PAC-INV01','Potencia AC INV-S01','OPC-UA','1s','4.82 MW','ok'],
      ['PDC-INV01','Potencia DC INV-S01','OPC-UA','1s','4.95 MW','ok'],
      ['IRRAD-WS01','Irradiancia POA','MQTT','5s','945 W/m2','ok'],
      ['TMOD-WS01','Temp Modulo','MQTT','10s','52 C','delayed'],
      ['VSTR-01','Voltaje String 01','OPC-UA','2s','1,100 V','ok'],
      ['FREQ-SE01','Frecuencia Red','OPC-UA','1s','60.01 Hz','ok']
    ],
    tandemSync: {lastSync:'hace 1 min',propsSynced:847,streamsActive:48,dataQuality:'99.2'},
    tandemActivity: [
      'Property IRRADIANCIA updated via MQTT - 3s ago',
      'Tracker angle updated: 35.2 deg - 1 min ago',
      'String STR-042 current anomaly cleared - 10 min ago',
      'Performance ratio calculated: 84.2% - 15 min ago',
      'OT PM-FV-2201 limpieza paneles bloque 3 - 2 hr ago',
      'Model sync completed: 847 properties updated - 3 hr ago'
    ]
  }
};

// ===============================================================
// GENERATE ACC PANEL HTML
// ===============================================================
function generateACCPanel(config) {
  let submittalsHTML = '';
  config.accSubmittals.forEach(s => {
    submittalsHTML += `<div class="acc-submittal"><span class="acc-sub-id">${s[0]}</span><span class="acc-sub-name">${s[1]}</span><span class="acc-sub-badge ${s[3]}">${s[2]}</span></div>`;
  });
  let rfisHTML = '';
  config.accRfis.forEach(r => {
    rfisHTML += `<div class="acc-submittal"><span class="acc-sub-id">${r[0]}</span><span class="acc-sub-name">${r[1]}</span><span class="acc-sub-badge ${r[3]}">${r[2]}</span></div>`;
  });

  return `
<!-- ACC Header -->
<div style="background:#1a1a2e;border:1px solid rgba(0,200,240,0.15);border-radius:6px;padding:12px;margin:12px 12px 10px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
    <div style="background:#0696D7;color:#fff;padding:3px 8px;border-radius:3px;font-size:10px;font-weight:700;">ACC</div>
    <span style="font-size:13px;font-weight:600;color:#E8F4FF;">Autodesk Construction Cloud</span>
  </div>
  <div style="font-size:10px;color:#7AAAC8;">Proyecto: ${config.code} | CDE: Activo | Ultimo sync: hace 3 min</div>
</div>

<div style="padding:0 12px 12px;overflow-y:auto;">
  <div style="font-size:11px;font-weight:600;color:#7AAAC8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;font-family:'IBM Plex Mono',monospace;">Explorador de Documentos</div>
  ${config.accFolders}

  <div style="font-size:11px;font-weight:600;color:#7AAAC8;text-transform:uppercase;letter-spacing:1px;margin:16px 0 8px;font-family:'IBM Plex Mono',monospace;">Submittals</div>
  ${submittalsHTML}

  <div style="font-size:11px;font-weight:600;color:#7AAAC8;text-transform:uppercase;letter-spacing:1px;margin:16px 0 8px;font-family:'IBM Plex Mono',monospace;">RFIs</div>
  ${rfisHTML}
</div>`;
}

// ===============================================================
// GENERATE TANDEM PANEL HTML
// ===============================================================
function generateTandemPanel(config) {
  const p = config.tandemProps;
  let propsHTML = '';
  p.props.forEach(pr => {
    propsHTML += `<div class="td-prop-row"><span class="td-pk">${pr[0]}</span><span class="td-pv">${pr[1]}</span></div>`;
  });
  let streamsHTML = '';
  config.tandemStreams.forEach(s => {
    const statusCls = s[5] === 'ok' ? 'ok' : s[5] === 'delayed' ? 'delayed' : 'disc';
    streamsHTML += `<div class="td-stream"><div class="td-stream-dot ${statusCls}"></div><div class="td-stream-info"><div class="td-stream-name">${s[0]} - ${s[1]}</div><div class="td-stream-meta">${s[2]} | ${s[3]} | ${s[4]}</div></div></div>`;
  });
  const sync = config.tandemSync;
  let activityHTML = '';
  config.tandemActivity.forEach(a => {
    activityHTML += `<div class="td-activity-item">${a}</div>`;
  });

  const critColor = p.criticality === 'ALTA' ? '#E02020' : p.criticality === 'MEDIA' ? '#F0A000' : '#10D858';

  return `
<!-- Tandem Header -->
<div style="background:#1a1a2e;border:1px solid rgba(0,200,240,0.15);border-radius:6px;padding:12px;margin:12px 12px 10px;">
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
    <div style="background:#00C8F0;color:#0A1420;padding:3px 8px;border-radius:3px;font-size:10px;font-weight:700;">TANDEM</div>
    <span style="font-size:13px;font-weight:600;color:#E8F4FF;">Autodesk Tandem</span>
  </div>
  <div style="font-size:10px;color:#7AAAC8;">Facility: ${config.code} | Modelo sincronizado | IoT: Activo</div>
</div>

<div style="padding:0 12px 12px;overflow-y:auto;">
  <!-- Asset Graph -->
  <div class="td-section-hdr">Grafo de Activos</div>
  <div class="td-tree">
    ${config.tandemAssets}
  </div>

  <!-- Properties Panel -->
  <div class="td-section-hdr">Propiedades del Activo</div>
  <div class="td-props-card">
    <div class="td-props-group">Identity</div>
    <div class="td-prop-row"><span class="td-pk">Nombre</span><span class="td-pv">${p.name}</span></div>
    <div class="td-prop-row"><span class="td-pk">Tag</span><span class="td-pv">${p.tag}</span></div>
    <div class="td-prop-row"><span class="td-pk">SAP Object</span><span class="td-pv">${p.sap}</span></div>
    <div class="td-prop-row"><span class="td-pk">Categoria</span><span class="td-pv">${p.category}</span></div>

    <div class="td-props-group">Clasificacion</div>
    <div class="td-prop-row"><span class="td-pk">Sistema</span><span class="td-pv">${p.system}</span></div>
    <div class="td-prop-row"><span class="td-pk">Subsistema</span><span class="td-pv">${p.subsystem}</span></div>
    <div class="td-prop-row"><span class="td-pk">Criticidad</span><span class="td-pv" style="color:${critColor};font-weight:700;">${p.criticality}</span></div>

    <div class="td-props-group">Fisico</div>
    <div class="td-prop-row"><span class="td-pk">Dimensiones</span><span class="td-pv">${p.dimensions}</span></div>
    <div class="td-prop-row"><span class="td-pk">Capacidad</span><span class="td-pv">${p.capacity}</span></div>
    <div class="td-prop-row"><span class="td-pk">Material</span><span class="td-pv">${p.material}</span></div>

    <div class="td-props-group">Operacional</div>
    <div class="td-prop-row"><span class="td-pk">Estado</span><span class="td-pv" style="color:#10D858">${p.status}</span></div>
    <div class="td-prop-row"><span class="td-pk">Ult. Inspeccion</span><span class="td-pv">${p.lastInsp}</span></div>
    <div class="td-prop-row"><span class="td-pk">Proxima PM</span><span class="td-pv">${p.nextPM}</span></div>

    <div class="td-props-group">Custom Properties</div>
    ${propsHTML}
  </div>

  <!-- Streams -->
  <div class="td-section-hdr">Streams (IoT)</div>
  <div class="td-streams-card">
    ${streamsHTML}
  </div>

  <!-- Sync Status -->
  <div class="td-section-hdr">Sync Status</div>
  <div class="td-sync-card">
    <div class="td-prop-row"><span class="td-pk">Ultimo sync modelo</span><span class="td-pv">${sync.lastSync}</span></div>
    <div class="td-prop-row"><span class="td-pk">Properties synced</span><span class="td-pv">${sync.propsSynced}</span></div>
    <div class="td-prop-row"><span class="td-pk">Streams activos</span><span class="td-pv">${sync.streamsActive}</span></div>
    <div class="td-prop-row"><span class="td-pk">Data quality</span><span class="td-pv" style="color:#10D858">${sync.dataQuality}%</span></div>
  </div>

  <!-- Recent Activity -->
  <div class="td-section-hdr">Actividad Reciente</div>
  <div class="td-activity-card">
    ${activityHTML}
  </div>
</div>`;
}

// ===============================================================
// CSS FOR ACC AND TANDEM (injected once per file)
// ===============================================================
const SHARED_CSS = `
/* ══════════════════════════════════
   ACC FOLDER EXPLORER
   ══════════════════════════════════ */
.acc-folder{margin-bottom:2px}
.acc-folder-hdr{display:flex;align-items:center;gap:6px;padding:7px 10px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:4px;cursor:pointer;font-size:11px;font-weight:600;color:#7AAAC8;transition:background 0.15s}
.acc-folder-hdr:hover{background:rgba(255,255,255,0.06)}
.acc-arrow{font-size:8px;transition:transform 0.2s;display:inline-block;color:#3A607A}
.acc-folder.open .acc-arrow{transform:rotate(90deg)}
.acc-folder-body{display:none;padding:2px 0 2px 18px}
.acc-folder.open .acc-folder-body{display:block}
.acc-file{display:flex;align-items:center;gap:6px;padding:5px 8px;border-bottom:1px solid rgba(255,255,255,0.04);font-size:10px;transition:background 0.1s}
.acc-file:hover{background:rgba(255,255,255,0.04)}
.acc-ficon{display:inline-block;padding:1px 4px;border-radius:2px;font-size:8px;font-weight:700;font-family:'IBM Plex Mono',monospace;min-width:28px;text-align:center}
.acc-ficon.dwg{background:rgba(0,200,240,0.15);color:#00C8F0}
.acc-ficon.pdf{background:rgba(224,32,32,0.15);color:#E02020}
.acc-ficon.xlsx{background:rgba(16,216,88,0.15);color:#10D858}
.acc-ficon.rvt{background:rgba(255,85,0,0.15);color:#FF5500}
.acc-fname{flex:1;color:#E8F4FF;font-family:'IBM Plex Mono',monospace;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.acc-fbadge{padding:1px 5px;border-radius:2px;font-size:8px;font-weight:600;font-family:'IBM Plex Mono',monospace}
.acc-fbadge.current{background:rgba(16,216,88,0.15);color:#10D858}
.acc-fbadge.superseded{background:rgba(255,255,255,0.08);color:#666}
.acc-fbadge.review{background:rgba(240,160,0,0.15);color:#F0A000}
.acc-fdate{color:#3A607A;font-family:'IBM Plex Mono',monospace;font-size:9px;min-width:64px;text-align:right}
.acc-submittal{display:flex;align-items:center;gap:6px;padding:6px 8px;border-bottom:1px solid rgba(255,255,255,0.04);font-size:10px}
.acc-sub-id{color:#7AAAC8;font-family:'IBM Plex Mono',monospace;font-size:9px;min-width:80px}
.acc-sub-name{flex:1;color:#E8F4FF;font-size:10px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.acc-sub-badge{padding:1px 5px;border-radius:2px;font-size:8px;font-weight:600;font-family:'IBM Plex Mono',monospace}
.acc-sub-badge.approved{background:rgba(16,216,88,0.15);color:#10D858}
.acc-sub-badge.pending{background:rgba(240,160,0,0.15);color:#F0A000}
.acc-sub-badge.rejected{background:rgba(224,32,32,0.15);color:#E02020}

/* ══════════════════════════════════
   TANDEM PANELS
   ══════════════════════════════════ */
.td-section-hdr{font-size:10px;font-weight:600;color:#7AAAC8;text-transform:uppercase;letter-spacing:1px;margin:12px 0 6px;padding-bottom:4px;border-bottom:1px solid rgba(255,255,255,0.06);font-family:'IBM Plex Mono',monospace}
.td-tree{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:4px;padding:8px;font-size:11px}
.td-tree-root{cursor:pointer;padding:4px 6px;font-weight:600;color:#E8F4FF}
.td-tree-root:hover{color:#FF5500}
.td-arrow{font-size:8px;display:inline-block;transition:transform 0.2s;color:#3A607A;margin-right:4px}
.td-tree-root.open .td-arrow,.td-tree-branch.open .td-arrow{transform:rotate(90deg)}
.td-tree-children{display:none;padding-left:14px}
.td-tree-root.open+.td-tree-children,.td-tree-branch.open+.td-tree-children{display:block}
.td-tree-branch{cursor:pointer;padding:3px 6px;color:#7AAAC8;font-weight:500}
.td-tree-branch:hover{color:#E8F4FF}
.td-tree-leaf{padding:2px 6px;color:#E8F4FF;font-size:10px;display:flex;align-items:center;gap:5px}
.td-dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.td-dot.ok{background:#10D858;box-shadow:0 0 4px #10D858}
.td-dot.warn{background:#F0A000;box-shadow:0 0 4px #F0A000}
.td-dot.crit{background:#E02020;box-shadow:0 0 4px #E02020}
.td-tag-sm{font-family:'IBM Plex Mono',monospace;font-size:8px;color:#3A607A;margin-left:auto}
.td-props-card,.td-streams-card,.td-sync-card,.td-activity-card{background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.06);border-radius:4px;padding:8px}
.td-props-group{font-size:9px;font-weight:600;color:#3A607A;text-transform:uppercase;letter-spacing:0.8px;padding:6px 0 2px;border-bottom:1px solid rgba(255,255,255,0.04);font-family:'IBM Plex Mono',monospace}
.td-prop-row{display:flex;justify-content:space-between;padding:3px 0;font-size:10px}
.td-pk{color:#7AAAC8}.td-pv{color:#E8F4FF;font-family:'IBM Plex Mono',monospace;font-size:10px;text-align:right}
.td-stream{display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.04)}
.td-stream-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.td-stream-dot.ok{background:#10D858;box-shadow:0 0 4px #10D858}
.td-stream-dot.delayed{background:#F0A000;box-shadow:0 0 4px #F0A000}
.td-stream-dot.disc{background:#E02020;box-shadow:0 0 4px #E02020}
.td-stream-info{flex:1;min-width:0}
.td-stream-name{font-size:10px;font-weight:600;color:#E8F4FF;font-family:'IBM Plex Mono',monospace}
.td-stream-meta{font-size:9px;color:#3A607A;font-family:'IBM Plex Mono',monospace}
.td-activity-item{padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.04);font-size:10px;color:#7AAAC8;font-family:'IBM Plex Mono',monospace}

/* ══════════════════════════════════
   ENHANCED EQUIP PANEL
   ══════════════════════════════════ */
.ep-qr-wrap{text-align:center;margin:8px 0}
.ep-qr-box{display:inline-block;padding:6px;background:#fff;border-radius:6px}
.ep-qr-label{font-size:9px;color:#7AAAC8;margin-top:4px}
.ep-crit-badge{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:3px;font-weight:700}
.ep-crit-badge.critica{background:rgba(224,32,32,0.2);color:#E02020}
.ep-crit-badge.alta{background:rgba(255,85,0,0.2);color:#FF5500}
.ep-crit-badge.media{background:rgba(240,160,0,0.2);color:#F0A000}
.ep-crit-badge.baja{background:rgba(16,216,88,0.2);color:#10D858}
.ep-status-badge{display:inline-block;font-family:'IBM Plex Mono',monospace;font-size:9px;padding:2px 6px;border-radius:3px;font-weight:600;margin-left:6px}
.ep-status-badge.operativo{background:rgba(16,216,88,0.15);color:#10D858}
.ep-status-badge.mantenimiento{background:rgba(240,160,0,0.15);color:#F0A000}
.ep-status-badge.fuera{background:rgba(224,32,32,0.15);color:#E02020}
.ep-doc-link{display:flex;align-items:center;gap:6px;padding:5px 8px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:4px;margin-bottom:3px;font-size:10px;color:#7AAAC8;cursor:pointer;transition:background 0.15s}
.ep-doc-link:hover{background:rgba(255,255,255,0.06);color:#E8F4FF}
.ep-doc-icon{font-size:8px;font-weight:700;padding:1px 4px;border-radius:2px;font-family:'IBM Plex Mono',monospace;background:rgba(224,32,32,0.15);color:#E02020}
.ep-maint-row{display:flex;justify-content:space-between;padding:3px 0;font-size:10px}
.ep-maint-row .mk{color:#7AAAC8}.ep-maint-row .mv{color:#E8F4FF;font-family:'IBM Plex Mono',monospace;font-size:10px}
.ep-trend-indicator{display:inline-block;font-size:10px;margin-left:4px}
`;

// ===============================================================
// QR CODE GENERATOR (JavaScript function to inject)
// ===============================================================
const QR_FUNCTION = `
function generateQR(tag) {
  var size = 80;
  var cells = 11;
  var cellSize = size / cells;
  var svg = '<svg width="'+size+'" height="'+size+'" xmlns="http://www.w3.org/2000/svg" style="background:#fff;border-radius:4px;">';
  // Fixed corner patterns
  function drawCorner(x, y) {
    svg += '<rect x="'+(x*cellSize)+'" y="'+(y*cellSize)+'" width="'+(3*cellSize)+'" height="'+(3*cellSize)+'" fill="#000"/>';
    svg += '<rect x="'+((x+0.5)*cellSize)+'" y="'+((y+0.5)*cellSize)+'" width="'+(2*cellSize)+'" height="'+(2*cellSize)+'" fill="#fff"/>';
    svg += '<rect x="'+((x+1)*cellSize)+'" y="'+((y+1)*cellSize)+'" width="'+cellSize+'" height="'+cellSize+'" fill="#000"/>';
  }
  drawCorner(0, 0);
  drawCorner(cells - 3, 0);
  drawCorner(0, cells - 3);
  // Deterministic pattern from tag
  var hash = 0;
  for (var i = 0; i < tag.length; i++) { hash = ((hash << 5) - hash) + tag.charCodeAt(i); hash |= 0; }
  for (var r = 0; r < cells; r++) {
    for (var c = 0; c < cells; c++) {
      if ((r < 3 && c < 3) || (r < 3 && c >= cells - 3) || (r >= cells - 3 && c < 3)) continue;
      var seed = (hash + r * 17 + c * 31) & 0x7FFFFFFF;
      if (seed % 3 === 0) {
        svg += '<rect x="'+(c*cellSize)+'" y="'+(r*cellSize)+'" width="'+cellSize+'" height="'+cellSize+'" fill="#000"/>';
      }
    }
  }
  svg += '</svg>';
  return '<div class="ep-qr-wrap"><div class="ep-qr-box">'+svg+'</div><div class="ep-qr-label">Escanear para abrir en campo</div></div>';
}
`;

// ===============================================================
// PROCESS EACH FILE
// ===============================================================
Object.keys(PLANT_CONFIG).forEach(filename => {
  const filepath = path.join(BASE, filename);
  let html = fs.readFileSync(filepath, 'utf8');
  const config = PLANT_CONFIG[filename];

  console.log(`Processing ${filename}...`);

  // ── STEP 0: Remove ALL emoji unicode characters ──
  // Remove common emoji ranges
  html = html.replace(/[\u{1F300}-\u{1F9FF}]/gu, '');
  html = html.replace(/[\u{2600}-\u{27BF}]/gu, function(m) {
    // Keep some safe symbols: arrows, technical symbols that aren't emojis
    const code = m.charCodeAt(0);
    // Keep: arrows (2190-21FF), technical (2300-23FF misc - but remove emoji-like ones), misc symbols that are used in UI
    // Remove clearly emoji ones: 2614, 2615, 2648-2653, 2660-2668, 2693, 2702-2708, 2712, 2714, 2716, 2728, 2733, 2734, 2744, 2747, 2753-2755, 2757, 2763, 2764
    // Actually let's be conservative - only remove the HTML entities that are clearly emojis
    return m;
  });

  // Remove emoji HTML entities that are clearly emojis (📁📄📊 etc)
  // &#128194; = 📂, &#128196; = 📄, &#128202; = 📊, &#128269; = 🔍, &#128268; = 🔌
  html = html.replace(/&#128194;/g, '');
  html = html.replace(/&#128196;/g, '');
  html = html.replace(/&#128202;/g, '');
  html = html.replace(/&#128269;/g, '');
  html = html.replace(/&#128268;/g, '');

  // ── STEP 1: VISIBLE HUB BUTTON ──
  const hubButton = `<a href="${config.hubHref}" style="display:flex;align-items:center;gap:6px;background:#FF5500;color:#fff;padding:6px 14px;border-radius:4px;text-decoration:none;font-size:12px;font-weight:600;letter-spacing:0.5px;transition:background 0.2s;" onmouseover="this.style.background='#cc4400'" onmouseout="this.style.background='#FF5500'"><span style="font-size:16px;">&#8592;</span> Hub Nacional</a>`;

  if (filename === 'tas-DT.html') {
    html = html.replace(
      /<a class="h-back" href="gas-hub\.html">&#8592; Hub<\/a>/,
      hubButton
    );
  } else if (filename === 'gnc-DT.html') {
    html = html.replace(
      /<a class="tb-back" href="gas-hub\.html">&#8592; Hub<\/a>/,
      hubButton
    );
  } else if (filename === 'lng-DT.html') {
    html = html.replace(
      /<a class="h-back" href="gas-hub\.html">&#8592; <span class="back-text">Hub<\/span><\/a>/,
      hubButton
    );
  } else if (filename === 'ductos-DT.html') {
    html = html.replace(
      /<a class="h-back" href="gas-hub\.html">&#8592; Hub<\/a>/,
      hubButton
    );
  } else if (filename === 'fv-DT.html') {
    html = html.replace(
      /<a class="h-btn" href="index\.html">&#8592; Hub<\/a>/,
      hubButton.replace('gas-hub.html', 'index.html')
    );
  }

  // ── STEP 2: INJECT SHARED CSS ──
  // Insert before </style>
  const styleCloseIdx = html.indexOf('</style>');
  if (styleCloseIdx !== -1) {
    html = html.slice(0, styleCloseIdx) + SHARED_CSS + html.slice(styleCloseIdx);
  }

  // ── STEP 3: REPLACE ACC TAB CONTENT ──
  const accPanelHTML = generateACCPanel(config);

  if (filename === 'tas-DT.html' || filename === 'lng-DT.html' || filename === 'ductos-DT.html') {
    // These use <div class="sl-panel" id="sl-acc">...</div>
    const accRegex = /(<div class="sl-panel" id="sl-acc">)([\s\S]*?)(<\/div>\s*<\/div>(?:\s*<\/div>)?(?:\s*<\/div>)?\s*(?=\n\s*(?:<!--|<div id="center|<\/div>)))/;
    // Safer: find the sl-acc div and replace its contents
    const accStartTag = '<div class="sl-panel" id="sl-acc">';
    const accStartIdx = html.indexOf(accStartTag);
    if (accStartIdx !== -1) {
      // Find the closing tag - need to count nested divs
      let depth = 1;
      let pos = accStartIdx + accStartTag.length;
      while (depth > 0 && pos < html.length) {
        const nextOpen = html.indexOf('<div', pos);
        const nextClose = html.indexOf('</div>', pos);
        if (nextClose === -1) break;
        if (nextOpen !== -1 && nextOpen < nextClose) {
          depth++;
          pos = nextOpen + 4;
        } else {
          depth--;
          if (depth === 0) {
            // Replace content between accStartTag and this closing tag
            html = html.slice(0, accStartIdx + accStartTag.length) + accPanelHTML + html.slice(nextClose);
            break;
          }
          pos = nextClose + 6;
        }
      }
    }
  } else if (filename === 'gnc-DT.html') {
    // Uses <div class="spanel" id="p-acc">
    const accStartTag = '<div class="spanel" id="p-acc">';
    const accStartIdx = html.indexOf(accStartTag);
    if (accStartIdx !== -1) {
      let depth = 1;
      let pos = accStartIdx + accStartTag.length;
      while (depth > 0 && pos < html.length) {
        const nextOpen = html.indexOf('<div', pos);
        const nextClose = html.indexOf('</div>', pos);
        if (nextClose === -1) break;
        if (nextOpen !== -1 && nextOpen < nextClose) {
          depth++;
          pos = nextOpen + 4;
        } else {
          depth--;
          if (depth === 0) {
            html = html.slice(0, accStartIdx + accStartTag.length) + accPanelHTML + html.slice(nextClose);
            break;
          }
          pos = nextClose + 6;
        }
      }
    }
  } else if (filename === 'fv-DT.html') {
    // Uses <div class="view" id="view-acc">
    const accStartTag = '<div class="view" id="view-acc">';
    const accStartIdx = html.indexOf(accStartTag);
    if (accStartIdx !== -1) {
      let depth = 1;
      let pos = accStartIdx + accStartTag.length;
      while (depth > 0 && pos < html.length) {
        const nextOpen = html.indexOf('<div', pos);
        const nextClose = html.indexOf('</div>', pos);
        if (nextClose === -1) break;
        if (nextOpen !== -1 && nextOpen < nextClose) {
          depth++;
          pos = nextOpen + 4;
        } else {
          depth--;
          if (depth === 0) {
            html = html.slice(0, accStartIdx + accStartTag.length) + accPanelHTML + html.slice(nextClose);
            break;
          }
          pos = nextClose + 6;
        }
      }
    }
  }

  // ── STEP 4: REPLACE TANDEM TAB CONTENT ──
  const tandemPanelHTML = generateTandemPanel(config);

  if (filename === 'tas-DT.html' || filename === 'lng-DT.html' || filename === 'ductos-DT.html') {
    const tandemStartTag = '<div class="sl-panel" id="sl-tandem">';
    const tandemStartIdx = html.indexOf(tandemStartTag);
    if (tandemStartIdx !== -1) {
      let depth = 1;
      let pos = tandemStartIdx + tandemStartTag.length;
      while (depth > 0 && pos < html.length) {
        const nextOpen = html.indexOf('<div', pos);
        const nextClose = html.indexOf('</div>', pos);
        if (nextClose === -1) break;
        if (nextOpen !== -1 && nextOpen < nextClose) {
          depth++;
          pos = nextOpen + 4;
        } else {
          depth--;
          if (depth === 0) {
            html = html.slice(0, tandemStartIdx + tandemStartTag.length) + tandemPanelHTML + html.slice(nextClose);
            break;
          }
          pos = nextClose + 6;
        }
      }
    }
  } else if (filename === 'gnc-DT.html') {
    const tandemStartTag = '<div class="spanel" id="p-tandem">';
    const tandemStartIdx = html.indexOf(tandemStartTag);
    if (tandemStartIdx !== -1) {
      let depth = 1;
      let pos = tandemStartIdx + tandemStartTag.length;
      while (depth > 0 && pos < html.length) {
        const nextOpen = html.indexOf('<div', pos);
        const nextClose = html.indexOf('</div>', pos);
        if (nextClose === -1) break;
        if (nextOpen !== -1 && nextOpen < nextClose) {
          depth++;
          pos = nextOpen + 4;
        } else {
          depth--;
          if (depth === 0) {
            html = html.slice(0, tandemStartIdx + tandemStartTag.length) + tandemPanelHTML + html.slice(nextClose);
            break;
          }
          pos = nextClose + 6;
        }
      }
    }
  } else if (filename === 'fv-DT.html') {
    const tandemStartTag = '<div class="view" id="view-tandem">';
    const tandemStartIdx = html.indexOf(tandemStartTag);
    if (tandemStartIdx !== -1) {
      let depth = 1;
      let pos = tandemStartIdx + tandemStartTag.length;
      while (depth > 0 && pos < html.length) {
        const nextOpen = html.indexOf('<div', pos);
        const nextClose = html.indexOf('</div>', pos);
        if (nextClose === -1) break;
        if (nextOpen !== -1 && nextOpen < nextClose) {
          depth++;
          pos = nextOpen + 4;
        } else {
          depth--;
          if (depth === 0) {
            html = html.slice(0, tandemStartIdx + tandemStartTag.length) + tandemPanelHTML + html.slice(nextClose);
            break;
          }
          pos = nextClose + 6;
        }
      }
    }
  }

  // ── STEP 5: INJECT QR FUNCTION ──
  // Add it before the first </script> tag or after the first <script> tag
  const firstScriptEnd = html.indexOf('</script>');
  if (firstScriptEnd !== -1) {
    // Find the script tag that contains the JS logic (after Three.js import)
    // Insert QR function into the main script block
    const mainScriptIdx = html.lastIndexOf('<script>');
    if (mainScriptIdx !== -1) {
      html = html.slice(0, mainScriptIdx + 8) + '\n' + QR_FUNCTION + '\n' + html.slice(mainScriptIdx + 8);
    }
  }

  // ── STEP 6: ENHANCE EQUIPMENT PANEL ──
  // Replace the showEquipPanel / updateRightPanel / selectAsset function to include QR code, enhanced info, docs, maintenance
  if (filename === 'tas-DT.html') {
    // Replace showEquipPanel function
    const oldFunc = `function showEquipPanel(asset){
  var panel=document.getElementById('equip-panel');
  panel.style.display='block';

  document.getElementById('epTag').textContent=asset.sap;
  document.getElementById('epName').textContent=asset.name;

  var confEl=document.getElementById('epConf');
  confEl.textContent='Criticidad: '+asset.criticality.toUpperCase();
  confEl.className='ep-conf '+asset.criticality;

  document.getElementById('epInfo').innerHTML=
    '<div class="ep-row"><span class="k">TAG</span><span class="v">'+asset.id+'</span></div>'+
    '<div class="ep-row"><span class="k">Sistema</span><span class="v">'+asset.system+'</span></div>'+
    '<div class="ep-row"><span class="k">Tipo</span><span class="v">'+asset.type+'</span></div>'+
    '<div class="ep-row"><span class="k">Capacidad</span><span class="v">'+asset.capacity+'</span></div>'+
    '<div class="ep-row"><span class="k">SAP Tag</span><span class="v">'+asset.sap+'</span></div>'+
    '<div class="ep-row"><span class="k">Estado</span><span class="v" style="color:var(--'+(asset.status==='ok'?'gr':asset.status==='warn'?'ye':'re')+')">'+(asset.status==='ok'?'NORMAL':asset.status==='warn'?'PRECAUCION':'ALARMA')+'</span></div>';

  var sensEl=document.getElementById('epSensors');
  sensEl.innerHTML='';
  asset.sensors.forEach(function(s){
    sensEl.innerHTML+='<div class="ep-sensor"><span class="sn">'+s.n+'</span><span class="sv '+s.s+'">'+s.v+(s.u?' '+s.u:'')+'</span></div>';
  });
}`;
    const newFunc = `function showEquipPanel(asset){
  var panel=document.getElementById('equip-panel');
  panel.style.display='block';
  var critMap={alta:'ALTA',media:'MEDIA',baja:'BAJA',critica:'CRITICA'};
  var critClass=asset.criticality;
  var statusText=asset.status==='ok'?'Operativo':asset.status==='warn'?'Mantenimiento':'Fuera';
  var statusClass=asset.status==='ok'?'operativo':asset.status==='warn'?'mantenimiento':'fuera';
  document.getElementById('epTag').textContent=asset.sap;
  document.getElementById('epName').textContent=asset.name;
  var confEl=document.getElementById('epConf');
  confEl.innerHTML='<span class="ep-crit-badge '+critClass+'">'+(critMap[critClass]||critClass.toUpperCase())+'</span><span class="ep-status-badge '+statusClass+'">'+statusText+'</span>';
  confEl.className='ep-conf';
  var qr=generateQR(asset.id);
  document.getElementById('epInfo').innerHTML=qr+
    '<div class="ep-row"><span class="k">TAG</span><span class="v">'+asset.id+'</span></div>'+
    '<div class="ep-row"><span class="k">Nombre</span><span class="v">'+asset.name+'</span></div>'+
    '<div class="ep-row"><span class="k">Sistema</span><span class="v">'+asset.system+'</span></div>'+
    '<div class="ep-row"><span class="k">Tipo</span><span class="v">'+asset.type+'</span></div>'+
    '<div class="ep-row"><span class="k">Capacidad</span><span class="v">'+asset.capacity+'</span></div>'+
    '<div class="ep-row"><span class="k">SAP Object</span><span class="v">'+asset.sap+'</span></div>'+
    '<div class="ep-row"><span class="k">Fabricante</span><span class="v">'+(asset.manufacturer||'N/A')+'</span></div>';
  var sensEl=document.getElementById('epSensors');
  sensEl.innerHTML='';
  asset.sensors.forEach(function(s){
    var trend=Math.random()>0.6?'&#9650;':Math.random()>0.3?'&#9660;':'&#9644;';
    var trendColor=s.s==='ok'?'#10D858':s.s==='warn'?'#F0A000':'#E02020';
    sensEl.innerHTML+='<div class="ep-sensor"><span class="sn">'+s.n+'</span><span class="sv '+s.s+'">'+s.v+(s.u?' '+s.u:'')+' <span class="ep-trend-indicator" style="color:'+trendColor+'">'+trend+'</span></span></div>';
  });
  // Documents linked section
  var docsDiv=document.createElement('div');
  docsDiv.innerHTML='<div class="ep-section">Documentos Vinculados</div>'+
    '<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Datasheet '+asset.id+'</div>'+
    '<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Manual O&M</div>'+
    '<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Ultimo reporte inspeccion</div>';
  sensEl.parentNode.insertBefore(docsDiv,sensEl.nextSibling.nextSibling||null);
  // Maintenance summary
  var maintDiv=document.createElement('div');
  var otNum='PM-TAS-'+(4000+Math.floor(Math.random()*1000));
  var hrsOp=Math.floor(2000+Math.random()*6000);
  maintDiv.innerHTML='<div class="ep-section">Resumen Mantenimiento</div>'+
    '<div class="ep-maint-row"><span class="mk">Ultima OT</span><span class="mv">'+otNum+'</span></div>'+
    '<div class="ep-maint-row"><span class="mk">Proxima PM</span><span class="mv">2026-05-'+(10+Math.floor(Math.random()*20))+'</span></div>'+
    '<div class="ep-maint-row"><span class="mk">Horas operacion</span><span class="mv">'+hrsOp.toLocaleString()+' h</span></div>';
  docsDiv.parentNode.insertBefore(maintDiv,docsDiv.nextSibling);
}`;
    html = html.replace(oldFunc, newFunc);

    // Also update the sensor refresh in updateSimulation
    const oldSensorUpdate = `sensEl.innerHTML+='<div class="ep-sensor"><span class="sn">'+s.n+'</span><span class="sv '+s.s+'">'+s.v+(s.u?' '+s.u:'')+'</span></div>';`;
    const newSensorUpdate = `var trend2=Math.random()>0.6?'&#9650;':Math.random()>0.3?'&#9660;':'&#9644;';var trendColor2=s.s==='ok'?'#10D858':s.s==='warn'?'#F0A000':'#E02020';sensEl.innerHTML+='<div class="ep-sensor"><span class="sn">'+s.n+'</span><span class="sv '+s.s+'">'+s.v+(s.u?' '+s.u:'')+' <span class="ep-trend-indicator" style="color:'+trendColor2+'">'+trend2+'</span></span></div>';`;
    // Only replace the one inside updateSimulation (the last occurrence)
    const lastIdx = html.lastIndexOf(oldSensorUpdate);
    if (lastIdx !== -1) {
      html = html.slice(0, lastIdx) + newSensorUpdate + html.slice(lastIdx + oldSensorUpdate.length);
    }
  }

  if (filename === 'ductos-DT.html') {
    // Replace showEquipPanel function
    const oldDuctosFunc = `function showEquipPanel(id){
  const a=ASSETS.find(x=>x.id===id);if(!a)return;
  const panel=document.getElementById('equip-panel');
  const content=document.getElementById('ep-content');
  const critClass=a.criticality==='alta'?'alta':a.criticality==='media'?'media':'baja';
  let html='<div class="ep-tag">'+a.tag+'</div>';
  html+='<div class="ep-name">'+a.name+'</div>';
  html+='<div class="ep-conf '+critClass+'">CRITICIDAD '+a.criticality.toUpperCase()+'</div>';
  html+='<div class="ep-section">Informacion</div>';
  html+='<div class="ep-row"><span class="k">Tipo</span><span class="v">'+a.type+'</span></div>';
  const stColor=a.status==='ok'?'gr':a.status==='warn'?'ye':'re';
  const stText=a.status==='ok'?'Operando':a.status==='warn'?'Alerta':'Critico';
  html+='<div class="ep-row"><span class="k">Estado</span><span class="v" style="color:var(--'+stColor+')">'+stText+'</span></div>';
  html+='<div class="ep-row"><span class="k">Tag</span><span class="v">'+a.tag+'</span></div>';
  html+='<div class="ep-section">Sensores en Tiempo Real</div>';
  a.sensors.forEach(s=>{
    const val=typeof s.v==='number'?s.v.toLocaleString():s.v;
    html+='<div class="ep-sensor"><span class="sn">'+s.n+'</span><span class="sv '+s.s+'">'+val+' '+s.u+'</span></div>';
  });
  html+='<button class="ep-btn" onclick="alert(\'Abriendo historico de '+a.tag+'...\')">Ver Historico</button>';
  html+='<button class="ep-btn" onclick="alert(\'Generando OT para '+a.tag+'...\')">Crear OT SAP</button>';
  content.innerHTML=html;
  panel.style.display='block';
}`;
    const newDuctosFunc = `function showEquipPanel(id){
  const a=ASSETS.find(x=>x.id===id);if(!a)return;
  const panel=document.getElementById('equip-panel');
  const content=document.getElementById('ep-content');
  const critClass=a.criticality==='alta'?'alta':a.criticality==='media'?'media':'baja';
  const statusText=a.status==='ok'?'Operativo':a.status==='warn'?'Mantenimiento':'Fuera';
  const statusClass=a.status==='ok'?'operativo':a.status==='warn'?'mantenimiento':'fuera';
  let html=generateQR(a.tag);
  html+='<div class="ep-tag">'+a.tag+'</div>';
  html+='<div class="ep-name">'+a.name+'</div>';
  html+='<span class="ep-crit-badge '+critClass+'">'+a.criticality.toUpperCase()+'</span>';
  html+='<span class="ep-status-badge '+statusClass+'">'+statusText+'</span>';
  html+='<div class="ep-section">Informacion General</div>';
  html+='<div class="ep-row"><span class="k">TAG</span><span class="v">'+a.id+'</span></div>';
  html+='<div class="ep-row"><span class="k">Nombre</span><span class="v">'+a.name+'</span></div>';
  html+='<div class="ep-row"><span class="k">Tipo</span><span class="v">'+a.type+'</span></div>';
  html+='<div class="ep-row"><span class="k">Tag</span><span class="v">'+a.tag+'</span></div>';
  const stColor=a.status==='ok'?'gr':a.status==='warn'?'ye':'re';
  html+='<div class="ep-row"><span class="k">Estado</span><span class="v" style="color:var(--'+stColor+')">'+statusText+'</span></div>';
  html+='<div class="ep-section">Sensores en Tiempo Real</div>';
  a.sensors.forEach(s=>{
    const val=typeof s.v==='number'?s.v.toLocaleString():s.v;
    const trend=Math.random()>0.6?'&#9650;':Math.random()>0.3?'&#9660;':'&#9644;';
    const trendColor=s.s==='ok'?'#10D858':s.s==='warn'?'#F0A000':'#E02020';
    html+='<div class="ep-sensor"><span class="sn">'+s.n+'</span><span class="sv '+s.s+'">'+val+' '+s.u+' <span class="ep-trend-indicator" style="color:'+trendColor+'">'+trend+'</span></span></div>';
  });
  html+='<div class="ep-section">Documentos Vinculados</div>';
  html+='<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Datasheet '+a.tag+'</div>';
  html+='<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Manual O&M</div>';
  html+='<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Ultimo reporte inspeccion</div>';
  html+='<div class="ep-section">Resumen Mantenimiento</div>';
  const otNum='PM-DUC-'+(8000+Math.floor(Math.random()*1000));
  const hrsOp=Math.floor(2000+Math.random()*6000);
  html+='<div class="ep-maint-row"><span class="mk">Ultima OT</span><span class="mv">'+otNum+'</span></div>';
  html+='<div class="ep-maint-row"><span class="mk">Proxima PM</span><span class="mv">2026-05-'+(10+Math.floor(Math.random()*20))+'</span></div>';
  html+='<div class="ep-maint-row"><span class="mk">Horas operacion</span><span class="mv">'+hrsOp.toLocaleString()+' h</span></div>';
  html+='<button class="ep-btn" onclick="alert(\'Abriendo historico de '+a.tag+'...\')">Ver Historico</button>';
  html+='<button class="ep-btn" onclick="alert(\'Generando OT para '+a.tag+'...\')">Crear OT SAP</button>';
  content.innerHTML=html;
  panel.style.display='block';
}`;
    html = html.replace(oldDuctosFunc, newDuctosFunc);
  }

  if (filename === 'lng-DT.html') {
    // Replace the selectAsset function content that builds the equipment panel
    const oldLngSelect = `  document.getElementById('epTag').textContent = a.tag;
  document.getElementById('epName').textContent = a.name;
  const conf = document.getElementById('epConf');
  conf.textContent = a.crit === 'alta' ? 'Criticidad Alta' : a.crit === 'media' ? 'Criticidad Media' : 'Normal';
  conf.className = 'ep-conf ' + a.crit;

  let infoHTML = '';
  for (const [k,v] of Object.entries(a.info)) {
    infoHTML += '<div class="ep-row"><span class="k">'+k+'</span><span class="v">'+v+'</span></div>';
  }
  document.getElementById('epInfo').innerHTML = infoHTML;

  let sensHTML = '';
  a.sensors.forEach(s => {
    sensHTML += '<div class="ep-sensor"><span class="sn">'+s.n+'</span><span class="sv '+s.s+'">'+s.v+'</span></div>';
  });
  document.getElementById('epSensors').innerHTML = sensHTML;
  document.getElementById('equip-panel').style.display = 'block';`;

    const newLngSelect = `  document.getElementById('epTag').textContent = a.tag;
  document.getElementById('epName').textContent = a.name;
  const conf = document.getElementById('epConf');
  const critClass = a.crit || 'baja';
  const statusText = a.status === 'ok' ? 'Operativo' : a.status === 'warn' ? 'Mantenimiento' : 'Fuera';
  const statusClass = a.status === 'ok' ? 'operativo' : a.status === 'warn' ? 'mantenimiento' : 'fuera';
  conf.innerHTML = '<span class="ep-crit-badge '+critClass+'">'+(critClass==='alta'?'ALTA':critClass==='media'?'MEDIA':'BAJA')+'</span><span class="ep-status-badge '+statusClass+'">'+statusText+'</span>';
  conf.className = 'ep-conf';
  let infoHTML = generateQR(a.tag || id);
  for (const [k,v] of Object.entries(a.info)) {
    infoHTML += '<div class="ep-row"><span class="k">'+k+'</span><span class="v">'+v+'</span></div>';
  }
  document.getElementById('epInfo').innerHTML = infoHTML;
  let sensHTML = '';
  a.sensors.forEach(s => {
    const trend=Math.random()>0.6?'&#9650;':Math.random()>0.3?'&#9660;':'&#9644;';
    const trendColor=s.s==='ok'?'#10D858':s.s==='warn'?'#F0A000':'#E02020';
    sensHTML += '<div class="ep-sensor"><span class="sn">'+s.n+'</span><span class="sv '+s.s+'">'+s.v+' <span class="ep-trend-indicator" style="color:'+trendColor+'">'+trend+'</span></span></div>';
  });
  sensHTML += '<div class="ep-section">Documentos Vinculados</div>';
  sensHTML += '<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Datasheet '+(a.tag||id)+'</div>';
  sensHTML += '<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Manual O&M</div>';
  sensHTML += '<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Ultimo reporte inspeccion</div>';
  sensHTML += '<div class="ep-section">Resumen Mantenimiento</div>';
  var otN='PM-LNG-'+(1000+Math.floor(Math.random()*1000));
  var hrsO=Math.floor(2000+Math.random()*6000);
  sensHTML += '<div class="ep-maint-row"><span class="mk">Ultima OT</span><span class="mv">'+otN+'</span></div>';
  sensHTML += '<div class="ep-maint-row"><span class="mk">Proxima PM</span><span class="mv">2026-06-'+(10+Math.floor(Math.random()*20))+'</span></div>';
  sensHTML += '<div class="ep-maint-row"><span class="mk">Horas operacion</span><span class="mv">'+hrsO.toLocaleString()+' h</span></div>';
  document.getElementById('epSensors').innerHTML = sensHTML;
  document.getElementById('equip-panel').style.display = 'block';`;
    html = html.replace(oldLngSelect, newLngSelect);
  }

  if (filename === 'gnc-DT.html') {
    // Replace updateRightPanel function
    const oldGncFunc = `function updateRightPanel(key) {
  var data = EQUIP_DATA[key];
  if (!data) return;

  var html = '<div class="rp-header">' +
    '<div class="rp-tag">' + data.tag + '</div>' +
    '<div class="rp-name">' + data.name + '</div>' +
    '<span class="rp-status ' + data.status + '">' + data.statusText + '</span>' +
    '</div><div class="rp-body">';

  data.info.forEach(function(sec) {
    html += '<div class="rp-sec">' + sec.section + '</div>';
    if (sec.rows) {
      sec.rows.forEach(function(r) {
        html += '<div class="rp-row"><span class="k">' + r[0] + '</span><span class="v">' + r[1] + '</span></div>';
      });
    }
    if (sec.sensors) {
      sec.sensors.forEach(function(s) {
        html += '<div class="rp-sensor"><span class="sn">' + s[0] + '</span><span class="sv ' + s[2] + '">' + s[1] + '</span></div>';
      });
    }
  });`;
    const newGncFunc = `function updateRightPanel(key) {
  var data = EQUIP_DATA[key];
  if (!data) return;

  var html = '<div class="rp-header">' +
    generateQR(data.tag) +
    '<div class="rp-tag">' + data.tag + '</div>' +
    '<div class="rp-name">' + data.name + '</div>' +
    '<span class="rp-status ' + data.status + '">' + data.statusText + '</span>' +
    '</div><div class="rp-body">';

  data.info.forEach(function(sec) {
    html += '<div class="rp-sec">' + sec.section + '</div>';
    if (sec.rows) {
      sec.rows.forEach(function(r) {
        html += '<div class="rp-row"><span class="k">' + r[0] + '</span><span class="v">' + r[1] + '</span></div>';
      });
    }
    if (sec.sensors) {
      sec.sensors.forEach(function(s) {
        var trend=Math.random()>0.6?'&#9650;':Math.random()>0.3?'&#9660;':'&#9644;';
        var trendColor=s[2]==='ok'?'#10D858':s[2]==='warn'?'#F0A000':'#E02020';
        html += '<div class="rp-sensor"><span class="sn">' + s[0] + '</span><span class="sv ' + s[2] + '">' + s[1] + ' <span class="ep-trend-indicator" style="color:'+trendColor+'">'+trend+'</span></span></div>';
      });
    }
  });`;
    html = html.replace(oldGncFunc, newGncFunc);

    // Now add docs and maintenance before the deselect button
    const oldDeselect = `  html += '<button class="rp-btn" onclick="clearSelection()">Deseleccionar</button></div>';`;
    const newDeselect = `  html += '<div class="rp-sec">DOCUMENTOS VINCULADOS</div>';
  html += '<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Datasheet ' + data.tag + '</div>';
  html += '<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Manual O&M</div>';
  html += '<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Ultimo reporte inspeccion</div>';
  html += '<div class="rp-sec">RESUMEN MANTENIMIENTO</div>';
  var otNum='PM-GNC-'+(3000+Math.floor(Math.random()*1000));
  var hrsOp=Math.floor(2000+Math.random()*6000);
  html += '<div class="ep-maint-row"><span class="mk">Ultima OT</span><span class="mv">'+otNum+'</span></div>';
  html += '<div class="ep-maint-row"><span class="mk">Proxima PM</span><span class="mv">2026-04-'+(10+Math.floor(Math.random()*20))+'</span></div>';
  html += '<div class="ep-maint-row"><span class="mk">Horas operacion</span><span class="mv">'+hrsOp.toLocaleString()+' h</span></div>';
  html += '<button class="rp-btn" onclick="clearSelection()">Deseleccionar</button></div>';`;
    html = html.replace(oldDeselect, newDeselect);
  }

  if (filename === 'fv-DT.html') {
    // Replace the selectAsset function
    const oldFvSelect = `function selectAsset(id){
  document.querySelectorAll('.asset-item').forEach(a=>a.classList.remove('active'));
  const el=document.querySelector(\`.asset-item[data-id="\${id}"]\`);
  if(el) el.classList.add('active');
  const data=ASSET_DATA[id];
  if(!data) return;
  document.getElementById('sr-title').textContent=data.title;
  document.getElementById('sr-tag').textContent=data.tag;
  let html='';
  html+='<div class="sr-section">Configuracion</div>';
  data.config.forEach(r=>html+=\`<div class="sr-row"><span class="k">\${r[0]}</span><span class="v">\${r[1]}</span></div>\`);
  html+='<div class="sr-section">Lecturas en Vivo</div>';
  data.sensors.forEach(s=>html+=\`<div class="sr-sensor"><span class="sn">\${s[0]}</span><span class="sv \${s[2]}">\${s[1]}</span></div>\`);
  html+='<div class="sr-section">Minitrend</div>';
  html+='<div class="sparkline" id="sr-spark2"></div>';
  html+=\`<button class="sr-btn" onclick="switchTab('monitor')">Ir a monitores</button>\`;
  document.getElementById('sr-body').innerHTML=html;`;

    const newFvSelect = `function selectAsset(id){
  document.querySelectorAll('.asset-item').forEach(a=>a.classList.remove('active'));
  const el=document.querySelector(\`.asset-item[data-id="\${id}"]\`);
  if(el) el.classList.add('active');
  const data=ASSET_DATA[id];
  if(!data) return;
  document.getElementById('sr-title').textContent=data.title;
  document.getElementById('sr-tag').textContent=data.tag;
  let html='';
  html+=generateQR(id);
  html+='<div class="sr-section">Configuracion</div>';
  data.config.forEach(r=>html+=\`<div class="sr-row"><span class="k">\${r[0]}</span><span class="v">\${r[1]}</span></div>\`);
  html+='<div class="sr-section">Lecturas en Vivo</div>';
  data.sensors.forEach(s=>{
    const trend=Math.random()>0.6?'&#9650;':Math.random()>0.3?'&#9660;':'&#9644;';
    const trendColor=s[2]==='ok'?'#10D858':s[2]==='warn'?'#F0A000':'#E02020';
    html+=\`<div class="sr-sensor"><span class="sn">\${s[0]}</span><span class="sv \${s[2]}">\${s[1]} <span class="ep-trend-indicator" style="color:\${trendColor}">\${trend}</span></span></div>\`;
  });
  html+='<div class="sr-section">Documentos Vinculados</div>';
  html+='<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Datasheet '+id+'</div>';
  html+='<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Manual O&M</div>';
  html+='<div class="ep-doc-link"><span class="ep-doc-icon">PDF</span>Ultimo reporte inspeccion</div>';
  html+='<div class="sr-section">Resumen Mantenimiento</div>';
  const otNum='PM-FV-'+(2000+Math.floor(Math.random()*1000));
  const hrsOp=Math.floor(2000+Math.random()*6000);
  html+=\`<div class="ep-maint-row"><span class="mk">Ultima OT</span><span class="mv">\${otNum}</span></div>\`;
  html+=\`<div class="ep-maint-row"><span class="mk">Proxima PM</span><span class="mv">2026-04-\${10+Math.floor(Math.random()*20)}</span></div>\`;
  html+=\`<div class="ep-maint-row"><span class="mk">Horas operacion</span><span class="mv">\${hrsOp.toLocaleString()} h</span></div>\`;
  html+='<div class="sr-section">Minitrend</div>';
  html+='<div class="sparkline" id="sr-spark2"></div>';
  html+=\`<button class="sr-btn" onclick="switchTab('monitor')">Ir a monitores</button>\`;
  document.getElementById('sr-body').innerHTML=html;`;
    html = html.replace(oldFvSelect, newFvSelect);
  }

  // Write the modified file
  fs.writeFileSync(filepath, html, 'utf8');
  console.log(`  Done: ${filename}`);
});

console.log('\nAll 5 files processed successfully.');
