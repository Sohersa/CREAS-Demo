"""
Agente autonomo con tool use (Opus 4.7 + adaptive thinking).

A diferencia de `agente_claude.interpretar_mensaje` (que solo interpreta
y devuelve JSON), este agente puede EJECUTAR acciones:
  - buscar_proveedores(categoria, municipio)
  - consultar_calificacion(proveedor_id)
  - verificar_presupuesto(usuario_id, monto)
  - consultar_historial_precios(producto, municipio)
  - calcular_distancia(origen, destino)

Se usa para tareas complejas donde el agente necesita razonar con datos
reales de la BD antes de responder (ej: "¿cual proveedor me conviene mas
para una obra en Tlaquepaque con presupuesto de $50k?").

USO TIPICO:
    from app.services.agente_autonomo import procesar_consulta_compleja
    respuesta = await procesar_consulta_compleja(db, usuario_id, pregunta)
"""
import json
import logging

import anthropic
from anthropic import Anthropic
from sqlalchemy.orm import Session

from app.config import settings
from app.models.proveedor import Proveedor
from app.models.precio_historico import PrecioHistorico
from app.models.empresa import Empresa
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)

client = Anthropic(
    api_key=settings.ANTHROPIC_API_KEY,
    max_retries=settings.CLAUDE_MAX_RETRIES,
)


# ═══════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════

TOOLS = [
    {
        "name": "guardar_preferencia_usuario",
        "description": (
            "Guarda una preferencia del usuario para recordarla en futuras conversaciones. "
            "Ej: proveedor favorito, municipio principal, metodo de pago preferido, "
            "frecuencia de compras. Se usa cuando el usuario expresa una preferencia clara."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "usuario_id": {"type": "integer"},
                "clave": {
                    "type": "string",
                    "description": "slug de la preferencia (ej: 'proveedor_favorito', 'municipio_principal')",
                },
                "valor": {"type": "string", "description": "valor de la preferencia"},
            },
            "required": ["usuario_id", "clave", "valor"],
        },
    },
    {
        "name": "leer_preferencias_usuario",
        "description": (
            "Lee todas las preferencias guardadas de un usuario. Usalo al inicio de cada "
            "conversacion compleja para personalizar la respuesta."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "usuario_id": {"type": "integer"},
            },
            "required": ["usuario_id"],
        },
    },
    {
        "name": "buscar_proveedores_web",
        "description": (
            "Busca proveedores de materiales de construccion en Google / internet cuando "
            "no tenemos suficientes en la BD. Util cuando el cliente pide algo exotico "
            "o en una zona donde tenemos poca cobertura. Retorna lista con nombres, "
            "telefonos publicos, y URLs que luego se pueden agregar como prospectos."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Consulta de busqueda (ej: 'concreto premezclado Tlaquepaque')",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "buscar_proveedores",
        "description": (
            "Busca proveedores activos por categoria y municipio. Devuelve hasta 10 "
            "proveedores con su id, nombre, calificacion, total_pedidos y tasa_puntualidad. "
            "Util cuando el usuario pregunta que proveedores hay disponibles o cuando "
            "necesitas recomendar opciones."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "categoria": {
                    "type": "string",
                    "description": "Categoria del material: concreto, acero, agregados, cementantes, block, etc.",
                },
                "municipio": {
                    "type": "string",
                    "description": "Municipio donde se necesita la entrega (ej: Zapopan, Tlaquepaque).",
                },
                "min_calificacion": {
                    "type": "number",
                    "description": "Calificacion minima (0-5). Default: 3.5",
                },
            },
            "required": ["categoria", "municipio"],
        },
    },
    {
        "name": "consultar_calificacion",
        "description": (
            "Consulta el desempeno detallado de un proveedor: calificacion, "
            "tasa de puntualidad, cantidad correcta, especificacion correcta, "
            "total de incidencias y ordenes completadas. Usalo antes de recomendar."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "proveedor_id": {
                    "type": "integer",
                    "description": "ID del proveedor",
                },
            },
            "required": ["proveedor_id"],
        },
    },
    {
        "name": "consultar_historial_precios",
        "description": (
            "Consulta el historial de precios de un producto en el mercado local. "
            "Devuelve precio promedio, minimo, maximo y cantidad de muestras del ultimo mes. "
            "Util para validar si un precio ofrecido es razonable."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "producto": {
                    "type": "string",
                    "description": "Nombre del producto (ej: 'Concreto fc250', 'Varilla 3/8')",
                },
                "municipio": {
                    "type": "string",
                    "description": "Municipio de la obra",
                },
            },
            "required": ["producto", "municipio"],
        },
    },
    {
        "name": "verificar_presupuesto",
        "description": (
            "Verifica si el usuario tiene presupuesto suficiente en su empresa "
            "para un monto dado. Devuelve: limite_usuario, disponible_empresa, "
            "requiere_aprobacion (bool)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "usuario_id": {
                    "type": "integer",
                    "description": "ID del usuario solicitante",
                },
                "monto": {
                    "type": "number",
                    "description": "Monto en MXN a verificar",
                },
            },
            "required": ["usuario_id", "monto"],
        },
    },
]


