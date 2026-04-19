"""
Reanalisis historico de incidencias con Claude Batch API (50% descuento).

Caso de uso:
Cada cierto tiempo (ej: fin de mes), queremos reclasificar todas las incidencias
abiertas con un modelo mas fuerte (Opus 4.7) para:
  - Detectar patrones que el keyword-matching no captura
  - Identificar incidencias mal categorizadas
  - Extraer causa raiz (culpa del proveedor / usuario / logistica / otro)
  - Sugerir resolucion automatica

Batch API:
  - 50% mas barato que la API sincrona
  - Hasta 100K requests por batch
  - Completa en < 1 hora (usualmente)
  - Resultados disponibles 29 dias

Uso tipico (desde el admin dashboard o un cron job):

    from app.services.reanalisis_batch import lanzar_reanalisis_incidencias
    batch_id = lanzar_reanalisis_incidencias(db)
    # ... tiempo despues ...
    procesar_resultados_batch(db, batch_id)
"""
import json
import logging
from datetime import datetime, timezone, timedelta

import anthropic
from anthropic import Anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.models.incidencia import IncidenciaEntrega

logger = logging.getLogger(__name__)

client = Anthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    max_retries=settings.CLAUDE_MAX_RETRIES,
)


SYSTEM_PROMPT_REANALISIS = """Eres un analista de calidad de servicio en la industria de construccion mexicana.

Re-clasifica incidencias de entrega reportadas por residentes de obra.

Tu output DEBE ser JSON con esta estructura (sin campos extra):

{
  "tipo": "cantidad_incorrecta" | "especificacion" | "entrega_tarde" | "material_danado" | "no_llego" | "cobro_diferente" | "otro",
  "severidad": "leve" | "media" | "grave",
  "culpa": "proveedor" | "usuario" | "logistica" | "indeterminado",
  "resolucion_sugerida": "string con una sugerencia breve de como resolver",
  "confianza": 0.0-1.0
}

Reglas:
- Si el material llego pero con menos cantidad -> cantidad_incorrecta, severidad segun % faltante
- Si llego material diferente al pedido -> especificacion, severidad grave si no sirve para la obra
- Si llego tarde pero el material era correcto -> entrega_tarde
- Si llego roto/mojado/danado -> material_danado
- Si NO llego nada -> no_llego, severidad grave
- Si el cobro no coincide con la cotizacion -> cobro_diferente
- Si es ambiguo -> otro, confianza < 0.5
"""

SCHEMA_REANALISIS = {
    "type": "object",
    "properties": {
        "tipo": {
            "type": "string",
            "enum": ["cantidad_incorrecta", "especificacion", "entrega_tarde",
                     "material_danado", "no_llego", "cobro_diferente", "otro"],
        },
        "severidad": {"type": "string", "enum": ["leve", "media", "grave"]},
        "culpa": {
            "type": "string",
            "enum": ["proveedor", "usuario", "logistica", "indeterminado"],
        },
        "resolucion_sugerida": {"type": "string"},
        "confianza": {"type": "number"},
    },
    "required": ["tipo", "severidad", "culpa", "resolucion_sugerida", "confianza"],
    "additionalProperties": False,
}


def lanzar_reanalisis_incidencias(
    db: Session,
    dias_atras: int = 30,
    solo_abiertas: bool = True,
) -> str | None:
    """
    Arma un batch con todas las incidencias del periodo y lo envia a Claude Batch API.

    Returns:
        batch_id (str) si se envio correctamente, None si no hay incidencias.
    """
    limite = datetime.now(timezone.utc) - timedelta(days=dias_atras)

    query = db.query(IncidenciaEntrega).filter(
        IncidenciaEntrega.created_at >= limite,
    )
    if solo_abiertas:
        query = query.filter(IncidenciaEntrega.status.in_(["abierta", "en_revision"]))

    incidencias = query.all()
    if not incidencias:
        logger.info("No hay incidencias para reanalizar")
        return None

    logger.info(f"Preparando batch de {len(incidencias)} incidencias para reanalisis")

    # Armar requests del batch
    requests = []
    for inc in incidencias:
        requests.append({
            "custom_id": f"incidencia_{inc.id}",
            "params": {
                "model": settings.CLAUDE_MODEL_AGENTE,  # Opus 4.7 para mejor analisis
                "max_tokens": 500,
                "system": SYSTEM_PROMPT_REANALISIS,
                "messages": [{
                    "role": "user",
                    "content": (
                        f"Incidencia reportada:\n\n"
                        f"{inc.descripcion_usuario or '(sin descripcion)'}\n\n"
                        f"Clasificacion actual: tipo={inc.tipo}, severidad={inc.severidad}"
                    ),
                }],
                "output_config": {
                    "format": {
                        "type": "json_schema",
                        "schema": SCHEMA_REANALISIS,
                    },
                },
            },
        })

    try:
        batch = client.messages.batches.create(requests=requests)
        logger.info(f"Batch creado: {batch.id} ({len(requests)} requests, 50% descuento)")
        return batch.id
    except anthropic.APIError as e:
        logger.error(f"Error creando batch: {e}")
        return None


