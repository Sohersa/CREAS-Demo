"""
Tests de parseo de webhooks WhatsApp — texto, audio, imagen, ubicacion, botones.
"""
from app.services.whatsapp import parsear_webhook, partir_mensaje


def _webhook_body(tipo="text", **kwargs):
    """Helper para generar bodies de webhook."""
    mensaje = {
        "from": "5213312345678",
        "id": "wamid.abc123",
        "timestamp": "1712000000",
        "type": tipo,
    }
    if tipo == "text":
        mensaje["text"] = {"body": kwargs.get("text", "Hola")}
    elif tipo == "audio":
        mensaje["audio"] = {"id": kwargs.get("media_id", "media_123")}
    elif tipo == "image":
        mensaje["image"] = {"id": kwargs.get("media_id", "img_123")}
    elif tipo == "location":
        mensaje["location"] = {
            "latitude": kwargs.get("lat", 20.6597),
            "longitude": kwargs.get("lng", -103.3496),
            "name": kwargs.get("name", ""),
            "address": kwargs.get("address", ""),
        }
    elif tipo == "interactive":
        mensaje["interactive"] = kwargs.get("interactive", {})

    return {
        "entry": [{
            "changes": [{
                "value": {
                    "contacts": [{"profile": {"name": kwargs.get("nombre", "Juan Test")}}],
                    "messages": [mensaje],
                }
            }]
        }]
    }


class TestParsearWebhook:
    def test_texto(self):
        r = parsear_webhook(_webhook_body("text", text="Necesito 15m3 de concreto"))
        assert r is not None
        assert r["tipo_mensaje"] == "texto"
        assert "concreto" in r["contenido"]
        assert r["telefono"] == "5213312345678"
        assert r["nombre"] == "Juan Test"

    def test_audio(self):
        r = parsear_webhook(_webhook_body("audio", media_id="audio_xyz"))
        assert r["tipo_mensaje"] == "audio"
        assert r["contenido"] == "audio_xyz"

    def test_imagen(self):
        r = parsear_webhook(_webhook_body("image", media_id="img_xyz"))
        assert r["tipo_mensaje"] == "imagen"
        assert r["contenido"] == "img_xyz"

    def test_ubicacion(self):
        r = parsear_webhook(_webhook_body("location", lat=20.65, lng=-103.34, address="Zapopan"))
        assert r["tipo_mensaje"] == "ubicacion"
        assert r["contenido"]["latitude"] == 20.65

    def test_boton_reply(self):
        interactive = {
            "type": "button_reply",
            "button_reply": {"id": "aprobar_42", "title": "Aprobar"},
        }
        r = parsear_webhook(_webhook_body("interactive", interactive=interactive))
        assert r["tipo_mensaje"] == "texto"
        assert r["contenido"] == "Aprobar"
        assert r["button_id"] == "aprobar_42"

    def test_list_reply(self):
        interactive = {
            "type": "list_reply",
            "list_reply": {"id": "prov_5_10", "title": "Materiales SA"},
        }
        r = parsear_webhook(_webhook_body("interactive", interactive=interactive))
        assert r["tipo_mensaje"] == "texto"
        assert r["contenido"] == "Materiales SA"

    def test_sin_mensajes(self):
        body = {"entry": [{"changes": [{"value": {"statuses": [{"id": "wamid.abc"}]}}]}]}
        assert parsear_webhook(body) is None

    def test_body_vacio(self):
        assert parsear_webhook({}) is None


class TestPartirMensaje:
    def test_mensaje_corto(self):
        partes = partir_mensaje("Hola mundo", 100)
        assert len(partes) == 1
        assert partes[0] == "Hola mundo"

    def test_mensaje_largo(self):
        msg = "\n".join([f"Linea {i}: " + "x" * 50 for i in range(100)])
        partes = partir_mensaje(msg, 500)
        assert len(partes) > 1
        for p in partes:
            assert len(p) <= 500

    def test_mensaje_sin_saltos(self):
        msg = "x" * 1000
        partes = partir_mensaje(msg, 300)
        assert len(partes) > 1
        for p in partes:
            assert len(p) <= 300
