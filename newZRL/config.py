import os
import logging

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    WTF_CSRF_SECRET = os.environ.get("SECRET_KEY") # Ensure CSRF uses the same secret
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOGGING_LEVEL = logging.INFO
    WTRL_API_COOKIE = os.environ.get("WTRL_API_COOKIE")

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("DEV_DATABASE_URL")
    LOGGING_LEVEL = logging.DEBUG
    SESSION_COOKIE_SECURE = False  # Allow session cookie over HTTP
    SESSION_COOKIE_HTTPONLY = True # Prevent client-side JS access to cookie
    SESSION_COOKIE_SAMESITE = 'Lax' # Allow session cookie to be sent on cross-site requests (e.g., embeds)

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
        # For platforms like Render, Railway, etc., which provide a DATABASE_URL
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
        
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