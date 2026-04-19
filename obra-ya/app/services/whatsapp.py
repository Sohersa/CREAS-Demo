"""
Servicio de integracion con WhatsApp Cloud API (Meta).
Envia y recibe mensajes via la API oficial de WhatsApp Business.

Si WHATSAPP_PROVIDER=twilio, las funciones principales delegan a whatsapp_twilio.
"""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v21.0"


def _using_twilio():
    """Devuelve True si el proveedor configurado es Twilio."""
    return settings.WHATSAPP_PROVIDER.lower() == "twilio"


def _usuario_prefiere_audio(telefono: str) -> bool:
    """
    Devuelve True si el usuario tiene la preferencia 'prefiere_audio' = 'si'.
    Se consulta via las preferencias guardadas por el memory tool.
    """
    try:
        from app.database import SessionLocal
        from app.models.usuario import Usuario
        from app.models.preferencia import PreferenciaUsuario
        db = SessionLocal()
        try:
            u = db.query(Usuario).filter(Usuario.telefono == telefono).first()
            if not u:
                return False
            p = db.query(PreferenciaUsuario).filter(
                PreferenciaUsuario.usuario_id == u.id,
                PreferenciaUsuario.clave == "prefiere_audio",
            ).first()
            return bool(p and (p.valor or "").lower() in ("si", "yes", "true", "1"))
        finally:
            db.close()
    except Exception:
        return False


async def enviar_mensaje_texto(telefono: str, mensaje: str) -> dict:
    """
    Envia un mensaje de texto por WhatsApp.
    telefono: numero con codigo de pais (ej: 5213312345678)
    mensaje: texto del mensaje (soporta formato WhatsApp *negritas* etc)

    Si el proveedor principal falla, intenta con el otro automaticamente.
    """
    # Si el usuario prefiere audio, intentar TTS primero
    if _usuario_prefiere_audio(telefono) and len(mensaje) > 20:
        try:
            from app.services.tts import responder_con_voz
            if await responder_con_voz(telefono, mensaje):
                return {"audio_sent": True}
        except Exception as e:
            logger.warning(f"TTS fallo, cayendo a texto: {e}")

    resultado = await _enviar_con_provider(telefono, mensaje, _using_twilio())

    # Si el error es critico (token expirado/invalido), intentar fallback
    # solo si el otro provider esta configurado con credenciales distintas
    if "error" in resultado:
        # No reintentar en mismo provider si el token esta mal
        if resultado.get("critical"):
            logger.error(
                f"Error critico de WhatsApp ({resultado.get('error')}). "
                f"Revisa /admin/api/whatsapp/health"
            )
            return resultado

        # Fallback si hay otro provider configurado
        otro_configurado = (
            settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN
            if not _using_twilio()
            else settings.WHATSAPP_TOKEN and settings.WHATSAPP_PHONE_ID
        )
        if otro_configurado:
            logger.warning(f"Provider principal fallo, intentando fallback para {telefono}")
            resultado_fallback = await _enviar_con_provider(
                telefono, mensaje, not _using_twilio()
            )
            if "error" not in resultado_fallback:
                return resultado_fallback
            logger.error(f"Ambos providers fallaron para {telefono}")
        else:
            logger.warning(
                f"Envio fallo para {telefono} y no hay provider fallback configurado"
            )

    return resultado


async def _enviar_con_provider(telefono: str, mensaje: str, use_twilio: bool) -> dict:
    """Envia mensaje usando el provider especificado."""
    if use_twilio:
        from app.services.whatsapp_twilio import enviar_mensaje_texto as twilio_enviar
        return await twilio_enviar(telefono, mensaje)

    url = f"{WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    if len(mensaje) > 4000:
        partes = partir_mensaje(mensaje, 4000)
        resultados = []
        for parte in partes:
            resultado = await _enviar_texto(url, headers, telefono, parte)
            resultados.append(resultado)
        return resultados[-1]

    return await _enviar_texto(url, headers, telefono, mensaje)


async def enviar_mensaje_template(telefono: str, template_name: str, parametros: list[str] = None) -> dict:
    """
    Envia un mensaje usando una plantilla aprobada de Meta WhatsApp.
    REQUERIDO para iniciar conversaciones con usuarios que no han escrito primero.

    telefono: numero con codigo de pais
    template_name: nombre de la plantilla aprobada en Meta Business
    parametros: lista de strings para los {{1}}, {{2}}, etc del template
    """
    from app.utils.telefono import normalizar_telefono_mx
    telefono = normalizar_telefono_mx(telefono)

    url = f"{WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    template_obj = {
        "name": template_name,
        "language": {"code": "es_MX"},
    }

    if parametros:
        template_obj["components"] = [{
            "type": "body",
            "parameters": [{"type": "text", "text": p} for p in parametros],
        }]

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telefono,
        "type": "template",
        "template": template_obj,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info(f"[Template:{template_name}] Mensaje enviado a {telefono}")
            return response.json()
        else:
            logger.error(f"[Template:{template_name}] Error: {response.status_code} - {response.text}")
            return {"error": response.text, "status_code": response.status_code}


