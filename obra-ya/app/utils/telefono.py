"""
Utilidad para normalizar numeros de telefono mexicanos.

WhatsApp usa el formato internacional sin +: 521XXXXXXXXXX
  - 52  = codigo de pais Mexico
  - 1   = prefijo para numeros moviles (obligatorio desde 2019)
  - XXXXXXXXXX = 10 digitos del numero local

Este modulo normaliza cualquier formato de entrada al formato correcto.
"""
import re


def normalizar_telefono_mx(telefono: str) -> str:
    """
    Normaliza un numero de telefono mexicano al formato WhatsApp: 521XXXXXXXXXX

    Acepta:
      - 3333859426       → 5213333859426
      - 523333859426     → 5213333859426
      - 5213333859426    → 5213333859426
      - +5213333859426   → 5213333859426
      - +523333859426    → 5213333859426
      - 33 3385 9426     → 5213333859426
    """
    if not telefono:
        return telefono

    # Quitar todo excepto digitos
    solo_digitos = re.sub(r"\D", "", telefono)

    if not solo_digitos:
        return telefono

    # Si tiene 10 digitos → es numero local, agregar 521
    if len(solo_digitos) == 10:
        return f"521{solo_digitos}"

    # Si tiene 12 digitos y empieza con 52 (sin el 1) → agregar el 1
    if len(solo_digitos) == 12 and solo_digitos.startswith("52") and not solo_digitos.startswith("521"):
        return f"521{solo_digitos[2:]}"

    # Si tiene 13 digitos y empieza con 521 → ya esta correcto
    if len(solo_digitos) == 13 and solo_digitos.startswith("521"):
        return solo_digitos

    # Cualquier otro caso, devolver solo digitos
    return solo_digitos
