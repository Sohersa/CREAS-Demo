"""
Servicio de control presupuestal de obra.
Gestiona presupuestos, partidas, consumos y alertas por WhatsApp.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.presupuesto import PresupuestoObra, PartidaPresupuesto
from app.models.usuario import Usuario
from app.models.catalogo import CatalogoMaestro
from app.services.whatsapp import enviar_mensaje_texto

logger = logging.getLogger(__name__)


# ─── Crear presupuesto ────────────────────────────────────────────

def crear_presupuesto(
    db: Session,
    usuario_id: int,
    nombre_obra: str,
    direccion: str = "",
    fecha_inicio: datetime = None,
    fecha_fin_estimada: datetime = None,
    partidas: list[dict] = None,
) -> PresupuestoObra:
    """
    Crea un presupuesto de obra con sus partidas.
    Cada partida: {nombre_material, categoria, unidad, cantidad_presupuestada,
                   precio_unitario_estimado, catalogo_id (opcional)}
    """
    presupuesto = PresupuestoObra(
        usuario_id=usuario_id,
        nombre_obra=nombre_obra,
        direccion=direccion,
        fecha_inicio=fecha_inicio,
        fecha_fin_estimada=fecha_fin_estimada,
        presupuesto_total=0,
        gastado_total=0,
        porcentaje_consumido=0,
        created_at=datetime.utcnow(),
    )
    db.add(presupuesto)
    db.flush()  # Get the ID

    total = 0.0
    if partidas:
        for p in partidas:
            cantidad = float(p.get("cantidad_presupuestada", 0))
            precio = float(p.get("precio_unitario_estimado", 0))
            monto = cantidad * precio
            total += monto

            partida = PartidaPresupuesto(
                presupuesto_id=presupuesto.id,
                catalogo_id=p.get("catalogo_id"),
                nombre_material=p["nombre_material"],
                categoria=p.get("categoria", ""),
                unidad=p.get("unidad", ""),
                cantidad_presupuestada=cantidad,
                cantidad_consumida=0,
                porcentaje_consumido=0,
                precio_unitario_estimado=precio,
                monto_presupuestado=monto,
                monto_gastado=0,
                created_at=datetime.utcnow(),
            )
            db.add(partida)

    presupuesto.presupuesto_total = total
    db.commit()
    db.refresh(presupuesto)
    return presupuesto


# ─── Registrar consumo ───────────────────────────────────────────

async def registrar_consumo(
    db: Session,
    presupuesto_id: int,
    partida_id: int = None,
    catalogo_id: int = None,
    cantidad: float = 0,
    monto: float = 0,
) -> dict:
    """
    Registra consumo de material contra una partida del presupuesto.
    Se puede identificar la partida por partida_id o por catalogo_id.
    Actualiza cantidades, montos y porcentajes. Dispara alertas si corresponde.
    """
    presupuesto = db.query(PresupuestoObra).filter(
        PresupuestoObra.id == presupuesto_id
    ).first()
    if not presupuesto:
        return {"error": "Presupuesto no encontrado"}

    # Find the partida
    if partida_id:
        partida = db.query(PartidaPresupuesto).filter(
            PartidaPresupuesto.id == partida_id,
            PartidaPresupuesto.presupuesto_id == presupuesto_id,
        ).first()
    elif catalogo_id:
        partida = db.query(PartidaPresupuesto).filter(
            PartidaPresupuesto.presupuesto_id == presupuesto_id,
            PartidaPresupuesto.catalogo_id == catalogo_id,
        ).first()
    else:
        return {"error": "Se requiere partida_id o catalogo_id"}

    if not partida:
        return {"error": "Partida no encontrada en este presupuesto"}

    if partida.bloqueado:
        return {
            "error": "Partida bloqueada",
            "mensaje": f"La partida de {partida.nombre_material} esta bloqueada por haber alcanzado el 100% del presupuesto.",
        }

    # Update consumed amounts
    partida.cantidad_consumida += cantidad
    partida.monto_gastado += monto

    # Recalculate percentage
    if partida.cantidad_presupuestada > 0:
        partida.porcentaje_consumido = round(
            (partida.cantidad_consumida / partida.cantidad_presupuestada) * 100, 2
        )

    # Update presupuesto totals
    presupuesto.gastado_total += monto
    if presupuesto.presupuesto_total > 0:
        presupuesto.porcentaje_consumido = round(
            (presupuesto.gastado_total / presupuesto.presupuesto_total) * 100, 2
        )

    db.commit()

    # Check and send alerts
    await verificar_alertas(db, presupuesto_id)

    return {
        "ok": True,
        "partida": partida.nombre_material,
        "porcentaje": partida.porcentaje_consumido,
        "bloqueado": partida.bloqueado,
    }


# ─── Verificar disponibilidad ───────────────────────────────────

def verificar_disponibilidad(
    db: Session,
    usuario_id: int,
    catalogo_id: int,
    cantidad: float,
) -> dict:
    """
    Antes de ordenar, verifica si el presupuesto del usuario permite la compra.
    Busca en todos los presupuestos activos del usuario.
    Returns: {permitido, porcentaje_actual, cantidad_restante, mensaje}
    """
    # Find active budgets for this user that have this material
    partidas = (
        db.query(PartidaPresupuesto)
        .join(PresupuestoObra)
        .filter(
            PresupuestoObra.usuario_id == usuario_id,
            PresupuestoObra.activo == True,
            PartidaPresupuesto.catalogo_id == catalogo_id,
        )
        .all()
    )

    if not partidas:
        # No budget constraint for this material — allow
        return {
            "permitido": True,
            "porcentaje_actual": 0,
            "cantidad_restante": None,
            "mensaje": "Sin presupuesto asignado para este material. Compra libre.",
        }

    # Check each partida (could be in multiple budgets)
    for partida in partidas:
        if partida.bloqueado:
            presupuesto = db.query(PresupuestoObra).get(partida.presupuesto_id)
            return {
                "permitido": False,
                "porcentaje_actual": partida.porcentaje_consumido,
                "cantidad_restante": 0,
                "mensaje": f"Partida de {partida.nombre_material} bloqueada en obra '{presupuesto.nombre_obra}'. Presupuesto agotado.",
            }

        restante = partida.cantidad_presupuestada - partida.cantidad_consumida
        if cantidad > restante:
            presupuesto = db.query(PresupuestoObra).get(partida.presupuesto_id)
            return {
                "permitido": False,
                "porcentaje_actual": partida.porcentaje_consumido,
                "cantidad_restante": restante,
                "mensaje": (
                    f"Cantidad solicitada ({cantidad} {partida.unidad}) excede lo disponible "
                    f"({restante} {partida.unidad}) en obra '{presupuesto.nombre_obra}'."
                ),
            }

    # All checks passed
    partida = partidas[0]
    restante = partida.cantidad_presupuestada - partida.cantidad_consumida
    return {
        "permitido": True,
        "porcentaje_actual": partida.porcentaje_consumido,
        "cantidad_restante": restante,
        "mensaje": "Disponible dentro del presupuesto.",
    }


# ─── Verificar alertas ──────────────────────────────────────────

async def verificar_alertas(db: Session, presupuesto_id: int):
    """
    Revisa todas las partidas del presupuesto y envia alertas
    por WhatsApp al 50%, 80% y 100% de consumo.
    """
    presupuesto = db.query(PresupuestoObra).filter(
        PresupuestoObra.id == presupuesto_id
    ).first()
    if not presupuesto:
        return

    usuario = db.query(Usuario).filter(Usuario.id == presupuesto.usuario_id).first()
    if not usuario or not usuario.telefono:
        return

    partidas = db.query(PartidaPresupuesto).filter(
        PartidaPresupuesto.presupuesto_id == presupuesto_id
    ).all()

    for partida in partidas:
        pct = partida.porcentaje_consumido
        obra = presupuesto.nombre_obra
        material = partida.nombre_material
        unidad = partida.unidad or ""
        consumido = partida.cantidad_consumida
        total = partida.cantidad_presupuestada
        restante = total - consumido

        # 50% alert
        if pct >= 50 and not partida.alerta_50_enviada:
            msg = (
                f"Tu partida de {material} para {obra} ya lleva el 50% consumido "
                f"({consumido}/{total} {unidad}). Vas bien, pero toma nota."
            )
            await enviar_mensaje_texto(usuario.telefono, msg)
            partida.alerta_50_enviada = True
            logger.info(f"Alerta 50% enviada: {material} en {obra}")

        # 80% alert
        if pct >= 80 and not partida.alerta_80_enviada:
            msg = (
                f"*ALERTA:* Tu partida de {material} ya va al 80%. "
                f"Solo te quedan {restante} {unidad} del presupuesto."
            )
            await enviar_mensaje_texto(usuario.telefono, msg)
            partida.alerta_80_enviada = True
            logger.info(f"Alerta 80% enviada: {material} en {obra}")

        # 100% alert — block
        if pct >= 100 and not partida.alerta_100_enviada:
            msg = (
                f"*PRESUPUESTO AGOTADO:* La partida de {material} llego al 100%. "
                f"Se bloqueo la compra de este material. "
                f"Contacta a tu administrador para ampliar el presupuesto."
            )
            await enviar_mensaje_texto(usuario.telefono, msg)
            partida.alerta_100_enviada = True
            bloquear_partida(db, partida.id)
            logger.info(f"Alerta 100% y bloqueo: {material} en {obra}")

    db.commit()


# ─── Bloquear partida ───────────────────────────────────────────

def bloquear_partida(db: Session, partida_id: int):
    """Marca una partida como bloqueada (100% alcanzado)."""
    partida = db.query(PartidaPresupuesto).filter(
        PartidaPresupuesto.id == partida_id
    ).first()
    if partida:
        partida.bloqueado = True
        db.commit()


# ─── Desbloquear partida (admin) ─────────────────────────────────

def desbloquear_partida(db: Session, partida_id: int):
    """Desbloquea una partida — uso administrativo para ampliar presupuesto."""
    partida = db.query(PartidaPresupuesto).filter(
        PartidaPresupuesto.id == partida_id
    ).first()
    if partida:
        partida.bloqueado = False
        partida.alerta_100_enviada = False  # Reset so it can fire again
        db.commit()


# ─── Resumen de presupuesto ──────────────────────────────────────

def obtener_resumen_presupuesto(db: Session, presupuesto_id: int) -> dict:
    """Devuelve resumen completo del presupuesto con todas sus partidas."""
    presupuesto = db.query(PresupuestoObra).filter(
        PresupuestoObra.id == presupuesto_id
    ).first()
    if not presupuesto:
        return {"error": "Presupuesto no encontrado"}

    partidas = db.query(PartidaPresupuesto).filter(
        PartidaPresupuesto.presupuesto_id == presupuesto_id
    ).all()

    partidas_list = []
    for p in partidas:
        partidas_list.append({
            "id": p.id,
            "catalogo_id": p.catalogo_id,
            "nombre_material": p.nombre_material,
            "categoria": p.categoria,
            "unidad": p.unidad,
            "cantidad_presupuestada": p.cantidad_presupuestada,
            "cantidad_consumida": p.cantidad_consumida,
            "porcentaje_consumido": p.porcentaje_consumido,
            "precio_unitario_estimado": p.precio_unitario_estimado,
            "monto_presupuestado": p.monto_presupuestado,
            "monto_gastado": p.monto_gastado,
            "bloqueado": p.bloqueado,
            "alerta_50": p.alerta_50_enviada,
            "alerta_80": p.alerta_80_enviada,
            "alerta_100": p.alerta_100_enviada,
        })

    return {
        "id": presupuesto.id,
        "usuario_id": presupuesto.usuario_id,
        "nombre_obra": presupuesto.nombre_obra,
        "direccion": presupuesto.direccion,
        "presupuesto_total": presupuesto.presupuesto_total,
        "gastado_total": presupuesto.gastado_total,
        "porcentaje_consumido": presupuesto.porcentaje_consumido,
        "activo": presupuesto.activo,
        "fecha_inicio": presupuesto.fecha_inicio.isoformat() if presupuesto.fecha_inicio else None,
        "fecha_fin_estimada": presupuesto.fecha_fin_estimada.isoformat() if presupuesto.fecha_fin_estimada else None,
        "created_at": presupuesto.created_at.isoformat() if presupuesto.created_at else None,
        "partidas": partidas_list,
    }


# ─── Listar presupuestos de usuario ─────────────────────────────

def obtener_presupuestos_usuario(db: Session, usuario_id: int) -> list[dict]:
    """Lista todos los presupuestos de un usuario."""
    presupuestos = db.query(PresupuestoObra).filter(
        PresupuestoObra.usuario_id == usuario_id
    ).order_by(PresupuestoObra.created_at.desc()).all()

    result = []
    for p in presupuestos:
        partidas_count = db.query(PartidaPresupuesto).filter(
            PartidaPresupuesto.presupuesto_id == p.id
        ).count()
        bloqueadas = db.query(PartidaPresupuesto).filter(
            PartidaPresupuesto.presupuesto_id == p.id,
            PartidaPresupuesto.bloqueado == True,
        ).count()

        result.append({
            "id": p.id,
            "nombre_obra": p.nombre_obra,
            "direccion": p.direccion,
            "presupuesto_total": p.presupuesto_total,
            "gastado_total": p.gastado_total,
            "porcentaje_consumido": p.porcentaje_consumido,
            "activo": p.activo,
            "partidas_count": partidas_count,
            "partidas_bloqueadas": bloqueadas,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        })

    return result


# ─── Agregar partida ─────────────────────────────────────────────

def agregar_partida(
    db: Session,
    presupuesto_id: int,
    nombre_material: str,
    cantidad_presupuestada: float,
    precio_unitario_estimado: float,
    categoria: str = "",
    unidad: str = "",
    catalogo_id: int = None,
) -> PartidaPresupuesto:
    """Agrega una partida a un presupuesto existente."""
    presupuesto = db.query(PresupuestoObra).filter(
        PresupuestoObra.id == presupuesto_id
    ).first()
    if not presupuesto:
        return None

    monto = cantidad_presupuestada * precio_unitario_estimado

    partida = PartidaPresupuesto(
        presupuesto_id=presupuesto_id,
        catalogo_id=catalogo_id,
        nombre_material=nombre_material,
        categoria=categoria,
        unidad=unidad,
        cantidad_presupuestada=cantidad_presupuestada,
        cantidad_consumida=0,
        porcentaje_consumido=0,
        precio_unitario_estimado=precio_unitario_estimado,
        monto_presupuestado=monto,
        monto_gastado=0,
        created_at=datetime.utcnow(),
    )
    db.add(partida)

    # Update total
    presupuesto.presupuesto_total += monto
    if presupuesto.presupuesto_total > 0:
        presupuesto.porcentaje_consumido = round(
            (presupuesto.gastado_total / presupuesto.presupuesto_total) * 100, 2
        )

    db.commit()
    db.refresh(partida)
    return partida


# ─── Actualizar partida ──────────────────────────────────────────

def actualizar_partida(
    db: Session,
    partida_id: int,
    datos: dict,
) -> PartidaPresupuesto:
    """Actualiza campos de una partida."""
    partida = db.query(PartidaPresupuesto).filter(
        PartidaPresupuesto.id == partida_id
    ).first()
    if not partida:
        return None

    presupuesto = db.query(PresupuestoObra).filter(
        PresupuestoObra.id == partida.presupuesto_id
    ).first()

    # Remove old amount from total
    old_monto = partida.monto_presupuestado or 0

    for key in ["nombre_material", "categoria", "unidad", "catalogo_id"]:
        if key in datos:
            setattr(partida, key, datos[key])

    if "cantidad_presupuestada" in datos:
        partida.cantidad_presupuestada = float(datos["cantidad_presupuestada"])
    if "precio_unitario_estimado" in datos:
        partida.precio_unitario_estimado = float(datos["precio_unitario_estimado"])

    # Recalculate monto
    partida.monto_presupuestado = partida.cantidad_presupuestada * (partida.precio_unitario_estimado or 0)

    # Recalculate percentage
    if partida.cantidad_presupuestada > 0:
        partida.porcentaje_consumido = round(
            (partida.cantidad_consumida / partida.cantidad_presupuestada) * 100, 2
        )

    # Update presupuesto total
    if presupuesto:
        presupuesto.presupuesto_total = presupuesto.presupuesto_total - old_monto + partida.monto_presupuestado
        if presupuesto.presupuesto_total > 0:
            presupuesto.porcentaje_consumido = round(
                (presupuesto.gastado_total / presupuesto.presupuesto_total) * 100, 2
            )

    db.commit()
    db.refresh(partida)
    return partida


# ─── Eliminar partida ────────────────────────────────────────────

def eliminar_partida(db: Session, partida_id: int) -> bool:
    """Elimina una partida y recalcula el total del presupuesto."""
    partida = db.query(PartidaPresupuesto).filter(
        PartidaPresupuesto.id == partida_id
    ).first()
    if not partida:
        return False

    presupuesto = db.query(PresupuestoObra).filter(
        PresupuestoObra.id == partida.presupuesto_id
    ).first()

    if presupuesto:
        presupuesto.presupuesto_total -= (partida.monto_presupuestado or 0)
        presupuesto.gastado_total -= (partida.monto_gastado or 0)
        if presupuesto.presupuesto_total > 0:
            presupuesto.porcentaje_consumido = round(
                (presupuesto.gastado_total / presupuesto.presupuesto_total) * 100, 2
            )
        else:
            presupuesto.porcentaje_consumido = 0

    db.delete(partida)
    db.commit()
    return True
