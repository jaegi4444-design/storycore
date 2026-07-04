"""classroom-manager FastAPI 앱."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from api.exceptions import LoginRequired
from api.init_db import init_database
from api.template_filters import format_account_number, format_tx_datetime
from api.routes.auth import register_auth_routes
from api.routes.children import register_children_routes
from api.routes.classes import register_class_routes
from api.routes.main import register_main_routes
from api.routes.points import register_point_routes
from config.settings import IS_VERCEL, SESSION_SECRET_KEY, UPLOAD_DIR

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "web" / "templates"
STATIC_DIR = BASE_DIR / "web" / "static"

if not IS_VERCEL:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
init_database()

app = FastAPI(
    title="Classroom Manager",
    description="선생님 반·아이 관리 MVP (이름 기반 간편 로그인)",
    version="0.1.0",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    https_only=IS_VERCEL,
    same_site="lax",
)

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.filters["format_tx_datetime"] = format_tx_datetime
templates.env.filters["format_account_number"] = format_account_number

app.include_router(register_auth_routes(templates))
app.include_router(register_main_routes(templates))
app.include_router(register_class_routes(templates))
app.include_router(register_children_routes(templates))
app.include_router(register_point_routes(templates))

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
if not IS_VERCEL and UPLOAD_DIR.is_dir():
    app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.exception_handler(LoginRequired)
async def login_required_handler(request: Request, exc: LoginRequired):
    return RedirectResponse(url="/login", status_code=303)


@app.on_event("startup")
def on_startup() -> None:
    init_database()


@app.get("/health")
def health() -> dict:
    from config.settings import SUPABASE_PROJECT_REF, USE_SUPABASE

    return {
        "status": "ok",
        "database": "supabase" if USE_SUPABASE else "sqlite",
        "project": SUPABASE_PROJECT_REF or None,
    }
