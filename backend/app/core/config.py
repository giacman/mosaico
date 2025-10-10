"""
Mosaico Configuration Settings
Using Pydantic Settings for environment variables
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Google Cloud
    gcp_project_id: str
    gcp_location: str = "us-central1"
    
    # Vertex AI
    vertex_ai_model: str = "gemini-2.5-pro"
    vertex_ai_model_flash: str = "gemini-2.5-flash"
    
    # Cloud Storage
    gcs_bucket_prompts: str = "mosaico-prompts"
    gcs_bucket_examples: str = "mosaico-examples"
    
    # API
    api_title: str = "Mosaico API"
    api_version: str = "1.0.0"
    environment: str = "development"
    
    # Rate Limiting
    rate_limit_per_second: int = 5
    rate_limit_burst: int = 10
    
    # CORS
    allowed_origins: str = "*"
    
    # Logging
    log_level: str = "INFO"
    
    # Authentication (optional - for local dev with service account)
    google_application_credentials: str | None = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",")]


# Global settings instance
settings = Settings()
