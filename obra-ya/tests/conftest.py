"""
Pytest fixtures compartidos — BD en memoria, mocks de WhatsApp/Claude.
"""
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base


@pytest.fixture
def db():
    """Base de datos SQLite en memoria para cada test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_whatsapp():
    """Mock de todas las funciones de WhatsApp."""
    with patch("app.services.whatsapp.enviar_mensaje_texto", new_callable=AsyncMock) as m_texto, \
         patch("app.services.whatsapp.enviar_mensaje_con_botones", new_callable=AsyncMock) as m_botones, \
         patch("app.services.whatsapp.enviar_mensaje_con_lista", new_callable=AsyncMock) as m_lista, \
         patch("app.services.whatsapp.marcar_como_leido", new_callable=AsyncMock) as m_leido:
        m_texto.return_value = {"messages": [{"id": "wamid.test123"}]}
        m_botones.return_value = {"messages": [{"id": "wamid.test456"}]}
        m_lista.return_value = {"messages": [{"id": "wamid.test789"}]}
        m_leido.return_value = {"success": True}
        yield {
            "texto": m_texto,
            "botones": m_botones,
            "lista": m_lista,
            "leido": m_leido,
        }


@pytest.fixture
def usuario_test(db):
    """Crea un usuario de prueba."""
    from app.models.usuario import Usuario
    u = Usuario(
        telefono="5213312345678",
        nombre="Juan Test",
        tipo="residente",
        municipio_principal="Zapopan",
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@pytest.fixture
def proveedor_test(db):
    """Crea un proveedor de prueba."""
    from app.models.proveedor import Proveedor
    p = Proveedor(
        nombre="Materiales Test SA",
        tipo="mediano",
        telefono_whatsapp="5213399998888",
        municipio="Zapopan",
        categorias='["concreto","acero","agregados"]',
        calificacion=4.5,
        activo=True,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p
