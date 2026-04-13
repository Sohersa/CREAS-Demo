"""
Configuracion del proyecto ObraYa.
Carga variables de entorno desde .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde la raiz del proyecto
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(str(_env_path), override=True)


class Settings:
    """Variables de configuracion del proyecto."""

    # Anthropic API
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # WhatsApp Cloud API
    WHATSAPP_TOKEN: str = os.getenv("WHATSAPP_TOKEN", "")
    WHATSAPP_PHONE_ID: str = os.getenv("WHATSAPP_PHONE_ID", "")
    WHATSAPP_VERIFY_TOKEN: str = os.getenv("WHATSAPP_VERIFY_TOKEN", "obra_ya_verify_2026")

    # Twilio WhatsApp
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_WHATSAPP_NUMBER: str = os.getenv("TWILIO_WHATSAPP_NUMBER", "")  # whatsapp:+14155238886
    WHATSAPP_PROVIDER: str = os.getenv("WHATSAPP_PROVIDER", "meta")  # "meta" or "twilio"

    # Base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./obra_ya.db")

    # Stripe (pagos)
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Auth / JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "obraya-secret-change-in-production-2026")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = int(os.getenv("JWT_EXPIRE_HOURS", "72"))
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    MICROSOFT_CLIENT_ID: str = os.getenv("MICROSOFT_CLIENT_ID", "")

    # Entorno
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "debug")


settings = Settings()
