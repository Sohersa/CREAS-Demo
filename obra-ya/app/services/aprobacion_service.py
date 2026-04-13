"""
Servicio de aprobaciones corporativas.
Maneja el flujo: residente pide material → compras/director aprueba → se procesa la orden.

En construccion, el residente de obra NO es quien aprueba compras.
Este servicio conecta ambos roles via WhatsApp.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.models.empresa import Empresa
from app.models.miembro_empresa import MiembroEmpresa
from app.models.aprobacion import Aprobacion
from app.models.orden import Orden
from app.models.usuario import Usuario
from app.models.presupuesto import PresupuestoObra, PartidaPresupuesto
from app.services.whatsapp import enviar_mensaje_texto, enviar_mensaje_con_botones

logger = logging.getLogger(__name__)

EXPIRACION_HORAS = 24
MAX_RECORDATORIOS = 3


def necesita_aprobacion(db: Session, usuario_id: int, monto: float) -> bool:
    """
    Verifica si el usuario pertenece a una empresa que requiere aprobacion
    y si el monto supera el limite de compra sin autorizacion.

    Returns True si se necesita aprobacion, False si puede proceder directo.
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.empresa_id:
        return False

    empresa = db.query(Empresa).filter(
        Empresa.id == usuario.empresa_id,
        Empresa.activo == True,
    ).first()
    if not empresa or not empresa.requiere_aprobacion:
        return False

    # Si el monto esta por debajo del limite, no necesita aprobacion
    if empresa.limite_sin_aprobacion and monto <= empresa.limite_sin_aprobacion:
        return False

    # Verificar si el usuario mismo tiene permiso de aprobar por este monto
    miembro = db.query(MiembroEmpresa).filter(
        MiembroEmpresa.empresa_id == empresa.id,
        MiembroEmpresa.usuario_id == usuario_id,
        MiembroEmpresa.activo == True,
    ).first()
    if miembro and miembro.puede_aprobar:
        if miembro.limite_aprobacion is None or monto <= miembro.limite_aprobacion:
            return False  # El usuario puede auto-aprobar

    return True


async def solicitar_aprobacion(db: Session, orden_id: int, usuario_id: int, nota: str = "") -> Aprobacion | None:
    """
    Crea una solicitud de aprobacion y envia WhatsApp a los aprobadores de la empresa.
    Returns la Aprobacion creada o None si no se pudo crear.
    """
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.empresa_id:
        logger.error(f"Usuario {usuario_id} no tiene empresa asignada")
        return None

    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        logger.error(f"Orden {orden_id} no encontrada")
        return None

    ahora = datetime.now(timezone.utc)

    aprobacion = Aprobacion(
        orden_id=orden_id,
        empresa_id=usuario.empresa_id,
        solicitante_id=usuario_id,
        monto=orden.total,
        nota_solicitud=nota,
        solicitada_at=ahora,
        expira_at=ahora + timedelta(hours=EXPIRACION_HORAS),
    )
    db.add(aprobacion)
    db.commit()
    db.refresh(aprobacion)

    # Enviar WhatsApp a todos los aprobadores de la empresa
    aprobadores = db.query(MiembroEmpresa).filter(
        MiembroEmpresa.empresa_id == usuario.empresa_id,
        MiembroEmpresa.puede_aprobar == True,
        MiembroEmpresa.activo == True,
    ).all()

    msg_data = componer_mensaje_aprobacion(orden, usuario, db=db)

    for aprobador_miembro in aprobadores:
        # Solo enviar a quienes tengan limite suficiente (o sin limite)
        if aprobador_miembro.limite_aprobacion is not None and orden.total > aprobador_miembro.limite_aprobacion:
            continue

        aprobador_usuario = db.query(Usuario).filter(
            Usuario.id == aprobador_miembro.usuario_id
        ).first()
        if aprobador_usuario and aprobador_usuario.telefono:
            try:
                resultado = await enviar_mensaje_con_botones(
                    aprobador_usuario.telefono,
                    msg_data["texto"],
                    msg_data["botones"],
                    header="Aprobacion requerida",
                )
                if not aprobacion.mensaje_enviado_id and resultado.get("messages"):
                    aprobacion.mensaje_enviado_id = resultado["messages"][0].get("id")
                    db.commit()
            except Exception as e:
                logger.error(f"Error enviando aprobacion a {aprobador_usuario.telefono}: {e}")

    logger.info(
        f"Aprobacion #{aprobacion.id} creada para orden #{orden_id} "
        f"— ${orden.total:,.0f} — {len(aprobadores)} aprobadores notificados"
    )
    return aprobacion