# ═══════════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS (ejecutan consultas a la BD)
# ═══════════════════════════════════════════════════════════════════

def _tool_buscar_proveedores(db: Session, categoria: str, municipio: str, min_calificacion: float = 3.5) -> dict:
    """Ejecuta la busqueda de proveedores en BD."""
    proveedores = db.query(Proveedor).filter(
        Proveedor.activo == True,
        Proveedor.municipio.ilike(f"%{municipio}%"),
        Proveedor.calificacion >= min_calificacion,
        Proveedor.categorias.ilike(f"%{categoria}%"),
    ).limit(10).all()

    return {
        "total": len(proveedores),
        "proveedores": [
            {
                "id": p.id,
                "nombre": p.nombre,
                "calificacion": p.calificacion,
                "total_pedidos": p.total_pedidos,
                "tasa_puntualidad": p.tasa_puntualidad,
                "municipio": p.municipio,
                "tiempo_respuesta_promedio_min": p.tiempo_respuesta_promedio,
            }
            for p in proveedores
        ],
    }


def _tool_consultar_calificacion(db: Session, proveedor_id: int) -> dict:
    """Devuelve metricas detalladas del proveedor."""
    p = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if not p:
        return {"error": f"Proveedor {proveedor_id} no encontrado"}
    return {
        "nombre": p.nombre,
        "calificacion": p.calificacion,
        "total_ordenes_completadas": p.total_ordenes_completadas,
        "total_incidencias": p.total_incidencias,
        "tasa_puntualidad": p.tasa_puntualidad,
        "tasa_cantidad_correcta": p.tasa_cantidad_correcta,
        "tasa_especificacion_correcta": p.tasa_especificacion_correcta,
    }


def _tool_historial_precios(db: Session, producto: str, municipio: str) -> dict:
    """Consulta precios historicos del ultimo mes."""
    from datetime import datetime, timezone, timedelta
    from sqlalchemy import func

    limite = datetime.now(timezone.utc) - timedelta(days=30)

    row = db.query(
        func.avg(PrecioHistorico.precio_unitario).label("avg"),
        func.min(PrecioHistorico.precio_unitario).label("min"),
        func.max(PrecioHistorico.precio_unitario).label("max"),
        func.count(PrecioHistorico.id).label("muestras"),
    ).filter(
        PrecioHistorico.producto_nombre.ilike(f"%{producto}%"),
        PrecioHistorico.municipio.ilike(f"%{municipio}%"),
        PrecioHistorico.created_at >= limite,
    ).first()

    if not row or not row.muestras:
        return {"muestras": 0, "mensaje": "Sin historial para este producto/zona en los ultimos 30 dias"}

    return {
        "precio_promedio": float(row.avg) if row.avg else 0,
        "precio_minimo": float(row.min) if row.min else 0,
        "precio_maximo": float(row.max) if row.max else 0,
        "muestras": row.muestras,
    }


