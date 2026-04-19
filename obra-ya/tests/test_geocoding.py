"""
Tests del servicio de geocoding — parseo de Nominatim, validacion de area de servicio.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_coordenadas_invalidas():
    from app.services.geocoding import resolver_ubicacion
    r = await resolver_ubicacion("abc", "xyz")
    assert r["ok"] is False
    assert "invalidas" in r["fuera_servicio_motivo"]


@pytest.mark.asyncio
async def test_coordenadas_fuera_rango():
    from app.services.geocoding import resolver_ubicacion
    r = await resolver_ubicacion(200, 200)  # lat > 90
    assert r["ok"] is False


@pytest.mark.asyncio
async def test_ubicacion_en_zapopan_es_area_servicio():
    """Coordenadas de Zapopan (Av. Lopez Mateos 2375) deben estar en area."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "display_name": "Av. Jose Guadalupe Gallo 2375, Ciudad Granja, Zapopan, Jalisco, 45010, Mexico",
        "address": {
            "road": "Avenida Jose Guadalupe Gallo",
            "house_number": "2375",
            "neighbourhood": "Ciudad Granja",
            "city": "Zapopan",
            "state": "Jalisco",
            "postcode": "45010",
            "country": "Mexico",
        },
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        from app.services.geocoding import resolver_ubicacion
        r = await resolver_ubicacion(20.6597, -103.4265)

    assert r["ok"] is True
    assert r["en_area_servicio"] is True
    assert r["municipio"] == "Zapopan"
    assert r["estado"] == "Jalisco"
    assert r["colonia"] == "Ciudad Granja"
    assert "2375" in r["calle"]
    assert r["codigo_postal"] == "45010"


@pytest.mark.asyncio
async def test_ubicacion_en_cdmx_NO_es_area_servicio():
    """CDMX debe ser rechazada como fuera de area."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "display_name": "Paseo de la Reforma 300, Cuauhtemoc, Ciudad de Mexico",
        "address": {
            "road": "Paseo de la Reforma",
            "house_number": "300",
            "city": "Ciudad de Mexico",
            "state": "Ciudad de Mexico",
            "country": "Mexico",
        },
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        from app.services.geocoding import resolver_ubicacion
        r = await resolver_ubicacion(19.4326, -99.1332)

    assert r["ok"] is True
    assert r["en_area_servicio"] is False
    assert r["municipio"] == "Ciudad de Mexico"
    assert "zona" in r["fuera_servicio_motivo"].lower() or "metropolitana" in r["fuera_servicio_motivo"].lower() or "area" in r["fuera_servicio_motivo"].lower()


@pytest.mark.asyncio
async def test_ubicacion_en_tlaquepaque_area_servicio():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "display_name": "Calle Independencia 123, San Pedro Tlaquepaque, Jalisco",
        "address": {
            "road": "Calle Independencia",
            "house_number": "123",
            "city": "San Pedro Tlaquepaque",
            "state": "Jalisco",
            "country": "Mexico",
        },
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
        from app.services.geocoding import resolver_ubicacion
        r = await resolver_ubicacion(20.6406, -103.3140)

    assert r["ok"] is True
    assert r["en_area_servicio"] is True


def test_formatear_ubicacion_corta_completa():
    from app.services.geocoding import formatear_ubicacion_corta
    info = {
        "calle": "Avenida Lopez Mateos 2375",
        "colonia": "Ciudad Granja",
        "municipio": "Zapopan",
        "estado": "Jalisco",
    }
    resultado = formatear_ubicacion_corta(info)
    assert "Lopez Mateos" in resultado
    assert "Ciudad Granja" in resultado
    assert "Zapopan" in resultado


def test_formatear_ubicacion_corta_fallback():
    """Sin calle/colonia, usa display_name."""
    from app.services.geocoding import formatear_ubicacion_corta
    info = {"direccion_completa": "Algun lugar en GDL"}
    assert formatear_ubicacion_corta(info) == "Algun lugar en GDL"


def test_bbox_jalisco_incluye_guadalajara():
    from app.services.geocoding import _en_bbox_jalisco
    # Guadalajara centro
    assert _en_bbox_jalisco(20.6597, -103.3496) is True
    # Zapopan
    assert _en_bbox_jalisco(20.7214, -103.3907) is True
    # CDMX
    assert _en_bbox_jalisco(19.4326, -99.1332) is False
    # Monterrey
    assert _en_bbox_jalisco(25.6866, -100.3161) is False