async def _enviar_texto(url: str, headers: dict, telefono: str, mensaje: str) -> dict:
    """Envio interno de un solo mensaje de texto libre (solo funciona dentro de ventana 24h)."""
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telefono,
        "type": "text",
        "text": {"body": mensaje}
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info(f"Mensaje enviado a {telefono}")
            return response.json()

        # Categorizar errores para mejor diagnostico
        try:
            err = response.json().get("error", {})
        except Exception:
            err = {}
        codigo = err.get("code")
        subcodigo = err.get("error_subcode")
        meta_msg = err.get("message", response.text)[:200]

        # Errores de token — criticos, afectan todos los envios
        if response.status_code == 401 or codigo == 190:
            if subcodigo == 463:
                logger.critical(
                    f"TOKEN WHATSAPP EXPIRADO — renuevalo en Meta Business. "
                    f"Ver /admin/api/whatsapp/health para instrucciones. Msg: {meta_msg}"
                )
                return {"error": "token_expired", "detail": meta_msg, "critical": True}
            logger.critical(f"TOKEN WHATSAPP INVALIDO (code=190): {meta_msg}")
            return {"error": "token_invalid", "detail": meta_msg, "critical": True}

        # Destinatario no es tester (dev) o no acepta mensajes
        if codigo == 131026:
            logger.warning(f"Destinatario {telefono} no es tester o bloqueo mensajes")
            return {"error": "recipient_not_allowed", "detail": meta_msg}

        # Fuera de ventana 24h — requiere template
        if codigo == 131047:
            logger.info(f"Fuera de ventana 24h para {telefono}, requiere template")
            return {"error": "requires_template", "detail": meta_msg}

        # Rate limit
        if response.status_code == 429 or codigo == 80007:
            logger.warning(f"Rate limit de WhatsApp para {telefono}")
            return {"error": "rate_limit", "detail": meta_msg}

        # Otros errores
        logger.error(
            f"Error WhatsApp status={response.status_code} code={codigo} "
            f"subcode={subcodigo} msg={meta_msg}"
        )
        return {"error": meta_msg, "status_code": response.status_code, "code": codigo}


async def marcar_como_leido(message_id: str) -> dict:
    """Marca un mensaje como leido (doble palomita azul)."""
    if _using_twilio():
        from app.services.whatsapp_twilio import marcar_como_leido as twilio_marcar
        return await twilio_marcar(message_id)

    url = f"{WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        return response.json()


async def descargar_audio(media_id: str, source: str = "") -> bytes:
    """
    Descarga un archivo de audio de WhatsApp (para mensajes de voz).
    source: "meta" o "twilio" — indica de donde vino el mensaje.
    Si no se especifica, usa la config WHATSAPP_PROVIDER.
    """
    use_twilio = source == "twilio" if source else _using_twilio()

    if use_twilio:
        from app.services.whatsapp_twilio import descargar_audio as twilio_descargar
        return await twilio_descargar(media_id)

    # Paso 1: Obtener URL del archivo
    url_media = f"{WHATSAPP_API_URL}/{media_id}"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url_media, headers=headers)
        media_data = response.json()
        download_url = media_data.get("url")

        if not download_url:
            logger.error(f"No se pudo obtener URL del audio: {media_data}")
            return b""

        # Paso 2: Descargar el archivo
        response = await client.get(download_url, headers=headers)
        return response.content


def parsear_webhook(body: dict) -> dict | None:
    """
    Parsea el cuerpo del webhook de WhatsApp y extrae la info relevante.
    Devuelve dict con: telefono, nombre, tipo_mensaje, contenido, message_id
    O None si no es un mensaje valido.
    """
    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return None

        mensaje = messages[0]
        contacto = value.get("contacts", [{}])[0]

        resultado = {
            "telefono": mensaje.get("from", ""),
            "nombre": contacto.get("profile", {}).get("name", ""),
            "message_id": mensaje.get("id", ""),
            "timestamp": mensaje.get("timestamp", ""),
            "source": "meta",
        }

        tipo = mensaje.get("type", "")

        if tipo == "text":
            resultado["tipo_mensaje"] = "texto"
            resultado["contenido"] = mensaje.get("text", {}).get("body", "")
        elif tipo == "audio":
            resultado["tipo_mensaje"] = "audio"
            resultado["contenido"] = mensaje.get("audio", {}).get("id", "")
        elif tipo == "image":
            resultado["tipo_mensaje"] = "imagen"
            resultado["contenido"] = mensaje.get("image", {}).get("id", "")
        elif tipo == "location":
            resultado["tipo_mensaje"] = "ubicacion"
            loc = mensaje.get("location", {})
            resultado["contenido"] = {
                "latitude": loc.get("latitude"),
                "longitude": loc.get("longitude"),
                "name": loc.get("name", ""),
                "address": loc.get("address", ""),
            }
        elif tipo == "interactive":
            # Botones o listas interactivas
            interactive = mensaje.get("interactive", {})
            if interactive.get("type") == "button_reply":
                resultado["tipo_mensaje"] = "texto"
                btn = interactive.get("button_reply", {})
                resultado["contenido"] = btn.get("title", "")
                resultado["button_id"] = btn.get("id", "")
            elif interactive.get("type") == "list_reply":
                resultado["tipo_mensaje"] = "texto"
                lst = interactive.get("list_reply", {})
                resultado["contenido"] = lst.get("title", "")
                resultado["button_id"] = lst.get("id", "")
            else:
                resultado["tipo_mensaje"] = tipo
                resultado["contenido"] = ""
        else:
            resultado["tipo_mensaje"] = tipo
            resultado["contenido"] = ""

        return resultado

    except (IndexError, KeyError) as e:
        logger.error(f"Error parseando webhook: {e}")
        return None


