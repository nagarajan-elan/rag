from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Pydantic will auto-map these uppercase env vars to lowercase attributes
    app_name: str = "RAG Backend"
    app_version: str = "1.0.0"
    database_url: str
    jwt_secret_key: int = "dev-secret-key"

    # Configure Pydantic to read from a .env file if it exists
    model_config = SettingsConfigDict(env_file=".env")

# Instantiate once to share across the application
settings = Settings()
