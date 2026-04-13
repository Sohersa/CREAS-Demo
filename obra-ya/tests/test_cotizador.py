"""
Tests para el motor de cotizacion.
Verifica que busque proveedores y genere cotizaciones correctas.

Ejecutar: python -m tests.test_cotizador
"""
import json
import sys
import os

# Fix encoding para emojis en Windows
sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, crear_tablas
from app.services.cotizador import generar_cotizaciones, buscar_producto_en_bd
from app.services.comparador import generar_comparativa_simple, resumir_pedido


def test_busqueda_productos():
    """Prueba que la busqueda de productos funcione."""
    crear_tablas()
    db = SessionLocal()

    print("=" * 60)
    print("TEST: Busqueda de productos en BD")
    print("=" * 60)

    productos_a_buscar = [
        ("Concreto Premezclado f'c 250", "concreto"),
        ("Varilla Corrugada 3/8", "acero"),
        ("Grava 3/4", "agregados"),
        ("Cemento Gris", "cementantes"),
        ("Block Concreto 15x20x40", "block"),
        ("Tubo PVC Sanitario 4", "tuberia"),
        ("Impermeabilizante Acrilico", "impermeabilizante"),
        ("Cable THW Cal 12", "electrico"),
    ]

    for nombre, categoria in productos_a_buscar:
        resultados = buscar_producto_en_bd(db, nombre, categoria)
        print(f"\n  {nombre}:")
        if resultados:
            for r in resultados[:3]:
                print(f"    - {r['proveedor_nombre']}: ${r['precio_unitario']:,.0f}/{r['unidad']}")
        else:
            print(f"    (sin resultados)")

    db.close()


def test_cotizacion_concreto():
    """Prueba cotizacion de un pedido de concreto."""
    db = SessionLocal()

    print("\n" + "=" * 60)
    print("TEST: Cotizacion de 15m3 concreto f'c 250")
    print("=" * 60)

    pedido = {
        "status": "completo",
        "pedido": {
            "items": [
                {
                    "categoria": "concreto",
                    "producto": "Concreto Premezclado f'c 250",
                    "cantidad": 15,
                    "unidad": "m3",
                }
            ],
            "entrega": {
                "direccion": "Zapopan, Jalisco",
                "fecha": "2026-04-10",
            }
        }
    }

    cotizaciones = generar_cotizaciones(db, pedido)
    resumen = resumir_pedido(pedido)

    print(f"\nProveedores encontrados: {len(cotizaciones)}")
    for cot in cotizaciones:
        print(f"  {cot['proveedor_nombre']}: ${cot['total']:,.0f} (subtotal ${cot['subtotal']:,.0f} + flete ${cot['costo_flete']:,.0f})")

    if cotizaciones:
        print("\n--- COMPARATIVA WHATSAPP ---")
        comparativa = generar_comparativa_simple(cotizaciones, resumen)
        print(comparativa)

    db.close()


def test_cotizacion_mixta():
    """Prueba cotizacion de pedido con multiples categorias."""
    db = SessionLocal()

    print("\n" + "=" * 60)
    print("TEST: Pedido mixto (concreto + varilla + grava + cemento)")
    print("=" * 60)

    pedido = {
        "status": "completo",
        "pedido": {
            "items": [
                {"categoria": "concreto", "producto": "Concreto Premezclado f'c 250", "cantidad": 10, "unidad": "m3"},
                {"categoria": "acero", "producto": "Varilla Corrugada 3/8", "cantidad": 200, "unidad": "piezas"},
                {"categoria": "agregados", "producto": "Grava 3/4", "cantidad": 21, "unidad": "m3"},
                {"categoria": "cementantes", "producto": "Cemento Gris", "cantidad": 100, "unidad": "bultos"},
            ],
            "entrega": {
                "direccion": "Zapopan, Jalisco",
                "fecha": "2026-04-10",
            }
        }
    }

    cotizaciones = generar_cotizaciones(db, pedido)
    resumen = resumir_pedido(pedido)

    print(f"\nProveedores con alguna disponibilidad: {len(cotizaciones)}")
    for cot in cotizaciones:
        print(f"  {cot['proveedor_nombre']}: ${cot['total']:,.0f} ({cot['items_disponibles']}/{cot['total_items_pedido']} materiales)")

    if cotizaciones:
        print("\n--- COMPARATIVA WHATSAPP ---")
        comparativa = generar_comparativa_simple(cotizaciones, resumen)
        print(comparativa)

    db.close()


if __name__ == "__main__":
    # Primero asegurarnos de que hay datos
    try:
        from seed import cargar_semilla
        cargar_semilla()
    except Exception:
        print("Ejecuta primero: python seed.py")

    test_busqueda_productos()
    test_cotizacion_concreto()
    test_cotizacion_mixta()
