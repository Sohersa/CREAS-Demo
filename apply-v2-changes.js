const fs = require('fs');
const path = 'C:/Users/geren/Downloads/CREAS/avicola-DT-v2.html';
let html = fs.readFileSync(path, 'utf-8');

// ============================================================
// 1. REPLACE ALL EMOJIS WITH TEXT LABELS
// ============================================================

// --- Topbar area buttons ---
html = html.replace('🌾 Granja Completa', 'Granja Completa');
html = html.replace('🥚 Postura', 'Postura');
html = html.replace('🐣 Crianza', 'Crianza');
html = html.replace('🏭 Incubadora', 'Incubadora');
html = html.replace('⚙️ Planta', 'Planta');
html = html.replace('📦 Silos', 'Silos');
html = html.replace('💧 Agua', 'Agua');

// --- Demo banner ---
html = html.replace('⚠ DEMO', 'AVISO: DEMO');

// --- Left sidebar tabs ---
html = html.replace(/<span class="stab-icon">📊<\/span>DASHBOARD/, '<span class="stab-icon">D</span>DASHBOARD');
html = html.replace(/<span class="stab-icon">⚡<\/span>SIMULAR/, '<span class="stab-icon">S</span>SIMULAR');
html = html.replace(/<span class="stab-icon">⚙️<\/span>SAP/, '<span class="stab-icon">E</span>SAP');
html = html.replace(/<span class="stab-icon">📡<\/span>IoT/, '<span class="stab-icon">I</span>IoT');

// --- Right sidebar tabs ---
html = html.replace(/<span class="stab-icon">🏭<\/span>EDIFICIOS/, '<span class="stab-icon">E</span>EDIFICIOS');
html = html.replace(/<span class="stab-icon">📹<\/span>CÁMARA/, '<span class="stab-icon">C</span>CAMARA');
html = html.replace(/<span class="stab-icon">🤖<\/span>IA CHAT/, '<span class="stab-icon">IA</span>IA CHAT');

// --- Mobile bottom nav ---
html = html.replace(/<span class="mn-icon">🏭<\/span>3D/, '<span class="mn-icon">3D</span>3D');
html = html.replace(/<span class="mn-icon">📊<\/span>Panel/, '<span class="mn-icon">P</span>Panel');
html = html.replace(/<span class="mn-icon">⚡<\/span>Alertas/, '<span class="mn-icon">!</span>Alertas');
html = html.replace(/<span class="mn-icon">💬<\/span>Chat/, '<span class="mn-icon">AI</span>Chat');

// --- Mobile badge ---
html = html.replace('📱 Mobile conectado', 'Mobile conectado');

// --- Alert button ---
html = html.replace(/⚡ ACTIVAR ALERTA/g, 'ACTIVAR ALERTA');

// --- Machine icons in M constant ---
html = html.replace(/icon:'🌀'/g, "icon:'[VNT]'");
html = html.replace(/icon:'🌾'/g, "icon:'[ALM]'");
html = html.replace(/icon:'💧'/g, "icon:'[H2O]'");
html = html.replace(/icon:'🔥'/g, "icon:'[GAS]'");
html = html.replace(/icon:'⚖️'/g, "icon:'[BAL]'");
html = html.replace(/icon:'🌡'/g, "icon:'[ENV]'");
html = html.replace(/icon:'🥚'/g, "icon:'[SET]'");
html = html.replace(/icon:'🐥'/g, "icon:'[HAT]'");
html = html.replace(/icon:'🔬'/g, "icon:'[CLS]'");
html = html.replace(/icon:'💉'/g, "icon:'[VAC]'");
html = html.replace(/icon:'⚙️'/g, "icon:'[MOL]'");
html = html.replace(/icon:'🔄'/g, "icon:'[MIX]'");
html = html.replace(/icon:'🔩'/g, "icon:'[PEL]'");
html = html.replace(/icon:'⛽'/g, "icon:'[BOM]'");
html = html.replace(/icon:'📊'/g, "icon:'[SIL]'");

// --- Particle/flow emojis (line ~1687) - CRITICAL: remove beer emoji ---
html = html.replace(
  "var emojis={egg:'🥚',water:'💧',chick:'🐣',grain:'🌽',feed:'🍺'};",
  "var emojis={egg:'H',water:'A',chick:'P',grain:'G',feed:'F'};"
);

