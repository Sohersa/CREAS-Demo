"""
Multi-tenancy helper — aisla datos por empresa.

Uso:
  from app.services.tenant_scope import filtrar_por_empresa, empresa_de_usuario

  pedidos = filtrar_por_empresa(db.query(Pedido), usuario).all()

El aislamiento se hace filtrando por usuario_id IN (usuarios de la empresa).
Para evitar N+1, cacheamos los IDs por empresa en memoria (invalidar cuando se
agregan miembros).
"""
from functools import lru_cache
from typing import Optional

from sqlalchemy.orm import Session, Query

from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.miembro_empresa import MiembroEmpresa


def empresa_de_usuario(db: Session, usuario_id: int) -> Optional[Empresa]:
    """Devuelve la empresa del usuario (o None si es individual)."""
    u = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not u or not u.empresa_id:
        return None
    return db.query(Empresa).filter(Empresa.id == u.empresa_id).first()


def ids_usuarios_empresa(db: Session, empresa_id: int) -> list[int]:
    """Lista de IDs de usuarios que pertenecen a una empresa."""
    rows = db.query(MiembroEmpresa.usuario_id).filter(
        MiembroEmpresa.empresa_id == empresa_id,
        MiembroEmpresa.activo == True,
    ).all()
    return [r[0] for r in rows]


def filtrar_por_empresa(query: Query, usuario: Usuario, columna_usuario="usuario_id") -> Query:
    """
    Filtra un query para que solo muestre registros de la empresa del usuario.
    Si el usuario no tiene empresa (individual), solo ve los suyos.

    columna_usuario: nombre de la FK al usuario en el modelo base del query.
    """
    if not usuario:
        return query.filter(False)  # bloqueo total si no hay usuario

    modelo = query.column_descriptions[0]["entity"]
    col = getattr(modelo, columna_usuario, None)
    if col is None:
        return query  # el modelo no tiene FK a usuario, dejamos pasar

    if not usuario.empresa_id:
        # Individual: solo los suyos
        return query.filter(col == usuario.id)

    # Empresarial: todos los de su empresa
    db = query.session
    ids = ids_usuarios_empresa(db, usuario.empresa_id)
    if not ids:
        return query.filter(col == usuario.id)
    return query.filter(col.in_(ids))


def usuario_puede_ver(db: Session, usuario_solicitante: Usuario, usuario_objetivo_id: int) -> bool:
    """True si el solicitante puede ver datos del usuario objetivo."""
    if not usuario_solicitante:
        return False
    if usuario_solicitante.id == usuario_objetivo_id:
        return True
    if not usuario_solicitante.empresa_id:
        return False
    # Mismo workspace?
    ids = ids_usuarios_empresa(db, usuario_solicitante.empresa_id)
    return usuario_objetivo_id in ids
