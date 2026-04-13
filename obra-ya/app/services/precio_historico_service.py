"""
Servicio de Precios Historicos — alimenta la base de datos maestra de precios.

Este servicio se activa AUTOMATICAMENTE cada vez que:
  1. Un proveedor responde a una solicitud de cotizacion
  2. Se importan precios manualmente
  3. Se registra un precio de referencia

Con el tiempo, esta tabla permite:
  - Graficar tendencias de precio por producto
  - Detectar estacionalidad (cemento sube en temporada de lluvias, etc.)
  - Predecir aumentos con ML
  - Rankear proveedores por precio promedio
  - Dar precios de referencia mas precisos a nuevos usuarios
"""
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, extract

from app.models.precio_historico import PrecioHistorico
from app.models.catalogo import CatalogoMaestro, AliasProducto
from app.models.proveedor import Proveedor

logger = logging.getLogger(__name__)


# ============================================================
# 1. REGISTRAR PRECIOS DESDE RESPUESTA DE PROVEEDOR
# ============================================================

def registrar_precios_desde_respuesta(
    db: Session,
    proveedor_id: int,
    proveedor_nombre: str,
    respuesta_parseada: dict,
    pedido_id: int = None,
    solicitud_id: int = None,
    zona: str = None,
) -> list[PrecioHistorico]:
    """
    Extrae cada linea de precio de la respuesta del proveedor
    y la guarda en la tabla de precios historicos.

    Se llama desde registrar_respuesta_proveedor() en cotizacion_activa.py
    """
    if not respuesta_parseada or not respuesta_parseada.get("tiene_precio"):
        return []

    desglose = respuesta_parseada.get("desglose", [])
    if not desglose:
        return []

    ahora = datetime.now(timezone.utc)
    costo_flete_total = respuesta_parseada.get("costo_flete", 0) or 0
    incluye_flete = respuesta_parseada.get("incluye_flete", False)
    tiempo_entrega = respuesta_parseada.get("tiempo_entrega", "")
    disponibilidad = respuesta_parseada.get("disponibilidad", "")
    condiciones = respuesta_parseada.get("condiciones", "")

    # Prorratear flete entre items
    num_items = len(desglose)
    flete_por_item = costo_flete_total / num_items if num_items > 0 and costo_flete_total > 0 else 0

    precios_guardados = []

    for item in desglose:
        producto_nombre = item.get("producto", "Desconocido")
        precio_unitario = item.get("precio_unitario", 0)
        cantidad = item.get("cantidad", 0)
        unidad = item.get("unidad", "pieza")
        subtotal = item.get("subtotal", 0)

        if not precio_unitario or precio_unitario <= 0:
            continue

        # Intentar mapear al catalogo maestro
        catalogo_id, producto_normalizado, categoria = _buscar_en_catalogo(db, producto_nombre)

        # Calcular flete por unidad
        flete_unidad = flete_por_item / cantidad if cantidad > 0 and flete_por_item > 0 else 0

        # Precio efectivo = unitario + flete prorrateado
        precio_efectivo = precio_unitario + flete_unidad

        precio = PrecioHistorico(
            catalogo_id=catalogo_id,
            producto_nombre=producto_nombre,
            producto_normalizado=producto_normalizado,
            categoria=categoria,
            proveedor_id=proveedor_id,
            proveedor_nombre=proveedor_nombre,
            precio_unitario=precio_unitario,
            unidad=unidad,
            cantidad_cotizada=cantidad,
            subtotal=subtotal,
            incluye_flete=incluye_flete,
            costo_flete=flete_por_item,
            flete_por_unidad=flete_unidad,
            precio_efectivo=precio_efectivo,
            zona=zona,
            tiempo_entrega=tiempo_entrega,
            disponibilidad=disponibilidad,
            condiciones=condiciones,
            pedido_id=pedido_id,
            solicitud_id=solicitud_id,
            fuente="cotizacion_activa",
            fecha=ahora,
            dia_semana=ahora.weekday(),
            mes=ahora.month,
            anio=ahora.year,
            trimestre=(ahora.month - 1) // 3 + 1,
            confianza=1.0,
        )

        # Detectar outliers (precio muy diferente al promedio historico)
        precio.es_outlier = _es_outlier(db, catalogo_id, precio_unitario, unidad)

        db.add(precio)
        precios_guardados.append(precio)

    db.commit()

    logger.info(
        f"Precios historicos registrados: {len(precios_guardados)} items "
        f"de proveedor '{proveedor_nombre}' (pedido #{pedido_id})"
    )

    # Actualizar precio de referencia en catalogo maestro
    for precio in precios_guardados:
        if precio.catalogo_id:
            _actualizar_precio_referencia(db, precio.catalogo_id)

    return precios_guardados


