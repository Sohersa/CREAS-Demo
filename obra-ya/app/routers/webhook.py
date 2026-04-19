"""
Webhook de WhatsApp — recibe mensajes y los procesa.

FLUJO INTELIGENTE POR CONTEXTO:
1. Si el usuario tiene un pedido en status "enviado" → esta eligiendo proveedor
2. Si tiene una orden en "en_obra" → esta confirmando entrega o reportando problema
3. Si tiene una orden activa y reporta problema → incidencia
4. Si no tiene nada activo → nuevo pedido (flujo original)
"""
import json
import logging
import re
import httpx
from fastapi import APIRouter, Request, Query, Depends, BackgroundTasks
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(key_func=get_remote_address)
from app.database import get_db, SessionLocal
from app.services.whatsapp import (
    parsear_webhook, enviar_mensaje_texto, marcar_como_leido, descargar_audio,
    enviar_mensaje_con_botones, enviar_mensaje_con_lista, descargar_imagen,
)
from app.services.whatsapp_twilio import parsear_webhook_twilio
from app.services.agente_claude import interpretar_mensaje, limpiar_conversacion
from app.services.transcriptor import transcribir_audio
from app.services.cotizador import generar_cotizaciones, guardar_cotizaciones
from app.services.comparador import generar_comparativa_simple, resumir_pedido
from app.services.orden_service import (
    crear_orden, confirmar_entrega, cancelar_orden,
    obtener_orden_activa_por_usuario,
)
from app.services.incidencia_service import crear_incidencia
from app.services.calificacion_service import calcular_calificacion
from app.services.notificaciones import (
    notificar_orden_confirmada, notificar_entrega_completada,
    notificar_incidencia_registrada, notificar_orden_confirmada_proveedor,
)
from app.services.cotizacion_activa import (
    enviar_solicitudes_a_proveedores, registrar_respuesta_proveedor,
    hay_suficientes_respuestas, obtener_resumen_solicitudes, marcar_sin_respuesta,
)
from app.services.parser_respuesta_proveedor import (
    es_mensaje_de_proveedor, obtener_proveedor_por_telefono, parsear_respuesta_proveedor,
)
from app.services.comparativa_activa import (
    generar_comparativa_desde_respuestas, generar_mensaje_esperando,
)
from app.models.usuario import Usuario
from app.models.pedido import Pedido
from app.models.cotizacion import Cotizacion, Comparativa
from app.models.solicitud_proveedor import SolicitudProveedor
from app.services.aprobacion_service import (
    aprobar_orden as aprobar_aprobacion,
    rechazar_orden as rechazar_aprobacion,
    obtener_aprobaciones_pendientes,
    componer_mensaje_resultado,
    necesita_aprobacion,
    solicitar_aprobacion,
)
from app.models.aprobacion import Aprobacion

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])

def _extraer_municipio(direccion: str) -> str:
    """
    Extrae el municipio/ciudad de una direccion.
    Busca patrones comunes: 'Zapopan', 'Col. Centro, Guadalajara', etc.
    Usa la penultima parte separada por coma (tipicamente ciudad/municipio).
    """
    if not direccion:
        return ""
    partes = [p.strip() for p in direccion.split(",") if p.strip()]
    if len(partes) >= 3:
        # En formato "Calle, Colonia, Municipio, Estado" → penultima
        return partes[-2]
    elif len(partes) == 2:
        # "Calle, Municipio" → ultima
        return partes[-1]
    return partes[0] if partes else ""


# Idempotencia: evitar procesar el mismo mensaje dos veces (WhatsApp retries)
from collections import OrderedDict
_mensajes_procesados = OrderedDict()

# Cache en memoria de la ultima ubicacion GPS recibida por telefono.
# Se usa cuando se crea el pedido para copiar coords/municipio/codigo_postal.
# LRU de 1000 entradas (auto-limpieza).
_ubicacion_reciente: "OrderedDict[str, dict]" = OrderedDict()


def _guardar_ubicacion_reciente(telefono: str, info: dict):
    """Guarda la ultima ubicacion del usuario, mantiene tamano maximo."""
    _ubicacion_reciente[telefono] = info
    if len(_ubicacion_reciente) > 1000:
        _ubicacion_reciente.popitem(last=False)


def _obtener_ubicacion_reciente(telefono: str) -> dict | None:
    """Devuelve la ultima ubicacion GPS que mando el usuario (si hay)."""
    return _ubicacion_reciente.get(telefono)
_MAX_DEDUP_SIZE = 5000

def _ya_procesado(message_id: str) -> bool:
    """Retorna True si el message_id ya fue procesado. Usa cache LRU en memoria."""
    if not message_id:
        return False
    if message_id in _mensajes_procesados:
        return True
    _mensajes_procesados[message_id] = True
    if len(_mensajes_procesados) > _MAX_DEDUP_SIZE:
        _mensajes_procesados.popitem(last=False)
    return False


# === Deteccion de contexto ===

def detectar_contexto(db: Session, usuario_id: int) -> tuple[str, object]:
    """
    Detecta en que parte del flujo esta el usuario.
    Retorna (contexto, objeto_relevante).

    Contextos:
      - "seleccion_proveedor": tiene pedido enviado, esperando que elija
      - "confirmacion_entrega": tiene orden en_obra, esperando OK
      - "orden_activa": tiene orden activa (puede reportar o preguntar status)
      - "nuevo_pedido": no tiene nada activo, flujo normal
    """
    # 0a. Pedido sin_respuesta? (esperando que usuario diga SI para reintentar)
    pedido_sin_respuesta = db.query(Pedido).filter(
        Pedido.usuario_id == usuario_id,
        Pedido.status == "sin_respuesta",
    ).order_by(Pedido.created_at.desc()).first()

    if pedido_sin_respuesta:
        return "reintento_cotizacion", pedido_sin_respuesta

    # 0. Pedido en cotizacion? (esperando respuestas de proveedores)
    pedido_cotizando = db.query(Pedido).filter(
        Pedido.usuario_id == usuario_id,
        Pedido.status == "cotizando",
    ).order_by(Pedido.created_at.desc()).first()

    if pedido_cotizando:
        return "esperando_cotizaciones", pedido_cotizando

    # 1. Pedido enviado esperando seleccion? (acepta "enviado" y legacy "comparando")
    pedido_enviado = db.query(Pedido).filter(
        Pedido.usuario_id == usuario_id,
        Pedido.status.in_(["enviado", "comparando"]),
    ).order_by(Pedido.created_at.desc()).first()

    if pedido_enviado:
        return "seleccion_proveedor", pedido_enviado

    # 2. Orden activa?
    from app.models.orden import Orden
    orden_activa = db.query(Orden).filter(
        Orden.usuario_id == usuario_id,
        Orden.status.notin_(["entregada", "cancelada"]),
    ).order_by(Orden.created_at.desc()).first()

    if orden_activa:
        if orden_activa.status == "en_obra":
            return "confirmacion_entrega", orden_activa
        return "orden_activa", orden_activa

    # 3. Nada activo → nuevo pedido
    return "nuevo_pedido", None


def interpretar_seleccion(texto: str, num_opciones: int) -> int | None:
    """
    Interpreta la respuesta del usuario para elegir proveedor.
    Acepta: "1", "el primero", "el mas barato", "2", "el segundo", etc.
    """
    texto_lower = texto.lower().strip()

    # Numero directo
    match = re.match(r"^(\d+)$", texto_lower)
    if match:
        num = int(match.group(1))
        if 1 <= num <= num_opciones:
            return num

    # Palabras clave
    primero = ["1", "primero", "primera", "uno", "el primero", "la primera", "mas barato", "el mas barato", "barato"]
    segundo = ["2", "segundo", "segunda", "dos", "el segundo"]
    tercero = ["3", "tercero", "tercera", "tres", "el tercero"]

    for keyword in primero:
        if keyword in texto_lower:
            return 1
    for keyword in segundo:
        if keyword in texto_lower and num_opciones >= 2:
            return 2
    for keyword in tercero:
        if keyword in texto_lower and num_opciones >= 3:
            return 3

    return None


def es_confirmacion(texto: str) -> bool:
    """Detecta si el usuario esta confirmando recepcion."""
    confirmaciones = [
        "ok", "okey", "si", "sí", "todo bien", "recibido", "listo",
        "correcto", "todo correcto", "afirmativo", "va", "sale",
        "confir", "recib", "completo", "bien",
    ]
    texto_lower = texto.lower().strip()
    return any(c in texto_lower for c in confirmaciones)


def es_reporte_problema(texto: str) -> bool:
    """Detecta si el usuario esta reportando un problema."""
    problemas = [
        "problema", "mal", "menos", "falt", "tarde", "no llego",
        "incorrecto", "equivocado", "roto", "danado", "diferente",
        "no era", "cobr", "quebraron", "mojado", "no es lo que",
    ]
    texto_lower = texto.lower().strip()
    return any(p in texto_lower for p in problemas)


def es_pregunta_status(texto: str) -> bool:
    """Detecta si pregunta por el status de su orden."""
    status_kw = [
        "status", "estado", "como va", "donde va", "ya llego",
        "cuando llega", "en camino", "mi pedido", "mi orden",
    ]
    texto_lower = texto.lower().strip()
    return any(s in texto_lower for s in status_kw)


def es_aprobacion(texto: str, button_id: str = "") -> tuple[bool, int | None, str]:
    """
    Detecta si el usuario está aprobando una orden.
    Soporta: botones interactivos, comando APROBAR {id}, y lenguaje natural.
    Returns (es_aprobacion, orden_id, nota).
    """
    # 1. Boton interactivo: "aprobar_{orden_id}"
    if button_id:
        match = re.match(r'^aprobar_(\d+)$', button_id)
        if match:
            return True, int(match.group(1)), ""

    texto_upper = texto.strip().upper()

    # 2. Comando explicito: APROBAR 42
    match = re.match(r'^APROBAR\s+(\d+)\s*(.*)', texto_upper)
    if match:
        return True, int(match.group(1)), match.group(2).strip()

    # 3. Lenguaje natural afirmativo (se resuelve con aprobaciones pendientes en el caller)
    AFIRMATIVOS = {"sí", "si", "dale", "va", "ok", "okey", "aprobado", "autorizado",
                   "adelante", "procede", "sale", "jalale", "simón", "simon", "órale", "orale",
                   "está bien", "esta bien", "de acuerdo", "apruebo", "yes"}
    texto_limpio = texto.strip().lower().rstrip(".!,")
    if texto_limpio in AFIRMATIVOS:
        return True, None, ""  # orden_id=None → resolver con pendientes

    return False, None, ""


def es_rechazo(texto: str, button_id: str = "") -> tuple[bool, int | None, str]:
    """
    Detecta si el usuario está rechazando una orden.
    Soporta: botones interactivos, comando RECHAZAR {id}, y lenguaje natural.
    Returns (es_rechazo, orden_id, motivo).
    """
    # 1. Boton interactivo: "rechazar_{orden_id}"
    if button_id:
        match = re.match(r'^rechazar_(\d+)$', button_id)
        if match:
            return True, int(match.group(1)), ""

    texto_upper = texto.strip().upper()

    # 2. Comando explicito: RECHAZAR 42 motivo
    match = re.match(r'^RECHAZAR\s+(\d+)\s*(.*)', texto_upper)
    if match:
        return True, int(match.group(1)), match.group(2).strip()

    # 3. Lenguaje natural negativo
    NEGATIVOS = {"no", "nel", "rechazado", "rechaza", "no autorizado", "muy caro",
                 "no procede", "cancelar", "cancela", "nope", "negativo", "no va"}
    texto_limpio = texto.strip().lower().rstrip(".!,")
    if texto_limpio in NEGATIVOS:
        return True, None, ""  # orden_id=None → resolver con pendientes

    return False, None, ""


# === Endpoints ===

@router.get("/whatsapp")
async def verificar_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    """Verificacion del webhook de Meta."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verificado correctamente")
        return PlainTextResponse(content=hub_challenge, status_code=200)

    logger.warning(f"Verificacion fallida: mode={hub_mode}, token={hub_verify_token}")
    return PlainTextResponse(content="Verificacion fallida", status_code=403)


@router.post("/whatsapp")
@limiter.limit("30/minute")
async def recibir_mensaje(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Recibe mensajes de WhatsApp y procesa en background."""
    body = await request.json()

    msg = parsear_webhook(body)
    if not msg:
        return {"status": "ok"}

    # Idempotencia: rechazar mensajes duplicados (WhatsApp retries)
    if _ya_procesado(msg.get("message_id", "")):
        logger.info(f"Mensaje duplicado ignorado: {msg.get('message_id')}")
        return {"status": "ok"}

    logger.info(f"Mensaje recibido de {msg['telefono']}: {msg['tipo_mensaje']}")

    background_tasks.add_task(procesar_mensaje, msg, db)
    return {"status": "ok"}


