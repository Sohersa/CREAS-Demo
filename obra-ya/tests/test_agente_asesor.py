"""
Tests de la deteccion de preguntas de asesor y del routing al agente autonomo.
"""


def test_es_pregunta_asesor_recomendaciones():
    from app.routers.webhook import es_pregunta_asesor
    assert es_pregunta_asesor("¿qué proveedor me conviene en Zapopan?")
    assert es_pregunta_asesor("¿cuál recomiendas para concreto?")
    assert es_pregunta_asesor("¿cuál es el mejor proveedor?")


def test_es_pregunta_asesor_precios():
    from app.routers.webhook import es_pregunta_asesor
    assert es_pregunta_asesor("¿es justo pagar $45k por 15m3 de concreto?")
    assert es_pregunta_asesor("¿cómo está el precio de la varilla?")
    assert es_pregunta_asesor("¿cuál es el precio promedio del cemento?")


def test_es_pregunta_asesor_presupuesto():
    from app.routers.webhook import es_pregunta_asesor
    assert es_pregunta_asesor("¿tengo presupuesto para esta compra?")
    assert es_pregunta_asesor("¿puedo gastar 50 mil en cemento?")


def test_no_es_pregunta_asesor_pedidos():
    from app.routers.webhook import es_pregunta_asesor
    # Pedidos normales NO deben triggerar el asesor
    assert not es_pregunta_asesor("Necesito 15m3 de concreto fc250")
    assert not es_pregunta_asesor("Manda 200 varillas del 3/8")
    assert not es_pregunta_asesor("Hola")
    assert not es_pregunta_asesor("Ok")
    assert not es_pregunta_asesor("Mándame la cotización")


def test_no_es_pregunta_asesor_confirmaciones():
    from app.routers.webhook import es_pregunta_asesor
    assert not es_pregunta_asesor("Primera opción")
    assert not es_pregunta_asesor("Sí")
    assert not es_pregunta_asesor("Concretos JAL")


def test_agente_autonomo_tools_registradas():
    from app.services.agente_autonomo import TOOLS
    nombres = {t["name"] for t in TOOLS}
    assert "buscar_proveedores" in nombres
    assert "consultar_calificacion" in nombres
    assert "consultar_historial_precios" in nombres
    assert "verificar_presupuesto" in nombres


def test_reanalisis_schema_valido():
    from app.services.reanalisis_batch import SCHEMA_REANALISIS
    # Verifica que el schema tenga todos los campos requeridos
    required = set(SCHEMA_REANALISIS["required"])
    assert "tipo" in required
    assert "severidad" in required
    assert "culpa" in required
    assert "confianza" in required

    # Verifica enums
    tipos_validos = SCHEMA_REANALISIS["properties"]["tipo"]["enum"]
    assert "cantidad_incorrecta" in tipos_validos
    assert "especificacion" in tipos_validos
    assert "no_llego" in tipos_validos


def test_parser_schema_tiene_todos_los_campos():
    from app.services.parser_respuesta_proveedor import SCHEMA_RESPUESTA_PROVEEDOR
    required = set(SCHEMA_RESPUESTA_PROVEEDOR["required"])
    assert "tiene_precio" in required
    assert "precio_total" in required
    assert "desglose" in required
    assert "incluye_flete" in required
    assert "tiempo_entrega" in required
