from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_error_handlers
from app.routers import auth, comments, errors, likes, public, reports, studies, todos


def create_app(app_env: str = "development") -> FastAPI:
    # 서버 자동 문서(/docs)는 개발 환경에서만 열어 둔다.
    is_development = app_env == "development"
    application = FastAPI(
        title="BuildLog",
        docs_url="/docs" if is_development else None,
        redoc_url="/redoc" if is_development else None,
        openapi_url="/openapi.json" if is_development else None,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(application)
    for router in (
        auth.router,
        studies.router,
        todos.router,
        errors.router,
        public.router,
        comments.router,
        likes.router,
        reports.router,
    ):
        application.include_router(router)

    @application.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app(settings.app_env)
