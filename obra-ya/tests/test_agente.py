"""
Tests para validar que el agente interpreta correctamente
mensajes tipicos de obra en Mexico.

Ejecutar: python -m tests.test_agente
"""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.agente_claude import interpretar_mensaje

# Mensajes de prueba reales de obra
MENSAJES_TEST = [
    # CONCRETO
    "Necesito 15 metros cubicos de concreto f'c 250 para el jueves en Zapopan",
    "Mandame 3 ollas de concreto del 200, con bomba, para el lunes a primera hora",
    # ACERO
    "Manda 100 varillas del 3/8 a la obra",
    "Ocupo 50 varillas del medio y 10 hojas de malla 6x6",
    "Necesito 20 armex del 15x20 y 30 kilos de alambre recocido",
    # AGREGADOS
    "Ocupo 2 viajes de grava y 1 de arena",
    "Quiero un viaje de tepetate para relleno y medio viaje de piedra braza",
    # CEMENTANTES
    "Necesito 50 bultos del gris y 20 varillas del numero 4",
    "Manda una tonelada de cemento y 30 bultos de cal",
    # BLOCK
    "Necesito un millar de block del 15 y medio millar de tabique rojo",
    # MENSAJES AMBIGUOS
    "Necesito cemento",
    "Mandame varilla",
    "Cuanto cuesta la grava?",
    # VOZ TRANSCRITA (con errores tipicos)
    "necesito quince metros de concreto efe prima ce doscientos cincuenta",
    "manda cien varillas del tres octavos grado cuarenta y dos",
    # PEDIDO COMPLEJO
    "Necesito para la obra de Zapopan: 10m3 de concreto del 250 con bomba, 200 varillas del 3/8, 50 del medio, 3 viajes de grava, 100 bultos de cemento, y un millar de block del 15. Todo para el jueves.",
]


async def test_todos():
    print("=" * 60)
    print("PROBANDO AGENTE DE INTERPRETACION OBRAYA")
    print("=" * 60)

    exitosos = 0
    fallidos = 0

    for i, mensaje in enumerate(MENSAJES_TEST):
        print(f"\n{'='*60}")
        print(f"TEST {i+1}/{len(MENSAJES_TEST)}")
        print(f"MENSAJE: {mensaje}")
        print("-" * 60)

        try:
            resultado = await interpretar_mensaje(f"test_{i}", mensaje)

            status = resultado.get("status", "N/A")
            print(f"STATUS: {status}")

            msg_usuario = resultado.get("mensaje_usuario", "")
            if msg_usuario:
                print(f"RESPUESTA: {msg_usuario[:300]}")

            if status in ("completo", "incompleto"):
                exitosos += 1
                items = resultado.get("pedido", {}).get("items", [])
                if items:
                    print(f"ITEMS DETECTADOS: {len(items)}")
                    for item in items:
                        print(f"  - {item.get('cantidad', '?')} {item.get('unidad', '?')} {item.get('producto', '?')}")

                preguntas = resultado.get("preguntas_pendientes", [])
                if preguntas:
                    print(f"PREGUNTAS: {preguntas}")
            elif status == "conversacion":
                exitosos += 1  # Respuestas conversacionales tambien son validas
            else:
                fallidos += 1
                print(f"  RESULTADO INESPERADO: {json.dumps(resultado, indent=2, ensure_ascii=False)[:500]}")

        except Exception as e:
            fallidos += 1
            print(f"  ERROR: {e}")

    print(f"\n{'='*60}")
    print(f"RESULTADOS: {exitosos}/{len(MENSAJES_TEST)} exitosos, {fallidos} fallidos")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(test_todos())