# ============================================================
# 2. BUSCAR EN CATALOGO MAESTRO
# ============================================================

def _buscar_en_catalogo(db: Session, producto_nombre: str) -> tuple:
    """
    Intenta mapear el nombre del producto al catalogo maestro.
    Retorna (catalogo_id, nombre_normalizado, categoria) o (None, None, None).
    """
    nombre_lower = producto_nombre.lower().strip()

    # Buscar por nombre exacto en catalogo
    cat = db.query(CatalogoMaestro).filter(
        func.lower(CatalogoMaestro.nombre) == nombre_lower
    ).first()

    if cat:
        return cat.id, cat.nombre, cat.categoria

    # Buscar por alias
    alias = db.query(AliasProducto).filter(
        func.lower(AliasProducto.alias) == nombre_lower,
        AliasProducto.activo == True,
    ).first()

    if alias:
        cat = db.query(CatalogoMaestro).filter(CatalogoMaestro.id == alias.catalogo_id).first()
        if cat:
            # Incrementar uso del alias
            alias.veces_usado = (alias.veces_usado or 0) + 1
            db.commit()
            return cat.id, cat.nombre, cat.categoria

    # Buscar parcial (contiene)
    cats = db.query(CatalogoMaestro).filter(
        func.lower(CatalogoMaestro.nombre).contains(nombre_lower.split()[0] if nombre_lower else "")
    ).first()

    if cats:
        return cats.id, cats.nombre, cats.categoria

    return None, None, None


# ============================================================
# 3. DETECCION DE OUTLIERS
# ============================================================

def _es_outlier(db: Session, catalogo_id: int, precio: float, unidad: str) -> bool:
    """
    Detecta si un precio es muy diferente al promedio historico.
    Un outlier es > 3x o < 0.3x del promedio.
    """
    if not catalogo_id or not precio:
        return False

    stats = db.query(
        func.avg(PrecioHistorico.precio_unitario),
        func.count(PrecioHistorico.id),
    ).filter(
        PrecioHistorico.catalogo_id == catalogo_id,
        PrecioHistorico.unidad == unidad,
        PrecioHistorico.es_outlier == False,
    ).first()

    promedio, total = stats
    if not promedio or total < 5:  # Necesitamos al menos 5 datos
        return False

    ratio = precio / promedio
    if ratio > 3.0 or ratio < 0.3:
        logger.warning(
            f"Outlier detectado: catalogo #{catalogo_id}, "
            f"precio={precio}, promedio={promedio:.2f}, ratio={ratio:.2f}"
        )
        return True

    return False


# ============================================================
# 4. ACTUALIZAR PRECIO DE REFERENCIA EN CATALOGO
# ============================================================

