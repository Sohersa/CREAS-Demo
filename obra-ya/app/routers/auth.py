"""
Router de autenticacion — registro, login, OAuth, perfil.
"""
import logging
import httpx
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.config import settings
from app.services.auth_service import (
    registrar_usuario, login_email, login_o_registrar_oauth,
    crear_token, verificar_token,
)
from app.models.usuario import Usuario

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


# ─── Schemas ──────────────────────────────────────────────────────────

class RegisterBody(BaseModel):
    email: str
    password: str
    nombre: str
    telefono: str = ""
    telefono_codigo_pais: str = "+52"
    empresa: str = ""
    tipo: str = "comprador"  # comprador | proveedor
    es_proveedor: bool = False


class LoginBody(BaseModel):
    email: str
    password: str


class OAuthBody(BaseModel):
    token: str  # ID token from Google/Microsoft
    provider: str  # "google" | "microsoft"


# ─── Helper: get current user from JWT ────────────────────────────────

def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> Usuario | None:
    if not authorization:
        return None
    token = authorization.replace("Bearer ", "")
    payload = verificar_token(token)
    if not payload:
        return None
    user_id = int(payload.get("sub", 0))
    return db.query(Usuario).filter(Usuario.id == user_id).first()


# ─── Endpoints ────────────────────────────────────────────────────────

@router.post("/register")
def register(body: RegisterBody, db: Session = Depends(get_db)):
    """Registro con email y contrasena."""
    if len(body.password) < 6:
        return {"ok": False, "error": "La contrasena debe tener al menos 6 caracteres."}

    if not body.email or "@" not in body.email:
        return {"ok": False, "error": "Correo electronico invalido."}

    usuario, error = registrar_usuario(
        db=db,
        email=body.email,
        password=body.password,
        nombre=body.nombre,
        telefono=body.telefono,
        telefono_codigo_pais=body.telefono_codigo_pais,
        empresa=body.empresa,
        tipo="proveedor" if body.es_proveedor else body.tipo,
        es_proveedor=body.es_proveedor,
    )

    if error:
        return {"ok": False, "error": error}

    token = crear_token(usuario.id, usuario.email or "", usuario.nombre or "")
    return {
        "ok": True,
        "token": token,
        "user": _user_dict(usuario),
    }


@router.post("/login")
def login(body: LoginBody, db: Session = Depends(get_db)):
    """Login con email y contrasena."""
    usuario, error = login_email(db, body.email, body.password)
    if error:
        return {"ok": False, "error": error}

    token = crear_token(usuario.id, usuario.email or "", usuario.nombre or "")
    return {
        "ok": True,
        "token": token,
        "user": _user_dict(usuario),
    }


@router.post("/oauth")
async def oauth_login(body: OAuthBody, db: Session = Depends(get_db)):
    """Login/registro via Google o Microsoft OAuth."""
    if body.provider == "google":
        user_info = await _verify_google_token(body.token)
    elif body.provider == "microsoft":
        user_info = await _verify_microsoft_token(body.token)
    else:
        return {"ok": False, "error": "Proveedor OAuth no soportado."}

    if not user_info:
        return {"ok": False, "error": "Token invalido o expirado."}

    usuario, es_nuevo = login_o_registrar_oauth(
        db=db,
        email=user_info["email"],
        nombre=user_info.get("name", ""),
        provider=body.provider,
        provider_id=user_info.get("sub", user_info.get("id", "")),
        avatar_url=user_info.get("picture", ""),
    )

    token = crear_token(usuario.id, usuario.email or "", usuario.nombre or "")
    return {
        "ok": True,
        "token": token,
        "user": _user_dict(usuario),
        "es_nuevo": es_nuevo,
    }


@router.get("/me")
def get_me(db: Session = Depends(get_db), authorization: str = Header(None)):
    """Obtener datos del usuario autenticado."""
    if not authorization:
        return {"ok": False, "error": "No autenticado."}

    token = authorization.replace("Bearer ", "")
    payload = verificar_token(token)
    if not payload:
        return {"ok": False, "error": "Token invalido o expirado."}

    user_id = int(payload.get("sub", 0))
    usuario = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not usuario:
        return {"ok": False, "error": "Usuario no encontrado."}

    return {"ok": True, "user": _user_dict(usuario)}


# ─── OAuth token verification ────────────────────────────────────────

async def _verify_google_token(id_token: str) -> dict | None:
    """Verifica un Google ID token usando el endpoint de Google."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
                timeout=10,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            # Verificar audience si tenemos client_id configurado
            if settings.GOOGLE_CLIENT_ID and data.get("aud") != settings.GOOGLE_CLIENT_ID:
                logger.warning(f"Google token audience mismatch: {data.get('aud')}")
                return None
            return {
                "email": data.get("email", ""),
                "name": data.get("name", ""),
                "sub": data.get("sub", ""),
                "picture": data.get("picture", ""),
            }
    except Exception as e:
        logger.error(f"Error verificando Google token: {e}")
        return None


async def _verify_microsoft_token(access_token: str) -> dict | None:
    """Verifica un Microsoft access token usando Graph API."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            if resp.status_code != 200:
                return None
            data = resp.json()
            return {
                "email": data.get("mail") or data.get("userPrincipalName", ""),
                "name": data.get("displayName", ""),
                "sub": data.get("id", ""),
                "id": data.get("id", ""),
            }
    except Exception as e:
        logger.error(f"Error verificando Microsoft token: {e}")
        return None


# ─── Helpers ──────────────────────────────────────────────────────────

def _user_dict(u: Usuario) -> dict:
    return {
        "id": u.id,
        "email": u.email,
        "nombre": u.nombre,
        "empresa": u.empresa,
        "telefono": u.telefono,
        "telefono_codigo_pais": u.telefono_codigo_pais,
        "tipo": u.tipo,
        "es_proveedor": u.es_proveedor,
        "avatar_url": u.avatar_url,
        "auth_provider": u.auth_provider,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }
