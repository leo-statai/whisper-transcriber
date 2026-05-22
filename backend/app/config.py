from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    REDIS_URL: str = "redis://redis:6379/0"
    DATA_DIR: Path = Path("/data")
    UPLOAD_DIR: Path = Path("/data/uploads")
    MODELS_DIR: Path = Path("/data/models")
    DB_PATH: Path = Path("/data/transcritor.db")

    WHISPER_MODEL: str = "large-v3"
    WHISPER_COMPUTE_TYPE: str = "float16"
    WHISPER_BEAM_SIZE: int = 5
    WHISPER_VAD_FILTER: bool = True
    WHISPER_LANGUAGE: str = ""

    WORKER_CONCURRENCY: int = 1


settings = Settings()
