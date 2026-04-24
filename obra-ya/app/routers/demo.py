"""
Modo demo — permite a visitantes del Landing probar el agente ObraYa
sin crear cuenta. Manda mensaje por WhatsApp real al bot, trackea
el lead, y los invita a sumarse despues.

Flujo:
  1. Visitante llena el form del Landing con su WhatsApp + mensaje
  2. POST /api/demo/probar crea un LeadDemo + lo registra como Usuario temporal
  3. Manda al bot un primer mensaje "simulando" al usuario (como si hubiera
     escrito el mensaje por WhatsApp real)
  4. El bot responde por WhatsApp al telefono del visitante
  5. Interacciones posteriores se trackean en LeadDemo.mensajes_*
  6. Admin puede ver leads en /admin/api/leads-demo

Tambien permite iniciar sesion rapida con solo el telefono (para devs).
"""
import logging
import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.lead_demo import LeadDemo
from app.models.usuario import Usuario
from app.utils.telefono import normalizar_telefono_mx

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["demo"])


class DemoProbarRequest(BaseModel):
    telefono: str
    nombre: str = ""
    empresa: str = ""
    email: str = ""
    mensaje: str = ""   # Lo que quiere probar — si esta vacio usa un default
    origen: str = "landing"


@router.post("/probar")
async def probar_demo(body: DemoProbarRequest, request: Request, db: Session = Depends(get_db)):
    """
    Recibe los datos del visitante desde el Landing.
    - Valida telefono mexicano
    - Crea LeadDemo + Usuario temporal (si no existe)
    - Manda mensaje por WhatsApp al bot en nombre del usuario
    - Retorna confirmacion al frontend
    """
    telefono = normalizar_telefono_mx(body.telefono)
    if not telefono or len(telefono) < 12 or not telefono.startswith("521"):
        return JSONResponse(
            {"ok": False, "error": "Telefono invalido. Usa 10 digitos (ej: 3312345678)."},
            status_code=400,
        )

    # Mensaje que va a mandar al bot "como si fuera el usuario"
    mensaje = body.mensaje.strip() or (
        "Hola, vengo del landing de ObraYa. Quiero probar como funciona "
        "para cotizar materiales. Por ejemplo, necesito 15m3 de concreto "
        "fc250 para manana en Zapopan."
    )

    # Crear/actualizar lead
    lead = db.query(LeadDemo).filter(
        LeadDemo.telefono == telefono,
        LeadDemo.origen == body.origen,
    ).first()
    if not lead:
        lead = LeadDemo(
            telefono=telefono,
            nombre=(body.nombre or "").strip()[:150] or None,
            email=(body.email or "").strip()[:150] or None,
            empresa=(body.empresa or "").strip()[:150] or None,
            mensaje_inicial=mensaje[:1000],
            origen=body.origen,
            user_agent=request.headers.get("user-agent", "")[:300],
            ip=(request.headers.get("x-forwarded-for", "") or (request.client.host if request.client else ""))[:50],
            referer=request.headers.get("referer", "")[:300],
            status="nuevo",
        )
        db.add(lead)
    else:
        # Re-engagement: si ya existe, actualiza el ultimo mensaje
        lead.mensaje_inicial = mensaje[:1000]
        lead.updated_at = datetime.now(timezone.utc)

    # Crear Usuario temporal si no existe (para que el flujo del bot funcione)
    usuario = db.query(Usuario).filter(Usuario.telefono == telefono).first()
    if not usuario:
        usuario = Usuario(
            telefono=telefono,
            nombre=body.nombre or "Invitado Demo",
            empresa=body.empresa or None,
            email=body.email or None,
            tipo="residente",
            municipio_principal="Guadalajara",
        )
        db.add(usuario)

    db.commit()
    db.refresh(lead)
    if usuario.id is None:
        db.refresh(usuario)

    # Mandar mensaje al telefono del visitante (primera interaccion del bot)
    from app.services.whatsapp import enviar_mensaje_texto
    saludo = (
        f"¡Hola{' ' + body.nombre.split()[0] if body.nombre else ''}! 👷\n\n"
        f"Soy el agente de *ObraYa*. Estas probando el demo desde nuestra "
        f"pagina web.\n\n"
        f"Cuentame que material necesitas y te cotizo con proveedores reales "
        f"de Guadalajara en menos de 30 min.\n\n"
        f"Ejemplo:  _\"15m3 de concreto fc250 para manana en Zapopan\"_"
    )
    try:
        resultado = await enviar_mensaje_texto(telefono, saludo)
        lead.mensajes_enviados = (lead.mensajes_enviados or 0) + 1
        lead.ultimo_contacto = datetime.now(timezone.utc)
        if "error" in resultado:
            logger.warning(f"Demo: no se pudo mandar a {telefono}: {resultado.get('error')}")
            db.commit()
            return {
                "ok": True,
                "lead_id": lead.id,
                "status": "saludo_fallido",
                "detalle": (
                    "Guardamos tu info pero WhatsApp no pudo mandarte el mensaje "
                    "(probablemente tu numero no esta en modo tester del numero demo). "
                    "Puedes escribirnos directo a +52 1 33 1852 6297 para probar."
                ),
                "wa_link": f"https://wa.me/5213318526297?text={mensaje.replace(' ', '%20')[:200]}",
            }
        db.commit()
        return {
            "ok": True,
            "lead_id": lead.id,
            "status": "mensaje_enviado",
            "mensaje": "Revisa tu WhatsApp, te acabo de escribir.",
            "wa_link": f"https://wa.me/5213318526297",
        }
    except Exception as e:
        logger.error(f"Error en demo: {e}")
        db.commit()
        return {
            "ok": True,
            "lead_id": lead.id,
            "status": "pendiente",
            "mensaje": "Guardamos tu info. Escribenos directo en WhatsApp.",
            "wa_link": f"https://wa.me/5213318526297?text={mensaje.replace(' ', '%20')[:200]}",
        }


