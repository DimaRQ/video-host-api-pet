import json
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, SecretStr
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

    uvicorn_host: str = Field("localhost", alias="UVICORN_HOST")
    uvicorn_port: int = Field(8000, alias="UVICORN_PORT")

    database_url: str = Field(..., alias="DATABASE_URL")
    kafka_servers: List[str] = Field(..., alias="KAFKA_SERVERS")
    kafka_topic: str = Field("videos", alias="KAFKA_TOPIC")

    s3_baseurl: str = Field(..., alias="S3_BASEURL")
    s3_region: str = Field(..., alias="S3_REGION")
    s3_endpoint: str = Field(..., alias="S3_ENDPOINT")
    s3_bucket: Optional[str] = Field(None, alias="S3_BUCKET")
    s3_access_key: Optional[SecretStr] = Field(None, alias="S3_ACCESS_KEY")
    s3_secret_key: Optional[SecretStr] = Field(None, alias="S3_SECRET_KEY")

    secret_key: SecretStr = Field(..., alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    algorithm: str = Field("HS256", alias="ALGORITHM")

    video_max_size: int = Field(50 * 1024 * 1024, alias="VIDEO_MAX_SIZE")

    redis_host: str = Field("localhost", alias="REDIS_HOST")
    redis_port: int = Field(6379, alias="REDIS_PORT")
    redis_ip_ban_counter_expiration: int = Field(1, alias="IP_BAN_COUNTER_EXPIRATION")
    redis_threshold_404_request: int = Field(500, alias="IP_THRESHOLD_404_REQUESTS")
    redis_response_per_min_limit: int = Field(10, alias="IP_RATE_LIMIT_PER_MIN")
    redis_ip_ban_time: int = Field(60, alias="IP_BAN_TIME")

    app_debug: bool = Field(False, alias="APP_DEBUG")

    @field_validator("kafka_servers", mode="before")
    def _parse_kafka_servers(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()
