"""QR 스캔 — 선생님 자동 로그인 후 지급·차감."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates

from api.deps import (
    enable_qr_mode,
    flash,
    get_current_user,
    get_qr_child_id,
    is_qr_mode,
    login_user,
    pop_flashes,
)
from api.entities import User
from api.repository import ChildAccessDeniedError, get_child_for_teacher, get_class_by_teacher
from api.services.code_service import resolve_class_currency_name
from api.services.point_service import deposit, get_child_balance, withdraw
from api.services.qr_service import build_child_qr_url, resolve_child_from_qr_token
from api.qr_image import generate_qr_svg
from api.wallet_repository import InsufficientBalanceError, InvalidAmountError

router = APIRouter(tags=["qr"])


def _require_qr_child(request: Request, child_id: int, user: User):
    if not is_qr_mode(request):
        raise ChildAccessDeniedError("QR 전용 페이지입니다.")
    if get_qr_child_id(request) != child_id:
        raise ChildAccessDeniedError("접근 권한이 없습니다.")
    return get_child_for_teacher(child_id, user)


def register_qr_routes(templates: Jinja2Templates) -> APIRouter:
    @router.get("/children/{child_id}/qr.svg")
    def child_qr_svg(
        request: Request, child_id: int, user: User = Depends(get_current_user)
    ):
        try:
            get_child_for_teacher(child_id, user)
        except ChildAccessDeniedError:
            return RedirectResponse(url="/login", status_code=303)

        url = build_child_qr_url(request, child_id)
        return Response(
            content=generate_qr_svg(url),
            media_type="image/svg+xml",
            headers={"Cache-Control": "private, max-age=3600"},
        )

    @router.get("/q/{token}")
    def qr_scan_entry(request: Request, token: str):
        resolved = resolve_child_from_qr_token(token)
        if resolved is None:
            return templates.TemplateResponse(
                request,
                "qr_error.html",
                {"message": "유효하지 않거나 만료된 QR 코드입니다."},
                status_code=404,
            )

        child, teacher = resolved
        login_user(request, teacher)
        enable_qr_mode(request, child.id)
        return RedirectResponse(url=f"/qr/children/{child.id}", status_code=303)

    @router.get("/qr/children/{child_id}", response_class=HTMLResponse)
    def qr_action_page(
        request: Request, child_id: int, user: User = Depends(get_current_user)
    ):
        try:
            child = _require_qr_child(request, child_id, user)
            balance = get_child_balance(child_id, user)
            school_class = get_class_by_teacher(user.id)
        except ChildAccessDeniedError:
            return RedirectResponse(url="/login", status_code=303)

        return templates.TemplateResponse(
            request,
            "qr_action.html",
            {
                "child": child,
                "balance": balance,
                "currency_name": resolve_class_currency_name(school_class),
                "flashes": pop_flashes(request),
            },
        )

    @router.get("/qr/children/{child_id}/deposit", response_class=HTMLResponse)
    def qr_deposit_page(
        request: Request, child_id: int, user: User = Depends(get_current_user)
    ):
        try:
            child = _require_qr_child(request, child_id, user)
            balance = get_child_balance(child_id, user)
            school_class = get_class_by_teacher(user.id)
        except ChildAccessDeniedError:
            return RedirectResponse(url="/login", status_code=303)

        return templates.TemplateResponse(
            request,
            "qr_point_deposit.html",
            {
                "child": child,
                "balance": balance,
                "currency_name": resolve_class_currency_name(school_class),
                "flashes": pop_flashes(request),
            },
        )

    @router.post("/qr/children/{child_id}/deposit")
    def qr_deposit_submit(
        request: Request,
        child_id: int,
        user: User = Depends(get_current_user),
        amount: Annotated[str, Form()] = "",
        memo: Annotated[str, Form()] = "",
    ):
        try:
            _require_qr_child(request, child_id, user)
            deposit(child_id, amount, memo, user)
        except InvalidAmountError as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(
                url=f"/qr/children/{child_id}/deposit", status_code=303
            )
        except ChildAccessDeniedError:
            return RedirectResponse(url="/login", status_code=303)
        except Exception as exc:
            flash(request, f"지급 처리 중 오류가 발생했습니다: {exc}", "error")
            return RedirectResponse(
                url=f"/qr/children/{child_id}/deposit", status_code=303
            )

        return RedirectResponse(
            url=f"/qr/children/{child_id}/done?action=deposit&amount={amount.strip()}",
            status_code=303,
        )

    @router.get("/qr/children/{child_id}/withdraw", response_class=HTMLResponse)
    def qr_withdraw_page(
        request: Request, child_id: int, user: User = Depends(get_current_user)
    ):
        try:
            child = _require_qr_child(request, child_id, user)
            balance = get_child_balance(child_id, user)
            school_class = get_class_by_teacher(user.id)
        except ChildAccessDeniedError:
            return RedirectResponse(url="/login", status_code=303)

        return templates.TemplateResponse(
            request,
            "qr_point_withdraw.html",
            {
                "child": child,
                "balance": balance,
                "currency_name": resolve_class_currency_name(school_class),
                "flashes": pop_flashes(request),
            },
        )

    @router.post("/qr/children/{child_id}/withdraw")
    def qr_withdraw_submit(
        request: Request,
        child_id: int,
        user: User = Depends(get_current_user),
        amount: Annotated[str, Form()] = "",
        memo: Annotated[str, Form()] = "",
    ):
        try:
            _require_qr_child(request, child_id, user)
            withdraw(child_id, amount, memo, user)
        except (InsufficientBalanceError, InvalidAmountError) as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(
                url=f"/qr/children/{child_id}/withdraw", status_code=303
            )
        except ChildAccessDeniedError:
            return RedirectResponse(url="/login", status_code=303)
        except Exception as exc:
            flash(request, f"차감 처리 중 오류가 발생했습니다: {exc}", "error")
            return RedirectResponse(
                url=f"/qr/children/{child_id}/withdraw", status_code=303
            )

        return RedirectResponse(
            url=f"/qr/children/{child_id}/done?action=withdraw&amount={amount.strip()}",
            status_code=303,
        )

    @router.get("/qr/children/{child_id}/done", response_class=HTMLResponse)
    def qr_done_page(
        request: Request,
        child_id: int,
        user: User = Depends(get_current_user),
        action: str = "deposit",
        amount: str = "",
    ):
        try:
            child = _require_qr_child(request, child_id, user)
            school_class = get_class_by_teacher(user.id)
        except ChildAccessDeniedError:
            return RedirectResponse(url="/login", status_code=303)

        action_label = "지급" if action == "deposit" else "차감"
        return templates.TemplateResponse(
            request,
            "qr_done.html",
            {
                "child": child,
                "action_label": action_label,
                "amount": amount,
                "currency_name": resolve_class_currency_name(school_class),
            },
        )

    return router
