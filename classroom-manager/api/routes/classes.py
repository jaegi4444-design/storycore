"""반 관리 라우트."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from api.deps import flash, get_current_user, pop_flashes
from api.entities import User
from api.services.child_service import get_children_by_class, resolve_photo_display
from api.services.class_service import (
    ClassAlreadyExistsError,
    InvalidCurrencyError,
    create_class,
    get_class_by_teacher,
    update_class_currency_name,
    update_class_name,
    verify_class_owner,
)
from api.services.code_service import resolve_class_currency_name
from api.services.qr_service import build_child_qr_url
from api.wallet_repository import get_wallets_for_children

router = APIRouter(prefix="/classes", tags=["classes"])


def register_class_routes(templates: Jinja2Templates) -> APIRouter:
    @router.get("/create", response_class=HTMLResponse)
    def class_create_page(
        request: Request,
        user: User = Depends(get_current_user),
    ):
        existing = get_class_by_teacher(user.id)
        if existing:
            flash(request, "이미 반이 존재합니다.", "error")
            return RedirectResponse(url="/classes/manage", status_code=303)

        return templates.TemplateResponse(
            request,
            "class_create.html",
            {
                "user": user,
                "default_currency_name": "콩",
                "flashes": pop_flashes(request),
            },
        )

    @router.post("/create")
    def class_create_submit(
        request: Request,
        user: User = Depends(get_current_user),
        class_name: Annotated[str, Form()] = "",
        currency_name: Annotated[str, Form()] = "콩",
    ):
        existing = get_class_by_teacher(user.id)
        if existing:
            flash(request, "이미 반이 존재합니다.", "error")
            return RedirectResponse(url="/classes/manage", status_code=303)

        try:
            create_class(user, class_name, currency_name)
            flash(request, "반이 생성되었습니다.", "success")
            return RedirectResponse(url="/classes/manage", status_code=303)
        except ClassAlreadyExistsError as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(url="/classes/manage", status_code=303)
        except (InvalidCurrencyError, ValueError) as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(url="/classes/create", status_code=303)

    def _child_cards_for_class(request: Request, school_class, children, currency_name):
        wallets = get_wallets_for_children(
            [c.id for c in children], school_class.currency_code
        )
        child_cards = []
        for child in children:
            wallet = wallets.get(child.id)
            balance = wallet.balance if wallet else 0
            child_cards.append(
                {
                    "child": child,
                    "photo_display": resolve_photo_display(child),
                    "balance": balance,
                    "currency_name": currency_name,
                    "qr_url": build_child_qr_url(request, child.id),
                }
            )
        return child_cards

    @router.get("/manage", response_class=HTMLResponse)
    def class_manage_page(
        request: Request,
        user: User = Depends(get_current_user),
    ):
        school_class = get_class_by_teacher(user.id)
        if school_class is None:
            return RedirectResponse(url="/classes/create", status_code=303)

        children = get_children_by_class(school_class.id)
        currency_name = resolve_class_currency_name(school_class)
        child_cards = _child_cards_for_class(request, school_class, children, currency_name)

        return templates.TemplateResponse(
            request,
            "class_manage.html",
            {
                "user": user,
                "school_class": school_class,
                "currency_name": currency_name,
                "children": child_cards,
                "flashes": pop_flashes(request),
            },
        )

    @router.get("/my/qr-list", response_class=HTMLResponse)
    def children_qr_list_page(
        request: Request,
        user: User = Depends(get_current_user),
    ):
        school_class = get_class_by_teacher(user.id)
        if school_class is None:
            return RedirectResponse(url="/classes/create", status_code=303)

        children = get_children_by_class(school_class.id)
        currency_name = resolve_class_currency_name(school_class)
        child_cards = _child_cards_for_class(request, school_class, children, currency_name)

        return templates.TemplateResponse(
            request,
            "children_qr_list.html",
            {
                "user": user,
                "school_class": school_class,
                "currency_name": currency_name,
                "children": child_cards,
                "flashes": pop_flashes(request),
            },
        )

    @router.post("/update")
    def class_update_submit(
        request: Request,
        user: User = Depends(get_current_user),
        class_name: Annotated[str, Form()] = "",
    ):
        school_class = get_class_by_teacher(user.id)
        if school_class is None or not verify_class_owner(school_class, user):
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/", status_code=303)

        try:
            update_class_name(school_class, class_name)
            flash(request, "반 이름이 수정되었습니다.", "success")
        except ValueError as exc:
            flash(request, str(exc), "error")

        return RedirectResponse(url="/classes/manage", status_code=303)

    @router.post("/update-currency")
    def class_update_currency_submit(
        request: Request,
        user: User = Depends(get_current_user),
        currency_name: Annotated[str, Form()] = "",
    ):
        school_class = get_class_by_teacher(user.id)
        if school_class is None or not verify_class_owner(school_class, user):
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/", status_code=303)

        try:
            update_class_currency_name(school_class, currency_name)
            flash(request, "화폐 단위가 수정되었습니다.", "success")
        except ValueError as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(url="/classes/manage?currency_edit=1", status_code=303)
        except Exception:
            flash(request, "화폐 단위 저장 중 오류가 발생했습니다.", "error")
            return RedirectResponse(url="/classes/manage?currency_edit=1", status_code=303)

        return RedirectResponse(url="/classes/manage", status_code=303)

    return router
