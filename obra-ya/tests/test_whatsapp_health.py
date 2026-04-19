"""
Tests del diagnostico de WhatsApp — categorizacion de errores de Meta.
"""
import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_not_configured():
    """Sin credenciales, debe retornar not_configured."""
    with patch("app.services.whatsapp_health.settings") as mock_s:
        mock_s.WHATSAPP_PROVIDER = "meta"
        mock_s.WHATSAPP_TOKEN = ""
        mock_s.WHATSAPP_PHONE_ID = ""
        from app.services.whatsapp_health import verificar_whatsapp
        r = await verificar_whatsapp()
        assert r["ok"] is False
        assert r["status"] == "not_configured"


@pytest.mark.asyncio
async def test_token_expired_detection():
    """Debe detectar token expirado por code=190 subcode=463."""
    mock_response = AsyncMock()
    mock_response.status_code = 401
    mock_response.json = lambda: {
        "error": {
            "message": "Error validating access token: Session has expired on Friday, 03-Apr-26 13:00:00 PDT.",
            "type": "OAuthException",
            "code": 190,
            "error_subcode": 463,
        }
    }

    with patch("app.services.whatsapp_health.settings") as mock_s:
        mock_s.WHATSAPP_PROVIDER = "meta"
        mock_s.WHATSAPP_TOKEN = "fake"
        mock_s.WHATSAPP_PHONE_ID = "123"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            from app.services.whatsapp_health import verificar_whatsapp
            r = await verificar_whatsapp()

    assert r["ok"] is False
    assert r["status"] == "token_expired"
    assert "expir" in r["mensaje"].lower()
    assert "System User" in r["sugerencia"] or "Meta Business" in r["sugerencia"]


@pytest.mark.asyncio
async def test_phone_id_invalid():
    """404 debe detectarse como phone_id_invalid."""
    mock_response = AsyncMock()
    mock_response.status_code = 404
    mock_response.text = "Unknown path components"

    with patch("app.services.whatsapp_health.settings") as mock_s:
        mock_s.WHATSAPP_PROVIDER = "meta"
        mock_s.WHATSAPP_TOKEN = "fake"
        mock_s.WHATSAPP_PHONE_ID = "999999"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            from app.services.whatsapp_health import verificar_whatsapp
            r = await verificar_whatsapp()

    assert r["ok"] is False
    assert r["status"] == "phone_id_invalid"


@pytest.mark.asyncio
async def test_healthy():
    """200 con datos del numero debe retornar healthy."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "display_phone_number": "+52 33 1234 5678",
        "verified_name": "ObraYa",
        "quality_rating": "GREEN",
    }

    with patch("app.services.whatsapp_health.settings") as mock_s:
        mock_s.WHATSAPP_PROVIDER = "meta"
        mock_s.WHATSAPP_TOKEN = "valid_token"
        mock_s.WHATSAPP_PHONE_ID = "123"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )
            from app.services.whatsapp_health import verificar_whatsapp
            r = await verificar_whatsapp()

    assert r["ok"] is True
    assert r["status"] == "healthy"
    assert r["detalles"]["verified_name"] == "ObraYa"
