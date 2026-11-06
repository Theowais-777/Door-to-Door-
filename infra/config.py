"""
Production Configuration Loader
Reads settings from infra/.env and environment variables.
"""
import os
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent.parent
INFRA_DIR = BASE_DIR / "infra"
ENV_FILE = INFRA_DIR / ".env"

def load_env_file(filepath: Path):
    if not filepath.exists():
        return
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = val

load_env_file(ENV_FILE)

class Settings:
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Network
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    GRPC_HOST: str = os.getenv("GRPC_HOST", "127.0.0.1")
    GRPC_PORT: int = int(os.getenv("GRPC_PORT", "50051"))
    
    # DB
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'doortodoor.db'}")
    
    # Auth & JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "d2d-kashmir-jwt-prod-secret-987654321")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Google SSO
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "407408718192.apps.googleusercontent.com")
    
    # Spatial H3
    H3_BASE_RESOLUTION: int = int(os.getenv("H3_BASE_RESOLUTION", "7"))
    H3_NEIGHBOR_DEFAULT_RING: int = int(os.getenv("H3_NEIGHBOR_DEFAULT_RING", "1"))

settings = Settings()

