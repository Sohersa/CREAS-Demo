"""
Motor de cotizacion.
Recibe un pedido interpretado, busca proveedores en la BD via CATALOGO MAESTRO,
y genera cotizaciones con precios reales.

FLUJO:
1. Usuario dice "varilla del tres octavos"
2. Buscamos en aliases_producto → encontramos catalogo_id = 6
3. Buscamos todos los productos con catalogo_id = 6 → todos los proveedores que venden esa varilla
4. Comparamos manzanas con manzanas sin importar como le llame cada proveedor
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models.catalogo import CatalogoMaestro, AliasProducto
from app.models.proveedor import Proveedor
from app.models.producto import Producto
from app.models.cotizacion import Cotizacion

logger = logging.getLogger(__name__)

# Flete estimado por municipio desde centro GDL (en MXN)
FLETE_POR_MUNICIPIO = {
    "guadalajara": 800,
    "zapopan": 1200,
    "tlaquepaque": 1000,
    "tonala": 1500,
    "tlajomulco": 1800,
    "el salto": 2000,
    "ixtlahuacan": 2500,
}


def resolver_catalogo_id(db: Session, nombre_producto: str) -> int | None:
    """
    Dado un nombre de producto (como sea que lo digan), encuentra el catalogo_id.
    Busca en la tabla de aliases con multiples estrategias.
    """
    nombre_lower = nombre_producto.lower().strip()

    # Estrategia 1: Match exacto en aliases
    alias = db.query(AliasProducto).filter(
        AliasProducto.alias == nombre_lower,
        AliasProducto.activo == True,
    ).first()
    if alias:
        # Incrementar contador de uso
        alias.veces_usado = (alias.veces_usado or 0) + 1
        db.flush()
        return alias.catalogo_id

    # Estrategia 2: El alias esta contenido en el nombre o viceversa
    aliases = db.query(AliasProducto).filter(AliasProducto.activo == True).all()
    mejor_match = None
    mejor_score = 0

    for a in aliases:
        alias_text = a.alias.lower()

        # El nombre contiene el alias completo
        if alias_text in nombre_lower:
            score = len(alias_text) * 2  # Bonus por match completo
            if score > mejor_score:
                mejor_score = score
                mejor_match = a

        # El alias contiene el nombre completo
        elif nombre_lower in alias_text:
            score = len(nombre_lower)
            if score > mejor_score:
                mejor_score = score
                mejor_match = a

        # Match parcial: comparten al menos 2 palabras significativas
        else:
            palabras_nombre = set(nombre_lower.split())
            palabras_alias = set(alias_text.split())
            # Quitar palabras muy cortas
            palabras_nombre = {p for p in palabras_nombre if len(p) > 2}
            palabras_alias = {p for p in palabras_alias if len(p) > 2}
            comunes = palabras_nombre & palabras_alias
            if len(comunes) >= 2:
                score = len(comunes) * 3
                if score > mejor_score:
                    mejor_score = score
                    mejor_match = a

    if mejor_match and mejor_score >= 4:
        mejor_match.veces_usado = (mejor_match.veces_usado or 0) + 1
        db.flush()
        return mejor_match.catalogo_id

    # Estrategia 3: Buscar directamente en catalogo_maestro por nombre
    maestro = db.query(CatalogoMaestro).filter(
        CatalogoMaestro.nombre.ilike(f"%{nombre_lower}%"),
        CatalogoMaestro.activo == True,
    ).first()
    if maestro:
        return maestro.id

    logger.warning(f"No se encontro catalogo para: '{nombre_producto}'")
    return None


def buscar_producto_en_bd(db: Session, nombre_producto: str, categoria: str) -> list[dict]:
    """
    Busca un producto usando el CATALOGO MAESTRO.
    1. Resuelve el nombre a un catalogo_id via aliases
    2. Busca TODOS los proveedores que venden ese catalogo_id
    3. Devuelve lista ordenada por precio
    """
    resultados = []

    # Paso 1: Resolver a catalogo_id
    catalogo_id = resolver_catalogo_id(db, nombre_producto)

    if catalogo_id:
        # Paso 2: Buscar todos los productos con ese catalogo_id
        productos = db.query(Producto).join(Proveedor).filter(
            Producto.catalogo_id == catalogo_id,
            Producto.activo == True,
            Proveedor.activo == True,
        ).all()

        for prod in productos:
            proveedor = db.query(Proveedor).filter(Proveedor.id == prod.proveedor_id).first()
            if proveedor:
                resultados.append({
                    "producto_id": prod.id,
                    "catalogo_id": catalogo_id,
                    "proveedor_id": proveedor.id,
                    "proveedor_nombre": proveedor.nombre,
                    "proveedor_tipo": proveedor.tipo,
                    "proveedor_municipio": proveedor.municipio,
                    "proveedor_calificacion": proveedor.calificacion,
                    "proveedor_total_pedidos": proveedor.total_pedidos,
                    "producto_nombre": prod.nombre,
                    "nombre_proveedor": prod.nombre_proveedor or prod.nombre,
                    "precio_unitario": prod.precio_unitario,
                    "unidad": prod.unidad,
                    "disponibilidad": prod.disponibilidad,
                    "incluye_flete": prod.precio_incluye_flete,
                })

    # Fallback: busqueda por texto si no hay catalogo_id
    if not resultados:
        logger.info(f"Fallback a busqueda por texto para: '{nombre_producto}'")
        productos = db.query(Producto).join(Proveedor).filter(
            Producto.nombre.ilike(f"%{nombre_producto}%"),
            Producto.activo == True,
            Proveedor.activo == True,
        ).all()

        for prod in productos:
            proveedor = db.query(Proveedor).filter(Proveedor.id == prod.proveedor_id).first()
            if proveedor and not any(r["producto_id"] == prod.id for r in resultados):
                resultados.append({
                    "producto_id": prod.id,
                    "catalogo_id": prod.catalogo_id,
                    "proveedor_id": proveedor.id,
                    "proveedor_nombre": proveedor.nombre,
                    "proveedor_tipo": proveedor.tipo,
                    "proveedor_municipio": proveedor.municipio,
                    "proveedor_calificacion": proveedor.calificacion,
                    "proveedor_total_pedidos": proveedor.total_pedidos,
                    "producto_nombre": prod.nombre,
                    "nombre_proveedor": prod.nombre_proveedor or prod.nombre,
                    "precio_unitario": prod.precio_unitario,
                    "unidad": prod.unidad,
                    "disponibilidad": prod.disponibilidad,
                    "incluye_flete": prod.precio_incluye_flete,
                })

    # Ordenar por precio
    resultados.sort(key=lambda x: x["precio_unitario"])
    return resultados


def calcular_flete(municipio_proveedor: str, municipio_entrega: str) -> float:
    """Estima el costo de flete entre municipios de GDL."""
    flete_base = FLETE_POR_MUNICIPIO.get(municipio_entrega.lower(), 1500)
    if municipio_proveedor.lower() == municipio_entrega.lower():
        return flete_base * 0.5
    return flete_base


def generar_cotizaciones(db: Session, pedido_data: dict) -> list[dict]:
    """
    Recibe el pedido interpretado (JSON) y genera cotizaciones
    de todos los proveedores disponibles.
    """
    items = pedido_data.get("pedido", {}).get("items", [])
    entrega = pedido_data.get("pedido", {}).get("entrega", {})
    municipio_entrega = entrega.get("direccion", "Guadalajara").split(",")[0].strip()

    if not items:
        return []

    items_con_proveedores = []
    for item in items:
        producto = item.get("producto", "")
        categoria = item.get("categoria", "")
        cantidad = item.get("cantidad", 1)
        unidad = item.get("unidad", "pieza")

        opciones = buscar_producto_en_bd(db, producto, categoria)
        items_con_proveedores.append({
            "item": item,
            "cantidad": cantidad,
            "unidad": unidad,
            "opciones": opciones,
        })

    # Agrupar por proveedor
    proveedores_dict: dict[int, dict] = {}

    for item_info in items_con_proveedores:
        for opcion in item_info["opciones"]:
            prov_id = opcion["proveedor_id"]
            if prov_id not in proveedores_dict:
                proveedores_dict[prov_id] = {
                    "proveedor_id": prov_id,
                    "proveedor_nombre": opcion["proveedor_nombre"],
                    "proveedor_tipo": opcion["proveedor_tipo"],
                    "proveedor_municipio": opcion["proveedor_municipio"],
                    "proveedor_calificacion": opcion["proveedor_calificacion"],
                    "proveedor_total_pedidos": opcion["proveedor_total_pedidos"],
                    "items": [],
                    "subtotal": 0,
                    "items_disponibles": 0,
                    "total_items_pedido": len(items),
                }

            subtotal_item = opcion["precio_unitario"] * item_info["cantidad"]
            proveedores_dict[prov_id]["items"].append({
                "producto": opcion["producto_nombre"],
                "precio_unitario": opcion["precio_unitario"],
                "cantidad": item_info["cantidad"],
                "unidad": item_info["unidad"],
                "subtotal": subtotal_item,
                "disponibilidad": opcion["disponibilidad"],
            })
            proveedores_dict[prov_id]["subtotal"] += subtotal_item
            proveedores_dict[prov_id]["items_disponibles"] += 1

    # Calcular flete y total
    cotizaciones = []
    for prov_id, cot in proveedores_dict.items():
        flete = calcular_flete(cot["proveedor_municipio"], municipio_entrega)
        if cot["proveedor_tipo"] == "grande" and cot["subtotal"] > 30000:
            flete = 0

        cot["costo_flete"] = flete
        cot["total"] = cot["subtotal"] + flete
        cot["vigencia"] = (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()
        cotizaciones.append(cot)

    cotizaciones.sort(key=lambda x: x["total"])
    return cotizaciones


def guardar_cotizaciones(db: Session, pedido_id: int, cotizaciones: list[dict]) -> list[int]:
    """Guarda las cotizaciones en la BD y devuelve sus IDs."""
    ids = []
    for cot in cotizaciones:
        nueva = Cotizacion(
            pedido_id=pedido_id,
            proveedor_id=cot["proveedor_id"],
            status="respondida",
            items=json.dumps(cot["items"], ensure_ascii=False),
            subtotal=cot["subtotal"],
            costo_flete=cot["costo_flete"],
            total=cot["total"],
            tiempo_entrega=cot["items"][0]["disponibilidad"] if cot["items"] else "24h",
            vigencia=datetime.fromisoformat(cot["vigencia"]),
        )
        db.add(nueva)
        db.flush()
        ids.append(nueva.id)

    db.commit()
    return ids
