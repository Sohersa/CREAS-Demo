"""
Configuracion de la base de datos con SQLAlchemy.
Soporta SQLite (desarrollo) y PostgreSQL (produccion).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# Configurar engine segun el tipo de base de datos
_is_sqlite = settings.DATABASE_URL.startswith("sqlite")

_engine_kwargs = {"echo": False}
if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL: pool de conexiones para concurrencia
    _engine_kwargs["pool_size"] = 20
    _engine_kwargs["max_overflow"] = 10
    _engine_kwargs["pool_pre_ping"] = True

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

# Sesion para interactuar con la BD
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Clase base para todos los modelos."""
    pass


def get_db():
    """Genera una sesion de BD para cada request. Se cierra automaticamente."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def crear_tablas():
    """Crea todas las tablas en la BD si no existen."""
    # Importar modelos para que SQLAlchemy los registre
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