@router.post("/login-rapido")
async def login_rapido(body: DemoProbarRequest, db: Session = Depends(get_db)):
    """
    Login rapido con solo el telefono — para que los visitantes del Landing
    entren al portal sin crear cuenta completa.
    Crea el usuario si no existe, devuelve un JWT.
    """
    from app.services.auth_service import crear_token

    telefono = normalizar_telefono_mx(body.telefono)
    if not telefono or len(telefono) < 12:
        return JSONResponse({"ok": False, "error": "Telefono invalido"}, status_code=400)

    usuario = db.query(Usuario).filter(Usuario.telefono == telefono).first()
    if not usuario:
        usuario = Usuario(
            telefono=telefono,
            nombre=(body.nombre or "").strip()[:150] or f"Usuario {telefono[-4:]}",
            email=(body.email or "").strip()[:150] or None,
            empresa=(body.empresa or "").strip()[:150] or None,
            tipo="residente",
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

    token = crear_token({"sub": str(usuario.id), "telefono": usuario.telefono})
    return {
        "ok": True,
        "token": token,
        "usuario": {
            "id": usuario.id,
            "nombre": usuario.nombre,
            "telefono": usuario.telefono,
        },
        "redirect": "/portal",
    }


class TrackRequest(BaseModel):
    mensaje: str = ""
    origen: str = "probar"
    telefono: str = ""


@router.post("/track")
async def track_interaccion(body: TrackRequest, request: Request, db: Session = Depends(get_db)):
    """
    Endpoint ligero para registrar que alguien inicio el demo interactivo.
    Acepta opcionalmente el telefono si lo dio. Si no, solo trackea anonimo.
    """
    try:
        # Si hay telefono valido, crear/actualizar LeadDemo
        telefono = normalizar_telefono_mx(body.telefono) if body.telefono else ""
        if telefono and len(telefono) >= 12:
            lead = db.query(LeadDemo).filter(
                LeadDemo.telefono == telefono,
                LeadDemo.origen == body.origen,
            ).first()
            if not lead:
                lead = LeadDemo(
                    telefono=telefono,
                    mensaje_inicial=body.mensaje[:1000],
                    origen=body.origen,
                    user_agent=request.headers.get("user-agent", "")[:300],
                    ip=(request.headers.get("x-forwarded-for", "") or (request.client.host if request.client else ""))[:50],
                    referer=request.headers.get("referer", "")[:300],
                    status="nuevo",
                )
                db.add(lead)
            else:
                lead.mensaje_inicial = body.mensaje[:1000]
                lead.updated_at = datetime.now(timezone.utc)
            db.commit()
        else:
            # Anonimo: solo log
            logger.info(f"Demo track anonimo — origen={body.origen} msg={body.mensaje[:80]}")
    except Exception as e:
        logger.error(f"Error en track: {e}")

    return {"ok": True}


@router.get("/leads")
def listar_leads(limit: int = 50, db: Session = Depends(get_db)):
    """Admin: ve leads del demo (para re-engagement)."""
    leads = db.query(LeadDemo).order_by(LeadDemo.created_at.desc()).limit(limit).all()
    return [
        {
            "id": l.id,
            "telefono": l.telefono,
            "nombre": l.nombre,
            "empresa": l.empresa,
            "email": l.email,
            "origen": l.origen,
            "status": l.status,
            "mensaje_inicial": (l.mensaje_inicial or "")[:150],
            "mensajes_enviados": l.mensajes_enviados,
            "mensajes_recibidos": l.mensajes_recibidos,
            "created_at": l.created_at.isoformat() if l.created_at else None,
            "ultimo_contacto": l.ultimo_contacto.isoformat() if l.ultimo_contacto else None,
        }
        for l in leads
    ]