def aprobar_orden(db: Session, aprobacion_id: int, aprobador_id: int, nota: str = "") -> Aprobacion | None:
    """
    Aprueba una orden. Actualiza el status y notifica al solicitante.
    Returns la Aprobacion actualizada o None si no se encontro.
    """
    aprobacion = db.query(Aprobacion).filter(
        Aprobacion.id == aprobacion_id,
        Aprobacion.status == "pendiente",
    ).first()
    if not aprobacion:
        logger.error(f"Aprobacion {aprobacion_id} no encontrada o ya resuelta")
        return None

    # Verificar que el aprobador tiene permisos
    miembro = db.query(MiembroEmpresa).filter(
        MiembroEmpresa.empresa_id == aprobacion.empresa_id,
        MiembroEmpresa.usuario_id == aprobador_id,
        MiembroEmpresa.puede_aprobar == True,
        MiembroEmpresa.activo == True,
    ).first()
    if not miembro:
        logger.error(f"Usuario {aprobador_id} no tiene permiso de aprobar en empresa {aprobacion.empresa_id}")
        return None

    if miembro.limite_aprobacion is not None and aprobacion.monto > miembro.limite_aprobacion:
        logger.error(
            f"Monto ${aprobacion.monto:,.0f} excede limite de aprobacion "
            f"${miembro.limite_aprobacion:,.0f} del usuario {aprobador_id}"
        )
        return None

    aprobacion.status = "aprobada"
    aprobacion.aprobador_id = aprobador_id
    aprobacion.nota_respuesta = nota
    aprobacion.respondida_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(aprobacion)

    logger.info(f"Orden #{aprobacion.orden_id} aprobada por usuario {aprobador_id}")
    return aprobacion


def rechazar_orden(db: Session, aprobacion_id: int, aprobador_id: int, nota: str = "") -> Aprobacion | None:
    """
    Rechaza una orden. Actualiza el status y notifica al solicitante con el motivo.
    Returns la Aprobacion actualizada o None.
    """
    aprobacion = db.query(Aprobacion).filter(
        Aprobacion.id == aprobacion_id,
        Aprobacion.status == "pendiente",
    ).first()
    if not aprobacion:
        logger.error(f"Aprobacion {aprobacion_id} no encontrada o ya resuelta")
        return None

    # Verificar permisos del aprobador
    miembro = db.query(MiembroEmpresa).filter(
        MiembroEmpresa.empresa_id == aprobacion.empresa_id,
        MiembroEmpresa.usuario_id == aprobador_id,
        MiembroEmpresa.puede_aprobar == True,
        MiembroEmpresa.activo == True,
    ).first()
    if not miembro:
        logger.error(f"Usuario {aprobador_id} no tiene permiso de aprobar")
        return None

    aprobacion.status = "rechazada"
    aprobacion.aprobador_id = aprobador_id
    aprobacion.nota_respuesta = nota
    aprobacion.respondida_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(aprobacion)

    logger.info(f"Orden #{aprobacion.orden_id} rechazada por usuario {aprobador_id}: {nota}")
    return aprobacion


def obtener_aprobaciones_pendientes(db: Session, aprobador_id: int) -> list[Aprobacion]:
    """
    Lista las aprobaciones pendientes para un aprobador.
    Solo muestra las de su empresa y dentro de su limite.
    """
    # Obtener empresas donde el usuario es aprobador
    membresias = db.query(MiembroEmpresa).filter(
        MiembroEmpresa.usuario_id == aprobador_id,
        MiembroEmpresa.puede_aprobar == True,
        MiembroEmpresa.activo == True,
    ).all()

    if not membresias:
        return []

    pendientes = []
    for membresia in membresias:
        query = db.query(Aprobacion).filter(
            Aprobacion.empresa_id == membresia.empresa_id,
            Aprobacion.status == "pendiente",
        )
        # Filtrar por limite de aprobacion si aplica
        if membresia.limite_aprobacion is not None:
            query = query.filter(Aprobacion.monto <= membresia.limite_aprobacion)

        pendientes.extend(query.all())

    # Ordenar por fecha de solicitud (mas antiguas primero)
    pendientes.sort(key=lambda a: a.solicitada_at)
    return pendientes


