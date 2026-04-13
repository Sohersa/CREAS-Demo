"""
Tests para el parseo de webhooks de WhatsApp.

Ejecutar: python -m tests.test_mensajes
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.whatsapp import parsear_webhook, partir_mensaje


def test_parsear_webhook_texto():
    """Prueba parseo de un mensaje de texto de WhatsApp."""
    print("TEST: Parsear webhook de texto")

    body = {
        "entry": [{
            "changes": [{
                "value": {
                    "contacts": [{"profile": {"name": "Juan Perez"}}],
                    "messages": [{
                        "from": "5213312345678",
                        "id": "wamid.abc123",
                        "timestamp": "1712000000",
                        "type": "text",
                        "text": {"body": "Necesito 15m3 de concreto del 250"}
                    }]
                }
            }]
        }]
    }

    resultado = parsear_webhook(body)
    assert resultado is not None, "Deberia parsear correctamente"
    assert resultado["telefono"] == "5213312345678"
    assert resultado["nombre"] == "Juan Perez"
    assert resultado["tipo_mensaje"] == "texto"
    assert "concreto" in resultado["contenido"]
    print(f"  OK: {resultado}")


def test_parsear_webhook_audio():
    """Prueba parseo de un mensaje de audio."""
    print("\nTEST: Parsear webhook de audio")

    body = {
        "entry": [{
            "changes": [{
                "value": {
                    "contacts": [{"profile": {"name": "Maria Lopez"}}],
                    "messages": [{
                        "from": "5213398765432",
                        "id": "wamid.xyz789",
                        "timestamp": "1712000001",
                        "type": "audio",
                        "audio": {"id": "media_id_12345", "mime_type": "audio/ogg"}
                    }]
                }
            }]
        }]
    }

    resultado = parsear_webhook(body)
    assert resultado is not None
    assert resultado["tipo_mensaje"] == "audio"
    assert resultado["contenido"] == "media_id_12345"
    print(f"  OK: {resultado}")


def test_parsear_webhook_vacio():
    """Prueba que un webhook sin mensajes devuelva None."""
    print("\nTEST: Parsear webhook sin mensajes")

    body = {"entry": [{"changes": [{"value": {"statuses": [{"id": "wamid.abc"}]}}]}]}
    resultado = parsear_webhook(body)
    assert resultado is None, "Deberia devolver None para notificaciones sin mensaje"
    print("  OK: None (correcto)")


def test_partir_mensaje():
    """Prueba que mensajes largos se partan correctamente."""
    print("\nTEST: Partir mensaje largo")

    mensaje_largo = "\n".join([f"Linea {i}: " + "x" * 50 for i in range(100)])
    partes = partir_mensaje(mensaje_largo, 500)

    print(f"  Mensaje original: {len(mensaje_largo)} chars")
    print(f"  Partes generadas: {len(partes)}")
    for i, parte in enumerate(partes):
        print(f"    Parte {i+1}: {len(parte)} chars")
        assert len(parte) <= 500, f"Parte {i+1} excede el limite"

    print("  OK: Todas las partes dentro del limite")


if __name__ == "__main__":
    print("=" * 60)
    print("TESTS DE WHATSAPP")
    print("=" * 60)

    test_parsear_webhook_texto()
    test_parsear_webhook_audio()
    test_parsear_webhook_vacio()
    test_partir_mensaje()

    print(f"\n{'='*60}")
    print("TODOS LOS TESTS PASARON")
    print(f"{'='*60}")
