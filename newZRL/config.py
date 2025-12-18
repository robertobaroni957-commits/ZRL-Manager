import os
import logging
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGGING_LEVEL = logging.INFO
    WTRL_API_COOKIE = os.environ.get("WTRL_API_COOKIE")

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URL")
    LOGGING_LEVEL = logging.DEBUG

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False
    SECRET_KEY = "a-secret-key-for-testing"

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = None

    # PythonAnywhere specific configuration
    PA_DB_USER = os.environ.get("PA_DB_USER")
    PA_DB_PASSWORD = os.environ.get("PA_DB_PASSWORD")
    PA_DB_HOST = os.environ.get("PA_DB_HOST")
    PA_DB_NAME = os.environ.get("PA_DB_NAME")

    if PA_DB_USER and PA_DB_PASSWORD and PA_DB_HOST and PA_DB_NAME:
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{PA_DB_USER}:{PA_DB_PASSWORD}@{PA_DB_HOST}/{PA_DB_NAME}"
    else:
        # Fallback for Railway-like platforms or .env files
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or os.environ.get("PROD_DATABASE_URL")
        
        # Heroku and other PaaS provide postgres URLs, which need to be updated for SQLAlchemy
        if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

        # Convert mysql:// URL for SQLAlchemy
        if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("mysql://"):
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("mysql://", "mysql+pymysql://", 1)


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}