def verificar_expiradas(db: Session) -> list[Aprobacion]:
    """
    Marca como expiradas las aprobaciones que pasaron 24hrs sin respuesta.
    Pensado para correr en un scheduler periodico.
    Returns lista de aprobaciones que se expiraron.
    """
    ahora = datetime.now(timezone.utc)
    expiradas = db.query(Aprobacion).filter(
        Aprobacion.status == "pendiente",
        Aprobacion.expira_at <= ahora,
    ).all()

    for aprobacion in expiradas:
        aprobacion.status = "expirada"
        aprobacion.respondida_at = ahora
        logger.info(f"Aprobacion #{aprobacion.id} expirada (orden #{aprobacion.orden_id})")

    if expiradas:
        db.commit()

    return expiradas


def componer_mensaje_aprobacion(orden: Orden, solicitante: Usuario, db: Session = None) -> dict:
    """
    Compone el mensaje corto de WhatsApp para aprobacion.
    Retorna dict con 'texto' y 'botones' para enviar interactivamente.
    """
    nombre = solicitante.nombre or solicitante.telefono

    # Resumen compacto de items
    items_resumen = ""
    try:
        items_list = json.loads(orden.items) if orden.items else []
        partes = []
        for item in items_list:
            nombre_mat = item.get("nombre") or item.get("material") or item.get("descripcion", "Material")
            cantidad = item.get("cantidad", "")
            unidad = item.get("unidad", "")
            parte = nombre_mat
            if cantidad:
                parte = f"{cantidad}{unidad} {nombre_mat}" if unidad else f"{cantidad} {nombre_mat}"
            partes.append(parte)
        items_resumen = ", ".join(partes) if partes else "(sin detalle)"
    except (json.JSONDecodeError, TypeError):
        items_resumen = "(sin detalle)"

    mensaje = f"*Aprobacion requerida*\n\n"
    mensaje += f"{nombre} pide:\n{items_resumen}\n"
    mensaje += f"Total: *${orden.total:,.0f} MXN*\n"

    if orden.direccion_entrega:
        mensaje += f"Obra: {orden.direccion_entrega}\n"

    # Presupuesto solo si hay alerta (>60%)
    if db and solicitante.empresa_id:
        presupuesto = db.query(PresupuestoObra).filter(
            PresupuestoObra.empresa_id == solicitante.empresa_id,
            PresupuestoObra.activo == True,
        ).first()
        if presupuesto and presupuesto.presupuesto_total and presupuesto.presupuesto_total > 0:
            pct = presupuesto.porcentaje_consumido or 0
            if pct > 60:
                mensaje += f"⚠ Presupuesto al {pct:.0f}%\n"

    mensaje += "\nExpira en 24 horas."

    botones = [
        {"id": f"aprobar_{orden.id}", "title": "Aprobar"},
        {"id": f"rechazar_{orden.id}", "title": "Rechazar"},
    ]

    return {"texto": mensaje, "botones": botones}


def componer_mensaje_resultado(aprobacion: Aprobacion, aprobada: bool, nombre_aprobador: str = "") -> str:
    """
    Compone el mensaje de WhatsApp que recibe el solicitante
    con el resultado de su solicitud.
    """
    if aprobada:
        mensaje = (
            f"*Compra aprobada!*\n\n"
            f"Orden #{aprobacion.orden_id} — ${aprobacion.monto:,.0f} MXN\n"
        )
        if nombre_aprobador:
            mensaje += f"Aprobada por: {nombre_aprobador}\n"
        if aprobacion.nota_respuesta:
            mensaje += f"Nota: {aprobacion.nota_respuesta}\n"
        mensaje += "\nTu pedido se esta procesando."
    else:
        mensaje = (
            f"*Compra rechazada*\n\n"
            f"Orden #{aprobacion.orden_id} — ${aprobacion.monto:,.0f} MXN\n"
        )
        if nombre_aprobador:
            mensaje += f"Rechazada por: {nombre_aprobador}\n"
        if aprobacion.nota_respuesta:
            mensaje += f"Motivo: {aprobacion.nota_respuesta}\n"
        mensaje += "\nSi necesitas ajustar el pedido, mandame mensaje."

    return mensaje
