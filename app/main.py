from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api.routes import chat, health, interview, session
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.modules.block1_resume_constructor.router import router as block1_router
from app.services.moderation import ModerationRejected


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Resume Designer",
        description=(
            "ИИ-конструктор резюме для студентов и выпускников. "
            "Интеграция с мессенджером через JSON API, LLM — GigaChat (Сбер)."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ModerationRejected)
    async def moderation_handler(_request, exc: ModerationRejected) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    app.include_router(health)
    app.include_router(chat, prefix="/api/v1")
    app.include_router(block1_router, prefix="/api/v1")
    app.include_router(interview, prefix="/api/v1")
    app.include_router(session, prefix="/session")

    @app.get("/", include_in_schema=False)
    async def root() -> RedirectResponse:
        return RedirectResponse(url="/site/", status_code=307)

    @app.get("/meta", tags=["Meta"])
    async def meta() -> dict:
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "health": "/health",
            "messenger_endpoint": "/api/v1/chat",
            "block1": "/api/v1/resume/chat",
            "site": "/site/",
            "block2_status": "planned",
        }

    # Mount static site last so API routes stay available
    app.mount("/site", StaticFiles(directory="app/static", html=True), name="site")

    return app


app = create_app()
