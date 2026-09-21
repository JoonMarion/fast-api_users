from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import Settings, load_settings
from app.providers.jsonplaceholder import JsonPlaceholderUserProvider
from app.services.user_service import UserService


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings if settings is not None else load_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        timeout = httpx.Timeout(app_settings.provider_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout) as client:
            provider = JsonPlaceholderUserProvider(
                client=client,
                base_url=app_settings.provider_base_url,
            )
            application.state.user_service = UserService(
                provider=provider,
                max_concurrency=app_settings.max_concurrency,
            )
            yield

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