def _tool_verificar_presupuesto(db: Session, usuario_id: int, monto: float) -> dict:
    """Verifica disponibilidad presupuestal."""
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        return {"error": "Usuario no encontrado"}

    if not usuario.empresa_id:
        return {
            "requiere_aprobacion": False,
            "motivo": "Usuario sin empresa — compras individuales",
        }

    empresa = db.query(Empresa).filter(Empresa.id == usuario.empresa_id).first()
    if not empresa or not empresa.requiere_aprobacion:
        return {"requiere_aprobacion": False, "motivo": "Empresa sin flujo de aprobacion"}

    limite = empresa.limite_sin_aprobacion or 0
    return {
        "requiere_aprobacion": monto > limite,
        "limite_sin_aprobacion": limite,
        "monto_solicitado": monto,
        "empresa": empresa.nombre_legal,
    }


def _tool_guardar_preferencia(db: Session, usuario_id: int, clave: str, valor: str) -> dict:
    """Guarda preferencia persistente del usuario (upsert)."""
    from app.models.preferencia import PreferenciaUsuario
    existente = db.query(PreferenciaUsuario).filter(
        PreferenciaUsuario.usuario_id == usuario_id,
        PreferenciaUsuario.clave == clave,
    ).first()
    if existente:
        existente.valor = valor[:2000]
    else:
        db.add(PreferenciaUsuario(usuario_id=usuario_id, clave=clave, valor=valor[:2000]))
    db.commit()
    return {"guardado": True, "clave": clave}


def _tool_leer_preferencias(db: Session, usuario_id: int) -> dict:
    """Lee todas las preferencias guardadas del usuario."""
    from app.models.preferencia import PreferenciaUsuario
    prefs = db.query(PreferenciaUsuario).filter(
        PreferenciaUsuario.usuario_id == usuario_id
    ).all()
    return {"preferencias": {p.clave: p.valor for p in prefs}}


def _tool_buscar_web(query: str) -> dict:
    """
    Busca proveedores en web via DuckDuckGo (sin API key).
    Es basico — retorna top 5 resultados. Para resultados mejores se puede
    upgradear a Brave Search API o Google Custom Search.
    """
    import httpx
    try:
        # DuckDuckGo Instant Answer API (gratis, sin key)
        url = f"https://duckduckgo.com/?q={query} proveedor material construccion Guadalajara&format=json&no_html=1&skip_disambig=1"
        with httpx.Client(timeout=8, follow_redirects=True) as c:
            r = c.get(url)
            if r.status_code == 200:
                data = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
                results = [
                    {"title": t.get("Text", ""), "url": t.get("FirstURL", "")}
                    for t in (data.get("RelatedTopics") or [])[:5]
                    if t.get("Text")
                ]
                if results:
                    return {"resultados": results}
        # Fallback: sugerir al usuario lo haga manualmente
        return {
            "resultados": [],
            "nota": f"Sin resultados automaticos. Buscar manualmente: 'https://www.google.com/search?q={query.replace(' ','+')}+proveedor+material+Guadalajara'"
        }
    except Exception as e:
        logger.error(f"Error web search: {e}")
        return {"resultados": [], "error": str(e)}


