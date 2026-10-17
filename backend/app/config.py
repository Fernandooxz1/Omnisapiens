from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # env_file es relativo al cwd: los comandos se corren desde backend/.
    model_config = SettingsConfigDict(env_file=".env")

    env: str = "local"

    database_url: str
    redis_url: str
    jwt_secret: str
    admin_token: str
    cors_origins: str

    jwt_ttl_days: int = 30
    reconnect_grace_seconds: int = 20
    room_idle_timeout_seconds: int = 600
    # Tres heartbeats del cliente (ping cada 15 s, §10.3). Sin esto, un socket
    # que muere sin `close` deja la silla "conectada" y la gracia nunca arranca.
    ws_idle_timeout_seconds: int = 45


# mypy no ve que BaseSettings llena los campos desde el entorno.
settings = Settings()  # type: ignore[call-arg]
