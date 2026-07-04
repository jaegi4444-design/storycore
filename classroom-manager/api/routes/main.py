"""메인 화면 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from api.deps import get_current_user, pop_flashes
from api.entities import User
from api.services.class_service import get_class_by_teacher

router = APIRouter(tags=["main"])


def register_main_routes(templates: Jinja2Templates) -> APIRouter:
    @router.get("/", response_class=HTMLResponse)
    def main_page(
        request: Request,
        user: User = Depends(get_current_user),
    ):
        school_class = get_class_by_teacher(user.id)
        return templates.TemplateResponse(
            request,
            "main.html",
            {
                "user": user,
                "school_class": school_class,
                "flashes": pop_flashes(request),
            },
        )

    return router
