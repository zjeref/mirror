from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # MongoDB
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "mirror"

    # JWT
    jwt_secret_key: str = "dev-secret-change-in-production"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    jwt_algorithm: str = "HS256"

    # Claude API (Bedrock)
    anthropic_api_key: str = ""
    aws_region: str = "us-east-1"
    bedrock_model: str = "us.anthropic.claude-sonnet-4-20250514-v1:0"

    # VAPID (Web Push)
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_email: str = "mailto:admin@mirror.app"

    # App
    environment: str = "development"
    app_name: str = "Mirror"

    # CORS
    cors_origins: str = "http://localhost:5173"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }

    @property
    def is_bedrock_key(self) -> bool:
        return self.anthropic_api_key.startswith("ABSK")


settings = Settings()
