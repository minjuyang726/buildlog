from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import register_error_handlers
from app.routers import auth, errors, public, studies, todos

app = FastAPI(title="BuildLog")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(auth.router)
app.include_router(studies.router)
app.include_router(todos.router)
app.include_router(errors.router)
app.include_router(public.router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
