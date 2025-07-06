import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as redis
import uvicorn
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from src.auth.router import router as user_router
from src.background.background import S3UploadWorker
from src.kafka import kafka_producer
from src.utils.config import get_settings
from src.utils.logger import get_logger
from src.video.router import router as video_router

settings = get_settings()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init redis, start producer and consumer
    app.state.redis = redis.Redis(
        host=settings.redis_host, port=settings.redis_port, decode_responses=True
    )
    await kafka_producer.start()
    background_worker = asyncio.create_task(
        S3UploadWorker(bucket=settings.s3_bucket).start()
    )
    yield
    await kafka_producer.stop()
    background_worker.cancel()


app = FastAPI(title="Video Host API", lifespan=lifespan)
app.include_router(user_router)
app.include_router(video_router)


@app.middleware("http")
async def ban_ip_middleware(request: Request, call_next):
    """Simple IP-based rate limiting middleware."""
    redis_client = request.app.state.redis
    client_ip = request.client.host
    banned_key = f"banned:{client_ip}"
    rate_key = f"rate:{client_ip}"

    if await redis_client.exists(banned_key):
        ttl = await redis_client.ttl(banned_key)
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": f"IP is temporarily blocked for {ttl} seconds."},
        )

    request_count = await redis_client.incr(rate_key)
    if request_count == 1:
        await redis_client.expire(rate_key, 60)

    if request_count > settings.redis_response_per_min_limit:
        await redis_client.set(banned_key, 1, ex=settings.redis_ip_ban_time * 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, IP temporarily blocked.",
        )

    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception(f"Internal server error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )

    return response


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.uvicorn_host,
        port=settings.uvicorn_port,
        reload=settings.app_debug,
    )
