import logging
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware

from app.auth import CurrentUser, require_admin, require_authenticated, require_employee
from app.config import get_settings
from app.database import check_database
from app.documents import router as documents_router
from app.questions import admin_router, answers_router, router as questions_router

settings = get_settings()
logger = logging.getLogger("team_policy_assistant")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "http_request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "request_id": request_id,
            "duration_ms": duration_ms,
        },
    )
    return response


app.include_router(documents_router)
app.include_router(questions_router)
app.include_router(answers_router)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    if not check_database():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        )
    return {"status": "ready", "environment": settings.environment}


@app.get("/api/v1/me")
def current_user(user: CurrentUser = Depends(require_authenticated)) -> dict[str, object]:
    return {"subject": user.subject, "username": user.username, "roles": sorted(user.roles)}


@app.get("/api/v1/admin/ping")
def admin_ping(user: CurrentUser = Depends(require_admin)) -> dict[str, str]:
    return {"status": "ok", "subject": user.subject}


@app.get("/api/v1/employee/ping")
def employee_ping(user: CurrentUser = Depends(require_employee)) -> dict[str, str]:
    return {"status": "ok", "subject": user.subject}
