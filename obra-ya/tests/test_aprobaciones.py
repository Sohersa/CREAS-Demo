"""
Tests del flujo de aprobaciones — deteccion de lenguaje natural, botones, flujo completo.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_es_aprobacion_comando():
    from app.routers.webhook import es_aprobacion
    ok, orden_id, nota = es_aprobacion("APROBAR 42")
    assert ok is True
    assert orden_id == 42

    ok, orden_id, nota = es_aprobacion("APROBAR 99 todo bien")
    assert ok is True
    assert orden_id == 99
    assert nota == "TODO BIEN"


def test_es_aprobacion_boton():
    from app.routers.webhook import es_aprobacion
    ok, orden_id, nota = es_aprobacion("Aprobar", button_id="aprobar_42")
    assert ok is True
    assert orden_id == 42


def test_es_aprobacion_natural():
    from app.routers.webhook import es_aprobacion
    afirmativos = ["dale", "va", "ok", "sí", "si", "simon", "orale", "adelante", "sale"]
    for palabra in afirmativos:
        ok, orden_id, nota = es_aprobacion(palabra)
        assert ok is True, f"'{palabra}' deberia detectarse como aprobacion"
        assert orden_id is None  # Se resuelve con pendientes


def test_es_aprobacion_no_falso_positivo():
    from app.routers.webhook import es_aprobacion
    no_aprobacion = ["necesito cemento", "cuanto cuesta", "hola", "manda 50 varillas"]
    for texto in no_aprobacion:
        ok, _, _ = es_aprobacion(texto)
        assert ok is False, f"'{texto}' NO deberia detectarse como aprobacion"


def test_es_rechazo_comando():
    from app.routers.webhook import es_rechazo
    ok, orden_id, motivo = es_rechazo("RECHAZAR 42 muy caro")
    assert ok is True
    assert orden_id == 42
    assert "MUY CARO" in motivo


def test_es_rechazo_boton():
    from app.routers.webhook import es_rechazo
    ok, orden_id, _ = es_rechazo("Rechazar", button_id="rechazar_42")
    assert ok is True
    assert orden_id == 42


def test_es_rechazo_natural():
    from app.routers.webhook import es_rechazo
    negativos = ["no", "nel", "rechazado", "negativo", "no va", "cancela"]
    for palabra in negativos:
        ok, orden_id, _ = es_rechazo(palabra)
        assert ok is True, f"'{palabra}' deberia detectarse como rechazo"
        assert orden_id is None


def test_componer_mensaje_aprobacion(db, usuario_test, proveedor_test):
    from app.models.orden import Orden
    from app.models.pedido import Pedido
    from app.models.cotizacion import Cotizacion
    from app.services.aprobacion_service import componer_mensaje_aprobacion
    import json

    pedido = Pedido(usuario_id=usuario_test.id, mensaje_original="test", status="enviado")
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    cotizacion = Cotizacion(
        pedido_id=pedido.id, proveedor_id=proveedor_test.id,
        total=45000, subtotal=43000, costo_flete=2000, status="respondida",
    )
    db.add(cotizacion)
    db.commit()
    db.refresh(cotizacion)

    orden = Orden(
        pedido_id=pedido.id,
        cotizacion_id=cotizacion.id,
        usuario_id=usuario_test.id,
        proveedor_id=proveedor_test.id,
        total=45000.0,
        items=json.dumps([{"nombre": "Concreto f'c 250", "cantidad": 15, "unidad": "m3"}]),
        direccion_entrega="Zapopan, Jalisco",
        status="pendiente_aprobacion",
    )
    db.add(orden)
    db.commit()
    db.refresh(orden)

    resultado = componer_mensaje_aprobacion(orden, usuario_test, db=db)
    assert "texto" in resultado
    assert "botones" in resultado
    assert len(resultado["botones"]) == 2
    assert "Aprobar" in resultado["botones"][0]["title"]
    assert "$45,000" in resultado["texto"]


def test_necesita_aprobacion_sin_empresa(db, usuario_test):
    from app.services.aprobacion_service import necesita_aprobacion
    assert necesita_aprobacion(db, usuario_test.id, 50000) is False
