from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

SECRET_KEY_MIN_LENGTH = 32


class Env(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    SECRET_KEY: SecretStr = Field(min_length=SECRET_KEY_MIN_LENGTH)
    DEBUG: bool = False
    ALLOWED_HOSTS: str = ''

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_HOST: str = 'localhost'
    POSTGRES_PORT: int = 5432

    @property
    def allowed_hosts(self):
        return [host.strip() for host in self.ALLOWED_HOSTS.split(',') if host.strip()]


env = Env()
