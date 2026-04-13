"""
Servicio de cotizacion activa — Nico contacta proveedores por WhatsApp.

Cuando un usuario pide materiales, este servicio:
1. Selecciona los ~20 proveedores mas relevantes (por categoria + cercania)
2. Les manda WhatsApp pidiendo cotizacion
3. Espera respuestas
4. Insiste a los que no contestan
5. Cuando hay suficientes respuestas, arma la comparativa

NO es un catalogo de precios estaticos. Son cotizaciones en tiempo real.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.proveedor import Proveedor
from app.models.vendedor import Vendedor
from app.models.solicitud_proveedor import SolicitudProveedor
from app.models.pedido import Pedido
from app.services.whatsapp import enviar_mensaje_texto, enviar_mensaje_template
from app.utils.telefono import normalizar_telefono_mx

logger = logging.getLogger(__name__)

# Config
MAX_PROVEEDORES_POR_PEDIDO = 20
TIMEOUT_RESPUESTA_MINUTOS = 30
MINIMO_RESPUESTAS_PARA_COMPARATIVA = 1


# ============================================================
# ZONAS METROPOLITANAS — ciudades cercanas que pueden atenderse mutuamente
# ============================================================

ZONAS_METROPOLITANAS = {
    "guadalajara": ["guadalajara", "zapopan", "tlaquepaque", "tonala", "tlajomulco", "el salto", "ixtlahuacan", "juanacatlan"],
    "monterrey": ["monterrey", "san pedro garza garcia", "san nicolas", "apodaca", "guadalupe", "santa catarina", "escobedo", "garcia"],
    "cdmx": ["ciudad de mexico", "cdmx", "naucalpan", "tlalnepantla", "ecatepec", "coacalco", "cuautitlan", "atizapan", "huixquilucan"],
    "mazatlan": ["mazatlan"],
    "culiacan": ["culiacan", "navolato"],
    "leon": ["leon", "silao", "guanajuato"],
    "queretaro": ["queretaro", "corregidora", "el marques", "huimilpan"],
    "puebla": ["puebla", "cholula", "san andres cholula", "cuautlancingo"],
    "merida": ["merida", "kanasín", "uman", "conkal", "progreso"],
    "tijuana": ["tijuana", "rosarito", "tecate"],
    "aguascalientes": ["aguascalientes", "jesus maria", "san francisco de los romo"],
}


def _misma_zona_metropolitana(mun1: str, mun2: str) -> bool:
    """Check if two municipios are in the same metropolitan zone."""
    mun1 = mun1.lower().strip()
    mun2 = mun2.lower().strip()
    for zona, municipios in ZONAS_METROPOLITANAS.items():
        if mun1 in municipios and mun2 in municipios:
            return True
    return False


# ============================================================
# 1. SELECCIONAR PROVEEDORES
# ============================================================

def seleccionar_proveedores(db: Session, pedido: dict, max_proveedores: int = MAX_PROVEEDORES_POR_PEDIDO) -> list[Proveedor]:
    """
    Selecciona los proveedores mas relevantes para un pedido.
    Criterios:
      - Tienen las categorias de los items del pedido
      - Estan activos
      - Tienen WhatsApp
      - Ordenados por: calificacion > pedidos cumplidos > tiempo de respuesta
    """
    # Extraer categorias del pedido
    items = pedido.get("pedido", {}).get("items", [])
    categorias_pedido = set()
    for item in items:
        cat = item.get("categoria", "").lower()
        if cat:
            categorias_pedido.add(cat)

    if not categorias_pedido:
        return []

    # Buscar proveedores activos con WhatsApp
    proveedores = db.query(Proveedor).filter(
        Proveedor.activo == True,
        Proveedor.telefono_whatsapp != None,
        Proveedor.telefono_whatsapp != "",
    ).order_by(
        Proveedor.calificacion.desc(),
        Proveedor.pedidos_cumplidos.desc(),
        Proveedor.tiempo_respuesta_promedio.asc(),
    ).all()

    # Filtrar por categorias (el proveedor maneja al menos 1 categoria del pedido)
    proveedores_relevantes = []
    for prov in proveedores:
        try:
            cats_proveedor = set(c.lower().strip() for c in json.loads(prov.categorias)) if prov.categorias else set()
        except (json.JSONDecodeError, TypeError):
            cats_proveedor = set()

        if cats_proveedor & categorias_pedido:  # Interseccion
            proveedores_relevantes.append(prov)

    # Geographic filtering: prioritize providers near the delivery location
    municipio_entrega = (pedido.get("pedido", {}).get("municipio_entrega") or "").strip().lower()

    scored = []
    for p in proveedores_relevantes:
        score = p.calificacion or 3.0
        municipio_prov = (p.municipio or "").strip().lower()

        # Geographic bonus: same city gets big boost
        if municipio_entrega and municipio_prov:
            if municipio_entrega == municipio_prov:
                score += 5.0  # Strong preference for same city
            elif _misma_zona_metropolitana(municipio_entrega, municipio_prov):
                score += 3.0  # Nearby cities in same metro area
            else:
                score -= 2.0  # Penalize distant providers

        scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [p for _, p in scored[:max_proveedores]]


# ============================================================
# 2. COMPONER MENSAJE PARA EL PROVEEDOR
# ============================================================

def componer_mensaje_cotizacion(pedido: dict, nombre_proveedor: str) -> str:
    """
    Compone el mensaje que Nico le manda al proveedor pidiendo cotizacion.
    Tono profesional pero directo — como un comprador real.
    """
    items = pedido.get("pedido", {}).get("items", [])
    entrega = pedido.get("pedido", {}).get("entrega", {})

    # Armar lista de materiales
    lineas_material = []
    for item in items:
        cantidad = item.get("cantidad", "?")
        unidad = item.get("unidad", "")
        producto = item.get("producto", "Material")
        specs = item.get("especificaciones", {})

        linea = f"  - {cantidad} {unidad} de {producto}"
        if specs:
            detalles = ", ".join(f"{v}" for v in specs.values() if v)
            if detalles:
                linea += f" ({detalles})"
        lineas_material.append(linea)

    materiales_texto = "\n".join(lineas_material)

    # Datos de entrega
    direccion = entrega.get("direccion", "")
    fecha = entrega.get("fecha", "")
    horario = entrega.get("horario", "")

    entrega_texto = ""
    if direccion:
        entrega_texto += f"Entrega en: {direccion}\n"
    if fecha:
        entrega_texto += f"Fecha: {fecha}\n"
    if horario:
        entrega_texto += f"Horario: {horario}\n"

    mensaje = (
        f"Hola, buen dia. Soy Nico de ObraYa.\n\n"
        f"Tengo un cliente que necesita los siguientes materiales:\n\n"
        f"{materiales_texto}\n\n"
    )

    if entrega_texto:
        mensaje += f"{entrega_texto}\n"

    # Include delivery municipio/address so provider knows WHERE
    municipio_entrega = pedido.get("pedido", {}).get("municipio_entrega", "")
    direccion_entrega = pedido.get("pedido", {}).get("direccion_entrega", "")
    if municipio_entrega:
        mensaje += f"\n📍 Entrega en: {municipio_entrega}"
    if direccion_entrega:
        mensaje += f"\n🏗️ Dirección: {direccion_entrega}"
    if municipio_entrega or direccion_entrega:
        mensaje += "\n\n"

    mensaje += (
        f"Me podrias pasar tu mejor precio con flete incluido?\n"
        f"Si puedes indicar tiempo de entrega, mejor.\n\n"
        f"Gracias!"
    )

    return mensaje


def extraer_resumen_materiales(pedido: dict) -> str:
    """Extrae un resumen corto de materiales para usar como parametro de template."""
    items = pedido.get("pedido", {}).get("items", [])
    partes = []
    for item in items:
        cantidad = item.get("cantidad", "?")
        unidad = item.get("unidad", "")
        producto = item.get("producto", "Material")
        partes.append(f"{cantidad} {unidad} de {producto}")

    resumen = ", ".join(partes)

    # Agregar info de entrega si hay
    entrega = pedido.get("pedido", {}).get("entrega", {})
    direccion = entrega.get("direccion", "")
    if direccion:
        resumen += f"\nEntrega en: {direccion}"

    return resumen


def componer_recordatorio(nombre_proveedor: str, pedido_resumen: str) -> str:
    """Mensaje de follow-up para proveedores que no han respondido."""
    return (
        f"Hola, soy Nico de ObraYa.\n\n"
        f"Te habia mandado una solicitud de cotizacion hace rato:\n"
        f"{pedido_resumen}\n\n"
        f"Todavia tienes chance de cotizar?\n"
        f"Si no manejas algun material, no hay problema, dime."
    )


# ============================================================
# 3. ENVIAR SOLICITUDES
# ============================================================

async def enviar_solicitudes_a_proveedores(
    db: Session,
    pedido_id: int,
    pedido: dict,
) -> list[SolicitudProveedor]:
    """
    Selecciona proveedores y les manda WhatsApp pidiendo cotizacion.
    Retorna las solicitudes creadas.
    """
    proveedores = seleccionar_proveedores(db, pedido)

    if not proveedores:
        logger.warning(f"Pedido #{pedido_id}: no se encontraron proveedores relevantes")
        return []

    solicitudes = []
    ahora = datetime.now(timezone.utc)

    for prov in proveedores:
        mensaje = componer_mensaje_cotizacion(pedido, prov.nombre)

        # Crear registro de solicitud
        solicitud = SolicitudProveedor(
            pedido_id=pedido_id,
            proveedor_id=prov.id,
            status="enviada",
            mensaje_enviado=mensaje,
            enviada_at=ahora,
        )
        db.add(solicitud)
        db.flush()

        # Enviar WhatsApp — prefer vendor's best salesperson, fallback to main number
        try:
            vendedor = db.query(Vendedor).filter(
                Vendedor.proveedor_id == prov.id,
                Vendedor.activo == True,
                Vendedor.disponible == True,
            ).order_by(Vendedor.tiempo_respuesta_promedio.asc().nullslast()).first()

            telefono_destino = vendedor.telefono_whatsapp if vendedor else prov.telefono_whatsapp
            telefono = normalizar_telefono_mx(telefono_destino)
            resumen = extraer_resumen_materiales(pedido)

            # Intentar con template primero (funciona fuera de ventana 24h)
            resultado = await enviar_mensaje_template(
                telefono, "solicitud_cotizacion", [resumen]
            )

            # Si template falla (no aprobado aun), intentar texto libre como fallback
            if "error" in resultado:
                logger.warning(f"Template fallo para {prov.nombre}, intentando texto libre")
                resultado = await enviar_mensaje_texto(telefono, mensaje)

            if "error" not in resultado:
                wamid = resultado.get("messages", [{}])[0].get("id", "")
                solicitud.whatsapp_msg_id = wamid
                logger.info(f"Solicitud enviada a {prov.nombre} ({telefono}) — Pedido #{pedido_id} — wamid={wamid}")
            else:
                logger.error(f"Fallo envio a {prov.nombre}: {resultado}")
                solicitud.status = "error_envio"
                solicitud.error_envio = str(resultado.get("error", ""))[:500]
        except Exception as e:
            logger.error(f"Error enviando a {prov.nombre}: {e}")
            solicitud.status = "error_envio"

        solicitudes.append(solicitud)

    db.commit()
    logger.info(f"Pedido #{pedido_id}: {len(solicitudes)} solicitudes enviadas a proveedores")
    return solicitudes


# ============================================================
# 4. ENVIAR RECORDATORIOS
# ============================================================

async def enviar_recordatorios(db: Session, pedido_id: int, pedido_resumen: str = ""):
    """
    Envia recordatorios a proveedores que no han respondido.
    Se llama periodicamente o despues de un timeout.
    """
    solicitudes_pendientes = db.query(SolicitudProveedor).filter(
        SolicitudProveedor.pedido_id == pedido_id,
        SolicitudProveedor.status.in_(["enviada", "recordatorio_enviado"]),
        SolicitudProveedor.recordatorios_enviados < 2,  # Max 2 recordatorios
    ).all()

    ahora = datetime.now(timezone.utc)

    for sol in solicitudes_pendientes:
        # Solo insistir si ya pasaron al menos 10 minutos
        if sol.enviada_at:
            tiempo_desde_envio = ahora - sol.enviada_at.replace(tzinfo=timezone.utc)
            if tiempo_desde_envio.total_seconds() < 600:  # 10 minutos
                continue

        proveedor = db.query(Proveedor).filter(Proveedor.id == sol.proveedor_id).first()
        if not proveedor:
            continue

        mensaje = componer_recordatorio(proveedor.nombre, pedido_resumen)

        try:
            await enviar_mensaje_texto(proveedor.telefono_whatsapp, mensaje)
            sol.status = "recordatorio_enviado"
            sol.recordatorio_at = ahora
            sol.recordatorios_enviados = (sol.recordatorios_enviados or 0) + 1
            logger.info(f"Recordatorio #{sol.recordatorios_enviados} enviado a {proveedor.nombre}")
        except Exception as e:
            logger.error(f"Error enviando recordatorio a {proveedor.nombre}: {e}")

    db.commit()


# ============================================================
# 5. PROCESAR RESPUESTA DE PROVEEDOR
# ============================================================

def registrar_respuesta_proveedor(
    db: Session,
    proveedor_id: int,
    texto_respuesta: str,
    respuesta_parseada: dict,
) -> SolicitudProveedor | None:
    """
    Registra la respuesta de un proveedor a una solicitud.
    respuesta_parseada viene del agente Claude que interpreto el mensaje.
    """
    # Buscar la solicitud pendiente mas reciente de este proveedor
    solicitud = db.query(SolicitudProveedor).filter(
        SolicitudProveedor.proveedor_id == proveedor_id,
        SolicitudProveedor.status.in_(["enviada", "recordatorio_enviado"]),
    ).order_by(SolicitudProveedor.created_at.desc()).first()

    if not solicitud:
        logger.warning(f"Proveedor #{proveedor_id} respondio pero no tiene solicitud pendiente")
        return None

    ahora = datetime.now(timezone.utc)

    # Actualizar solicitud
    solicitud.status = "respondida"
    solicitud.respuesta_cruda = texto_respuesta
    solicitud.respondida_at = ahora

    # Calcular tiempo de respuesta
    if solicitud.enviada_at:
        delta = ahora - solicitud.enviada_at.replace(tzinfo=timezone.utc)
        solicitud.tiempo_respuesta_minutos = int(delta.total_seconds() / 60)

    # Datos parseados
    if respuesta_parseada:
        solicitud.precio_total = respuesta_parseada.get("precio_total")
        solicitud.precio_desglose = json.dumps(respuesta_parseada.get("desglose", []), ensure_ascii=False)
        solicitud.tiempo_entrega = respuesta_parseada.get("tiempo_entrega", "")
        solicitud.incluye_flete = respuesta_parseada.get("incluye_flete", False)
        solicitud.costo_flete = respuesta_parseada.get("costo_flete", 0)
        solicitud.notas = respuesta_parseada.get("notas", "")
        solicitud.disponibilidad = respuesta_parseada.get("disponibilidad", "")

        # Si dijo que no tiene stock
        if respuesta_parseada.get("sin_stock"):
            solicitud.status = "rechazada"
            solicitud.disponibilidad = "sin stock"

    db.commit()

    logger.info(
        f"Respuesta registrada — Proveedor #{proveedor_id}, "
        f"Pedido #{solicitud.pedido_id}, "
        f"Precio: ${solicitud.precio_total or 'N/A'}, "
        f"Tiempo: {solicitud.tiempo_respuesta_minutos}min"
    )

    # === ALIMENTAR BASE DE DATOS MAESTRA DE PRECIOS ===
    try:
        from app.services.precio_historico_service import registrar_precios_desde_respuesta
        proveedor = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
        nombre_prov = proveedor.nombre if proveedor else f"Proveedor #{proveedor_id}"
        registrar_precios_desde_respuesta(
            db=db,
            proveedor_id=proveedor_id,
            proveedor_nombre=nombre_prov,
            respuesta_parseada=respuesta_parseada,
            pedido_id=solicitud.pedido_id,
            solicitud_id=solicitud.id,
        )
    except Exception as e:
        logger.error(f"Error registrando precios historicos: {e}")

    return solicitud


# ============================================================
# 6. MARCAR TIMEOUT (SIN RESPUESTA)
# ============================================================

def marcar_sin_respuesta(db: Session, pedido_id: int):
    """
    Marca como sin_respuesta las solicitudes que excedieron el timeout.
    Se llama cuando decidimos armar la comparativa con lo que tenemos.
    """
    solicitudes_pendientes = db.query(SolicitudProveedor).filter(
        SolicitudProveedor.pedido_id == pedido_id,
        SolicitudProveedor.status.in_(["enviada", "recordatorio_enviado"]),
    ).all()

    for sol in solicitudes_pendientes:
        sol.status = "sin_respuesta"

    db.commit()
    logger.info(f"Pedido #{pedido_id}: {len(solicitudes_pendientes)} solicitudes marcadas sin_respuesta")


# ============================================================
# 7. VERIFICAR SI HAY SUFICIENTES RESPUESTAS
# ============================================================

def obtener_respuestas(db: Session, pedido_id: int) -> list[SolicitudProveedor]:
    """Respuestas recibidas para un pedido."""
    return db.query(SolicitudProveedor).filter(
        SolicitudProveedor.pedido_id == pedido_id,
        SolicitudProveedor.status == "respondida",
    ).order_by(SolicitudProveedor.precio_total.asc()).all()


def hay_suficientes_respuestas(db: Session, pedido_id: int) -> bool:
    """Verifica si ya hay suficientes respuestas para armar comparativa."""
    respuestas = obtener_respuestas(db, pedido_id)
    return len(respuestas) >= MINIMO_RESPUESTAS_PARA_COMPARATIVA


def tiempo_agotado(db: Session, pedido_id: int) -> bool:
    """Verifica si ya paso el timeout desde que se enviaron las solicitudes."""
    primera = db.query(SolicitudProveedor).filter(
        SolicitudProveedor.pedido_id == pedido_id,
    ).order_by(SolicitudProveedor.enviada_at.asc()).first()

    if not primera or not primera.enviada_at:
        return False

    ahora = datetime.now(timezone.utc)
    enviada = primera.enviada_at.replace(tzinfo=timezone.utc)
    transcurrido = (ahora - enviada).total_seconds() / 60

    return transcurrido >= TIMEOUT_RESPUESTA_MINUTOS


def obtener_resumen_solicitudes(db: Session, pedido_id: int) -> dict:
    """Resumen del estado de solicitudes para un pedido."""
    solicitudes = db.query(SolicitudProveedor).filter(
        SolicitudProveedor.pedido_id == pedido_id,
    ).all()

    return {
        "total_enviadas": len(solicitudes),
        "respondidas": sum(1 for s in solicitudes if s.status == "respondida"),
        "pendientes": sum(1 for s in solicitudes if s.status in ("enviada", "recordatorio_enviado")),
        "sin_respuesta": sum(1 for s in solicitudes if s.status == "sin_respuesta"),
        "rechazadas": sum(1 for s in solicitudes if s.status == "rechazada"),
    }
