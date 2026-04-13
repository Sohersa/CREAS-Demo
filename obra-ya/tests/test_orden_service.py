"""
Tests del servicio de ordenes — creacion, transiciones, estados.
"""
import json

from app.models.orden import Orden
from app.models.pedido import Pedido
from app.models.cotizacion import Cotizacion
from app.services.orden_service import crear_orden, TRANSICIONES


class TestTransiciones:
    def test_transiciones_validas(self):
        assert "confirmada" in TRANSICIONES
        assert "preparando" in TRANSICIONES["confirmada"]
        assert "cancelada" in TRANSICIONES["confirmada"]

    def test_pendiente_aprobacion_transiciones(self):
        assert "pendiente_aprobacion" in TRANSICIONES
        assert "confirmada" in TRANSICIONES["pendiente_aprobacion"]
        assert "cancelada" in TRANSICIONES["pendiente_aprobacion"]

    def test_no_puede_retroceder(self):
        assert "cotizando" not in TRANSICIONES.get("confirmada", [])
        assert "confirmada" not in TRANSICIONES.get("entregada", [])


class TestCrearOrden:
    def _crear_pedido_y_cotizacion(self, db, usuario_test, proveedor_test, total=45000):
        pedido = Pedido(
            usuario_id=usuario_test.id,
            mensaje_original="15m3 concreto",
            status="enviado",
        )
        db.add(pedido)
        db.commit()
        db.refresh(pedido)

        cotizacion = Cotizacion(
            pedido_id=pedido.id,
            proveedor_id=proveedor_test.id,
            total=total,
            subtotal=total - 2000,
            costo_flete=2000,
            tiempo_entrega="24h",
            status="respondida",
        )
        db.add(cotizacion)
        db.commit()
        db.refresh(cotizacion)
        return pedido, cotizacion

    def test_crear_orden_basica(self, db, usuario_test, proveedor_test):
        pedido, cotizacion = self._crear_pedido_y_cotizacion(db, usuario_test, proveedor_test)

        orden = crear_orden(db, usuario_test.id, cotizacion.id)
        assert orden is not None
        assert orden.total == 45000
        assert orden.proveedor_id == proveedor_test.id
        assert orden.status == "confirmada"

    def test_crear_orden_pendiente_aprobacion(self, db, usuario_test, proveedor_test):
        pedido, cotizacion = self._crear_pedido_y_cotizacion(db, usuario_test, proveedor_test, total=100000)

        orden = crear_orden(db, usuario_test.id, cotizacion.id, status_inicial="pendiente_aprobacion")
        assert orden is not None
        assert orden.status == "pendiente_aprobacion"
