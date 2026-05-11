from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.common.audit import register_audit_subscribers
from app.common.errors import register_exception_handlers
from app.common.telemetry import configure_logging
from app.config import get_settings
from app.extraction.api import router as extraction_router
from app.ingestion.api import router as ingestion_router
from app.output.api import router as output_router
from app.projects.api import router as projects_router
from app.review.api import router as review_router
from app.vocabulary.api import router as vocabulary_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    register_audit_subscribers()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AI Document Processing",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)

    app.include_router(projects_router, prefix="/projects", tags=["projects"])
    app.include_router(ingestion_router, prefix="/documents", tags=["documents"])
    app.include_router(extraction_router, prefix="/extractions", tags=["extractions"])
    app.include_router(review_router, prefix="/review", tags=["review"])
    app.include_router(vocabulary_router, prefix="/vocabularies", tags=["vocabularies"])
    app.include_router(output_router, prefix="/output", tags=["output"])

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "env": settings.app_env}

    return app


app = create_app()
