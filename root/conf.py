from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY_MIN_LENGTH = 32


class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file=BASE_DIR / '.env', extra='ignore')

    SECRET_KEY: SecretStr = Field(min_length=SECRET_KEY_MIN_LENGTH)
    DEBUG: bool = False
    ALLOWED_HOSTS: str = ''

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432

    CORS_ALLOWED_ORIGINS: str = ''

    INSTAGRAM_APP_SECRET: SecretStr = SecretStr('')
    INSTAGRAM_WEBHOOK_VERIFY_TOKEN: SecretStr = SecretStr('')

    TELEGRAM_BOT_TOKEN: SecretStr = SecretStr('')
    TELEGRAM_DEBUG_CHAT_ID: str = ''

    @property
    def allowed_hosts(self):
        return self._split(self.ALLOWED_HOSTS)

    @property
    def cors_allowed_origins(self):
        return self._split(self.CORS_ALLOWED_ORIGINS)

    @staticmethod
    def _split(raw):
        return [entry.strip() for entry in raw.split(',') if entry.strip()]


env = Env()
