from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="OLLYMPICS_",
        extra="ignore",
    )

    ollama_host: str = "http://localhost:11434"
    db_url: str = "sqlite:///./data/ollympics.db"
    tasks_dir: Path = Path("./tasks")
    deepseek_api_key: str | None = None
    deepseek_model: str = "deepseek-chat"
    enable_watts: bool = False
    sampler_interval_ms: int = 250

    @property
    def db_path(self) -> Path:
        return Path(self.db_url.replace("sqlite:///", ""))


class LLMSettings(BaseSettings):
    """Generic LLM provider config for content generation agents.

    Reads LLM_API_KEY, LLM_MODEL, LLM_BASE_URL from .env without prefix so it
    can drive any OpenAI-compatible provider (DeepSeek, OpenAI, etc.).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    LLM_API_KEY: str | None = None
    LLM_MODEL: str = "deepseek-chat"
    LLM_BASE_URL: str = "https://api.deepseek.com/v1"


settings = Settings()
llm_settings = LLMSettings()
