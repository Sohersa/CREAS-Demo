"""
Actualiza variables en el archivo .env y recarga la config en caliente.
Sin reinicio del servidor requerido.
"""
import os
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)

_ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"


def actualizar_env_var(key: str, value: str) -> Tuple[bool, str]:
    """
    Actualiza (o crea) una variable en el .env de forma atomica.

    Returns:
        (ok, mensaje)
    """
    if not _ENV_PATH.exists():
        return False, f"Archivo .env no existe en {_ENV_PATH}"

    # Leer .env actual
    lineas = _ENV_PATH.read_text(encoding="utf-8").splitlines()
    encontrado = False

    for i, ln in enumerate(lineas):
        stripped = ln.strip()
        if stripped.startswith(f"{key}="):
            lineas[i] = f"{key}={value}"
            encontrado = True
            break

    if not encontrado:
        # Agregar al final si no existe
        if lineas and lineas[-1].strip():
            lineas.append("")
        lineas.append(f"{key}={value}")

    # Escritura atomica: escribir en .tmp y rename
    tmp_path = _ENV_PATH.with_suffix(".env.tmp")
    try:
        tmp_path.write_text("\n".join(lineas) + "\n", encoding="utf-8")
        tmp_path.replace(_ENV_PATH)
    except Exception as e:
        logger.error(f"Error escribiendo .env: {e}")
        try:
            tmp_path.unlink()
        except Exception:
            pass
        return False, f"Error escribiendo .env: {e}"

    # Actualizar os.environ inmediatamente
    os.environ[key] = value

    # Recargar settings en caliente
    try:
        from app.config import settings
        setattr(settings, key, value)
    except Exception as e:
        logger.warning(f"Variable actualizada en .env pero no se pudo recargar en memoria: {e}")

    logger.info(f"Variable {key} actualizada en .env (len={len(value)})")
    return True, f"Variable {key} actualizada correctamente"
