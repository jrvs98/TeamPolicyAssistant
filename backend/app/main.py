from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "environment": settings.environment}


@app.get("/api/v1/me")
def current_user() -> dict[str, str | None]:
    return {"role": None, "subject": None, "status": "authentication_pending"}