def _actualizar_precio_referencia(db: Session, catalogo_id: int):
    """
    Recalcula el precio de referencia del catalogo maestro
    basado en los ultimos 30 precios no-outlier.
    """
    precios_recientes = db.query(PrecioHistorico.precio_unitario).filter(
        PrecioHistorico.catalogo_id == catalogo_id,
        PrecioHistorico.es_outlier == False,
    ).order_by(PrecioHistorico.fecha.desc()).limit(30).all()

    if len(precios_recientes) < 3:
        return

    valores = [p[0] for p in precios_recientes if p[0]]
    if not valores:
        return

    promedio = sum(valores) / len(valores)

    cat = db.query(CatalogoMaestro).filter(CatalogoMaestro.id == catalogo_id).first()
    if cat:
        cat.precio_referencia = round(promedio, 2)
        db.commit()
        logger.info(f"Precio referencia actualizado: {cat.nombre} = ${promedio:.2f}")


# ============================================================
# 5. CONSULTAS DE ANALYTICS
# ============================================================

def obtener_tendencia_precio(
    db: Session,
    catalogo_id: int = None,
    producto_nombre: str = None,
    meses: int = 6,
) -> list[dict]:
    """
    Devuelve la tendencia de precio mensual de un producto.
    Retorna lista de {mes, anio, precio_promedio, precio_min, precio_max, num_cotizaciones}.
    """
    query = db.query(
        PrecioHistorico.anio,
        PrecioHistorico.mes,
        func.avg(PrecioHistorico.precio_unitario).label("promedio"),
        func.min(PrecioHistorico.precio_unitario).label("minimo"),
        func.max(PrecioHistorico.precio_unitario).label("maximo"),
        func.count(PrecioHistorico.id).label("cotizaciones"),
    ).filter(
        PrecioHistorico.es_outlier == False,
    )

    if catalogo_id:
        query = query.filter(PrecioHistorico.catalogo_id == catalogo_id)
    elif producto_nombre:
        query = query.filter(
            func.lower(PrecioHistorico.producto_normalizado).contains(producto_nombre.lower())
        )

    resultados = query.group_by(
        PrecioHistorico.anio,
        PrecioHistorico.mes,
    ).order_by(
        PrecioHistorico.anio.desc(),
        PrecioHistorico.mes.desc(),
    ).limit(meses).all()

    return [
        {
            "anio": r.anio,
            "mes": r.mes,
            "precio_promedio": round(r.promedio, 2) if r.promedio else 0,
            "precio_min": round(r.minimo, 2) if r.minimo else 0,
            "precio_max": round(r.maximo, 2) if r.maximo else 0,
            "num_cotizaciones": r.cotizaciones,
        }
        for r in reversed(resultados)
    ]


def obtener_precio_actual(db: Session, catalogo_id: int) -> dict:
    """
    Precio actual de mercado basado en las ultimas 10 cotizaciones.
    """
    precios = db.query(PrecioHistorico).filter(
        PrecioHistorico.catalogo_id == catalogo_id,
        PrecioHistorico.es_outlier == False,
    ).order_by(PrecioHistorico.fecha.desc()).limit(10).all()

    if not precios:
        return {"precio_promedio": 0, "datos": 0}

    valores = [p.precio_unitario for p in precios if p.precio_unitario]
    efectivos = [p.precio_efectivo for p in precios if p.precio_efectivo]

    return {
        "precio_promedio": round(sum(valores) / len(valores), 2) if valores else 0,
        "precio_con_flete": round(sum(efectivos) / len(efectivos), 2) if efectivos else 0,
        "precio_min": round(min(valores), 2) if valores else 0,
        "precio_max": round(max(valores), 2) if valores else 0,
        "datos": len(precios),
        "ultimo": precios[0].fecha.isoformat() if precios else None,
        "unidad": precios[0].unidad if precios else "",
    }