async def enviar_mensaje_con_botones(
    telefono: str, texto_body: str, botones: list[dict], header: str = ""
) -> dict:
    """
    Envia mensaje interactivo con botones (max 3).
    botones: [{"id": "btn_1", "title": "Opción 1"}, ...]
    title max 20 chars por botón.
    Fallback a texto plano si falla o es Twilio.
    """
    if _using_twilio():
        # Twilio no soporta interactive — fallback a texto con opciones
        opciones = "\n".join(f"  *{b['title']}*" for b in botones)
        return await enviar_mensaje_texto(telefono, f"{texto_body}\n\n{opciones}")

    from app.utils.telefono import normalizar_telefono_mx
    telefono = normalizar_telefono_mx(telefono)

    url = f"{WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    interactive = {
        "type": "button",
        "body": {"text": texto_body[:1024]},
        "action": {
            "buttons": [
                {"type": "reply", "reply": {"id": b["id"], "title": b["title"][:20]}}
                for b in botones[:3]
            ]
        }
    }
    if header:
        interactive["header"] = {"type": "text", "text": header[:60]}

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telefono,
        "type": "interactive",
        "interactive": interactive,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info(f"[Botones] Mensaje enviado a {telefono}")
            return response.json()
        else:
            logger.warning(f"[Botones] Fallo ({response.status_code}), fallback a texto para {telefono}")
            opciones = "\n".join(f"  *{b['title']}*" for b in botones)
            return await enviar_mensaje_texto(telefono, f"{texto_body}\n\n{opciones}")


async def enviar_mensaje_con_lista(
    telefono: str, texto_body: str, texto_boton: str, secciones: list[dict]
) -> dict:
    """
    Envia mensaje interactivo con lista desplegable (max 10 opciones).
    texto_boton: texto del botón que abre la lista (max 20 chars)
    secciones: [{"title": "Opciones", "rows": [{"id": "opt_1", "title": "Opción 1", "description": "..."}]}]
    Fallback a texto plano si falla o es Twilio.
    """
    if _using_twilio():
        lineas = []
        for sec in secciones:
            for row in sec.get("rows", []):
                desc = f" — {row['description']}" if row.get("description") else ""
                lineas.append(f"  *{row['title']}*{desc}")
        return await enviar_mensaje_texto(telefono, f"{texto_body}\n\n" + "\n".join(lineas))

    from app.utils.telefono import normalizar_telefono_mx
    telefono = normalizar_telefono_mx(telefono)

    url = f"{WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": telefono,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": texto_body[:1024]},
            "action": {
                "button": texto_boton[:20],
                "sections": secciones,
            }
        }
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info(f"[Lista] Mensaje enviado a {telefono}")
            return response.json()
        else:
            logger.warning(f"[Lista] Fallo ({response.status_code}), fallback a texto para {telefono}")
            lineas = []
            for sec in secciones:
                for row in sec.get("rows", []):
                    desc = f" — {row['description']}" if row.get("description") else ""
                    lineas.append(f"  *{row['title']}*{desc}")
            return await enviar_mensaje_texto(telefono, f"{texto_body}\n\n" + "\n".join(lineas))


async def descargar_imagen(media_id: str, source: str = "") -> bytes:
    """
    Descarga una imagen de WhatsApp (para fotos de listas de materiales).
    Mismo patrón que descargar_audio.
    """
    use_twilio = source == "twilio" if source else _using_twilio()

    if use_twilio:
        from app.services.whatsapp_twilio import descargar_audio as twilio_descargar
        return await twilio_descargar(media_id)

    url_media = f"{WHATSAPP_API_URL}/{media_id}"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url_media, headers=headers)
        media_data = response.json()
        download_url = media_data.get("url")

        if not download_url:
            logger.error(f"No se pudo obtener URL de imagen: {media_data}")
            return b""

        response = await client.get(download_url, headers=headers)
        return response.content


def partir_mensaje(texto: str, max_chars: int = 4000) -> list[str]:
    """Parte un mensaje largo en pedazos respetando saltos de linea."""
    if len(texto) <= max_chars:
        return [texto]

    partes = []
    while texto:
        if len(texto) <= max_chars:
            partes.append(texto)
            break

        # Buscar el ultimo salto de linea antes del limite
        corte = texto.rfind("\n", 0, max_chars)
        if corte == -1:
            corte = max_chars

        partes.append(texto[:corte])
        texto = texto[corte:].lstrip("\n")

    return partes
