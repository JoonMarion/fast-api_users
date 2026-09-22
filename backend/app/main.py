import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from redis.backoff import NoBackoff
from redis.retry import Retry

from app.api.routes import router
from app.cache.redis import RedisUserCache
from app.config import Settings, load_settings
from app.logging_config import configure_logging
from app.providers.cached import CachedUserProvider
from app.providers.jsonplaceholder import JsonPlaceholderUserProvider
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings if settings is not None else load_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        configure_logging()
        timeout = httpx.Timeout(app_settings.provider_timeout_seconds)
        redis_client = Redis.from_url(
            app_settings.redis_url,
            retry=Retry(NoBackoff(), 0),
            socket_connect_timeout=app_settings.cache_timeout_seconds,
            socket_timeout=app_settings.cache_timeout_seconds,
        )
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                external_provider = JsonPlaceholderUserProvider(
                    client=client,
                    base_url=app_settings.provider_base_url,
                )
                provider = CachedUserProvider(
                    provider=external_provider,
                    cache=RedisUserCache(redis_client),
                    ttl_seconds=app_settings.cache_ttl_seconds,
                )
                application.state.user_service = UserService(
                    provider=provider,
                    max_concurrency=app_settings.max_concurrency,
                )
                logger.info(
                    "Application resources initialized",
                    extra={
                        "event": "application_started",
                        "max_concurrency": app_settings.max_concurrency,
                    },
                )
                try:
                    yield
                finally:
                    logger.info(
                        "Application resources released",
                        extra={"event": "application_stopped"},
                    )
        finally:
            await redis_client.aclose()

    application = FastAPI(lifespan=lifespan)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[app_settings.frontend_origin],
        allow_methods=["POST"],
        allow_headers=["Content-Type"],
    )
    application.include_router(router)
    return application


app = create_app()
