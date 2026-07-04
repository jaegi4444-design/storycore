"""인증 라우트."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from api.deps import flash, get_current_user_optional, login_user, logout_user, pop_flashes
from api.entities import User
from api.services.auth_service import find_or_create_user_by_name

router = APIRouter(tags=["auth"])


def register_auth_routes(templates: Jinja2Templates) -> APIRouter:
    @router.get("/login", response_class=HTMLResponse)
    def login_page(request: Request):
        user = get_current_user_optional(request)
        if user:
            return RedirectResponse(url="/", status_code=303)

        return templates.TemplateResponse(
            request,
            "login.html",
            {"flashes": pop_flashes(request)},
        )

    @router.post("/login")
    def login_submit(
        request: Request,
        name: Annotated[str, Form()] = "",
    ):
        try:
            user = find_or_create_user_by_name(name)
        except ValueError as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(url="/login", status_code=303)

        login_user(request, user)
        return RedirectResponse(url="/", status_code=303)

    @router.post("/logout")
    def logout(request: Request):
        logout_user(request)
        return RedirectResponse(url="/login", status_code=303)

    return router
