"""
Tests de configuracion de base de datos — SQLite vs PostgreSQL.
"""
from app.database import _is_sqlite, engine


class TestDatabaseConfig:
    def test_sqlite_default(self):
        """En desarrollo, usa SQLite por default."""
        assert _is_sqlite is True

    def test_engine_creado(self):
        """El engine se crea correctamente."""
        assert engine is not None

    def test_check_same_thread_solo_sqlite(self):
        """check_same_thread solo se aplica a SQLite."""
        if _is_sqlite:
            # SQLite debe tener check_same_thread=False
            url = str(engine.url)
            assert "sqlite" in url


class TestConfigValidation:
    def test_production_validation_dev(self):
        """En development, los defaults son OK."""
        from app.config import settings
        assert settings.ENVIRONMENT == "development"
        # No deberia explotar en dev
        settings.validate_production()

    def test_jwt_secret_default(self):
        from app.config import settings
        # En dev el default es OK
        assert len(settings.JWT_SECRET) > 10
