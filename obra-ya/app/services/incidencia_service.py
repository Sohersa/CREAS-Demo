"""
Servicio de incidencias — reportes de problemas en entregas.
El usuario reporta por WhatsApp con texto libre, y la IA clasifica.
"""
import json
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.incidencia import IncidenciaEntrega
from app.models.orden import Orden

logger = logging.getLogger(__name__)

# Palabras clave para clasificar tipo de incidencia
KEYWORDS_TIPO = {
    "cantidad_incorrecta": [
        "menos", "faltaron", "faltan", "falta", "incompleto", "no llego todo",
        "metros de menos", "bultos de menos", "piezas de menos",
    ],
    "especificacion": [
        "no era", "equivocado", "otro", "diferente", "resistencia",
        "no es lo que pedi", "material equivocado",
    ],
    "entrega_tarde": [
        "tarde", "retraso", "no llego a tiempo", "tardo", "demoro",
        "llego despues", "horas despues",
    ],
    "material_danado": [
        "roto", "danado", "mojado", "golpeado", "quebrado", "maltratado",
    ],
    "no_llego": [
        "no llego", "no vino", "no aparecio", "nunca llego", "no ha llegado",
    ],
    "cobro_diferente": [
        "cobro de mas", "precio diferente", "me cobraron", "factura no coincide",
    ],
}


def clasificar_incidencia(texto: str) -> tuple[str, str]:
    """
    Clasifica el tipo y severidad de una incidencia basado en texto del usuario.
    Retorna (tipo, severidad).
    """
    texto_lower = texto.lower()

    tipo_detectado = "otro"
    mejor_matches = 0

    for tipo, keywords in KEYWORDS_TIPO.items():
        matches = sum(1 for kw in keywords if kw in texto_lower)
        if matches > mejor_matches:
            mejor_matches = matches
            tipo_detectado = tipo

    # Determinar severidad
    severidad = "media"  # default

    if tipo_detectado == "no_llego":
        severidad = "grave"
    elif tipo_detectado == "especificacion":
        severidad = "grave"
    elif tipo_detectado == "entrega_tarde":
        severidad = "leve"
    elif tipo_detectado == "material_danado":
        severidad = "media"

    # Intensificadores
    palabras_graves = ["jamas", "nunca", "nada", "todo mal", "inaceptable", "pesimo"]
    if any(p in texto_lower for p in palabras_graves):
        severidad = "grave"

    return tipo_detectado, severidad


def extraer_cantidades(texto: str) -> tuple[float | None, float | None, str | None]:
    """
    Intenta extraer cantidad esperada y recibida del texto.
    Ej: "pedi 15 metros y llegaron 12" → (15, 12, "m3")
    """
    import re

    # Patrones comunes
    patrones = [
        # "pedi 15 y llegaron 12"
        r"ped[ií]\w*\s+(\d+\.?\d*)\s*(?:y|pero)\s*(?:llegar?on|vinieron|solo)\s*(\d+\.?\d*)",
        # "15 metros y solo vinieron 12"
        r"(\d+\.?\d*)\s*(?:metros?|m3|bultos?|piezas?|viajes?)\s*(?:y|pero)\s*(?:solo|nomas)?\s*(?:llegar?on|vinieron)\s*(\d+\.?\d*)",
        # "esperaba 15, llego 12"
        r"esperaba\s+(\d+\.?\d*)\s*.*?(?:llego|recib[ií])\s*(\d+\.?\d*)",
    ]

    for patron in patrones:
        match = re.search(patron, texto.lower())
        if match:
            esperado = float(match.group(1))
            recibido = float(match.group(2))

            # Detectar unidad
            unidad = None
            if "metro" in texto.lower() or "m3" in texto.lower():
                unidad = "m3"
            elif "bulto" in texto.lower():
                unidad = "bultos"
            elif "pieza" in texto.lower() or "varilla" in texto.lower():
                unidad = "piezas"
            elif "viaje" in texto.lower():
                unidad = "viajes"

            return esperado, recibido, unidad

    return None, None, None


def crear_incidencia(
    db: Session,
    orden_id: int,
    mensaje_texto: str,
    tipo: str = None,
    severidad: str = None,
) -> IncidenciaEntrega:
    """
    Crea una incidencia para una orden.
    Si no se pasa tipo/severidad, se auto-clasifican del texto.
    """
    orden = db.query(Orden).filter(Orden.id == orden_id).first()
    if not orden:
        raise ValueError(f"Orden {orden_id} no existe")

    # Auto-clasificar si no se pasa tipo
    if not tipo:
        tipo, severidad_auto = clasificar_incidencia(mensaje_texto)
        if not severidad:
            severidad = severidad_auto

    # Extraer cantidades si es problema de cantidad
    cantidad_esperada, cantidad_recibida, unidad = None, None, None
    if tipo == "cantidad_incorrecta":
        cantidad_esperada, cantidad_recibida, unidad = extraer_cantidades(mensaje_texto)

    incidencia = IncidenciaEntrega(
        orden_id=orden_id,
        proveedor_id=orden.proveedor_id,
        usuario_id=orden.usuario_id,
        tipo=tipo,
        severidad=severidad or "media",
        descripcion_usuario=mensaje_texto,
        cantidad_esperada=cantidad_esperada,
        cantidad_recibida=cantidad_recibida,
        unidad=unidad,
    )
    db.add(incidencia)

    # Marcar la orden como con_incidencia (si no esta ya entregada)
    if orden.status not in ("entregada", "cancelada"):
        orden.status = "con_incidencia"
        orden.updated_at = datetime.now(timezone.utc)

    db.commit()

    logger.info(
        f"Incidencia creada — Orden #{orden_id}: tipo={tipo}, "
        f"severidad={severidad}, proveedor={orden.proveedor_id}"
    )
    return incidencia


def resolver_incidencia(db: Session, incidencia_id: int, resolucion: str) -> IncidenciaEntrega:
    """Admin resuelve una incidencia."""
    inc = db.query(IncidenciaEntrega).filter(IncidenciaEntrega.id == incidencia_id).first()
    if not inc:
        raise ValueError(f"Incidencia {incidencia_id} no existe")

    inc.status = "resuelta"
    inc.resolucion = resolucion
    inc.resuelta_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"Incidencia #{incidencia_id} resuelta: {resolucion}")
    return inc


def obtener_incidencias_abiertas(db: Session, proveedor_id: int = None) -> list[IncidenciaEntrega]:
    """Incidencias abiertas, opcionalmente filtradas por proveedor."""
    query = db.query(IncidenciaEntrega).filter(IncidenciaEntrega.status == "abierta")
    if proveedor_id:
        query = query.filter(IncidenciaEntrega.proveedor_id == proveedor_id)
    return query.order_by(IncidenciaEntrega.created_at.desc()).all()