def ranking_proveedores_por_producto(db: Session, catalogo_id: int, top: int = 10) -> list[dict]:
    """
    Ranking de proveedores por precio promedio para un producto.
    """
    resultados = db.query(
        PrecioHistorico.proveedor_id,
        PrecioHistorico.proveedor_nombre,
        func.avg(PrecioHistorico.precio_efectivo).label("precio_promedio"),
        func.count(PrecioHistorico.id).label("cotizaciones"),
        func.avg(PrecioHistorico.costo_flete).label("flete_promedio"),
    ).filter(
        PrecioHistorico.catalogo_id == catalogo_id,
        PrecioHistorico.es_outlier == False,
        PrecioHistorico.proveedor_id != None,
    ).group_by(
        PrecioHistorico.proveedor_id,
        PrecioHistorico.proveedor_nombre,
    ).order_by(
        func.avg(PrecioHistorico.precio_efectivo).asc(),
    ).limit(top).all()

    return [
        {
            "posicion": i + 1,
            "proveedor_id": r.proveedor_id,
            "proveedor": r.proveedor_nombre,
            "precio_promedio": round(r.precio_promedio, 2) if r.precio_promedio else 0,
            "cotizaciones": r.cotizaciones,
            "flete_promedio": round(r.flete_promedio, 2) if r.flete_promedio else 0,
        }
        for i, r in enumerate(resultados)
    ]


def resumen_mercado(db: Session) -> dict:
    """
    Resumen general del mercado: total de datos, productos trackeados, etc.
    """
    total_precios = db.query(func.count(PrecioHistorico.id)).scalar() or 0
    total_proveedores = db.query(
        func.count(func.distinct(PrecioHistorico.proveedor_id))
    ).filter(PrecioHistorico.proveedor_id != None).scalar() or 0
    total_productos = db.query(
        func.count(func.distinct(PrecioHistorico.catalogo_id))
    ).filter(PrecioHistorico.catalogo_id != None).scalar() or 0

    # Precio promedio de los top 5 productos mas cotizados
    top_productos = db.query(
        PrecioHistorico.producto_normalizado,
        PrecioHistorico.catalogo_id,
        func.count(PrecioHistorico.id).label("cotizaciones"),
        func.avg(PrecioHistorico.precio_unitario).label("precio_promedio"),
    ).filter(
        PrecioHistorico.producto_normalizado != None,
        PrecioHistorico.es_outlier == False,
    ).group_by(
        PrecioHistorico.producto_normalizado,
        PrecioHistorico.catalogo_id,
    ).order_by(
        func.count(PrecioHistorico.id).desc(),
    ).limit(5).all()

    return {
        "total_datos_precio": total_precios,
        "proveedores_trackeados": total_proveedores,
        "productos_trackeados": total_productos,
        "top_productos": [
            {
                "producto": r.producto_normalizado,
                "catalogo_id": r.catalogo_id,
                "cotizaciones": r.cotizaciones,
                "precio_promedio": round(r.precio_promedio, 2) if r.precio_promedio else 0,
            }
            for r in top_productos
        ],
    }


def variacion_precio_mensual(db: Session, catalogo_id: int) -> dict:
    """
    Calcula la variacion porcentual mes a mes de un producto.
    Util para detectar tendencias de aumento.
    """
    tendencia = obtener_tendencia_precio(db, catalogo_id=catalogo_id, meses=12)

    if len(tendencia) < 2:
        return {"variaciones": [], "tendencia": "sin_datos"}

    variaciones = []
    for i in range(1, len(tendencia)):
        actual = tendencia[i]["precio_promedio"]
        anterior = tendencia[i - 1]["precio_promedio"]
        if anterior > 0:
            variacion = ((actual - anterior) / anterior) * 100
            variaciones.append({
                "mes": tendencia[i]["mes"],
                "anio": tendencia[i]["anio"],
                "precio": actual,
                "variacion_pct": round(variacion, 2),
            })

    # Determinar tendencia general
    if len(variaciones) >= 3:
        ultimas = [v["variacion_pct"] for v in variaciones[-3:]]
        promedio_variacion = sum(ultimas) / len(ultimas)
        if promedio_variacion > 2:
            tendencia_str = "alza"
        elif promedio_variacion < -2:
            tendencia_str = "baja"
        else:
            tendencia_str = "estable"
    else:
        tendencia_str = "sin_datos"

    return {
        "variaciones": variaciones,
        "tendencia": tendencia_str,
    }