// --- Sensor labels ---
html = html.replace(/label:G\.alert\?'⚡VNT/g, "label:G.alert?'VNT");
html = html.replace(/'💨 VNT '/g, "'VNT '");
html = html.replace(/'🌡 '/g, "'T ");
html = html.replace(/'🥚 '/g, "'INC ");
html = html.replace(/'📦 Maíz '/g, "'Maiz ");
html = html.replace(/'⚙️ 18/g, "'PLT 18");
html = html.replace(/'💧 4\.2/g, "'AGU 4.2");
html = html.replace(/'❄️ HVAC '/g, "'HVAC '");
// The two airflow labels
html = html.replace(/'💨 '\+G\.sens\.hvacCFM/g, "'CFM '+G.sens.hvacCFM");
html = html.replace(/'🌬️ PP-01/g, "'PP-01");
html = html.replace(/'🌬️ PP-05/g, "'PP-05");

// --- SIM step titles ---
html = html.replace(/title:'🥚 Postura/g, "title:'1. Postura");
html = html.replace(/title:'📋 Ronda/g, "title:'2. Ronda");
html = html.replace(/title:'⚖️ Control/g, "title:'3. Control");
html = html.replace(/title:'🚚 Traspaso/g, "title:'4. Traspaso");
html = html.replace(/title:'🏭 Incubación/g, "title:'5. Incubacion");
html = html.replace(/title:'🐥 Nacimiento/g, "title:'6. Nacimiento");
html = html.replace(/title:'🔬 Clasificación/g, "title:'7. Clasificacion");
html = html.replace(/title:'🐣 Crianza/g, "title:'8. Crianza");
html = html.replace(/title:'⚙️ Alimento/g, "title:'9. Alimento");

// --- SIM_VIZ node icons (production simulation) ---
html = html.replace(/\{i:'🐓'/g, "{i:'[G]'");
html = html.replace(/\{i:'⚖️'/g, "{i:'[B]'");
html = html.replace(/\{i:'📡'/g, "{i:'[S]'");
html = html.replace(/\{i:'📋'/g, "{i:'[D]'");
html = html.replace(/\{i:'📱'/g, "{i:'[M]'");
html = html.replace(/\{i:'📊'/g, "{i:'[R]'");
html = html.replace(/\{i:'💰'/g, "{i:'[F]'");
html = html.replace(/\{i:'📦'/g, "{i:'[P]'");
html = html.replace(/\{i:'📐'/g, "{i:'[C]'");
html = html.replace(/\{i:'🔄'/g, "{i:'[A]'");
html = html.replace(/\{i:'🍽️'/g, "{i:'[R]'");
html = html.replace(/\{i:'🥚'/g, "{i:'[H]'");
html = html.replace(/\{i:'🚚'/g, "{i:'[T]'");
html = html.replace(/\{i:'🏭'/g, "{i:'[I]'");
html = html.replace(/\{i:'🌡️'/g, "{i:'[T]'");
html = html.replace(/\{i:'💨'/g, "{i:'[V]'");
html = html.replace(/\{i:'🏗️'/g, "{i:'[DT]'");
html = html.replace(/\{i:'📷'/g, "{i:'[CV]'");
html = html.replace(/\{i:'🐣'/g, "{i:'[P]'");
html = html.replace(/\{i:'🔍'/g, "{i:'[Q]'");
html = html.replace(/\{i:'💉'/g, "{i:'[V]'");
html = html.replace(/\{i:'✅'/g, "{i:'[OK]'");
html = html.replace(/\{i:'🔥'/g, "{i:'[C]'");
html = html.replace(/\{i:'🌽'/g, "{i:'[S]'");
html = html.replace(/\{i:'⚙️'/g, "{i:'[P]'");
html = html.replace(/\{i:'5️⃣'/g, "{i:'[5]'");

// --- SAP panel icons ---
html = html.replace(/icon:'🔧'/g, "icon:'PM'");
html = html.replace(/icon:'🏭'/g, "icon:'PP'");
html = html.replace(/icon:'📦'/g, "icon:'MM'");
html = html.replace(/icon:'📊'/g, "icon:'CO'");
html = html.replace(/icon:'🚚'/g, "icon:'WM'");
html = html.replace(/icon:'✅'/g, "icon:'QM'");

// --- SAP Launchpad tile icons ---
function replaceSapTileEmoji(emoji, text) {
  // sapTile('emoji',... -> sapTile('text',...
  const re = new RegExp("sapTile\\('" + emoji.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&') + "'", 'g');
  html = html.replace(re, "sapTile('" + text + "'");
}
replaceSapTileEmoji('🔧', '[PM]');
replaceSapTileEmoji('🔔', '[NTF]');
replaceSapTileEmoji('⚙️', '[EQ]');
replaceSapTileEmoji('📏', '[MED]');
replaceSapTileEmoji('📋', '[HIS]');
replaceSapTileEmoji('🏭', '[PP]');
replaceSapTileEmoji('📈', '[GRF]');
replaceSapTileEmoji('📊', '[CB]');
replaceSapTileEmoji('🐓', '[AVE]');
replaceSapTileEmoji('📦', '[MOV]');
replaceSapTileEmoji('📉', '[STK]');
replaceSapTileEmoji('🚚', '[PED]');
replaceSapTileEmoji('💰', '[CO]');
replaceSapTileEmoji('✅', '[QM]');
replaceSapTileEmoji('🚛', '[WM]');

// --- Remaining scattered emojis ---
// SAP modal buttons
html = html.replace(/🏢 SAP Fiori/g, 'SAP Fiori');
html = html.replace(/🏗 Autodesk/g, 'Autodesk');
// Maintenance story buttons and icons
html = html.replace(/⚡ Ver cómo funciona/g, 'Ver como funciona');
html = html.replace(/⚡ Ver proceso automático/g, 'Ver proceso automatico');
html = html.replace(/'⚡ Ver Proceso'/g, "'Ver Proceso'");

// Alert center modal header
html = html.replace(/<span style="font-size:22px">🚨<\/span>/g, '<span style="font-size:14px;color:var(--re);font-weight:800">ALERTAS</span>');

// Notification modal header
html = html.replace(/<span style="font-size:20px">📲<\/span>/g, '<span style="font-size:14px;color:var(--cy);font-weight:800">NOTIF</span>');

// QR modal header
html = html.replace(/<span style="font-size:20px">🔲<\/span>/g, '<span style="font-size:14px;color:var(--cy);font-weight:800">QR</span>');

// Maintenance header icon
html = html.replace(/<div class="maint-hdr-icon">⚡<\/div>/, '<div class="maint-hdr-icon" style="font-size:14px;color:var(--or);font-weight:800">ALT</div>');

// CCTV AI label
html = html.replace(/🤖 IA YOLO/g, 'IA YOLO');

// Camera button
html = html.replace(/📹 Ver Cámara IP en Vivo/g, 'Ver Camara IP en Vivo');

// Open Mobile App button
html = html.replace(/📱 Abrir en App Móvil/g, 'Abrir en App Movil');

// SAP detail IoT flow nodes icons
html = html.replace(/sapIotNode\('🌡'/g, "sapIotNode('[S]'");
html = html.replace(/sapIotNode\('📡'/g, "sapIotNode('[GW]'");
html = html.replace(/sapIotNode\('🏗'/g, "sapIotNode('[DT]'");
html = html.replace(/sapIotNode\('⚡'/g, "sapIotNode('[BTP]'");
html = html.replace(/sapIotNode\('🔧'/g, "sapIotNode('[PM]'");

// SAP buttons
html = html.replace(/📋 Ver en SAP PM/g, 'Ver en SAP PM');
html = html.replace(/🖨 Imprimir/g, 'Imprimir');
html = html.replace(/✏️ Modificar/g, 'Modificar');
html = html.replace(/🏠 Launchpad/g, 'Launchpad');
html = html.replace(/🔗 Abrir orden en SAP PM/g, 'Abrir orden en SAP PM');

// Tandem tree emojis
html = html.replace(/<span class="tn-icon">🏠<\/span>/g, '<span class="tn-icon" style="font-size:10px;color:var(--gr)">[C]</span>');
html = html.replace(/<span class="tn-icon">🔬<\/span>/g, '<span class="tn-icon" style="font-size:10px;color:var(--cy)">[I]</span>');
html = html.replace(/<span class="tn-icon">⚙️<\/span>/g, '<span class="tn-icon" style="font-size:10px;color:var(--or)">[P]</span>');
html = html.replace(/<span class="tn-icon">💧<\/span>/g, '<span class="tn-icon" style="font-size:10px;color:var(--cy)">[A]</span>');
html = html.replace(/<span class="tn-icon">🌀<\/span>/g, '<span class="tn-icon" style="font-size:10px;color:var(--re)">[V]</span>');
html = html.replace(/<span class="tn-icon">🌡<\/span>/g, '<span class="tn-icon" style="font-size:10px;color:var(--cy)">[E]</span>');
html = html.replace(/<span class="tn-icon">🥚<\/span>/g, '<span class="tn-icon" style="font-size:10px;color:var(--ye)">[S]</span>');
html = html.replace(/<span class="tn-icon">⛽<\/span>/g, '<span class="tn-icon" style="font-size:10px;color:var(--cy)">[B]</span>');
html = html.replace(/<span class="tn-badge">⚡<\/span>/g, '<span class="tn-badge">ALT</span>');

// WhatsApp/Telegram icons
html = html.replace(/<div class="wa-avatar">👨‍🌾<\/div>/g, '<div class="wa-avatar" style="font-size:14px;font-weight:800">JR</div>');
html = html.replace(/<div class="tg-avatar">🤖<\/div>/g, '<div class="tg-avatar" style="font-size:12px;font-weight:800">BOT</div>');

// Notif tabs
html = html.replace(/📱 WhatsApp/g, 'WhatsApp');
html = html.replace(/✈️ Telegram/g, 'Telegram');
html = html.replace(/📧 Email/g, 'Email');

// Notification buttons
html = html.replace(/📲 Abrir WhatsApp/g, 'Abrir WhatsApp');
html = html.replace(/📲 Enviar alerta por Telegram/g, 'Enviar alerta por Telegram');
html = html.replace(/📧 Enviar email/g, 'Enviar email');
html = html.replace(/📲 Notificar WA\/TG/g, 'Notificar WA/TG');

// Alert center icons inside ALERT_TYPES
html = html.replace(/icon:'🌀'/g, "icon:'[VIB]'");
html = html.replace(/icon:'💀'/g, "icon:'[MORT]'");
html = html.replace(/icon:'🌡'/g, "icon:'[TEMP]'");
html = html.replace(/icon:'☁️'/g, "icon:'[NH3]'");
html = html.replace(/icon:'🌽'/g, "icon:'[SILO]'");
html = html.replace(/icon:'💧'/g, "icon:'[H2O]'");

// Sim toggle button text
html = html.replace(/⏸ Pausar/g, '|| Pausar');
html = html.replace(/▶ Continuar/g, '> Continuar');

// Alert toggle button replacements in JS
html = html.replace(/textContent='✓ RESOLVER ALERTA'/g, "textContent='RESOLVER ALERTA'");
html = html.replace(/textContent='⚡ ACTIVAR ALERTA'/g, "textContent='ACTIVAR ALERTA'");
html = html.replace(/textContent='🔔 '\+G_ALERTS\.length/g, "textContent='['+G_ALERTS.length");
// Fix the alert badge format
html = html.replace(/'🔔 '\+G_ALERTS\.length\+' ALERTA\(S\)'/g, "'['+G_ALERTS.length+'] ALERTA(S)'");

// System badge text
html = html.replace(/'⚡ ALERTA PP-04'/g, "'ALERTA PP-04'");

// CCTV alert text
html = html.replace(/'⚡ ALERTA — VNT-PP-04/g, "'ALERTA — VNT-PP-04");

// SAP order detail
html = html.replace(/'⚡ Orden abierta/g, "'Orden abierta");
html = html.replace(/⚡ Alta/g, 'Alta');
html = html.replace(/'⚡ Alerta PP-04'/g, "'Alerta PP-04'");

// Maintenance story nodes
html = html.replace(/icon:'🌡',title:'Sensor IoT'/g, "icon:'[S]',title:'Sensor IoT'");
html = html.replace(/icon:'📡',title:'Gateway 4G'/g, "icon:'[GW]',title:'Gateway 4G'");
html = html.replace(/icon:'🏗',title:'Autodesk Tandem'/g, "icon:'[DT]',title:'Autodesk Tandem'");
html = html.replace(/icon:'⚡',title:'SAP BTP IS'/g, "icon:'[BTP]',title:'SAP BTP IS'");
html = html.replace(/icon:'👷',title:'Técnico'/g, "icon:'[TEC]',title:'Tecnico'");

// Impact section emojis
html = html.replace(/📉/g, '[--]');
html = html.replace(/🌡/g, '[T]');
html = html.replace(/💧/g, '[A]');
html = html.replace(/💀/g, '[X]');
html = html.replace(/💸/g, '[$]');
html = html.replace(/✅/g, '[OK]');
html = html.replace(/🔔/g, '[!]');
html = html.replace(/📋/g, '[DOC]');
html = html.replace(/📦/g, '[MAT]');
html = html.replace(/💰/g, '[$]');

// Remaining emojis in JS strings
html = html.replace(/📱/g, '[MOB]');
html = html.replace(/📲/g, '[NOT]');

// Cloud icon in Tandem viewer
html = html.replace(/ctx\.fillText\('☁'/g, "ctx.fillText('C'");

// Hamburger menu is OK (it's a text char ☰)

// ============================================================
// 2. REMOVE "BACHOCO" references
// ============================================================
html = html.replace(/bachoco/gi, function(match) {
  // Preserve the reference in openMobileApp only if it's the filename
  if (match.toLowerCase() === 'bachoco') return 'avicola';
  return match;
});
// Fix the mobile app link specifically
html = html.replace("window.open('avicola-mobile.html", "window.open('avicola-mobile.html");

// ============================================================
// 3. REMOVE FEED PROCESSING PLANT SECTION
// ============================================================

// Remove hammer mill, mixer, pelletizer from PLT-ALM building mk array
html = html.replace(
  "mk:['hammer','mixer','pelletizer']",
  "mk:[]"
);

// Remove hammer, mixer, pelletizer from MACHINE_QR_DB
html = html.replace(/  hammer:\{id:'MOL-PLT-01'[\s\S]*?sap_id:'MOL-PLT-01',tandem_id:'SON03-MOL-PLT01'\},\n/, '');
html = html.replace(/  mixer:\{id:'MIX-PLT-01'[\s\S]*?sap_id:'MIX-PLT-01',tandem_id:'SON03-MIX-PLT01'\},\n/, '');
html = html.replace(/  pelletizer:\{id:'PEL-PLT-01'[\s\S]*?sap_id:'PEL-PLT-01',tandem_id:'SON03-PEL-PLT01'\},\n/, '');

// Remove hammer, mixer, pelletizer from M constant
html = html.replace(/hammer:\{name:'Molino Martillos CPM Champion HM44'[\s\S]*?cam:'planta'\},\n/, '');
html = html.replace(/mixer:\{name:'Mezcladora Horizontal Beta-Raven 4t'[\s\S]*?cam:'planta'\},\n/, '');
html = html.replace(/pelletizer:\{name:'Pelletizadora CPM 7700 Series'[\s\S]*?cam:'planta'\},\n/, '');

// Replace the buildPlanta function to remove hammer mill, mixer, pelletizer, conveyors
// Keep only grain reception hopper, bucket elevator, dosing hoppers, cooler, and electrical
html = html.replace(
  /function buildPlanta\(b,cx,cz,fy\)\{[\s\S]*?ic2\.rotation\.z=Math\.PI\/2;ic2\.position\.set\(cx,fy\+b\.h\*\.9,cz\);scene\.add\(ic2\);\n\}/,
  `function buildPlanta(b,cx,cz,fy){
  fy=.54;
  var stM=new THREE.MeshStandardMaterial({color:0x666666,roughness:.38,metalness:.76});
  var dkM=new THREE.MeshStandardMaterial({color:0x282828,roughness:.58,metalness:.7});

  // === GRAIN RECEPTION HOPPER ===
  var recX=b.x+1.5;
  var recHopM=new THREE.MeshStandardMaterial({color:0x706820,roughness:.4,metalness:.5});
  var recHop=new THREE.Mesh(new THREE.CylinderGeometry(.8,.2,1.2,8,1,true),recHopM);recHop.position.set(recX,fy+1.2,cz-b.d*.3);scene.add(recHop);
  var recRim=new THREE.Mesh(new THREE.TorusGeometry(.8,.06,4,10),recHopM);recRim.rotation.x=Math.PI/2;recRim.position.set(recX,fy+1.8,cz-b.d*.3);scene.add(recRim);
  var rampM=new THREE.MeshStandardMaterial({color:0x808070,metalness:.6,roughness:.4});
  var ramp=new THREE.Mesh(new THREE.BoxGeometry(2,.06,.8),rampM);ramp.position.set(recX-1.2,fy+.9,cz-b.d*.3);ramp.rotation.z=.3;scene.add(ramp);

  // === BUCKET ELEVATOR ===
  var elevX=b.x+3.5;
  var elevBody=new THREE.Mesh(new THREE.BoxGeometry(.6,b.h-.5,.6),stM);elevBody.position.set(elevX,fy+(b.h-.5)/2+.25,cz-b.d*.28);elevBody.castShadow=true;scene.add(elevBody);
  var elevH=new THREE.Mesh(new THREE.BoxGeometry(.85,.65,.85),dkM);elevH.position.set(elevX,fy+b.h-.15,cz-b.d*.28);scene.add(elevH);
  var bktM=new THREE.MeshStandardMaterial({color:0xD4A820,roughness:.48,metalness:.34});
  for(var ci3=0;ci3<6;ci3++){var bkt=new THREE.Mesh(new THREE.BoxGeometry(.25,.16,.28),bktM);bkt.position.set(elevX+.42,fy+.6+ci3*.85,cz-b.d*.28);scene.add(bkt);}

  // === DOSING HOPPERS (5 ingredients) ===
  var dsx=b.x+6;
  var hopCols=[0x5540A0,0x4060B0,0x40A040,0xC0A020,0xA04040];
  for(var di=0;di<5;di++){
    var dx=dsx+di*1.3;
    var dhM=new THREE.MeshStandardMaterial({color:hopCols[di],roughness:.4,metalness:.5});
    var dhop=new THREE.Mesh(new THREE.CylinderGeometry(.4,.1,.7,8,1,true),dhM);dhop.position.set(dx,fy+1.2,cz);scene.add(dhop);
    var dcap=new THREE.Mesh(new THREE.CylinderGeometry(.4,.4,.07,8),new THREE.MeshStandardMaterial({color:0x484848,metalness:.6}));dcap.position.set(dx,fy+1.56,cz);scene.add(dcap);
    var dleg=new THREE.Mesh(new THREE.CylinderGeometry(.03,.03,.6,6),stM);dleg.position.set(dx,fy+.48,cz);scene.add(dleg);
  }

  // === COOLER ===
  var coolX=b.x+b.w-2;
  var coolM=new THREE.MeshStandardMaterial({color:0x7090A0,roughness:.4,metalness:.5});
  var cooler=new THREE.Mesh(new THREE.BoxGeometry(1.4,2.0,1.2),coolM);cooler.position.set(coolX,fy+1.0,cz-b.d*.15);scene.add(cooler);
  var cFan=new THREE.Mesh(new THREE.TorusGeometry(.35,.04,6,12),new THREE.MeshStandardMaterial({color:0x606058,metalness:.6}));
  cFan.rotation.y=Math.PI/2;cFan.position.set(coolX+.72,fy+1.2,cz-b.d*.15);scene.add(cFan);

  // === ELECTRICAL & PNEUMATIC ===
  var cPipe=new THREE.Mesh(new THREE.CylinderGeometry(.08,.08,b.w*.72,8),stM);cPipe.rotation.z=Math.PI/2;cPipe.position.set(cx,fy+b.h*.85,cz);scene.add(cPipe);
  var ic2=new THREE.Mesh(new THREE.CylinderGeometry(.04,.04,b.w*.88,8),new THREE.MeshStandardMaterial({color:0xFF5500,roughness:.4,metalness:.7,emissive:new THREE.Color(0xFF4000),emissiveIntensity:.3}));
  ic2.rotation.z=Math.PI/2;ic2.position.set(cx,fy+b.h*.9,cz);scene.add(ic2);
}`
);

// ============================================================
// 4. MODIFY FLOWS — Feed goes directly from silos to casetas
// ============================================================
// Replace the FLOWS array
html = html.replace(
  /var FLOWS=\[[\s\S]*?\];(\nfunction buildFlows)/,
  `var FLOWS=[
  {from:'PP-01',to:'INC-01',col:0xE8C030,n:9,sp:.034,type:'egg'},{from:'PP-02',to:'INC-01',col:0xE8C030,n:9,sp:.032,type:'egg'},{from:'PP-03',to:'INC-01',col:0xE8C030,n:9,sp:.033,type:'egg'},{from:'PP-04',to:'INC-01',col:0xE8C030,n:7,sp:.035,type:'egg'},{from:'PP-05',to:'INC-01',col:0xE8C030,n:7,sp:.031,type:'egg'},
  {from:'SIL-01',to:'PP-01',col:0xFF9030,n:4,sp:.038,type:'feed'},{from:'SIL-01',to:'PP-02',col:0xFF9030,n:3,sp:.037,type:'feed'},{from:'SIL-01',to:'PP-03',col:0xFF9030,n:3,sp:.036,type:'feed'},
  {from:'SIL-02',to:'PP-04',col:0xFF9030,n:4,sp:.039,type:'feed'},{from:'SIL-02',to:'PP-05',col:0xFF9030,n:3,sp:.037,type:'feed'},{from:'SIL-01',to:'CP-01',col:0xFF9030,n:3,sp:.040,type:'feed'},
  {from:'AGU-01',to:'PP-01',col:0x2090E0,n:4,sp:.056,type:'water'},{from:'AGU-01',to:'PP-02',col:0x2090E0,n:4,sp:.054,type:'water'},{from:'AGU-01',to:'PP-03',col:0x2090E0,n:4,sp:.052,type:'water'},{from:'AGU-01',to:'PP-04',col:0x2090E0,n:4,sp:.055,type:'water'},{from:'AGU-01',to:'INC-01',col:0x2090E0,n:3,sp:.058,type:'water'},
  {from:'INC-01',to:'CP-01',col:0x14CC50,n:4,sp:.026,type:'chick'},
];$1`
);

// Also fix the buildPipes function to route feed from silos directly to houses
html = html.replace(
  /\/\/ Feed from PLT-ALM to houses\n  var pltCx=32\+7,pltCz=-18\+5;\n  BLDS\.forEach\(function\(b\)\{\n    if\(!b\.id\.startsWith\('PP'\)&&!b\.id\.startsWith\('CP'\)\)return;\n    var bcx=b\.x\+b\.w\/2,bcz=b\.z\+b\.d\/2;\n    buildPipeLine\(pltCx,2\.2,pltCz,bcx,2\.2,bcz,feedPipeM,supportM,\.055\);\n  \}\);/,
  `// Feed from Silos directly to houses
  var sil1Cx=16+2.5,sil1Cz=-22+2.5;
  var sil2Cx=23+2.5,sil2Cz=-22+2.5;
  BLDS.forEach(function(b){
    if(!b.id.startsWith('PP')&&!b.id.startsWith('CP'))return;
    var bcx=b.x+b.w/2,bcz=b.z+b.d/2;
    var silCx=(b.id==='PP-04'||b.id==='PP-05')?sil2Cx:sil1Cx;
    var silCz=(b.id==='PP-04'||b.id==='PP-05')?sil2Cz:sil1Cz;
    buildPipeLine(silCx,2.2,silCz,bcx,2.2,bcz,feedPipeM,supportM,.055);
  });`
);

// Fix flow legend
html = html.replace(
  'Alimento: Silo → Planta → Caseta',
  'Alimento: Silo → Caseta'
);

// Fix the label in the flow particle for feed type
html = html.replace(
  "feed:'Alimento caseta'",
  "feed:'Alimento directo'"
);
html = html.replace(
  "grain:'Grano a molino'",
  "grain:'Grano'"
);

// ============================================================
// 5. UPDATE TITLE AND REFERENCES
// ============================================================
html = html.replace(
  '<title>Digital Twin DEMO — Sector Avícola · EY CREAS</title>',
  '<title>Digital Twin DEMO — Sector Avicola v2 · EY CREAS</title>'
);

html = html.replace(
  'Digital Twin — Demo Sector Avícola',
  'Digital Twin — Demo Sector Avicola v2'
);

html = html.replace(
  'CREAS · Demo Avícola · SAP · IoT Activo',
  'CREAS · Avicola · SAP · IoT Activo'
);

// ============================================================
// 6. ADD URL PARAMETER-BASED FARM TYPE ADAPTATION
// ============================================================
// Insert after the G state definition, before the ts() function
const farmTypeAdaptation = `
// ═══════════════════════════════════════════════════
// FARM TYPE ADAPTATION (URL parameter ?type=XXX)
// ═══════════════════════════════════════════════════
var FARM_TYPE=(function(){var p=new URLSearchParams(window.location.search);return p.get('type')||'default';})();
var FARM_CONFIGS={
  progenitora:{title:'Granja Progenitora',sub:'Crianza + Postura Progenitora',kpis:['encasetado','mortalidad','huevo_incubable','huevo_impropio','huevo_roto','huevo_sucio','consumo_alimento','agua','gas','bioseguridad','salud_animal'],showBuildings:['CP-01','CP-02','PP-01','PP-02','PP-03','PP-04','PP-05','INC-01','SIL-01','SIL-02','PLT-ALM','ALM-INS','AGU-01','BIO']},
  reproductora:{title:'Granja Reproductora',sub:'Postura Reproductora — Huevo Incubable',kpis:['encasetado','mortalidad','produccion_huevo','consumo_alimento','agua','gas','bioseguridad','salud_animal'],showBuildings:['PP-01','PP-02','PP-03','PP-04','PP-05','INC-01','SIL-01','SIL-02','AGU-01','BIO']},
  engorde:{title:'Granja de Engorde',sub:'Engorde de Pollo — Peso, Conversion, Mortalidad',kpis:['peso_promedio','ganancia_diaria','conversion_alimenticia','mortalidad','temperatura','ventilacion','consumo_alimento','agua'],showBuildings:['CP-01','CP-02','SIL-01','SIL-02','AGU-01','BIO']},
  ligera:{title:'Linea Ligera',sub:'Produccion Huevo para Mesa',kpis:['produccion_huevo','mortalidad','consumo_alimento','agua','peso_huevo','calidad_cascaron'],showBuildings:['PP-01','PP-02','PP-03','PP-04','PP-05','SIL-01','SIL-02','AGU-01','BIO']},
  comercial:{title:'Postura Comercial',sub:'Produccion Huevo Comercial — Alto Volumen',kpis:['produccion_huevo','clasificacion_huevo','cdh_distribucion','mortalidad','consumo_alimento','agua'],showBuildings:['PP-01','PP-02','PP-03','PP-04','PP-05','SIL-01','SIL-02','AGU-01','BIO']},
  porcinos:{title:'Granja Porcinos',sub:'Reproduccion, Gestacion, Destete, Engorda',kpis:['cerdas_gestacion','lechones_nacidos','peso_destete','mortalidad_lactancia','conversion_engorda','temperatura'],showBuildings:['CP-01','CP-02','PP-01','PP-02','SIL-01','SIL-02','AGU-01','BIO']},
  default:{title:'Sector Avicola',sub:'Vista General',kpis:['postura','mortalidad','huevo_incubable','consumo_alimento','agua','temperatura'],showBuildings:null}
};
var activeFarmCfg=FARM_CONFIGS[FARM_TYPE]||FARM_CONFIGS['default'];

// Apply farm type to topbar
(function(){
  var el=document.querySelector('.tb-title');
  if(el&&FARM_TYPE!=='default')el.textContent='Digital Twin — '+activeFarmCfg.title;
  var sub=document.querySelector('.tb-sub');
  if(sub&&FARM_TYPE!=='default')sub.textContent='CREAS · '+activeFarmCfg.sub+' · SAP · IoT';
})();

`;

html = html.replace(
  "function ts(){",
  farmTypeAdaptation + "function ts(){"
);

// ============================================================
// 7. ADD ACTIVITY PANELS
// ============================================================
// Insert activity panel content into the dashboard builder
const activityPanelsHtml = `
  // Activity panels for farm operations
  var activityHTML='<div class="sec">GESTION DE LABORES</div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Encasetado</div><div class="ps-desc">Control de ingreso y distribucion de aves por caseta</div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Mortalidad</div><div class="ps-desc">Registro diario de bajas por caseta y causa</div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Control Alimento por Parvada</div><div class="ps-desc">Consumo por edad y cantidad, ajuste de racion</div></div></div>'+
    '<div class="sec">MANTENIMIENTO DE GRANJAS</div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Fin de Parvada</div><div class="ps-desc">Limpieza, desinfeccion y preparacion de casetas</div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Correctivos</div><div class="ps-desc">Ordenes de mantenimiento correctivo en curso</div></div></div>'+
    '<div class="sec">ALIMENTACION</div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Entrada de Alimento</div><div class="ps-desc">Recepcion y registro de alimento en silos</div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Consumo por Edad</div><div class="ps-desc">Trazabilidad de consumo por parvada y semana</div></div></div>'+
    '<div class="sec">BIOSEGURIDAD</div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Auditorias</div><div class="ps-desc">Auditorias periodicas de bioseguridad</div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Ambientes Controlados</div><div class="ps-desc">Monitoreo de condiciones ambientales</div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Permisos de Visita</div><div class="ps-desc">Control de acceso y bitacora de visitantes</div></div></div>'+
    '<div class="sec">SALUD ANIMAL</div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Bitacoras de Salud</div><div class="ps-desc">Registro de salud por parvada</div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Vacunacion</div><div class="ps-desc">Programa y registro de vacunas aplicadas</div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Calidad de Parvada</div><div class="ps-desc">Indicadores de calidad y mortalidad mensual</div></div></div>';
`;

// Add activity panels at end of buildDashboard
html = html.replace(
  "mkard('94.8%','PDI PELLET','ok','↑ vs 90%','up')+'</div>';",
  "mkard('94.8%','PDI PELLET','ok','vs 90%','up')+'</div>';\n" + activityPanelsHtml + "\n  return p + activityHTML;"
);
// Fix the return - the original function builds up the string and returns it
// We need to capture the original return value. Let's adjust the approach.
// Actually the function returns the string directly. Let me fix the approach.

// Revert and do it properly - wrap the return
html = html.replace(
  "return p + activityHTML;",
  "" // Remove this incorrect line
);

// Instead, add activity panels as a separate section that appends to the dashboard
// The buildDashboard function returns a string. We need to append to it.
// Let's add a left tab 4 for Activities
html = html.replace(
  `<div class="stab" id="lt3" onclick="setLTab(3)"><span class="stab-icon">I</span>IoT</div>`,
  `<div class="stab" id="lt3" onclick="setLTab(3)"><span class="stab-icon">I</span>IoT</div>
      <div class="stab" id="lt4" onclick="setLTab(4)"><span class="stab-icon">O</span>OPER</div>`
);

html = html.replace(
  `<!-- IoT panel -->
    <div class="spanel" id="lp3"></div>`,
  `<!-- IoT panel -->
    <div class="spanel" id="lp3"></div>
    <!-- Operations/Activity panel -->
    <div class="spanel" id="lp4"></div>`
);

// Update setLTab to handle 5 tabs
html = html.replace(
  "function setLTab(t){\n  G.ltab=t;\n  for(var i=0;i<4;i++){",
  "function setLTab(t){\n  G.ltab=t;\n  for(var i=0;i<5;i){"
);
// Fix the loop - we need proper increment
html = html.replace(
  "for(var i=0;i<5;i){",
  "for(var i=0;i<5;i++){"
);

// Update renderLeftPanel to handle tab 4
html = html.replace(
  "else if(G.ltab===3)panel.innerHTML=buildIoTPanel();",
  "else if(G.ltab===3)panel.innerHTML=buildIoTPanel();\n  else if(G.ltab===4)panel.innerHTML=buildActivityPanel();"
);

// Add the buildActivityPanel function after buildIoTPanel
const activityPanelFn = `
function buildActivityPanel(){
  return '<div class="sec" style="margin-top:4px">GESTION DE LABORES</div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Encasetado</div><div class="ps-desc">Control de ingreso y distribucion de aves por caseta. Registro de lote, cantidad, origen.</div><div class="ps-badges"><span class="ps-b sap">SAP PP</span><span class="ps-b iot">IoT Auto</span></div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Mortalidad Diaria</div><div class="ps-desc">Registro de bajas por caseta y causa. Calculo automatico de % mortalidad acumulada.</div><div class="ps-badges"><span class="ps-b sap">SAP FI-AA</span><span class="ps-b tandem">Tandem DT</span></div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Control Alimento por Parvada</div><div class="ps-desc">Consumo por edad, cantidad y formula. Ajuste de racion vs curva Cobb500.</div><div class="ps-badges"><span class="ps-b sap">SAP MM</span><span class="ps-b sap">SAP PP</span></div></div></div>'+
    '<div class="sec">MANTENIMIENTO DE GRANJAS</div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Fin de Parvada</div><div class="ps-desc">Proceso completo: desalojo, limpieza profunda, desinfeccion, flameo, encalado, descanso sanitario.</div><div class="ps-badges"><span class="ps-b sap">SAP PM</span></div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Mantenimiento Correctivo</div><div class="ps-desc">Ordenes PM generadas automaticamente por IoT o reportadas por tecnico en campo.</div><div class="ps-badges"><span class="ps-b sap">SAP PM</span><span class="ps-b iot">IoT Auto</span></div></div></div>'+
    '<div class="sec">ALIMENTACION</div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Entrada y Recepcion</div><div class="ps-desc">Registro de alimento recibido en silos. Verificacion de calidad y peso.</div><div class="ps-badges"><span class="ps-b sap">SAP MM</span></div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Consumo por Edad y Cantidad</div><div class="ps-desc">Trazabilidad completa de consumo por parvada, semana de edad y formula aplicada.</div><div class="ps-badges"><span class="ps-b sap">SAP PP</span><span class="ps-b iot">Sensor Silo</span></div></div></div>'+
    '<div class="sec">BIOSEGURIDAD</div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Auditorias de Bioseguridad</div><div class="ps-desc">Auditorias periodicas con checklist digital. Evaluacion de cumplimiento por zona.</div><div class="ps-badges"><span class="ps-b sap">SAP QM</span></div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Ambientes Controlados</div><div class="ps-desc">Monitoreo continuo de temperatura, humedad, CO2, NH3 por sensores IoT.</div><div class="ps-badges"><span class="ps-b iot">Vaisala</span><span class="ps-b tandem">Tandem</span></div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Permisos de Visita y Bitacora</div><div class="ps-desc">Control de acceso, registro de visitantes, fumigacion de vehiculos.</div><div class="ps-badges"><span class="ps-b sap">SAP RE-FX</span></div></div></div>'+
    '<div class="sec">TECNICO DE SALUD ANIMAL</div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Bitacoras de Salud</div><div class="ps-desc">Registro por parvada de estado sanitario, signos clinicos, tratamientos.</div><div class="ps-badges"><span class="ps-b sap">SAP PP</span></div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Programa de Vacunacion</div><div class="ps-desc">Calendario de vacunas por parvada. Registro de lotes y trazabilidad completa.</div><div class="ps-badges"><span class="ps-b sap">SAP MM</span><span class="ps-b sap">SAP QM</span></div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Calidad de Parvada</div><div class="ps-desc">Indicadores de calidad, uniformidad, mortalidad mensual acumulada.</div><div class="ps-badges"><span class="ps-b sap">SAP PP</span><span class="ps-b tandem">Tandem DT</span></div></div></div>'+
    '<div class="pstep"><div class="ps-body"><div class="ps-title">Mortalidad Mensual</div><div class="ps-desc">Reporte consolidado de mortalidad por caseta, causa y tendencia.</div><div class="ps-badges"><span class="ps-b sap">SAP CO</span></div></div></div>';
}
`;

html = html.replace(
  "function buildIoTPanel(){",
  activityPanelFn + "\nfunction buildIoTPanel(){"
);

// ============================================================
// 8. ADD BACK NAVIGATION BUTTON
// ============================================================
// Add a "Back to Hub" button in the topbar
html = html.replace(
  '<button class="mobile-menu-btn" onclick="toggleLeftDrawer()">',
  '<a href="avicola-hub.html" class="ta-btn" style="margin-right:6px;text-decoration:none;display:flex;align-items:center;gap:4px;padding:5px 12px;background:rgba(255,85,0,.08);border:1px solid rgba(255,85,0,.25);color:var(--or);border-radius:5px;font-size:11px;font-weight:700;font-family:Barlow,sans-serif;white-space:nowrap;">&larr; Hub</a><button class="mobile-menu-btn" onclick="toggleLeftDrawer()">'
);

// ============================================================
// 9. REMOVE REMAINING STRAY EMOJIS - comprehensive sweep
// ============================================================

// Fix the PLT-ALM sensor label - was referencing the plant
html = html.replace(
  "{x:32+7,y:6.5+4,z:-18+5,label:'[P] 18.4t/h",
  "{x:32+7,y:6.5+4,z:-18+5,label:'PLT 18.4t/h"
);

// Fix some emojis in notification/alert templates that use at.icon
// These are dynamic and already replaced via the icon property changes above

// Fix the SAP system prompt in chat
html = html.replace(
  'Granja Progenitora SON-03 de Demo Avícola',
  'Granja Progenitora SON-03 de Grupo Avicola'
);

// Fix remaining Bachoco references in mobile link
html = html.replace('avicola-mobile.html', 'avicola-mobile.html');

// Fix the '☰' hamburger - this is fine, it's a standard UI char

// Remove activity panel HTML that was injected incorrectly
html = html.replace(activityPanelsHtml, '');

// ============================================================
// 10. FIX PLT-ALM CCTV reference - it referenced molino
// ============================================================
html = html.replace(
  "planta:{id:'CAM-PLT-01',area:'PLT-ALM — Molino + Mezcladora'",
  "planta:{id:'CAM-PLT-01',area:'PLT-ALM — Almacen Alimento'"
);

// ============================================================
// 11. Clean up remaining emojis in stream/status messages
// ============================================================
// These are in JavaScript string templates and function calls
html = html.replace(/1️⃣/g, '1.');
html = html.replace(/2️⃣/g, '2.');
html = html.replace(/3️⃣/g, '3.');
html = html.replace(/4️⃣/g, '4.');

// Fix some remaining references in addS calls
html = html.replace(/'[DOC] Ronda '/g, "'Ronda '");

// Fix remaining stray emojis that are used in CCTV alert text within renderCCTV
html = html.replace(
  "ctx.fillText('[BTP] ALERTA — VNT-PP-04",
  "ctx.fillText('ALERTA — VNT-PP-04"
);

// ============================================================
// FINAL: Write the transformed file
// ============================================================
fs.writeFileSync(path, html, 'utf-8');
console.log('Transformation complete. File size:', html.length, 'chars');
console.log('Line count:', html.split('\n').length);
