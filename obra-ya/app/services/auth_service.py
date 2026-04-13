"""
Servicio de autenticacion — registro, login, JWT, OAuth.
"""
import logging
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import settings
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def crear_token(usuario_id: int, email: str = "", nombre: str = "") -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(usuario_id),
        "email": email,
        "nombre": nombre,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verificar_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def registrar_usuario(
    db: Session,
    email: str,
    password: str,
    nombre: str,
    telefono: str = "",
    telefono_codigo_pais: str = "+52",
    empresa: str = "",
    tipo: str = "comprador",
    es_proveedor: bool = False,
) -> tuple[Usuario | None, str]:
    """
    Registra un usuario con email/password.
    Returns (usuario, error_msg). Si error_msg != "", hubo error.
    """
    # Verificar email duplicado
    existente = db.query(Usuario).filter(Usuario.email == email.lower().strip()).first()
    if existente:
        return None, "Ya existe una cuenta con este correo."

    # Verificar telefono duplicado (si se proporcionó)
    telefono_completo = ""
    if telefono:
        telefono_limpio = telefono.strip().replace(" ", "").replace("-", "")
        telefono_completo = f"{telefono_codigo_pais}{telefono_limpio}" if not telefono_limpio.startswith("+") else telefono_limpio
        # Quitar el + para guardar consistente
        telefono_completo = telefono_completo.replace("+", "")

        existente_tel = db.query(Usuario).filter(Usuario.telefono == telefono_completo).first()
        if existente_tel:
            return None, "Ya existe una cuenta con este numero de telefono."

    usuario = Usuario(
        email=email.lower().strip(),
        password_hash=hash_password(password),
        nombre=nombre.strip(),
        telefono=telefono_completo or None,
        telefono_codigo_pais=telefono_codigo_pais,
        empresa=empresa.strip() if empresa else None,
        tipo=tipo,
        es_proveedor=es_proveedor,
        auth_provider="email",
        email_verificado=False,
        ultimo_login=datetime.now(timezone.utc),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    logger.info(f"Usuario registrado: {email} (tipo={tipo}, proveedor={es_proveedor})")
    return usuario, ""


def login_email(db: Session, email: str, password: str) -> tuple[Usuario | None, str]:
    """Login con email/password. Returns (usuario, error_msg)."""
    usuario = db.query(Usuario).filter(Usuario.email == email.lower().strip()).first()
    if not usuario:
        return None, "Correo o contrasena incorrectos."

    if not usuario.password_hash:
        provider = usuario.auth_provider or "otro metodo"
        return None, f"Esta cuenta se registro con {provider}. Usa ese metodo para iniciar sesion."

    if not verify_password(password, usuario.password_hash):
        return None, "Correo o contrasena incorrectos."

    usuario.ultimo_login = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"Login exitoso: {email}")
    return usuario, ""


def login_o_registrar_oauth(
    db: Session,
    email: str,
    nombre: str,
    provider: str,
    provider_id: str,
    avatar_url: str = "",
) -> tuple[Usuario, bool]:
    """
    Login o registro via Google/Microsoft OAuth.
    Returns (usuario, es_nuevo).
    """
    # Buscar por provider_id primero
    usuario = db.query(Usuario).filter(
        Usuario.auth_provider == provider,
        Usuario.auth_provider_id == provider_id,
    ).first()

    if usuario:
        usuario.ultimo_login = datetime.now(timezone.utc)
        if avatar_url:
            usuario.avatar_url = avatar_url
        db.commit()
        return usuario, False

    # Buscar por email (puede haber cuenta manual con el mismo email)
    usuario = db.query(Usuario).filter(Usuario.email == email.lower().strip()).first()
    if usuario:
        # Vincular OAuth a cuenta existente
        usuario.auth_provider = provider
        usuario.auth_provider_id = provider_id
        usuario.email_verificado = True
        usuario.ultimo_login = datetime.now(timezone.utc)
        if avatar_url:
            usuario.avatar_url = avatar_url
        if nombre and not usuario.nombre:
            usuario.nombre = nombre
        db.commit()
        return usuario, False

    # Crear cuenta nueva
    usuario = Usuario(
        email=email.lower().strip(),
        nombre=nombre,
        auth_provider=provider,
        auth_provider_id=provider_id,
        avatar_url=avatar_url,
        email_verificado=True,
        ultimo_login=datetime.now(timezone.utc),
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    logger.info(f"OAuth registro: {email} via {provider}")
    return usuario, True