@router.post("/twilio")
@limiter.limit("30/minute")
async def recibir_mensaje_twilio(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Recibe mensajes de WhatsApp via Twilio (form-urlencoded)."""
    form_data = await request.form()
    form_dict = dict(form_data)

    msg = parsear_webhook_twilio(form_dict)
    if not msg:
        return PlainTextResponse(
            content="<Response></Response>",
            media_type="application/xml",
        )

    # Idempotencia
    if _ya_procesado(msg.get("message_id", "")):
        logger.info(f"[Twilio] Mensaje duplicado ignorado: {msg.get('message_id')}")
        return PlainTextResponse(content="<Response></Response>", media_type="application/xml")

    logger.info(f"[Twilio] Mensaje recibido de {msg['telefono']}: {msg['tipo_mensaje']}")

    background_tasks.add_task(procesar_mensaje, msg, db)

    return PlainTextResponse(
        content="<Response></Response>",
        media_type="application/xml",
    )


async def procesar_mensaje(msg: dict, _db_unused: Session = None):
    """
    Logica principal — detecta contexto y rutea al flujo correcto.
    Crea su propia sesion DB para evitar race conditions con FastAPI.
    """
    telefono = msg["telefono"]
    nombre = msg["nombre"]
    db = SessionLocal()

    try:
        await marcar_como_leido(msg["message_id"])

        # Obtener o crear usuario
        es_nuevo = False
        usuario = db.query(Usuario).filter(Usuario.telefono == telefono).first()
        if not usuario:
            usuario = Usuario(telefono=telefono, nombre=nombre)
            db.add(usuario)
            db.commit()
            db.refresh(usuario)
            es_nuevo = True

        # Onboarding: mensaje de bienvenida para usuarios nuevos
        if es_nuevo:
            nombre_display = nombre.split()[0] if nombre else "Hola"
            await enviar_mensaje_texto(
                telefono,
                f"Hola {nombre_display}! Soy *Nico*, tu asistente de materiales en ObraYa.\n\n"
                f"Dime que necesitas y yo cotizo con proveedores en tu zona.\n\n"
                f"Ejemplo: \"15m3 de concreto fc250 para manana en Zapopan\"\n\n"
                f"Tambien acepto audios y ubicacion GPS."
            )

        # Obtener texto (soporta: texto, audio, ubicacion, imagenes)
        if msg["tipo_mensaje"] == "audio":
            source = msg.get("source", "")
            audio_bytes = await descargar_audio(msg["contenido"], source=source)
            if not audio_bytes:
                logger.error(f"No se pudo descargar audio de {telefono} (source={source})")
                await enviar_mensaje_texto(
                    telefono,
                    "No pude descargar tu nota de voz. Intenta de nuevo o escribe tu mensaje por texto."
                )
                return
            texto = await transcribir_audio(audio_bytes)
            if not texto:
                await enviar_mensaje_texto(
                    telefono,
                    "No pude entender el audio. Intenta de nuevo o escribe tu pedido por texto."
                )
                return
            logger.info(f"Audio transcrito de {telefono}: {texto[:100]}")

        elif msg["tipo_mensaje"] == "ubicacion":
            # Feedback inmediato para que el usuario sepa que llego
            await enviar_mensaje_texto(telefono, "Recibi tu ubicacion. Un segundo…")

            from app.services.geocoding import resolver_ubicacion, formatear_ubicacion_corta
            loc = msg["contenido"]
            lat_raw = loc.get("latitude", "")
            lng_raw = loc.get("longitude", "")
            nombre_lugar = loc.get("name", "")
            direccion_lugar = loc.get("address", "")

            info_ubicacion = await resolver_ubicacion(
                latitud=lat_raw,
                longitud=lng_raw,
                direccion_whatsapp=direccion_lugar,
                nombre_lugar=nombre_lugar,
            )

            if not info_ubicacion.get("ok"):
                await enviar_mensaje_texto(
                    telefono,
                    "No pude leer esa ubicacion. Puedes mandarla de nuevo o escribirme la direccion?"
                )
                return

            # Validar area de servicio
            if not info_ubicacion.get("en_area_servicio"):
                motivo = info_ubicacion.get("fuera_servicio_motivo", "")
                lugar = formatear_ubicacion_corta(info_ubicacion)
                await enviar_mensaje_texto(
                    telefono,
                    f"Detecte tu ubicacion en {lugar}.\n\n"
                    f"*Por ahora solo operamos en el area metropolitana de Guadalajara* "
                    f"(GDL, Zapopan, Tlaquepaque, Tonala, Tlajomulco, El Salto).\n\n"
                    f"Si crees que es un error o quieres que nos expandamos a tu zona, escribe *contactar* y te ayudamos."
                )
                return

            # Guardar la info en la sesion del usuario para que los handlers la usen
            _guardar_ubicacion_reciente(telefono, info_ubicacion)

            # Actualizar municipio principal del usuario si esta vacio
            if not usuario.municipio_principal and info_ubicacion.get("municipio"):
                usuario.municipio_principal = info_ubicacion["municipio"]
                db.commit()

            # Confirmacion visual al usuario
            resumen = formatear_ubicacion_corta(info_ubicacion)
            await enviar_mensaje_texto(
                telefono,
                f"*Ubicacion confirmada*: {resumen}\n\n"
                f"Esta direccion quedo guardada para tu pedido. "
                f"Ahora dime que materiales necesitas (o si ya me los habias dicho, "
                f"voy a cotizar con proveedores cercanos)."
            )

            # Inyectar como texto estructurado para Claude (con municipio explicito)
            muni = info_ubicacion.get("municipio", "")
            coords = f"{info_ubicacion['latitud']},{info_ubicacion['longitud']}"
            texto = (
                f"La entrega es en: {resumen}. "
                f"Municipio: {muni}. Coordenadas GPS: {coords}."
            )
            logger.info(f"Ubicacion validada de {telefono}: {resumen} ({muni})")

        elif msg["tipo_mensaje"] == "imagen":
            # Soporte de imágenes — fotos de listas de materiales, planos, etc.
            from app.services.whatsapp import descargar_imagen
            from app.services.agente_claude import interpretar_imagen
            source = msg.get("source", "")
            image_bytes = await descargar_imagen(msg["contenido"], source=source)
            if not image_bytes:
                await enviar_mensaje_texto(
                    telefono,
                    "No pude descargar la imagen. Intenta de nuevo o describe tu pedido por texto."
                )
                return
            await enviar_mensaje_texto(telefono, "Recibido. Analizando tu imagen...")
            texto = await interpretar_imagen(image_bytes)
            if not texto:
                await enviar_mensaje_texto(
                    telefono,
                    "No pude leer la imagen. Intenta con una foto mas clara o escribe tu pedido."
                )
                return
            logger.info(f"Imagen interpretada de {telefono}: {texto[:100]}")

        elif msg["tipo_mensaje"] == "texto":
            texto = msg["contenido"]

        else:
            await enviar_mensaje_texto(
                telefono,
                "Puedo recibir texto, audio, fotos y ubicacion. Manda tu pedido por cualquiera de esos medios."
            )
            return

        # === DETECTAR APROBACION/RECHAZO ===
        button_id = msg.get("button_id", "")
        aprueba, orden_id_apr, nota_apr = es_aprobacion(texto, button_id)
        rechaza, orden_id_rech, nota_rech = es_rechazo(texto, button_id)

        # Si es lenguaje natural (orden_id=None), buscar aprobacion pendiente mas reciente
        if aprueba and orden_id_apr is None:
            pendientes = obtener_aprobaciones_pendientes(db, usuario.id)
            if len(pendientes) == 1:
                orden_id_apr = pendientes[0].orden_id
            elif len(pendientes) > 1:
                await enviar_mensaje_texto(
                    telefono,
                    f"Tienes {len(pendientes)} aprobaciones pendientes. "
                    f"Especifica cual: APROBAR {{numero de orden}}"
                )
                return
            else:
                aprueba = False  # No hay pendientes, tratar como mensaje normal

        if rechaza and orden_id_rech is None:
            pendientes = obtener_aprobaciones_pendientes(db, usuario.id)
            if len(pendientes) == 1:
                orden_id_rech = pendientes[0].orden_id
            elif len(pendientes) > 1:
                await enviar_mensaje_texto(
                    telefono,
                    f"Tienes {len(pendientes)} aprobaciones pendientes. "
                    f"Especifica cual: RECHAZAR {{numero de orden}} {{motivo}}"
                )
                return
            else:
                rechaza = False

        if aprueba and orden_id_apr:
            await manejar_aprobacion(db, usuario, orden_id_apr, nota_apr, telefono)
            return
        if rechaza and orden_id_rech:
            await manejar_rechazo(db, usuario, orden_id_rech, nota_rech, telefono)
            return

        # === DETECTAR CODIGO DE REGISTRO DE PROVEEDOR ===
        match_registro = re.match(r'^REGISTRO\s+(\w+)', texto.strip(), re.IGNORECASE)
        if match_registro:
            codigo = match_registro.group(1).upper()
            from app.models.proveedor import Proveedor
            proveedor = db.query(Proveedor).filter(
                Proveedor.codigo_registro == codigo,
            ).first()
            if proveedor:
                # Vincular telefono al proveedor
                proveedor.telefono_whatsapp = telefono
                proveedor.activo = True
                db.commit()
                await enviar_mensaje_texto(
                    telefono,
                    f"Hola {proveedor.nombre}! Bienvenido a ObraYa.\n\n"
                    f"Cuando un cliente necesite materiales de tu zona, "
                    f"te mando la solicitud por aqui.\n"
                    f"Solo responde con tu precio y listo.\n\n"
                    f"Si tienes una orden activa, puedes actualizarla:\n"
                    f"  *PREPARANDO #* · *EN CAMINO #* · *ENTREGADO #*"
                )
                logger.info(f"Proveedor {proveedor.nombre} vinculado via codigo {codigo} → {telefono}")
                return
            else:
                await enviar_mensaje_texto(telefono, "Codigo de registro no valido. Verifica con tu contacto de ObraYa.")
                return

        # === DETECTAR SI ES PROSPECTO DE OUTREACH (respuesta a nuestro contacto) ===
        from app.models.prospecto import ProspectoProveedor
        prospecto = db.query(ProspectoProveedor).filter(
            ProspectoProveedor.telefono == telefono,
            ProspectoProveedor.activo == True,
            ProspectoProveedor.status.in_([
                "contactado", "dialogo_activo", "interesado", "sin_respuesta"
            ]),
        ).first()
        if prospecto:
            from app.services.prospect_response import procesar_respuesta_prospecto
            await procesar_respuesta_prospecto(db, prospecto, texto)
            return

        # === DETECTAR SI ES PROVEEDOR ===
        if es_mensaje_de_proveedor(db, telefono):
            await manejar_respuesta_proveedor(db, telefono, texto)
            return

        # === DETECTAR CONTEXTO (USUARIO) ===
        contexto, objeto = detectar_contexto(db, usuario.id)
        logger.info(f"Contexto para {telefono}: {contexto}")

        if contexto == "reintento_cotizacion":
            await manejar_reintento_cotizacion(db, usuario, objeto, texto, telefono)

        elif contexto == "esperando_cotizaciones":
            await manejar_esperando_cotizaciones(db, usuario, objeto, texto, telefono)

        elif contexto == "seleccion_proveedor":
            await manejar_seleccion_proveedor(db, usuario, objeto, texto, telefono)

        elif contexto == "confirmacion_entrega":
            await manejar_confirmacion_entrega(db, usuario, objeto, texto, telefono)

        elif contexto == "orden_activa":
            await manejar_orden_activa(db, usuario, objeto, texto, telefono)

        else:
            # Detectar si es pregunta de asesor (consulta compleja con datos reales)
            # ej: "que proveedor me conviene", "es justo este precio", "tengo presupuesto"
            if es_pregunta_asesor(texto):
                await manejar_consulta_asesor(db, usuario, texto, telefono)
            else:
                # Flujo original — nuevo pedido
                await manejar_nuevo_pedido(db, usuario, texto, telefono)

    except Exception as e:
        logger.error(f"Error procesando mensaje de {telefono}: {e}", exc_info=True)
        await enviar_mensaje_texto(
            telefono,
            "Ups, tuve un problema procesando tu mensaje. Intenta de nuevo en un momento."
        )
    finally:
        db.close()


# === Handlers por contexto ===

def es_pregunta_asesor(texto: str) -> bool:
    """
    Detecta si el mensaje es una pregunta compleja de asesor (no un pedido).
    El agente autonomo con tools responde mejor estas preguntas que el flujo normal.

    Ejemplos:
      - "¿que proveedor de concreto me conviene en Zapopan?"
      - "¿es justo pagar $45k por 15m3 de concreto?"
      - "¿tengo presupuesto para esta compra?"
      - "¿como esta el precio de la varilla este mes?"
    """
    t = texto.lower().strip()

    # Debe ser pregunta explicita (contiene ? o palabra interrogativa)
    tiene_pregunta = "?" in t or any(
        w in t for w in ["que ", "qué ", "cual", "cuál", "como ", "cómo ",
                         "donde", "dónde", "cuando", "cuándo", "porque", "porqué"]
    )
    if not tiene_pregunta:
        return False

    # Keywords de intencion de asesor
    ASESOR_KEYWORDS = [
        "conviene", "recomienda", "mejor proveedor", "mas barato", "más barato",
        "es justo", "es caro", "es razonable", "precio promedio",
        "presupuesto", "puedo gastar", "tengo para", "alcanza",
        "como esta el precio", "cómo está el precio", "precio del mes",
        "historial", "comparacion", "comparación",
        "calificacion", "calificación", "reputacion", "reputación",
        "vale la pena", "conviene mas", "conviene más",
    ]
    return any(kw in t for kw in ASESOR_KEYWORDS)


async def manejar_consulta_asesor(db, usuario, texto, telefono):
    """
    Invoca el agente autonomo con tool use para responder preguntas
    que requieren consultar datos reales (proveedores, precios, presupuesto).
    """
    from app.services.agente_autonomo import procesar_consulta_compleja

    # Feedback instantaneo (puede tardar varios segundos con tool calls)
    await enviar_mensaje_texto(telefono, "Dejame revisar los datos…")

    try:
        respuesta = await procesar_consulta_compleja(db, usuario.id, texto)
        if respuesta:
            await enviar_mensaje_texto(telefono, respuesta)
        else:
            await enviar_mensaje_texto(
                telefono,
                "No pude procesar tu pregunta. ¿Me la puedes reformular?"
            )
    except Exception as e:
        logger.error(f"Error en agente asesor para {telefono}: {e}")
        await enviar_mensaje_texto(
            telefono,
            "Tuve un problema consultando la informacion. Intenta mas tarde."
        )


async def manejar_seleccion_proveedor(db, usuario, pedido, texto, telefono):
    """El usuario tiene un pedido enviado y esta eligiendo proveedor."""
    # Permitir al usuario hacer un nuevo pedido si lo pide explicitamente
    if any(kw in texto.lower() for kw in ["nuevo pedido", "otro pedido", "cotizar otro", "nueva cotizacion"]):
        pedido.status = "cancelado"
        db.commit()
        await manejar_nuevo_pedido(db, usuario, texto, telefono)
        return

    # Obtener cotizaciones del pedido (cualquier status valido)
    cotizaciones = db.query(Cotizacion).filter(
        Cotizacion.pedido_id == pedido.id,
    ).order_by(Cotizacion.total).all()

    if not cotizaciones:
        await enviar_mensaje_texto(telefono, "No encontre cotizaciones para tu pedido. Intenta hacer un pedido nuevo.")
        pedido.status = "cancelado"
        db.commit()
        return

    seleccion = interpretar_seleccion(texto, len(cotizaciones))

    if seleccion:
        cotizacion_elegida = cotizaciones[seleccion - 1]

        # Verificar si necesita aprobacion corporativa ANTES de crear la orden
        requiere_aprobacion = necesita_aprobacion(db, usuario.id, cotizacion_elegida.total or 0)

        # Crear orden con status correcto
        orden = crear_orden(
            db, cotizacion_elegida.id, usuario.id,
            status_inicial="pendiente_aprobacion" if requiere_aprobacion else "confirmada",
        )

        # Marcar pedido como completado
        pedido.status = "orden_creada"
        db.commit()

        # Si requiere aprobacion, solicitar y NO notificar al proveedor aun
        if requiere_aprobacion:
            aprobacion = await solicitar_aprobacion(db, orden.id, usuario.id)
            if aprobacion:
                await enviar_mensaje_texto(
                    telefono,
                    f"Tu orden #{orden.id} por ${orden.total:,.0f} requiere aprobacion de tu empresa.\n"
                    f"Ya notifique a los responsables. Te aviso cuando respondan."
                )
                return

        # Obtener nombre del proveedor
        from app.models.proveedor import Proveedor
        proveedor = db.query(Proveedor).filter(Proveedor.id == cotizacion_elegida.proveedor_id).first()
        proveedor_nombre = proveedor.nombre if proveedor else "el proveedor"

        # Notificar al usuario directamente (no depender de notificaciones sync)
        items_resumen = ""
        try:
            items_data = json.loads(cotizacion_elegida.items) if cotizacion_elegida.items else []
            for item in items_data[:5]:
                items_resumen += f"  - {item.get('cantidad', '?')} {item.get('unidad', '')} {item.get('producto', '')}\n"
        except Exception:
            items_resumen = "  (ver detalle en la orden)\n"

        await enviar_mensaje_texto(
            telefono,
            f"*Pedido confirmado con {proveedor_nombre}!*\n\n"
            f"Orden #{orden.id}\n"
            f"{items_resumen}\n"
            f"Total: ${orden.total:,.0f} MXN\n"
            f"Entrega: {orden.direccion_entrega or pedido.direccion_entrega or 'por confirmar'}\n\n"
            f"Te voy avisando el status. Si hay cualquier tema, mandame mensaje."
        )

        # CRITICO: Notificar al PROVEEDOR que fue seleccionado
        try:
            notificar_orden_confirmada_proveedor(db, orden)
        except Exception as e:
            logger.error(f"Error notificando proveedor de orden #{orden.id}: {e}")

        logger.info(f"Orden #{orden.id} creada para {telefono}")

        # Limpiar historial de conversacion — ciclo completo
        await limpiar_conversacion(db, telefono)

    else:
        # No entendimos la seleccion — preguntar de nuevo con info util
        from app.models.proveedor import Proveedor
        opciones = []
        for i, cot in enumerate(cotizaciones[:5]):
            prov = db.query(Proveedor).filter(Proveedor.id == cot.proveedor_id).first()
            nombre = prov.nombre if prov else f"Proveedor {cot.proveedor_id}"
            opciones.append(f"  *{i+1}*. {nombre} — ${cot.total:,.0f}")

        await enviar_mensaje_texto(
            telefono,
            f"No entendi tu seleccion. Responde con el *numero* del proveedor que prefieras:\n\n"
            + "\n".join(opciones)
        )


async def manejar_confirmacion_entrega(db, usuario, orden, texto, telefono):
    """El usuario tiene una orden en_obra — esperamos OK o reporte de problema."""
    if es_confirmacion(texto):
        # Confirmar entrega
        orden = confirmar_entrega(db, orden.id)

        # Calcular calificacion
        try:
            calificacion = calcular_calificacion(db, orden.id)
        except Exception as e:
            logger.error(f"Error calculando calificacion: {e}")
            calificacion = None

        # Notificar
        try:
            notificar_entrega_completada(db, orden, calificacion)
        except Exception as e:
            logger.error(f"Error notificando entrega completada: {e}")

    elif es_reporte_problema(texto):
        # Crear incidencia
        incidencia = crear_incidencia(db, orden.id, texto)
        try:
            notificar_incidencia_registrada(db, incidencia)
        except Exception as e:
            logger.error(f"Error notificando incidencia: {e}")

    else:
        await enviar_mensaje_texto(
            telefono,
            f"Tienes el pedido #{orden.id} en tu obra.\n\n"
            f"Responde:\n"
            f"  *OK* → confirmo que recibi todo bien\n"
            f"  *Problema* → reportar un tema con el material"
        )


async def manejar_orden_activa(db, usuario, orden, texto, telefono):
    """Tiene una orden activa (no en_obra). Puede preguntar status o reportar."""
    if es_pregunta_status(texto):
        status_legible = {
            "confirmada": "Confirmada con el proveedor",
            "preparando": "Se esta preparando tu material",
            "en_transito": "Va en camino a tu obra",
            "en_obra": "Ya llego a tu obra, confirma recepcion",
            "con_incidencia": "Tiene un reporte abierto",
        }.get(orden.status, orden.status)

        mensaje = (
            f"*Estado de tu pedido #{orden.id}*\n\n"
            f"Status: {status_legible}\n"
            f"Total: ${orden.total:,.0f} MXN\n"
        )
        if orden.nombre_chofer:
            mensaje += f"Chofer: {orden.nombre_chofer}\n"
        if orden.placas_vehiculo:
            mensaje += f"Placas: {orden.placas_vehiculo}\n"

        await enviar_mensaje_texto(telefono, mensaje)

    elif es_reporte_problema(texto):
        incidencia = crear_incidencia(db, orden.id, texto)
        try:
            notificar_incidencia_registrada(db, incidencia)
        except Exception as e:
            logger.error(f"Error notificando incidencia: {e}")

    else:
        # Si dice algo que no es status ni problema → podria ser un nuevo pedido
        # Preguntamos para no confundir
        await enviar_mensaje_texto(
            telefono,
            f"Tienes el pedido #{orden.id} activo ({orden.status}).\n\n"
            f"Puedo ayudarte con:\n"
            f"  *Status* → ver estado actual\n"
            f"  *Problema* → reportar incidencia\n"
            f"  *Nuevo pedido* → cotizar algo nuevo"
        )


def _detectar_comando_proveedor(texto: str) -> tuple[str | None, int | None, str]:
    """
    Detecta comandos de actualizacion de status del proveedor.
    Comandos: PREPARANDO {id}, EN CAMINO {id}, LISTO {id}, ENTREGADO {id}, PROBLEMA {id} {detalle}
    Retorna (comando, orden_id, detalle).
    """
    texto_upper = texto.strip().upper()
    patrones = [
        (r'^PREPARANDO\s+(\d+)', "preparando"),
        (r'^EN\s*CAMINO\s+(\d+)', "en_transito"),
        (r'^LISTO\s+(\d+)', "en_transito"),
        (r'^ENTREGADO\s+(\d+)', "en_obra"),
        (r'^PROBLEMA\s+(\d+)\s*(.*)', "problema"),
    ]
    for patron, cmd in patrones:
        match = re.match(patron, texto_upper)
        if match:
            orden_id = int(match.group(1))
            detalle = match.group(2).strip() if match.lastindex >= 2 else ""
            return cmd, orden_id, detalle
    return None, None, ""


async def manejar_respuesta_proveedor(db, telefono, texto):
    """
    Un PROVEEDOR respondio por WhatsApp.
    1. Primero revisa si es un comando de actualizacion de orden
    2. Si no, intenta parsear como respuesta a cotizacion
    """
    proveedor = obtener_proveedor_por_telefono(db, telefono)
    if not proveedor:
        return

    logger.info(f"Respuesta de PROVEEDOR {proveedor.nombre}: {texto[:100]}")

    # === Detectar comandos de actualizacion de status de orden ===
    comando, orden_id, detalle = _detectar_comando_proveedor(texto)
    if comando and orden_id:
        from app.models.orden import Orden
        orden = db.query(Orden).filter(
            Orden.id == orden_id,
            Orden.proveedor_id == proveedor.id,
        ).first()

        if not orden:
            await enviar_mensaje_texto(telefono, f"No encontre la orden #{orden_id} asignada a ti.")
            return

        if comando == "problema":
            await enviar_mensaje_texto(telefono, f"Entendido. Le notifico al cliente sobre el problema con la orden #{orden_id}.")
            # Notificar al usuario
            usuario = db.query(Usuario).filter(Usuario.id == orden.usuario_id).first()
            if usuario:
                await enviar_mensaje_texto(
                    usuario.telefono,
                    f"*Aviso del proveedor sobre tu orden #{orden_id}*\n\n"
                    f"El proveedor reporta: {detalle or 'un inconveniente con tu pedido'}.\n"
                    f"Te mantengo informado."
                )
            return

        # Validar transicion
        from app.services.orden_service import TRANSICIONES
        transiciones_validas = TRANSICIONES.get(orden.status, [])
        if comando not in transiciones_validas:
            await enviar_mensaje_texto(
                telefono,
                f"La orden #{orden_id} esta en status '{orden.status}' y no puede moverse a '{comando}'."
            )
            return

        # Actualizar status
        status_anterior = orden.status
        orden.status = comando
        from app.models.seguimiento import SeguimientoEntrega
        seg = SeguimientoEntrega(
            orden_id=orden.id,
            status_anterior=status_anterior,
            status_nuevo=comando,
            origen="proveedor",
            nota=f"Actualizado por proveedor via WhatsApp",
        )
        db.add(seg)
        db.commit()

        await enviar_mensaje_texto(telefono, f"Orden #{orden_id} actualizada a *{comando}*. Gracias.")

        # Notificar al usuario del cambio
        from app.services.notificaciones import enviar_notificacion_por_status
        try:
            enviar_notificacion_por_status(db, orden)
        except Exception as e:
            logger.error(f"Error notificando status a usuario: {e}")
        return

    # === Si no es comando de status, buscar solicitud de cotizacion pendiente ===
    solicitud = db.query(SolicitudProveedor).filter(
        SolicitudProveedor.proveedor_id == proveedor.id,
        SolicitudProveedor.status.in_(["enviada", "recordatorio_enviado"]),
    ).order_by(SolicitudProveedor.created_at.desc()).first()

    if not solicitud:
        await enviar_mensaje_texto(
            telefono,
            f"Gracias por tu mensaje {proveedor.nombre}. No tengo solicitudes pendientes para ti.\n\n"
            f"Si necesitas actualizar una orden, usa:\n"
            f"  *PREPARANDO #* → ya estas preparando\n"
            f"  *EN CAMINO #* → ya salio el envio\n"
            f"  *ENTREGADO #* → ya llego a obra"
        )
        return

    # Parsear respuesta con IA
    contexto = solicitud.mensaje_enviado or ""
    respuesta_parseada = await parsear_respuesta_proveedor(texto, contexto)

    # Registrar respuesta
    registrar_respuesta_proveedor(db, proveedor.id, texto, respuesta_parseada)

    # Confirmar al proveedor
    if respuesta_parseada.get("tiene_precio"):
        precio = respuesta_parseada.get("precio_total", 0)
        await enviar_mensaje_texto(
            telefono,
            f"Recibido, gracias {proveedor.nombre}. Registro tu cotizacion por ${precio:,.0f}. Te aviso si el cliente acepta."
        )
    elif respuesta_parseada.get("sin_stock"):
        await enviar_mensaje_texto(
            telefono,
            f"Entendido, gracias por avisar {proveedor.nombre}."
        )

    # Verificar si ya hay suficientes respuestas para armar comparativa
    pedido_id = solicitud.pedido_id
    if hay_suficientes_respuestas(db, pedido_id):
        # Armar comparativa y enviar al usuario
        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if pedido and pedido.status == "cotizando":
            resultado_comp = generar_comparativa_desde_respuestas(db, pedido_id)
            if resultado_comp:
                from app.models.usuario import Usuario
                usuario = db.query(Usuario).filter(Usuario.id == pedido.usuario_id).first()
                if usuario:
                    opciones = resultado_comp["opciones"]
                    if len(opciones) <= 3:
                        # Botones interactivos (max 3)
                        botones = [{"id": o["id"], "title": o["title"]} for o in opciones]
                        await enviar_mensaje_con_botones(
                            usuario.telefono, resultado_comp["texto"], botones,
                            header="Comparativa de precios"
                        )
                    else:
                        # Lista interactiva (>3 opciones)
                        rows = [{"id": o["id"], "title": o["title"], "description": o["description"]} for o in opciones]
                        await enviar_mensaje_con_lista(
                            usuario.telefono, resultado_comp["texto"],
                            "Ver opciones", [{"title": "Proveedores", "rows": rows}]
                        )
                    pedido.status = "enviado"
                    db.commit()
                    logger.info(f"Comparativa enviada al usuario — Pedido #{pedido_id}")
    else:
        # Enviar notificacion parcial al comprador
        pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
        if pedido and pedido.status == "cotizando":
            from app.models.usuario import Usuario
            from app.services.cotizacion_activa import obtener_resumen_solicitudes
            from app.services.comparativa_activa import generar_mensaje_parcial
            resumen = obtener_resumen_solicitudes(db, pedido_id)
            respondidas = resumen.get("respondidas", 0)
            pendientes = resumen.get("pendientes", 0)
            usuario = db.query(Usuario).filter(Usuario.id == pedido.usuario_id).first()
            if usuario and respondidas > 0:
                msg = generar_mensaje_parcial(pedido_id, respondidas, pendientes)
                await enviar_mensaje_texto(usuario.telefono, msg)


async def manejar_aprobacion(db, usuario, orden_id, nota, telefono):
    """Maneja cuando un aprobador responde APROBAR {id}."""
    aprobacion = db.query(Aprobacion).filter(
        Aprobacion.orden_id == orden_id,
        Aprobacion.status == "pendiente",
    ).first()

    if not aprobacion:
        await enviar_mensaje_texto(telefono, f"No encontre solicitud pendiente para la orden #{orden_id}.")
        return

    resultado = aprobar_aprobacion(db, aprobacion.id, usuario.id, nota)
    if resultado:
        await enviar_mensaje_texto(telefono, f"Orden #{orden_id} aprobada. El solicitante sera notificado.")

        # Mover orden de pendiente_aprobacion → confirmada
        from app.models.orden import Orden
        orden = db.query(Orden).filter(Orden.id == orden_id).first()
        if orden and orden.status == "pendiente_aprobacion":
            from datetime import datetime, timezone
            orden.status = "confirmada"
            orden.confirmada_at = datetime.now(timezone.utc)
            db.commit()
            # Ahora SI notificar al proveedor
            try:
                notificar_orden_confirmada_proveedor(db, orden)
            except Exception as e:
                logger.error(f"Error notificando proveedor post-aprobacion: {e}")

        # Notificar al solicitante
        solicitante = db.query(Usuario).filter(Usuario.id == aprobacion.solicitante_id).first()
        if solicitante:
            msg = componer_mensaje_resultado(resultado, True, usuario.nombre or "")
            await enviar_mensaje_texto(solicitante.telefono, msg)
    else:
        await enviar_mensaje_texto(telefono, f"No se pudo aprobar la orden #{orden_id}. Verifica que tengas permisos suficientes.")


async def manejar_rechazo(db, usuario, orden_id, motivo, telefono):
    """Maneja cuando un aprobador responde RECHAZAR {id} {motivo}."""
    aprobacion = db.query(Aprobacion).filter(
        Aprobacion.orden_id == orden_id,
        Aprobacion.status == "pendiente",
    ).first()

    if not aprobacion:
        await enviar_mensaje_texto(telefono, f"No encontre solicitud pendiente para la orden #{orden_id}.")
        return

    resultado = rechazar_aprobacion(db, aprobacion.id, usuario.id, motivo)
    if resultado:
        await enviar_mensaje_texto(telefono, f"Orden #{orden_id} rechazada.")

        # Cancelar la orden asociada
        from app.models.orden import Orden
        orden = db.query(Orden).filter(Orden.id == orden_id).first()
        if orden and orden.status in ("pendiente_aprobacion", "confirmada"):
            orden.status = "cancelada"
            db.commit()
            logger.info(f"Orden #{orden_id} cancelada por rechazo de aprobacion")

        # Notificar al solicitante
        solicitante = db.query(Usuario).filter(Usuario.id == aprobacion.solicitante_id).first()
        if solicitante:
            msg = componer_mensaje_resultado(resultado, False, usuario.nombre or "")
            await enviar_mensaje_texto(solicitante.telefono, msg)
    else:
        await enviar_mensaje_texto(telefono, f"No se pudo rechazar la orden #{orden_id}. Verifica permisos.")


async def manejar_esperando_cotizaciones(db, usuario, pedido, texto, telefono):
    """
    El usuario tiene un pedido en status 'cotizando' — esta esperando
    respuestas de proveedores. Le informamos el progreso.
    """
    # Procesar cancelacion
    if "cancelar" in texto.lower():
        pedido.status = "cancelado"
        db.commit()
        await enviar_mensaje_texto(
            telefono,
            f"Pedido #{pedido.id} cancelado.\n\nSi necesitas cotizar algo nuevo, mandame tu pedido."
        )
        logger.info(f"Pedido #{pedido.id} cancelado por usuario {telefono}")
        return

    from app.services.cotizacion_activa import obtener_resumen_solicitudes
    resumen = obtener_resumen_solicitudes(db, pedido.id)
    respondidas = resumen.get("respondidas", 0)
    pendientes = resumen.get("pendientes", 0)
    total = resumen.get("total_enviadas", 0)

    await enviar_mensaje_texto(
        telefono,
        f"Tu pedido #{pedido.id} esta en proceso de cotizacion.\n\n"
        f"Contacte a *{total}* proveedores:\n"
        f"  *{respondidas}* ya respondieron\n"
        f"  *{pendientes}* faltan por contestar\n\n"
        f"Te aviso en cuanto tenga la comparativa lista. "
        f"Si quieres cancelar y hacer un nuevo pedido, escribe *cancelar*."
    )


async def manejar_reintento_cotizacion(db, usuario, pedido, texto, telefono):
    """
    El pedido quedo en 'sin_respuesta' (nadie contesto).
    Si el usuario dice SI, reintentamos con proveedores diferentes o zona ampliada.
    Si dice NO o cancelar, cancelamos el pedido.
    """
    texto_lower = texto.lower().strip()

    if any(kw in texto_lower for kw in ["si", "sí", "va", "dale", "ok", "reintentar", "intentar"]):
        # Reintentar: reabrir el pedido y contactar otros proveedores
        pedido.status = "cotizando"
        db.commit()

        # Recuperar la interpretacion original del pedido
        try:
            import ast
            resultado = ast.literal_eval(pedido.pedido_interpretado) if pedido.pedido_interpretado else {}
        except Exception:
            resultado = {}

        if resultado:
            solicitudes = await enviar_solicitudes_a_proveedores(db, pedido.id, resultado)
            if solicitudes:
                await enviar_mensaje_texto(
                    telefono,
                    f"Listo! Contacte a *{len(solicitudes)}* proveedores adicionales para tu pedido #{pedido.id}.\n"
                    f"Te aviso en cuanto respondan."
                )
                return

        # Si no hay mas proveedores
        pedido.status = "sin_proveedores"
        db.commit()
        await enviar_mensaje_texto(
            telefono,
            f"No encontre mas proveedores disponibles en tu zona para este pedido.\n"
            f"Puedes intentar con un pedido nuevo si quieres."
        )

    elif any(kw in texto_lower for kw in ["no", "cancelar", "ya no", "dejalo"]):
        pedido.status = "cancelado"
        db.commit()
        await enviar_mensaje_texto(telefono, f"Pedido #{pedido.id} cancelado. Mandame mensaje cuando necesites cotizar algo.")

    else:
        await enviar_mensaje_texto(
            telefono,
            f"Tu pedido #{pedido.id} — ningun proveedor respondio a tiempo.\n\n"
            f"Responde *SI* para que intente con otros proveedores, o *cancelar* para cancelar."
        )


async def manejar_nuevo_pedido(db, usuario, texto, telefono):
    """
    Flujo de nuevo pedido:
    1. Claude interpreta el mensaje
    2. Si esta completo, Nico contacta proveedores por WhatsApp
    3. Mientras espera, le da al usuario precios de referencia de la BD
    """
    # Feedback instantáneo — el usuario sabe que lo recibimos
    await enviar_mensaje_texto(telefono, "Recibido. Estoy procesando tu pedido...")

    resultado = await interpretar_mensaje(db, telefono, texto)
    status = resultado.get("status", "")

    if status == "completo":
        # Si el usuario mando su ubicacion GPS recientemente, usar esos datos
        # (tienen precedencia sobre lo que Claude extraiga del texto)
        ubicacion_gps = _obtener_ubicacion_reciente(telefono) or {}
        direccion_final = (
            ubicacion_gps.get("direccion_completa")
            or resultado.get("pedido", {}).get("entrega", {}).get("direccion", "")
        )
        municipio_final = (
            ubicacion_gps.get("municipio")
            or resultado.get("pedido", {}).get("entrega", {}).get("municipio", "")
            or _extraer_municipio(
                resultado.get("pedido", {}).get("entrega", {}).get("direccion", "")
            )
        )

        pedido = Pedido(
            usuario_id=usuario.id,
            status="cotizando",
            mensaje_original=texto,
            pedido_interpretado=str(resultado),
            direccion_entrega=direccion_final,
            municipio_entrega=municipio_final,
            latitud_entrega=ubicacion_gps.get("latitud"),
            longitud_entrega=ubicacion_gps.get("longitud"),
            colonia_entrega=ubicacion_gps.get("colonia"),
            codigo_postal_entrega=ubicacion_gps.get("codigo_postal"),
        )
        db.add(pedido)
        db.commit()
        db.refresh(pedido)

        # === COTIZACION ACTIVA: contactar proveedores por WhatsApp ===
        solicitudes = await enviar_solicitudes_a_proveedores(db, pedido.id, resultado)

        if solicitudes:
            # Avisar al usuario que estamos cotizando
            msg = generar_mensaje_esperando(pedido.id, len(solicitudes))
            await enviar_mensaje_texto(telefono, msg)

            # Tambien dar precios de referencia de la BD (instantaneo)
            cotizaciones_bd = generar_cotizaciones(db, resultado)
            if cotizaciones_bd:
                guardar_cotizaciones(db, pedido.id, cotizaciones_bd)
                resumen = resumir_pedido(resultado)
                comparativa = generar_comparativa_simple(cotizaciones_bd, resumen)
                await enviar_mensaje_texto(
                    telefono,
                    f"Mientras esperamos, aqui van precios de *referencia*:\n\n{comparativa}\n\n"
                    f"Cuando los proveedores respondan te mando la cotizacion real."
                )
        else:
            # Sin proveedores con WhatsApp — usar solo BD
            cotizaciones_bd = generar_cotizaciones(db, resultado)
            if cotizaciones_bd:
                guardar_cotizaciones(db, pedido.id, cotizaciones_bd)
                resumen = resumir_pedido(resultado)
                comparativa = generar_comparativa_simple(cotizaciones_bd, resumen)
                await enviar_mensaje_texto(telefono, comparativa)
                # Mensaje de accion claro
                await enviar_mensaje_texto(
                    telefono,
                    "Responde con el *numero* del proveedor que prefieras (ej: *1*) para confirmar tu pedido."
                )
                pedido.status = "enviado"
                db.commit()
            else:
                await enviar_mensaje_texto(
                    telefono,
                    "No encontre proveedores disponibles para esos materiales. Intenta con otros o contactanos directo."
                )
                pedido.status = "cancelado"
                db.commit()

        # NO limpiar conversacion aqui — el contexto se necesita
        # hasta que el comprador seleccione proveedor o cancele.

    elif status == "incompleto":
        mensaje = resultado.get("mensaje_usuario", "")
        if mensaje:
            await enviar_mensaje_texto(telefono, mensaje)

    else:
        mensaje = resultado.get("mensaje_usuario", "")
        if mensaje:
            await enviar_mensaje_texto(telefono, mensaje)


# ============================================================
# UTILIDADES
# ============================================================

async def _reverse_geocode(lat, lng) -> str:
    """
    Convierte coordenadas GPS a direccion legible usando Nominatim (OpenStreetMap).
    Gratis, sin API key. Respeta rate-limit con User-Agent.
    """
    try:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json",
            "addressdetails": 1,
            "accept-language": "es",
        }
        headers = {"User-Agent": "ObraYa/1.0 (contacto@obraya.com)"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params, headers=headers)
            if response.status_code == 200:
                data = response.json()
                direccion = data.get("display_name", "")
                logger.info(f"Reverse geocode: ({lat}, {lng}) → {direccion[:80]}")
                return direccion
    except Exception as e:
        logger.error(f"Error en reverse geocoding: {e}")

    return ""
