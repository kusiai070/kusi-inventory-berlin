"""
Configuration module for KusiSaaS Enterprise
Módulo de configuración centralizado
"""

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings loaded from environment variables"""
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@db:5432/restaurant_inventory"
    )
    
    # CORS
    PORT: str = os.getenv("PORT", "8000")
    FRONTEND_PORT: str = os.getenv("FRONTEND_PORT", "3000")
    ALLOWED_ORIGINS: List[str] = os.getenv(
        "ALLOWED_ORIGINS",
        f"http://localhost:{PORT},http://localhost:{FRONTEND_PORT}"
    ).split(",")
    
    # OCR Settings
    MAX_UPLOAD_SIZE_MB: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "10"))
    ALLOWED_FILE_TYPES: List[str] = os.getenv(
        "ALLOWED_FILE_TYPES",
        "image/jpeg,image/png,application/pdf"
    ).split(",")
    
    # Rate Limiting
    RATE_LIMIT_LOGIN_ATTEMPTS: int = int(os.getenv("RATE_LIMIT_LOGIN_ATTEMPTS", "5"))
    RATE_LIMIT_WINDOW_MINUTES: int = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "15"))
    
    @classmethod
    def validate(cls):
        """Validate critical settings"""
        if cls.SECRET_KEY == "dev-secret-key-change-in-production":
            print("⚠️  WARNING: Using default SECRET_KEY. Set SECRET_KEY in .env for production!")
        
        if len(cls.SECRET_KEY) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        
        return True

# Global settings instance
settings = Settings()

# Validate on import
settings.validate()
