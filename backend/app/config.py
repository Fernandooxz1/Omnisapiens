from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # env_file es relativo al cwd: los comandos se corren desde backend/.
    # `extra="ignore"`: una variable vieja en el .env no impide arrancar.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "local"
    # Nivel del root logger de la API. Los loggers de uvicorn mantienen el suyo.
    log_level: str = "INFO"

    database_url: str
    redis_url: str
    jwt_secret: str
    cors_origins: str

    jwt_ttl_days: int = 30
    reconnect_grace_seconds: int = 20
    room_idle_timeout_seconds: int = 600
    # Una partida `playing` más vieja que esto es de un proceso que murió a mitad:
    # el barrendero la anula al arrancar. El techo de una partida normal (7 rondas
    # de 30 s con gracia por ronda) ronda los 7 minutos.
    stale_match_minutes: int = 15
    # Tres heartbeats del cliente (ping cada 15 s, §10.3). Sin esto, un socket
    # que muere sin `close` deja la silla "conectada" y la gracia nunca arranca.
    ws_idle_timeout_seconds: int = 45

    @model_validator(mode="after")
    def _secret_long_outside_local(self) -> "Settings":
        # En dev el secreto puede ser corto; en cualquier otro entorno, no.
        if self.env != "local" and len(self.jwt_secret.encode()) < 32:
            raise ValueError("JWT_SECRET tiene que medir al menos 32 bytes")
        return self


# mypy no ve que BaseSettings llena los campos desde el entorno.
settings = Settings()  # type: ignore[call-arg]
