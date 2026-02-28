from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    postgres_user: str = "taskflow"
    postgres_password: str = "taskflow_dev"
    postgres_db: str = "taskflow"
    database_url: str = "postgresql://taskflow:taskflow_dev@postgres:5432/taskflow"
    
    # Redis Configuration
    redis_url: str = "redis://redis:6379/0"
    
    # MinIO S3-Compatible Storage
    minio_root_user: str = "minioadmin"
    minio_root_password: str = "minioadmin"
    s3_endpoint_url: str = "http://minio:9000"
    aws_access_key_id: str = "minioadmin"
    aws_secret_access_key: str = "minioadmin"
    s3_bucket_name: str = "taskflow-uploads"
    
    # JWT Configuration
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Celery Configuration
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    
    # Application Configuration
    default_avatar_url: str = "https://via.placeholder.com/150"
    log_level: str = "INFO"
    
    # Super Admin Configuration
    admin_username: str = "admin"
    admin_email: str = "admin@taskflow.local"
    admin_password: str = "admin123"
    
    @property
    def celery_broker(self) -> str:
        """Get Celery broker URL, defaults to redis_url"""
        return self.celery_broker_url or self.redis_url
    
    @property
    def celery_backend(self) -> str:
        """Get Celery result backend URL, defaults to redis_url"""
        return self.celery_result_backend or self.redis_url


# Global settings instance
settings = Settings()
