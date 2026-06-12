from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Production AI Agent"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # API Keys (Mock keys for local testing, replace with actual in .env for real use)
    OPENAI_API_KEY: str = "mock-openai-key"
    AGENT_API_KEY: str = "secret-agent-key"

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"

    # Rate Limiting & Cost Guard
    RATE_LIMIT_PER_MINUTE: int = 10
    MONTHLY_BUDGET_USD: float = 10.0

    # Conversation History
    CONVERSATION_HISTORY_LENGTH: int = 10 # Number of messages to keep in history
    CONVERSATION_HISTORY_TTL_SECONDS: int = 3600 # History expires after 1 hour

    LOG_LEVEL: str = "INFO"

settings = Settings()