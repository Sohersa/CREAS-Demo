"""
Tests de la comparativa — formato corto, botones/lista, guardado en BD.
"""
import json
from datetime import datetime, timezone

from app.models.pedido import Pedido
from app.models.proveedor import Proveedor
from app.models.solicitud_proveedor import SolicitudProveedor
from app.services.comparativa_activa import generar_comparativa_desde_respuestas


def _crear_pedido_con_respuestas(db, num_proveedores=3):
    """Helper: crea pedido + proveedores + respuestas."""
    pedido = Pedido(
        usuario_id=1,
        mensaje_original="15m3 de concreto fc250",
        status="cotizando",
    )
    db.add(pedido)
    db.commit()
    db.refresh(pedido)

    precios = [45000, 48000, 52000, 55000, 60000]
    for i in range(num_proveedores):
        prov = Proveedor(
            nombre=f"Proveedor {chr(65+i)}",
            tipo="mediano",
            municipio="Zapopan",
            calificacion=4.0 + (i * 0.2),
            activo=True,
        )
        db.add(prov)
        db.commit()
        db.refresh(prov)

        sol = SolicitudProveedor(
            pedido_id=pedido.id,
            proveedor_id=prov.id,
            status="respondida",
            precio_total=precios[i],
            costo_flete=2000 if i % 2 == 0 else 0,
            incluye_flete=(i % 2 != 0),
            tiempo_entrega="24h" if i == 0 else f"{(i+1)*24}h",
            respondida_at=datetime.now(timezone.utc),
        )
        db.add(sol)

    db.commit()
    return pedido


class TestComparativa:
    def test_genera_resultado_dict(self, db):
        pedido = _crear_pedido_con_respuestas(db, 3)
        resultado = generar_comparativa_desde_respuestas(db, pedido.id)

        assert resultado is not None
        assert "texto" in resultado
        assert "opciones" in resultado
        assert "num_opciones" in resultado
        assert resultado["num_opciones"] == 3

    def test_formato_corto(self, db):
        pedido = _crear_pedido_con_respuestas(db, 3)
        resultado = generar_comparativa_desde_respuestas(db, pedido.id)

        lineas = resultado["texto"].strip().split("\n")
        # Deberia ser max ~15 lineas (formato corto)
        assert len(lineas) < 25, f"Comparativa demasiado larga: {len(lineas)} lineas"

    def test_mas_barato_primero(self, db):
        pedido = _crear_pedido_con_respuestas(db, 3)
        resultado = generar_comparativa_desde_respuestas(db, pedido.id)

        assert "MÁS BARATO" in resultado["texto"]
        assert "$45,000" in resultado["texto"]

    def test_opciones_para_botones(self, db):
        pedido = _crear_pedido_con_respuestas(db, 2)
        resultado = generar_comparativa_desde_respuestas(db, pedido.id)

        assert len(resultado["opciones"]) == 2
        for opt in resultado["opciones"]:
            assert "id" in opt
            assert "title" in opt
            assert "description" in opt
            assert len(opt["title"]) <= 20

    def test_opciones_para_lista(self, db):
        pedido = _crear_pedido_con_respuestas(db, 5)
        resultado = generar_comparativa_desde_respuestas(db, pedido.id)

        assert resultado["num_opciones"] == 5

    def test_sin_respuestas_retorna_none(self, db):
        pedido = Pedido(usuario_id=1, mensaje_original="test", status="cotizando")
        db.add(pedido)
        db.commit()
        db.refresh(pedido)

        resultado = generar_comparativa_desde_respuestas(db, pedido.id)
        assert resultado is None

    def test_ahorro_calculado(self, db):
        pedido = _crear_pedido_con_respuestas(db, 3)
        resultado = generar_comparativa_desde_respuestas(db, pedido.id)

        # Ahorro = 52000 - 45000 = 7000
        assert "Ahorro" in resultado["texto"]
        assert "$7,000" in resultado["texto"]