def verificar_batch(batch_id: str) -> dict:
    """
    Consulta el estado del batch.
    Returns: dict con status, counts, y si ya se puede procesar.
    """
    try:
        batch = client.messages.batches.retrieve(batch_id)
        return {
            "id": batch.id,
            "status": batch.processing_status,
            "ended": batch.processing_status == "ended",
            "counts": {
                "processing": batch.request_counts.processing,
                "succeeded": batch.request_counts.succeeded,
                "errored": batch.request_counts.errored,
                "cancelled": batch.request_counts.canceled,
                "expired": batch.request_counts.expired,
            },
        }
    except anthropic.APIError as e:
        logger.error(f"Error consultando batch {batch_id}: {e}")
        return {"id": batch_id, "status": "error", "ended": False}


def procesar_resultados_batch(db: Session, batch_id: str) -> dict:
    """
    Descarga los resultados del batch y actualiza las incidencias en BD.
    Solo debe llamarse despues de verificar_batch retorne ended=True.

    Returns:
        dict con conteo de incidencias actualizadas/erroradas.
    """
    actualizadas = 0
    con_error = 0
    cambios_relevantes = []  # lista de cambios que el admin deberia revisar

    try:
        for result in client.messages.batches.results(batch_id):
            custom_id = result.custom_id
            if not custom_id.startswith("incidencia_"):
                continue

            incidencia_id = int(custom_id.split("_")[1])
            incidencia = db.query(IncidenciaEntrega).filter(
                IncidenciaEntrega.id == incidencia_id
            ).first()
            if not incidencia:
                continue

            if result.result.type != "succeeded":
                con_error += 1
                logger.warning(f"Batch result error para {custom_id}: {result.result.type}")
                continue

            # Extraer respuesta estructurada
            try:
                respuesta_texto = result.result.message.content[0].text
                analisis = json.loads(respuesta_texto)
            except (json.JSONDecodeError, AttributeError, IndexError) as e:
                logger.error(f"Error parseando batch result para {custom_id}: {e}")
                con_error += 1
                continue

            nuevo_tipo = analisis.get("tipo")
            nueva_severidad = analisis.get("severidad")
            confianza = analisis.get("confianza", 0)

            # Solo actualizar si la confianza es alta
            if confianza >= 0.7 and nuevo_tipo:
                if nuevo_tipo != incidencia.tipo or nueva_severidad != incidencia.severidad:
                    cambios_relevantes.append({
                        "id": incidencia.id,
                        "orden_id": incidencia.orden_id,
                        "tipo_original": incidencia.tipo,
                        "tipo_nuevo": nuevo_tipo,
                        "severidad_original": incidencia.severidad,
                        "severidad_nueva": nueva_severidad,
                        "culpa": analisis.get("culpa"),
                        "resolucion_sugerida": analisis.get("resolucion_sugerida"),
                        "confianza": confianza,
                    })
                    incidencia.tipo = nuevo_tipo
                    incidencia.severidad = nueva_severidad
                    # Guardamos la interpretacion refinada en el campo existente
                    incidencia.descripcion_interpretada = (
                        f"[Reanalisis Opus 4.7] Culpa: {analisis.get('culpa')}. "
                        f"Sugerencia: {analisis.get('resolucion_sugerida')}"
                    )
                    actualizadas += 1

        db.commit()

    except anthropic.APIError as e:
        logger.error(f"Error procesando resultados batch: {e}")
        db.rollback()

    return {
        "actualizadas": actualizadas,
        "con_error": con_error,
        "cambios_relevantes": cambios_relevantes,
    }
