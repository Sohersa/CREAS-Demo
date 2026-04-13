"""
Router de control presupuestal de obra.
Dashboard SPA (HTMLResponse) + API endpoints para CRUD de presupuestos y partidas.
Design system: Navy #0F1B2D, Orange #E67E22, Blue #2E86C1, Green #27AE60, Inter font.
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.presupuesto import PresupuestoObra, PartidaPresupuesto
from app.models.usuario import Usuario
from app.models.catalogo import CatalogoMaestro
from app.services.presupuesto_service import (
    crear_presupuesto,
    registrar_consumo,
    verificar_disponibilidad,
    obtener_resumen_presupuesto,
    obtener_presupuestos_usuario,
    agregar_partida,
    actualizar_partida,
    eliminar_partida,
    desbloquear_partida,
)

router = APIRouter(prefix="/presupuesto", tags=["presupuesto"])


# --- Pydantic models --------------------------------------------------------

class CrearPresupuestoRequest(BaseModel):
    usuario_id: int
    nombre_obra: str
    direccion: str = ""
    fecha_inicio: str = ""
    fecha_fin_estimada: str = ""
    partidas: list[dict] = []


class PartidaRequest(BaseModel):
    nombre_material: str
    cantidad_presupuestada: float
    precio_unitario_estimado: float
    categoria: str = ""
    unidad: str = ""
    catalogo_id: int = None


class UpdatePartidaRequest(BaseModel):
    nombre_material: str = None
    cantidad_presupuestada: float = None
    precio_unitario_estimado: float = None
    categoria: str = None
    unidad: str = None
    catalogo_id: int = None


class ConsumoRequest(BaseModel):
    partida_id: int = None
    catalogo_id: int = None
    cantidad: float = 0
    monto: float = 0


class LoginPresupuestoRequest(BaseModel):
    telefono: str
    nombre: str = ""


# --- API: Login -------------------------------------------------------------

@router.post("/api/login")
def api_login(body: LoginPresupuestoRequest, db: Session = Depends(get_db)):
    telefono = body.telefono.strip().replace(" ", "")
    usuario = db.query(Usuario).filter(Usuario.telefono == telefono).first()
    if not usuario:
        nombre = body.nombre.strip() if body.nombre else "Cliente"
        usuario = Usuario(
            telefono=telefono,
            nombre=nombre,
            tipo="residente",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "telefono": usuario.telefono,
    }


# --- API: List all presupuestos ---------------------------------------------

@router.get("/api/obras")
def api_list_obras(usuario_id: int = Query(...), db: Session = Depends(get_db)):
    return obtener_presupuestos_usuario(db, usuario_id)


# --- API: Create presupuesto ------------------------------------------------

@router.post("/api/obras")
def api_crear_obra(body: CrearPresupuestoRequest, db: Session = Depends(get_db)):
    fecha_inicio = None
    fecha_fin = None
    if body.fecha_inicio:
        try:
            fecha_inicio = datetime.fromisoformat(body.fecha_inicio)
        except ValueError:
            pass
    if body.fecha_fin_estimada:
        try:
            fecha_fin = datetime.fromisoformat(body.fecha_fin_estimada)
        except ValueError:
            pass

    presupuesto = crear_presupuesto(
        db=db,
        usuario_id=body.usuario_id,
        nombre_obra=body.nombre_obra,
        direccion=body.direccion,
        fecha_inicio=fecha_inicio,
        fecha_fin_estimada=fecha_fin,
        partidas=body.partidas,
    )
    return {"ok": True, "id": presupuesto.id, "nombre_obra": presupuesto.nombre_obra}


# --- API: Get presupuesto with partidas -------------------------------------

@router.get("/api/obras/{presupuesto_id}")
def api_get_obra(presupuesto_id: int, db: Session = Depends(get_db)):
    return obtener_resumen_presupuesto(db, presupuesto_id)


# --- API: Add partida -------------------------------------------------------

@router.post("/api/obras/{presupuesto_id}/partidas")
def api_add_partida(presupuesto_id: int, body: PartidaRequest, db: Session = Depends(get_db)):
    partida = agregar_partida(
        db=db,
        presupuesto_id=presupuesto_id,
        nombre_material=body.nombre_material,
        cantidad_presupuestada=body.cantidad_presupuestada,
        precio_unitario_estimado=body.precio_unitario_estimado,
        categoria=body.categoria,
        unidad=body.unidad,
        catalogo_id=body.catalogo_id,
    )
    if not partida:
        return {"error": "Presupuesto no encontrado"}
    return {"ok": True, "partida_id": partida.id}


# --- API: Update consumption ------------------------------------------------

@router.put("/api/partidas/{partida_id}/consumo")
def api_update_consumo(partida_id: int, body: ConsumoRequest, db: Session = Depends(get_db)):
    partida = db.query(PartidaPresupuesto).filter(
        PartidaPresupuesto.id == partida_id
    ).first()
    if not partida:
        return {"error": "Partida no encontrada"}

    presupuesto = db.query(PresupuestoObra).filter(
        PresupuestoObra.id == partida.presupuesto_id
    ).first()
    if not presupuesto:
        return {"error": "Presupuesto no encontrado"}

    if partida.bloqueado:
        return {
            "error": "Partida bloqueada",
            "mensaje": f"La partida de {partida.nombre_material} esta bloqueada por haber alcanzado el 100% del presupuesto.",
        }

    cantidad = body.cantidad
    monto = body.monto

    # If monto not provided, calculate from qty * unit price
    if monto == 0 and cantidad > 0 and partida.precio_unitario_estimado:
        monto = cantidad * partida.precio_unitario_estimado

    partida.cantidad_consumida += cantidad
    partida.monto_gastado += monto

    if partida.cantidad_presupuestada > 0:
        partida.porcentaje_consumido = round(
            (partida.cantidad_consumida / partida.cantidad_presupuestada) * 100, 2
        )

    presupuesto.gastado_total += monto
    if presupuesto.presupuesto_total > 0:
        presupuesto.porcentaje_consumido = round(
            (presupuesto.gastado_total / presupuesto.presupuesto_total) * 100, 2
        )

    # Check thresholds
    pct = partida.porcentaje_consumido
    alerts_triggered = []

    if pct >= 50 and not partida.alerta_50_enviada:
        partida.alerta_50_enviada = True
        alerts_triggered.append("50%")

    if pct >= 80 and not partida.alerta_80_enviada:
        partida.alerta_80_enviada = True
        alerts_triggered.append("80%")

    if pct >= 100 and not partida.alerta_100_enviada:
        partida.alerta_100_enviada = True
        partida.bloqueado = True
        alerts_triggered.append("100% - BLOQUEADA")

    db.commit()
    db.refresh(partida)

    return {
        "ok": True,
        "partida_id": partida.id,
        "nombre_material": partida.nombre_material,
        "cantidad_consumida": partida.cantidad_consumida,
        "porcentaje_consumido": partida.porcentaje_consumido,
        "monto_gastado": partida.monto_gastado,
        "bloqueado": partida.bloqueado,
        "alerts_triggered": alerts_triggered,
    }


# --- API: Get alerts --------------------------------------------------------

@router.get("/api/obras/{presupuesto_id}/alertas")
def api_get_alertas(presupuesto_id: int, db: Session = Depends(get_db)):
    presupuesto = db.query(PresupuestoObra).filter(
        PresupuestoObra.id == presupuesto_id
    ).first()
    if not presupuesto:
        return {"error": "Presupuesto no encontrado"}

    partidas = db.query(PartidaPresupuesto).filter(
        PartidaPresupuesto.presupuesto_id == presupuesto_id
    ).all()

    alertas = []
    for p in partidas:
        pct = p.porcentaje_consumido or 0
        if pct >= 100 or p.bloqueado:
            alertas.append({
                "partida_id": p.id,
                "nombre_material": p.nombre_material,
                "porcentaje": pct,
                "nivel": "bloqueado" if p.bloqueado else "100",
                "mensaje": f"{p.nombre_material}: presupuesto agotado ({pct:.1f}%)",
            })
        elif pct >= 80:
            alertas.append({
                "partida_id": p.id,
                "nombre_material": p.nombre_material,
                "porcentaje": pct,
                "nivel": "80",
                "mensaje": f"{p.nombre_material}: {pct:.1f}% consumido - nivel critico",
            })
        elif pct >= 50:
            alertas.append({
                "partida_id": p.id,
                "nombre_material": p.nombre_material,
                "porcentaje": pct,
                "nivel": "50",
                "mensaje": f"{p.nombre_material}: {pct:.1f}% consumido - atencion",
            })

    return {
        "presupuesto_id": presupuesto_id,
        "nombre_obra": presupuesto.nombre_obra,
        "porcentaje_global": presupuesto.porcentaje_consumido,
        "total_alertas": len(alertas),
        "alertas": alertas,
    }


# --- API: Update partida ----------------------------------------------------

@router.put("/api/partidas/{partida_id}")
def api_update_partida(partida_id: int, body: UpdatePartidaRequest, db: Session = Depends(get_db)):
    datos = {k: v for k, v in body.dict().items() if v is not None}
    partida = actualizar_partida(db, partida_id, datos)
    if not partida:
        return {"error": "Partida no encontrada"}
    return {"ok": True, "partida_id": partida.id}


# --- API: Delete partida ----------------------------------------------------

@router.delete("/api/partidas/{partida_id}")
def api_delete_partida(partida_id: int, db: Session = Depends(get_db)):
    ok = eliminar_partida(db, partida_id)
    if not ok:
        return {"error": "Partida no encontrada"}
    return {"ok": True}


# --- API: Desbloquear partida -----------------------------------------------

@router.post("/api/obras/{presupuesto_id}/desbloquear/{partida_id}")
def api_desbloquear(presupuesto_id: int, partida_id: int, db: Session = Depends(get_db)):
    desbloquear_partida(db, partida_id)
    return {"ok": True, "partida_id": partida_id}


# --- API: Catalogo (for dropdowns) ------------------------------------------

@router.get("/api/catalogo/productos")
def api_catalogo(db: Session = Depends(get_db)):
    productos = db.query(CatalogoMaestro).filter(CatalogoMaestro.activo == True).all()
    return [
        {
            "id": p.id,
            "nombre": p.nombre,
            "categoria": p.categoria,
            "unidad": p.unidad,
            "precio_referencia": p.precio_referencia,
        }
        for p in productos
    ]


# --- HTML SPA Dashboard -----------------------------------------------------

@router.get("/", response_class=HTMLResponse)
def presupuesto_page():
    return PRESUPUESTO_HTML


PRESUPUESTO_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ObraYa - Control Presupuestal</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:#F0F2F5;color:#1E293B;min-height:100vh}

:root{
  --navy:#0F1B2D;
  --navy-light:#162236;
  --navy-mid:#1B2D45;
  --orange:#E67E22;
  --orange-hover:#CF6D17;
  --blue:#2E86C1;
  --blue-light:#EBF5FB;
  --green:#27AE60;
  --green-light:#E8F8EF;
  --red:#E74C3C;
  --red-light:#FDEDEC;
  --yellow:#F39C12;
  --yellow-light:#FEF9E7;
  --gray:#64748B;
  --gray-light:#F8FAFC;
  --border:#E2E8F0;
  --shadow:0 1px 3px rgba(15,27,45,0.08),0 1px 2px rgba(15,27,45,0.06);
  --shadow-md:0 4px 6px rgba(15,27,45,0.07),0 2px 4px rgba(15,27,45,0.06);
  --shadow-lg:0 10px 15px rgba(15,27,45,0.1),0 4px 6px rgba(15,27,45,0.05);
  --radius:10px;
  --radius-lg:14px;
}

/* --- Header --- */
.header{
  background:var(--navy);color:#fff;padding:0 24px;height:60px;
  display:flex;align-items:center;justify-content:space-between;
  position:sticky;top:0;z-index:100;
}
.header-left{display:flex;align-items:center;gap:16px}
.header h1{font-size:18px;font-weight:700;letter-spacing:-0.3px}
.header .subtitle{font-size:12px;color:rgba(255,255,255,0.55);font-weight:400}
.header-right{display:flex;align-items:center;gap:10px}
.user-badge{
  background:rgba(255,255,255,0.1);padding:6px 14px;border-radius:20px;
  font-size:12px;color:rgba(255,255,255,0.85);font-weight:500;
}
.btn-logout{
  background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);
  color:rgba(255,255,255,0.8);padding:6px 14px;border-radius:6px;
  cursor:pointer;font-size:12px;font-family:'Inter',sans-serif;transition:all 0.15s;
}
.btn-logout:hover{background:rgba(255,255,255,0.18)}

/* --- Hamburger --- */
.hamburger{
  display:none;background:none;border:none;cursor:pointer;
  padding:4px;color:#fff;
}
.hamburger svg{width:24px;height:24px}

/* --- Mobile nav overlay --- */
.mobile-nav{
  position:fixed;top:60px;left:0;right:0;bottom:0;
  background:rgba(15,27,45,0.95);z-index:99;display:none;
  flex-direction:column;padding:24px;
}
.mobile-nav.open{display:flex}
.mobile-nav-item{
  color:#fff;padding:16px 0;border-bottom:1px solid rgba(255,255,255,0.1);
  font-size:16px;font-weight:600;cursor:pointer;background:none;
  border-top:none;border-left:none;border-right:none;text-align:left;
  font-family:'Inter',sans-serif;
}
.mobile-nav-item:hover{color:var(--orange)}

/* --- Container --- */
.container{max-width:1140px;margin:0 auto;padding:24px}

/* --- Cards --- */
.card{
  background:#fff;border-radius:var(--radius-lg);box-shadow:var(--shadow);
  padding:24px;margin-bottom:20px;border:1px solid var(--border);
}
.card-header{
  display:flex;justify-content:space-between;align-items:center;
  margin-bottom:16px;
}
.card-title{font-size:15px;font-weight:700;color:var(--navy)}

/* --- Buttons --- */
.btn{
  padding:9px 18px;border:none;border-radius:8px;font-size:13px;font-weight:600;
  cursor:pointer;font-family:'Inter',sans-serif;transition:all 0.15s;
  display:inline-flex;align-items:center;gap:6px;
}
.btn-primary{background:var(--orange);color:#fff}
.btn-primary:hover{background:var(--orange-hover)}
.btn-secondary{background:var(--blue);color:#fff}
.btn-secondary:hover{background:#2472A4}
.btn-success{background:var(--green);color:#fff}
.btn-success:hover{background:#1E8C4D}
.btn-danger{background:var(--red);color:#fff}
.btn-danger:hover{background:#C0392B}
.btn-sm{padding:6px 12px;font-size:11px}
.btn-outline{
  background:transparent;border:1.5px solid var(--border);color:var(--navy);
}
.btn-outline:hover{border-color:var(--navy);background:var(--gray-light)}
.btn-ghost{background:transparent;color:var(--gray);padding:6px 10px}
.btn-ghost:hover{color:var(--navy);background:var(--gray-light)}

/* --- Forms --- */
.form-group{margin-bottom:14px}
.form-group label{
  display:block;font-size:12px;font-weight:600;color:var(--navy);
  margin-bottom:5px;text-transform:uppercase;letter-spacing:0.3px;
}
.form-group input,.form-group select,.form-group textarea{
  width:100%;padding:9px 12px;border:1.5px solid var(--border);border-radius:8px;
  font-size:13px;font-family:'Inter',sans-serif;transition:border-color 0.15s;
  background:#fff;
}
.form-group input:focus,.form-group select:focus{
  outline:none;border-color:var(--blue);box-shadow:0 0 0 3px rgba(46,134,193,0.1);
}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.form-row-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}

/* --- Login --- */
.login-overlay{
  position:fixed;top:0;left:0;right:0;bottom:0;
  background:var(--navy);display:flex;align-items:center;
  justify-content:center;z-index:200;
}
.login-card{
  background:#fff;border-radius:16px;padding:40px;width:400px;
  max-width:92vw;box-shadow:var(--shadow-lg);
}
.login-card h2{text-align:center;color:var(--navy);margin-bottom:6px;font-size:22px}
.login-card p{text-align:center;color:var(--gray);margin-bottom:24px;font-size:13px}
.login-logo{
  width:48px;height:48px;background:var(--orange);border-radius:12px;
  display:flex;align-items:center;justify-content:center;
  margin:0 auto 16px;color:#fff;font-size:20px;font-weight:800;
}

/* --- Progress bars --- */
.progress-wrap{
  background:#E9ECEF;border-radius:20px;height:22px;
  overflow:hidden;position:relative;
}
.progress-bar{
  height:100%;border-radius:20px;transition:width 0.4s ease;
  display:flex;align-items:center;justify-content:flex-end;
  padding-right:8px;font-size:10px;font-weight:700;color:#fff;min-width:36px;
}
.progress-green{background:linear-gradient(90deg,#27AE60,#2ECC71)}
.progress-yellow{background:linear-gradient(90deg,#F39C12,#F1C40F)}
.progress-orange{background:linear-gradient(90deg,#E67E22,#F39C12)}
.progress-red{background:linear-gradient(90deg,#E74C3C,#C0392B)}

/* --- Stat cards --- */
.stat-grid{
  display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px;
}
.stat-card{
  background:#fff;border-radius:var(--radius-lg);box-shadow:var(--shadow);
  padding:20px;border:1px solid var(--border);
}
.stat-value{font-size:26px;font-weight:800;color:var(--navy);line-height:1.1}
.stat-label{font-size:11px;color:var(--gray);margin-top:4px;text-transform:uppercase;letter-spacing:0.4px;font-weight:500}
.stat-accent{color:var(--orange)}
.stat-icon{
  width:36px;height:36px;border-radius:8px;display:flex;align-items:center;
  justify-content:center;margin-bottom:10px;font-size:16px;font-weight:700;
}

/* --- Table --- */
.table-wrap{overflow-x:auto;margin:0 -24px;padding:0 24px}
table{width:100%;border-collapse:separate;border-spacing:0}
th{
  background:var(--navy);color:#fff;padding:10px 14px;text-align:left;
  font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.4px;
}
th:first-child{border-radius:8px 0 0 0}
th:last-child{border-radius:0 8px 0 0}
td{padding:10px 14px;border-bottom:1px solid var(--border);font-size:13px;vertical-align:middle}
tr:hover td{background:var(--gray-light)}

/* --- Badges --- */
.badge{
  display:inline-flex;align-items:center;gap:4px;
  padding:3px 10px;border-radius:20px;font-size:10px;font-weight:700;
  text-transform:uppercase;letter-spacing:0.3px;
}
.badge-ok{background:var(--green-light);color:#1E8C4D}
.badge-warn{background:var(--yellow-light);color:#D68910}
.badge-danger{background:var(--red-light);color:#C0392B}
.badge-blocked{background:var(--navy);color:#fff}

/* --- Budget list items --- */
.budget-item{
  padding:20px;border:1.5px solid var(--border);border-radius:var(--radius-lg);
  cursor:pointer;transition:all 0.15s;margin-bottom:12px;background:#fff;
}
.budget-item:hover{border-color:var(--blue);box-shadow:var(--shadow-md);transform:translateY(-1px)}
.budget-item-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.budget-item-name{font-size:15px;font-weight:700;color:var(--navy)}
.budget-item-pct{font-size:14px;font-weight:800}
.budget-item-meta{font-size:12px;color:var(--gray);margin-bottom:10px;display:flex;gap:12px;flex-wrap:wrap}
.budget-item-footer{display:flex;justify-content:space-between;margin-top:10px;font-size:12px;font-weight:600}

/* --- Tabs --- */
.tabs{
  display:flex;gap:2px;margin-bottom:24px;background:var(--navy);
  border-radius:10px;padding:4px;
}
.tab{
  padding:9px 20px;cursor:pointer;font-size:13px;font-weight:600;
  color:rgba(255,255,255,0.6);border:none;background:transparent;
  border-radius:7px;transition:all 0.15s;font-family:'Inter',sans-serif;
}
.tab.active{color:#fff;background:rgba(255,255,255,0.15)}
.tab:hover{color:#fff}

/* --- Partida row in create form --- */
.partida-row{
  display:grid;grid-template-columns:2.5fr 0.8fr 0.8fr 0.8fr auto;gap:8px;
  align-items:end;margin-bottom:8px;padding:10px;
  background:var(--gray-light);border-radius:8px;border:1px solid var(--border);
}
.partida-row input{
  padding:7px 10px;border:1.5px solid var(--border);border-radius:6px;
  font-size:12px;font-family:'Inter',sans-serif;
}
.partida-row input:focus{outline:none;border-color:var(--blue)}
.btn-remove{
  background:var(--red);color:#fff;border:none;width:30px;height:30px;
  border-radius:6px;cursor:pointer;font-size:14px;display:flex;
  align-items:center;justify-content:center;transition:background 0.15s;
}
.btn-remove:hover{background:#C0392B}

/* --- Slide-in panel --- */
.panel-overlay{
  position:fixed;top:0;left:0;right:0;bottom:0;
  background:rgba(15,27,45,0.4);z-index:300;display:none;
  opacity:0;transition:opacity 0.2s;
}
.panel-overlay.active{display:block;opacity:1}
.slide-panel{
  position:fixed;top:0;right:-480px;width:460px;max-width:100vw;height:100vh;
  background:#fff;z-index:301;transition:right 0.3s ease;
  box-shadow:-4px 0 20px rgba(15,27,45,0.15);
  display:flex;flex-direction:column;
}
.slide-panel.open{right:0}
.panel-header{
  padding:20px 24px;border-bottom:1px solid var(--border);
  display:flex;justify-content:space-between;align-items:center;
  background:var(--navy);color:#fff;flex-shrink:0;
}
.panel-header h3{font-size:16px;font-weight:700}
.panel-close{
  background:rgba(255,255,255,0.1);border:none;color:#fff;width:32px;height:32px;
  border-radius:6px;cursor:pointer;font-size:18px;display:flex;
  align-items:center;justify-content:center;
}
.panel-close:hover{background:rgba(255,255,255,0.2)}
.panel-body{padding:24px;overflow-y:auto;flex:1}
.panel-footer{
  padding:16px 24px;border-top:1px solid var(--border);
  display:flex;justify-content:flex-end;gap:10px;flex-shrink:0;
}

/* --- Alert cards --- */
.alert-card{
  padding:12px 16px;border-radius:8px;margin-bottom:8px;
  display:flex;align-items:center;gap:12px;font-size:13px;font-weight:500;
}
.alert-card-50{background:var(--yellow-light);border-left:4px solid var(--yellow);color:#7D6608}
.alert-card-80{background:#FDEDEC;border-left:4px solid var(--red);color:#922B21}
.alert-card-blocked{background:var(--navy);color:#fff;border-left:4px solid var(--orange)}

/* --- Empty state --- */
.empty-state{text-align:center;padding:60px 20px;color:var(--gray)}
.empty-state h3{font-size:17px;color:var(--navy);margin-bottom:6px}
.empty-state p{font-size:13px;max-width:360px;margin:0 auto}

/* --- Toast notification --- */
.toast{
  position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:10px;
  color:#fff;font-size:13px;font-weight:600;z-index:400;
  transform:translateY(80px);opacity:0;transition:all 0.3s ease;
  font-family:'Inter',sans-serif;
}
.toast.show{transform:translateY(0);opacity:1}
.toast-success{background:var(--green)}
.toast-error{background:var(--red)}
.toast-warn{background:var(--yellow);color:var(--navy)}

/* --- Responsive --- */
@media(max-width:768px){
  .hamburger{display:block}
  .header-right .user-badge,.header-right .btn-logout{display:none}
  .container{padding:16px}
  .stat-grid{grid-template-columns:1fr 1fr}
  .form-row,.form-row-3{grid-template-columns:1fr}
  .partida-row{grid-template-columns:1fr;gap:6px}
  .tabs{flex-wrap:wrap}
  .tab{font-size:12px;padding:8px 14px}
  .slide-panel{width:100vw}
  .budget-item-footer{flex-direction:column;gap:4px}
  th,td{padding:8px 10px;font-size:11px}
}
@media(max-width:480px){
  .stat-grid{grid-template-columns:1fr}
  .header h1{font-size:15px}
}
</style>
</head>
<body>

<!-- LOGIN -->
<div id="loginScreen" class="login-overlay">
  <div class="login-card">
    <div class="login-logo">OY</div>
    <h2>Control Presupuestal</h2>
    <p>Ingresa tu telefono para acceder a tus presupuestos de obra</p>
    <div class="form-group">
      <label>Telefono</label>
      <input type="tel" id="loginTel" placeholder="5213312345678" />
    </div>
    <div class="form-group">
      <label>Nombre (opcional)</label>
      <input type="text" id="loginNombre" placeholder="Tu nombre" />
    </div>
    <button class="btn btn-primary" style="width:100%;justify-content:center;padding:12px" onclick="doLogin()">Ingresar</button>
  </div>
</div>

<!-- MAIN APP -->
<div id="mainApp" style="display:none">

  <!-- Header -->
  <div class="header">
    <div class="header-left">
      <button class="hamburger" onclick="toggleMobileNav()" aria-label="Menu">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="6" x2="21" y2="6"/>
          <line x1="3" y1="12" x2="21" y2="12"/>
          <line x1="3" y1="18" x2="21" y2="18"/>
        </svg>
      </button>
      <div>
        <h1>ObraYa - Control Presupuestal</h1>
        <div class="subtitle" id="headerUser"></div>
      </div>
    </div>
    <div class="header-right">
      <span class="user-badge" id="headerBadge"></span>
      <button class="btn-logout" onclick="doLogout()">Salir</button>
    </div>
  </div>

  <!-- Mobile nav -->
  <div class="mobile-nav" id="mobileNav">
    <button class="mobile-nav-item" onclick="showTab('list');closeMobileNav()">Mis Presupuestos</button>
    <button class="mobile-nav-item" onclick="showTab('new');closeMobileNav()">Nuevo Presupuesto</button>
    <button class="mobile-nav-item" onclick="showTab('alerts');closeMobileNav()">Alertas</button>
    <button class="mobile-nav-item" onclick="doLogout()">Cerrar sesion</button>
  </div>

  <div class="container">
    <!-- Tabs -->
    <div class="tabs">
      <button class="tab active" onclick="showTab('list')" id="tabList">Mis Presupuestos</button>
      <button class="tab" onclick="showTab('detail')" id="tabDetail" style="display:none">Detalle</button>
      <button class="tab" onclick="showTab('new')" id="tabNew">Nuevo Presupuesto</button>
      <button class="tab" onclick="showTab('alerts')" id="tabAlerts">Alertas</button>
    </div>

    <!-- VIEW: Budget list -->
    <div id="viewList">
      <div id="budgetList"></div>
    </div>

    <!-- VIEW: Detail -->
    <div id="viewDetail" style="display:none"></div>

    <!-- VIEW: Alerts -->
    <div id="viewAlerts" style="display:none"></div>

    <!-- VIEW: New budget -->
    <div id="viewNew" style="display:none">
      <div class="card">
        <div class="card-title" style="margin-bottom:20px">Crear Nuevo Presupuesto</div>
        <div class="form-row">
          <div class="form-group">
            <label>Nombre de la Obra</label>
            <input type="text" id="newNombre" placeholder="Ej: Torre Norte, Residencial Los Pinos" />
          </div>
          <div class="form-group">
            <label>Direccion</label>
            <input type="text" id="newDireccion" placeholder="Direccion de la obra" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label>Fecha inicio</label>
            <input type="date" id="newFechaInicio" />
          </div>
          <div class="form-group">
            <label>Fecha fin estimada</label>
            <input type="date" id="newFechaFin" />
          </div>
        </div>

        <div style="margin-top:24px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
          <div class="card-title">Partidas de Material</div>
          <button class="btn btn-sm btn-secondary" onclick="addPartidaRow()">+ Agregar partida</button>
        </div>

        <div style="font-size:11px;color:var(--gray);margin-bottom:8px;display:grid;grid-template-columns:2.5fr 0.8fr 0.8fr 0.8fr auto;gap:8px;padding:0 10px;font-weight:600">
          <span>MATERIAL</span><span>UNIDAD</span><span>CANTIDAD</span><span>PRECIO U.</span><span></span>
        </div>
        <div id="partidasContainer"></div>

        <div style="margin-top:20px;display:flex;align-items:center;justify-content:flex-end;gap:16px">
          <span id="newTotal" style="font-size:15px;font-weight:700;color:var(--navy)">Total: $0.00</span>
          <button class="btn btn-primary" onclick="crearPresupuesto()">Crear Presupuesto</button>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- SLIDE-IN PANEL: Add partida -->
<div class="panel-overlay" id="panelOverlay" onclick="closePanel()"></div>
<div class="slide-panel" id="slidePanel">
  <div class="panel-header">
    <h3 id="panelTitle">Agregar Partida</h3>
    <button class="panel-close" onclick="closePanel()">X</button>
  </div>
  <div class="panel-body">
    <div class="form-group">
      <label>Producto del Catalogo (opcional)</label>
      <select id="panelCatalogo" onchange="fillFromCatalogo()">
        <option value="">-- Seleccionar del catalogo --</option>
      </select>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Material</label>
        <input type="text" id="panelMaterial" placeholder="Ej: Concreto f'c 250" />
      </div>
      <div class="form-group">
        <label>Categoria</label>
        <input type="text" id="panelCategoria" placeholder="concreto, acero..." />
      </div>
    </div>
    <div class="form-row-3">
      <div class="form-group">
        <label>Unidad</label>
        <input type="text" id="panelUnidad" placeholder="m3, kg, pzas" />
      </div>
      <div class="form-group">
        <label>Cantidad</label>
        <input type="number" id="panelCantidad" min="0" step="0.01" />
      </div>
      <div class="form-group">
        <label>Precio Unitario ($)</label>
        <input type="number" id="panelPrecio" min="0" step="0.01" />
      </div>
    </div>
  </div>
  <div class="panel-footer">
    <button class="btn btn-outline" onclick="closePanel()">Cancelar</button>
    <button class="btn btn-primary" id="panelSubmitBtn" onclick="submitPanelPartida()">Agregar</button>
  </div>
</div>

<!-- SLIDE-IN PANEL: Register consumption -->
<div class="panel-overlay" id="consumoOverlay" onclick="closeConsumoPanel()"></div>
<div class="slide-panel" id="consumoPanel">
  <div class="panel-header">
    <h3 id="consumoTitle">Registrar Consumo</h3>
    <button class="panel-close" onclick="closeConsumoPanel()">X</button>
  </div>
  <div class="panel-body">
    <div id="consumoInfo" style="margin-bottom:16px"></div>
    <div class="form-group">
      <label>Cantidad consumida</label>
      <input type="number" id="consumoCantidad" min="0" step="0.01" placeholder="Cantidad usada" />
    </div>
    <div class="form-group">
      <label>Monto gastado ($) (opcional, se calcula automaticamente)</label>
      <input type="number" id="consumoMonto" min="0" step="0.01" placeholder="Se calcula si se deja vacio" />
    </div>
  </div>
  <div class="panel-footer">
    <button class="btn btn-outline" onclick="closeConsumoPanel()">Cancelar</button>
    <button class="btn btn-success" onclick="submitConsumo()">Registrar Consumo</button>
  </div>
</div>

<!-- Toast -->
<div class="toast" id="toast"></div>

<script>
const API = '/presupuesto/api';
let currentUser = null;
let currentBudgetId = null;
let catalogo = [];
let partidaRows = [];
let partidaCounter = 0;
let consumoPartidaId = null;

// --- Toast ---

function showToast(msg, type) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast toast-' + (type || 'success') + ' show';
  setTimeout(function(){ t.classList.remove('show'); }, 3000);
}

// --- Login ---

async function doLogin() {
  const tel = document.getElementById('loginTel').value.trim();
  if (!tel) { showToast('Ingresa tu telefono', 'error'); return; }
  const nombre = document.getElementById('loginNombre').value.trim();
  try {
    const res = await fetch(API + '/login', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({telefono: tel, nombre: nombre})
    });
    const data = await res.json();
    if (data.id) {
      currentUser = data;
      document.getElementById('loginScreen').style.display = 'none';
      document.getElementById('mainApp').style.display = 'block';
      document.getElementById('headerUser').textContent = data.telefono;
      document.getElementById('headerBadge').textContent = data.nombre;
      loadCatalogo();
      loadBudgets();
    }
  } catch(e) { showToast('Error de conexion', 'error'); }
}

function doLogout() {
  currentUser = null;
  currentBudgetId = null;
  document.getElementById('loginScreen').style.display = 'flex';
  document.getElementById('mainApp').style.display = 'none';
  closeMobileNav();
}

// --- Mobile nav ---

function toggleMobileNav() {
  document.getElementById('mobileNav').classList.toggle('open');
}
function closeMobileNav() {
  document.getElementById('mobileNav').classList.remove('open');
}

// --- Tabs ---

function showTab(tab) {
  document.querySelectorAll('.tab').forEach(function(t){ t.classList.remove('active'); });
  document.getElementById('viewList').style.display = tab === 'list' ? 'block' : 'none';
  document.getElementById('viewDetail').style.display = tab === 'detail' ? 'block' : 'none';
  document.getElementById('viewNew').style.display = tab === 'new' ? 'block' : 'none';
  document.getElementById('viewAlerts').style.display = tab === 'alerts' ? 'block' : 'none';
  if (tab === 'list') { document.getElementById('tabList').classList.add('active'); loadBudgets(); }
  if (tab === 'detail') document.getElementById('tabDetail').classList.add('active');
  if (tab === 'new') document.getElementById('tabNew').classList.add('active');
  if (tab === 'alerts') { document.getElementById('tabAlerts').classList.add('active'); loadAllAlerts(); }
}

// --- Catalogo ---

async function loadCatalogo() {
  try {
    const res = await fetch(API + '/catalogo/productos');
    catalogo = await res.json();
  } catch(e) { catalogo = []; }
}

// --- Budget list ---

async function loadBudgets() {
  if (!currentUser) return;
  const res = await fetch(API + '/obras?usuario_id=' + currentUser.id);
  const data = await res.json();
  const container = document.getElementById('budgetList');

  if (!data.length) {
    container.innerHTML = '<div class="empty-state"><h3>Sin presupuestos</h3><p>Crea tu primer presupuesto de obra para comenzar a controlar tus gastos de material.</p></div>';
    return;
  }

  let html = '';
  for (const b of data) {
    const pctColor = getPctColor(b.porcentaje_consumido);
    const barClass = getBarClass(b.porcentaje_consumido);
    html += '<div class="budget-item" onclick="openBudget(' + b.id + ')">';
    html += '<div class="budget-item-header">';
    html += '<div class="budget-item-name">' + esc(b.nombre_obra) + '</div>';
    html += '<div class="budget-item-pct" style="color:' + pctColor + '">' + (b.porcentaje_consumido || 0).toFixed(1) + '%</div>';
    html += '</div>';
    html += '<div class="budget-item-meta">';
    html += '<span>' + esc(b.direccion || 'Sin direccion') + '</span>';
    html += '<span>' + b.partidas_count + ' partidas</span>';
    if (b.partidas_bloqueadas > 0) html += '<span style="color:var(--red);font-weight:600">' + b.partidas_bloqueadas + ' bloqueadas</span>';
    html += '</div>';
    html += '<div class="progress-wrap"><div class="progress-bar ' + barClass + '" style="width:' + Math.min(b.porcentaje_consumido || 0, 100) + '%">' + (b.porcentaje_consumido || 0).toFixed(1) + '%</div></div>';
    html += '<div class="budget-item-footer">';
    html += '<span>Gastado: <strong style="color:var(--navy)">$' + fmt(b.gastado_total) + '</strong></span>';
    html += '<span>Presupuesto: <strong style="color:var(--orange)">$' + fmt(b.presupuesto_total) + '</strong></span>';
    html += '</div></div>';
  }
  container.innerHTML = html;
}

// --- Budget detail ---

async function openBudget(id) {
  currentBudgetId = id;
  const res = await fetch(API + '/obras/' + id);
  const data = await res.json();
  if (data.error) { showToast(data.error, 'error'); return; }

  document.getElementById('tabDetail').style.display = 'block';
  showTab('detail');

  const container = document.getElementById('viewDetail');
  const pct = data.porcentaje_consumido || 0;
  const barClass = getBarClass(pct);
  const disponible = (data.presupuesto_total || 0) - (data.gastado_total || 0);

  let html = '';

  // Stats
  html += '<div class="stat-grid">';
  html += '<div class="stat-card"><div class="stat-icon" style="background:rgba(230,126,34,0.1);color:var(--orange)">$</div><div class="stat-value stat-accent">$' + fmt(data.presupuesto_total) + '</div><div class="stat-label">Presupuesto Total</div></div>';
  html += '<div class="stat-card"><div class="stat-icon" style="background:rgba(46,134,193,0.1);color:var(--blue)">G</div><div class="stat-value">$' + fmt(data.gastado_total) + '</div><div class="stat-label">Total Gastado</div></div>';
  html += '<div class="stat-card"><div class="stat-icon" style="background:rgba(39,174,96,0.1);color:var(--green)">D</div><div class="stat-value" style="color:' + (disponible >= 0 ? 'var(--green)' : 'var(--red)') + '">$' + fmt(disponible) + '</div><div class="stat-label">Disponible</div></div>';
  html += '<div class="stat-card"><div class="stat-icon" style="background:' + (pct >= 80 ? 'rgba(231,76,60,0.1)' : 'rgba(46,134,193,0.1)') + ';color:' + getPctColor(pct) + '">%</div><div class="stat-value" style="color:' + getPctColor(pct) + '">' + pct.toFixed(1) + '%</div><div class="stat-label">Consumido</div></div>';
  html += '</div>';

  // Obra info card
  html += '<div class="card">';
  html += '<div class="card-header"><div><div class="card-title">' + esc(data.nombre_obra) + '</div>';
  if (data.direccion) html += '<div style="color:var(--gray);font-size:12px;margin-top:2px">' + esc(data.direccion) + '</div>';
  html += '</div>';
  html += '<button class="btn btn-sm btn-secondary" onclick="openAddPanel()">+ Agregar Partida</button></div>';

  // Overall progress
  html += '<div class="progress-wrap" style="height:28px;margin-bottom:24px"><div class="progress-bar ' + barClass + '" style="width:' + Math.min(pct, 100) + '%">' + pct.toFixed(1) + '%</div></div>';

  // Partidas table
  html += '<div class="table-wrap"><table><thead><tr>';
  html += '<th>Material</th><th>Cat.</th><th>Presupuestado</th><th>Consumido</th><th>Progreso</th><th>Monto Pres.</th><th>Monto Gast.</th><th>Estado</th><th>Acciones</th>';
  html += '</tr></thead><tbody>';

  if (!data.partidas || !data.partidas.length) {
    html += '<tr><td colspan="9" style="text-align:center;padding:40px;color:var(--gray)">Sin partidas. Agrega materiales al presupuesto.</td></tr>';
  } else {
    for (const p of data.partidas) {
      const ppct = p.porcentaje_consumido || 0;
      const ppctColor = getPctColor(ppct);
      const pBarClass = getBarClass(ppct);
      let statusBadge = '';
      if (p.bloqueado) statusBadge = '<span class="badge badge-blocked">BLOQUEADO</span>';
      else if (ppct >= 80) statusBadge = '<span class="badge badge-danger">CRITICO</span>';
      else if (ppct >= 50) statusBadge = '<span class="badge badge-warn">ALERTA</span>';
      else statusBadge = '<span class="badge badge-ok">OK</span>';

      html += '<tr>';
      html += '<td><strong>' + esc(p.nombre_material) + '</strong></td>';
      html += '<td style="color:var(--gray)">' + esc(p.categoria || '-') + '</td>';
      html += '<td>' + p.cantidad_presupuestada + ' ' + esc(p.unidad || '') + '</td>';
      html += '<td>' + (p.cantidad_consumida || 0) + ' ' + esc(p.unidad || '') + '</td>';
      html += '<td><div style="display:flex;align-items:center;gap:6px"><div class="progress-wrap" style="height:14px;width:72px;flex-shrink:0"><div class="progress-bar ' + pBarClass + '" style="width:' + Math.min(ppct, 100) + '%;font-size:0"></div></div><span style="color:' + ppctColor + ';font-weight:700;font-size:11px">' + ppct.toFixed(1) + '%</span></div></td>';
      html += '<td>$' + fmt(p.monto_presupuestado) + '</td>';
      html += '<td>$' + fmt(p.monto_gastado) + '</td>';
      html += '<td>' + statusBadge + '</td>';
      html += '<td style="white-space:nowrap">';
      if (!p.bloqueado) {
        html += '<button class="btn btn-sm btn-success" onclick="openConsumoPanel(' + p.id + ',\'' + escAttr(p.nombre_material) + '\',' + p.cantidad_presupuestada + ',' + (p.cantidad_consumida||0) + ',\'' + escAttr(p.unidad||'') + '\',' + (p.precio_unitario_estimado||0) + ')">Consumo</button> ';
      }
      if (p.bloqueado) {
        html += '<button class="btn btn-sm btn-outline" onclick="desbloquear(' + data.id + ',' + p.id + ')">Desbloquear</button> ';
      }
      html += '<button class="btn btn-sm btn-ghost" style="color:var(--red)" onclick="eliminarPartida(' + p.id + ')">Eliminar</button>';
      html += '</td></tr>';
    }
  }

  html += '</tbody></table></div></div>';
  container.innerHTML = html;
}

// --- Alerts view ---

async function loadAllAlerts() {
  if (!currentUser) return;
  const container = document.getElementById('viewAlerts');
  container.innerHTML = '<div style="text-align:center;padding:40px;color:var(--gray)">Cargando alertas...</div>';

  const budgetsRes = await fetch(API + '/obras?usuario_id=' + currentUser.id);
  const budgets = await budgetsRes.json();

  if (!budgets.length) {
    container.innerHTML = '<div class="empty-state"><h3>Sin presupuestos</h3><p>Crea un presupuesto para ver alertas.</p></div>';
    return;
  }

  let allAlerts = [];
  for (const b of budgets) {
    try {
      const alertRes = await fetch(API + '/obras/' + b.id + '/alertas');
      const alertData = await alertRes.json();
      if (alertData.alertas && alertData.alertas.length) {
        for (const a of alertData.alertas) {
          a.obra = alertData.nombre_obra;
          a.presupuesto_id = b.id;
          allAlerts.push(a);
        }
      }
    } catch(e) {}
  }

  if (!allAlerts.length) {
    container.innerHTML = '<div class="card" style="text-align:center;padding:40px"><h3 style="color:var(--green);margin-bottom:8px">Sin alertas activas</h3><p style="color:var(--gray);font-size:13px">Todas las partidas estan dentro de su presupuesto.</p></div>';
    return;
  }

  let html = '<div class="card"><div class="card-title" style="margin-bottom:16px">Alertas Activas (' + allAlerts.length + ')</div>';
  for (const a of allAlerts) {
    let cls = 'alert-card-50';
    if (a.nivel === 'bloqueado' || a.nivel === '100') cls = 'alert-card-blocked';
    else if (a.nivel === '80') cls = 'alert-card-80';
    html += '<div class="alert-card ' + cls + '">';
    html += '<div style="flex:1"><strong>' + esc(a.obra) + '</strong> - ' + esc(a.mensaje) + '</div>';
    html += '<button class="btn btn-sm btn-outline" style="flex-shrink:0" onclick="openBudget(' + a.presupuesto_id + ')">Ver</button>';
    html += '</div>';
  }
  html += '</div>';
  container.innerHTML = html;
}

// --- Slide-in panel: Add partida ---

function openAddPanel() {
  const sel = document.getElementById('panelCatalogo');
  sel.innerHTML = '<option value="">-- Seleccionar del catalogo --</option>';
  for (const c of catalogo) {
    sel.innerHTML += '<option value="' + c.id + '" data-nombre="' + escAttr(c.nombre) + '" data-cat="' + escAttr(c.categoria) + '" data-unidad="' + escAttr(c.unidad) + '" data-precio="' + (c.precio_referencia||0) + '">' + esc(c.nombre) + ' (' + esc(c.categoria) + ')</option>';
  }
  document.getElementById('panelMaterial').value = '';
  document.getElementById('panelCategoria').value = '';
  document.getElementById('panelUnidad').value = '';
  document.getElementById('panelCantidad').value = '';
  document.getElementById('panelPrecio').value = '';
  document.getElementById('panelTitle').textContent = 'Agregar Partida';
  document.getElementById('panelSubmitBtn').textContent = 'Agregar';
  document.getElementById('panelOverlay').classList.add('active');
  setTimeout(function(){ document.getElementById('slidePanel').classList.add('open'); }, 10);
}

function closePanel() {
  document.getElementById('slidePanel').classList.remove('open');
  setTimeout(function(){ document.getElementById('panelOverlay').classList.remove('active'); }, 300);
}

function fillFromCatalogo() {
  const sel = document.getElementById('panelCatalogo');
  const opt = sel.options[sel.selectedIndex];
  if (!opt.value) return;
  document.getElementById('panelMaterial').value = opt.dataset.nombre || '';
  document.getElementById('panelCategoria').value = opt.dataset.cat || '';
  document.getElementById('panelUnidad').value = opt.dataset.unidad || '';
  document.getElementById('panelPrecio').value = opt.dataset.precio || '';
}

async function submitPanelPartida() {
  const material = document.getElementById('panelMaterial').value.trim();
  const cantidad = parseFloat(document.getElementById('panelCantidad').value) || 0;
  const precio = parseFloat(document.getElementById('panelPrecio').value) || 0;
  if (!material || !cantidad) { showToast('Material y cantidad son requeridos', 'error'); return; }

  const catSelect = document.getElementById('panelCatalogo');
  const catId = catSelect.value ? parseInt(catSelect.value) : null;

  const body = {
    nombre_material: material,
    categoria: document.getElementById('panelCategoria').value.trim(),
    unidad: document.getElementById('panelUnidad').value.trim(),
    cantidad_presupuestada: cantidad,
    precio_unitario_estimado: precio,
    catalogo_id: catId,
  };

  const res = await fetch(API + '/obras/' + currentBudgetId + '/partidas', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (data.ok) {
    closePanel();
    showToast('Partida agregada');
    openBudget(currentBudgetId);
  } else {
    showToast(data.error || 'Error al agregar partida', 'error');
  }
}

// --- Slide-in panel: Register consumption ---

function openConsumoPanel(partidaId, nombre, cantPres, cantCons, unidad, precioU) {
  consumoPartidaId = partidaId;
  document.getElementById('consumoTitle').textContent = 'Registrar Consumo';
  const restante = cantPres - cantCons;
  const pct = cantPres > 0 ? ((cantCons / cantPres) * 100).toFixed(1) : 0;
  document.getElementById('consumoInfo').innerHTML =
    '<div style="background:var(--gray-light);padding:14px;border-radius:8px;font-size:13px">' +
    '<strong>' + esc(nombre) + '</strong><br>' +
    '<span style="color:var(--gray)">Presupuestado: ' + cantPres + ' ' + esc(unidad) + ' | Consumido: ' + cantCons + ' ' + esc(unidad) + ' | Restante: ' + restante.toFixed(2) + ' ' + esc(unidad) + '</span><br>' +
    '<span style="color:var(--gray)">Progreso actual: <strong style="color:' + getPctColor(parseFloat(pct)) + '">' + pct + '%</strong> | Precio unitario: $' + fmt(precioU) + '</span></div>';
  document.getElementById('consumoCantidad').value = '';
  document.getElementById('consumoMonto').value = '';
  document.getElementById('consumoOverlay').classList.add('active');
  setTimeout(function(){ document.getElementById('consumoPanel').classList.add('open'); }, 10);
}

function closeConsumoPanel() {
  document.getElementById('consumoPanel').classList.remove('open');
  setTimeout(function(){ document.getElementById('consumoOverlay').classList.remove('active'); }, 300);
}

async function submitConsumo() {
  const cantidad = parseFloat(document.getElementById('consumoCantidad').value) || 0;
  const monto = parseFloat(document.getElementById('consumoMonto').value) || 0;
  if (cantidad <= 0) { showToast('Ingresa una cantidad valida', 'error'); return; }

  const res = await fetch(API + '/partidas/' + consumoPartidaId + '/consumo', {
    method: 'PUT',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify({cantidad: cantidad, monto: monto})
  });
  const data = await res.json();
  if (data.ok) {
    closeConsumoPanel();
    let msg = 'Consumo registrado: ' + data.porcentaje_consumido.toFixed(1) + '%';
    if (data.alerts_triggered && data.alerts_triggered.length) {
      msg += ' | Alertas: ' + data.alerts_triggered.join(', ');
      showToast(msg, 'warn');
    } else {
      showToast(msg);
    }
    openBudget(currentBudgetId);
  } else {
    showToast(data.error || data.mensaje || 'Error', 'error');
  }
}

// --- Desbloquear ---

async function desbloquear(presupuestoId, partidaId) {
  if (!confirm('Desbloquear esta partida? El usuario podra volver a ordenar este material.')) return;
  await fetch(API + '/obras/' + presupuestoId + '/desbloquear/' + partidaId, {method:'POST'});
  showToast('Partida desbloqueada');
  openBudget(presupuestoId);
}

// --- Eliminar partida ---

async function eliminarPartida(partidaId) {
  if (!confirm('Eliminar esta partida del presupuesto?')) return;
  await fetch(API + '/partidas/' + partidaId, {method:'DELETE'});
  showToast('Partida eliminada');
  openBudget(currentBudgetId);
}

// --- Create budget form: partida rows ---

function addPartidaRow() {
  partidaCounter++;
  const id = 'prow_' + partidaCounter;
  const container = document.getElementById('partidasContainer');
  const div = document.createElement('div');
  div.className = 'partida-row';
  div.id = id;
  div.innerHTML =
    '<input type="text" placeholder="Nombre del material" class="row-material" />' +
    '<input type="text" placeholder="Unidad" class="row-unidad" />' +
    '<input type="number" placeholder="Cant." class="row-cantidad" min="0" step="0.01" onchange="updateNewTotal()" oninput="updateNewTotal()" />' +
    '<input type="number" placeholder="$/u" class="row-precio" min="0" step="0.01" onchange="updateNewTotal()" oninput="updateNewTotal()" />' +
    '<button class="btn-remove" onclick="removePartidaRow(\\'' + id + '\\')">X</button>';
  container.appendChild(div);
  partidaRows.push(id);
}

function removePartidaRow(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
  partidaRows = partidaRows.filter(function(r){ return r !== id; });
  updateNewTotal();
}

function updateNewTotal() {
  let total = 0;
  for (const id of partidaRows) {
    const row = document.getElementById(id);
    if (!row) continue;
    const cant = parseFloat(row.querySelector('.row-cantidad').value) || 0;
    const precio = parseFloat(row.querySelector('.row-precio').value) || 0;
    total += cant * precio;
  }
  document.getElementById('newTotal').textContent = 'Total: $' + fmt(total);
}

async function crearPresupuesto() {
  const nombre = document.getElementById('newNombre').value.trim();
  if (!nombre) { showToast('Ingresa el nombre de la obra', 'error'); return; }

  const partidas = [];
  for (const id of partidaRows) {
    const row = document.getElementById(id);
    if (!row) continue;
    const material = row.querySelector('.row-material').value.trim();
    if (!material) continue;
    partidas.push({
      nombre_material: material,
      categoria: '',
      unidad: row.querySelector('.row-unidad').value.trim(),
      cantidad_presupuestada: parseFloat(row.querySelector('.row-cantidad').value) || 0,
      precio_unitario_estimado: parseFloat(row.querySelector('.row-precio').value) || 0,
    });
  }

  const body = {
    usuario_id: currentUser.id,
    nombre_obra: nombre,
    direccion: document.getElementById('newDireccion').value.trim(),
    fecha_inicio: document.getElementById('newFechaInicio').value,
    fecha_fin_estimada: document.getElementById('newFechaFin').value,
    partidas: partidas,
  };

  const res = await fetch(API + '/obras', {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: JSON.stringify(body)
  });
  const data = await res.json();
  if (data.ok) {
    showToast('Presupuesto creado: ' + data.nombre_obra);
    document.getElementById('newNombre').value = '';
    document.getElementById('newDireccion').value = '';
    document.getElementById('newFechaInicio').value = '';
    document.getElementById('newFechaFin').value = '';
    document.getElementById('partidasContainer').innerHTML = '';
    partidaRows = [];
    partidaCounter = 0;
    updateNewTotal();
    showTab('list');
  } else {
    showToast('Error: ' + JSON.stringify(data), 'error');
  }
}

// --- Helpers ---

function getPctColor(pct) {
  if (pct >= 100) return 'var(--red)';
  if (pct >= 80) return '#E67E22';
  if (pct >= 50) return 'var(--yellow)';
  return 'var(--green)';
}

function getBarClass(pct) {
  if (pct >= 100) return 'progress-red';
  if (pct >= 80) return 'progress-orange';
  if (pct >= 50) return 'progress-yellow';
  return 'progress-green';
}

function fmt(n) {
  if (n == null) return '0.00';
  return Number(n).toLocaleString('en-US', {minimumFractionDigits:2, maximumFractionDigits:2});
}

function esc(s) {
  if (!s) return '';
  const d = document.createElement('div');
  d.textContent = s;
  return d.innerHTML;
}

function escAttr(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/'/g,'&#39;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
</script>
</body>
</html>"""
