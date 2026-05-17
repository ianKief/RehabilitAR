import os
from dotenv import load_dotenv
load_dotenv()

class DevelopmentConfig:
    TESTING = False
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "flask-secret-key")
    SESSION_TYPE = os.getenv("FLASK_SESSION_TYPE", "filesystem")
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_FILE_DIR = os.getenv("SESSION_FILE_DIR", "./flask_session")
    PERMANENT_SESSION_LIFETIME = 3600

    # JWT Configuration
    JWT_SECRET = os.getenv("JWT_SECRET", "jwt-secret-key")
    JWT_ALGORITHM = "HS256"
    JWT_EXP_DELTA = 3600

    DB_SCHEME = os.getenv("DB_SCHEME", "postgresql+psycopg2")
    DB_USER   = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST   = os.getenv("DB_HOST")
    DB_PORT   = os.getenv("DB_PORT")
    DB_NAME   = os.getenv("DB_NAME")

    SQLALCHEMY_ENGINES = {
        "default": f"{DB_SCHEME}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    }

# Instancia única de configuración de desarrollo
config = DevelopmentConfig