def _ejecutar_tool(db: Session, nombre: str, inputs: dict) -> str:
    """Dispatcher de tools — devuelve JSON string del resultado."""
    try:
        if nombre == "buscar_proveedores":
            r = _tool_buscar_proveedores(db, **inputs)
        elif nombre == "consultar_calificacion":
            r = _tool_consultar_calificacion(db, **inputs)
        elif nombre == "consultar_historial_precios":
            r = _tool_historial_precios(db, **inputs)
        elif nombre == "verificar_presupuesto":
            r = _tool_verificar_presupuesto(db, **inputs)
        elif nombre == "guardar_preferencia_usuario":
            r = _tool_guardar_preferencia(db, **inputs)
        elif nombre == "leer_preferencias_usuario":
            r = _tool_leer_preferencias(db, **inputs)
        elif nombre == "buscar_proveedores_web":
            r = _tool_buscar_web(**inputs)
        else:
            return json.dumps({"error": f"Tool desconocida: {nombre}"})
        return json.dumps(r, default=str, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error ejecutando tool {nombre}: {e}")
        return json.dumps({"error": str(e)})


# ═══════════════════════════════════════════════════════════════════
# SYSTEM PROMPT
# ═══════════════════════════════════════════════════════════════════

SYSTEM_PROMPT_AGENTE = """Eres ObraYa Agent, un asistente autonomo para residentes de obra en Guadalajara.

Tienes acceso a herramientas que te permiten consultar datos reales de la plataforma:
proveedores activos, calificaciones, historial de precios y presupuestos.

Cuando el usuario te pregunte algo complejo (recomendaciones, comparaciones, validacion
de precios), USA las herramientas antes de responder. No inventes datos.

Cuando respondas al usuario final, escribe en espanol neutro, natural, tipo WhatsApp.
Mantenlo breve — 2-4 lineas cuando sea posible.

Reglas:
- Si buscas proveedores, consulta tambien su calificacion antes de recomendar
- Si validas un precio, compara contra el historial del ultimo mes
- Si el monto supera limites, avisa que requiere aprobacion
- Nunca afirmes algo sin respaldo de una tool cuando sea verificable
"""


async def procesar_consulta_compleja(
    db: Session,
    usuario_id: int,
    pregunta: str,
    max_iteraciones: int = 5,
) -> str:
    """
    Ejecuta el loop agentico con Opus 4.7 + tools.

    Args:
        db: sesion de BD
        usuario_id: id del usuario que pregunta (para contexto)
        pregunta: la pregunta en lenguaje natural
        max_iteraciones: limite de iteraciones del loop (evita costos fuera de control)

    Returns:
        Respuesta final en texto, lista para enviar por WhatsApp.
    """
    system_block = [{"type": "text", "text": SYSTEM_PROMPT_AGENTE}]
    if settings.CLAUDE_USE_PROMPT_CACHE:
        system_block[0]["cache_control"] = {"type": "ephemeral"}

    # Contexto inicial del usuario
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    ctx = ""
    if usuario:
        ctx = f"(Usuario: {usuario.nombre or usuario.telefono}, municipio: {usuario.municipio_principal or 'Guadalajara'})"

    messages = [{"role": "user", "content": f"{ctx}\n\n{pregunta}"}]

    for _ in range(max_iteraciones):
        try:
            response = client.messages.create(
                model=settings.CLAUDE_MODEL_AGENTE,  # Opus 4.7
                max_tokens=3000,
                thinking={"type": "adaptive"},
                system=system_block,
                tools=TOOLS,
                messages=messages,
            )
        except anthropic.APIError as e:
            logger.error(f"Error agente autonomo: {e}")
            return "Tuve un problema consultando la informacion. Intenta de nuevo."

        # Si terminó el turno, devolver texto final
        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""

        # Si invocó tools, ejecutar y continuar
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    resultado = _ejecutar_tool(db, block.name, block.input)
                    logger.info(f"Tool {block.name}({block.input}) → {resultado[:200]}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": resultado,
                    })

            messages.append({"role": "user", "content": tool_results})
            continue

        # Otros stop_reasons (max_tokens, pause_turn)
        logger.warning(f"Stop reason inesperado: {response.stop_reason}")
        break

    return "Me tomo mas tiempo del esperado analizar esto. ¿Puedes reformular la pregunta?"
