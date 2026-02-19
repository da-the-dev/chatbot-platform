__all__ = ["settings"]

from typing import Iterable
from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KAFKA")
    bootstrap_servers: str


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="REDIS_")

    host: str
    port: int = 6379
    password: str


class GatewaySettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GATEWAY_")

    url: str


class OtelSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OTEL_")

    span_exporter_endpoint: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )
    kafka: KafkaSettings
    redis: RedisSettings
    gateway: GatewaySettings
    otel: OtelSettings
    
    secure: bool = False


settings = Settings()
