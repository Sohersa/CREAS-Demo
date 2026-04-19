"""
Servicio de geocoding — convierte coordenadas GPS a direccion estructurada.

Usa Nominatim (OpenStreetMap) gratis, sin API key.
Parse estructurado: separa calle, colonia, municipio, estado, codigo postal.

Tambien valida si la ubicacion esta dentro del area de servicio.
"""
import logging
from typing import TypedDict, Optional

import httpx

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/reverse"

# Jalisco metropolitan area bounding box (incluye GDL, Zapopan, Tlaquepaque,
# Tonala, Tlajomulco, El Salto, Ixtlahuacan, Juanacatlan)
BBOX_JALISCO_METRO = {
    "min_lat": 20.40,
    "max_lat": 20.90,
    "min_lng": -103.70,
    "max_lng": -103.20,
}

# Municipios servibles (Jalisco)
MUNICIPIOS_SERVICIO = {
    "guadalajara", "zapopan", "tlaquepaque", "san pedro tlaquepaque",
    "tonala", "tonalá", "tlajomulco", "tlajomulco de zuniga",
    "el salto", "ixtlahuacan de los membrillos", "juanacatlan", "juanacatlán",
}


class LocationInfo(TypedDict, total=False):
    ok: bool
    latitud: float
    longitud: float
    direccion_completa: str         # display_name de Nominatim (ej: "Av. Lopez Mateos 2375, Zapopan, Jalisco")
    calle: str                      # "Avenida Lopez Mateos 2375"
    colonia: str                    # "Ciudad Granja"
    municipio: str                  # "Zapopan"
    estado: str                     # "Jalisco"
    codigo_postal: str              # "45010"
    pais: str                       # "Mexico"
    en_area_servicio: bool
    fuera_servicio_motivo: str


async def resolver_ubicacion(
    latitud: float,
    longitud: float,
    direccion_whatsapp: str = "",
    nombre_lugar: str = "",
) -> LocationInfo:
    """
    Convierte coordenadas GPS a informacion estructurada.
    Si WhatsApp ya nos mando una direccion, tambien la enriquece con la del
    servicio de geocoding.
    """
    # Validar rango GPS razonable
    try:
        lat = float(latitud)
        lng = float(longitud)
    except (ValueError, TypeError):
        return {"ok": False, "fuera_servicio_motivo": "coordenadas invalidas"}

    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return {"ok": False, "fuera_servicio_motivo": "coordenadas fuera de rango GPS"}

    # Bounding box rapido — evita llamar Nominatim si esta claramente fuera
    en_area = _en_bbox_jalisco(lat, lng)

    # Reverse geocoding
    info = await _consultar_nominatim(lat, lng)
    info["latitud"] = lat
    info["longitud"] = lng

    # Si el usuario mando nombre o direccion desde WhatsApp, combinar
    if nombre_lugar and not info.get("calle"):
        info["calle"] = nombre_lugar
    if direccion_whatsapp and not info.get("direccion_completa"):
        info["direccion_completa"] = direccion_whatsapp

    # Validacion de area de servicio (prioriza municipio real si lo tenemos)
    municipio_lower = info.get("municipio", "").lower().strip()
    if municipio_lower and municipio_lower in MUNICIPIOS_SERVICIO:
        info["en_area_servicio"] = True
    elif en_area and not municipio_lower:
        # Bbox dice si pero Nominatim no nos devolvio municipio — damos el beneficio de la duda
        info["en_area_servicio"] = True
    else:
        info["en_area_servicio"] = False
        if municipio_lower:
            info["fuera_servicio_motivo"] = f"{info.get('municipio', 'Ese municipio')} aun no esta en nuestra zona"
        else:
            info["fuera_servicio_motivo"] = "Ubicacion fuera del area metropolitana de Guadalajara"

    info["ok"] = True
    return info


def _en_bbox_jalisco(lat: float, lng: float) -> bool:
    """Check rapido de bounding box — antes de llamar Nominatim."""
    return (
        BBOX_JALISCO_METRO["min_lat"] <= lat <= BBOX_JALISCO_METRO["max_lat"]
        and BBOX_JALISCO_METRO["min_lng"] <= lng <= BBOX_JALISCO_METRO["max_lng"]
    )


async def _consultar_nominatim(lat: float, lng: float) -> dict:
    """Llama Nominatim y parsea la respuesta a campos estructurados."""
    params = {
        "lat": str(lat),
        "lon": str(lng),
        "format": "json",
        "addressdetails": 1,
        "accept-language": "es",
        "zoom": 18,  # max detalle
    }
    headers = {"User-Agent": "ObraYa/1.0 (gerencia@obraya.com)"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(NOMINATIM_URL, params=params, headers=headers)
        if r.status_code != 200:
            logger.warning(f"Nominatim respondio {r.status_code}")
            return {}
        data = r.json()
    except httpx.RequestError as e:
        logger.error(f"Error Nominatim: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error inesperado Nominatim: {e}")
        return {}

    addr = data.get("address", {})

    # Municipio: Nominatim usa varios campos segun el lugar
    municipio = (
        addr.get("city")
        or addr.get("town")
        or addr.get("municipality")
        or addr.get("county")
        or addr.get("village")
        or ""
    )

    # Colonia/suburbio
    colonia = (
        addr.get("neighbourhood")
        or addr.get("suburb")
        or addr.get("quarter")
        or addr.get("hamlet")
        or ""
    )

    # Calle con numero
    numero = addr.get("house_number", "")
    calle_nombre = addr.get("road", "") or addr.get("pedestrian", "")
    calle = f"{calle_nombre} {numero}".strip() if calle_nombre else ""

    return {
        "direccion_completa": data.get("display_name", "")[:300],
        "calle": calle[:100],
        "colonia": colonia[:100],
        "municipio": municipio[:100],
        "estado": addr.get("state", "")[:100],
        "codigo_postal": addr.get("postcode", "")[:10],
        "pais": addr.get("country", "")[:50],
    }


def formatear_ubicacion_corta(info: LocationInfo) -> str:
    """
    Formato compacto para mostrar al usuario:
    'Av. Lopez Mateos 2375, Ciudad Granja, Zapopan'
    """
    partes = []
    if info.get("calle"):
        partes.append(info["calle"])
    if info.get("colonia"):
        partes.append(info["colonia"])
    if info.get("municipio"):
        partes.append(info["municipio"])
    if not partes and info.get("direccion_completa"):
        # Fallback a display_name truncado
        return info["direccion_completa"][:100]
    return ", ".join(partes) if partes else f"({info.get('latitud')}, {info.get('longitud')})"
