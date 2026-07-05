"""포인트(콩) 지급·차감·거래내역 라우트."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from api.deps import flash, get_current_user, pop_flashes
from api.entities import User
from api.repository import ChildAccessDeniedError, get_child_for_teacher, get_class_by_teacher
from api.services.class_service import verify_class_owner
from api.services.code_service import resolve_class_currency_name
from api.services.point_service import (
    deposit,
    get_child_balance,
    get_child_transactions_for_teacher,
    get_class_transactions_for_teacher,
    withdraw,
)
from api.wallet_repository import (
    InsufficientBalanceError,
    InvalidAmountError,
    transaction_type_label,
)

router = APIRouter(tags=["points"])


def register_point_routes(templates: Jinja2Templates) -> APIRouter:
    @router.get("/children/{child_id}/points/deposit", response_class=HTMLResponse)
    def deposit_page(request: Request, child_id: int, user: User = Depends(get_current_user)):
        try:
            child = get_child_for_teacher(child_id, user)
            balance = get_child_balance(child_id, user)
            school_class = get_class_by_teacher(user.id)
        except ChildAccessDeniedError:
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/classes/manage", status_code=303)

        return templates.TemplateResponse(
            request,
            "point_deposit.html",
            {
                "user": user,
                "child": child,
                "balance": balance,
                "currency_name": resolve_class_currency_name(school_class),
                "flashes": pop_flashes(request),
            },
        )

    @router.post("/children/{child_id}/points/deposit")
    def deposit_submit(
        request: Request,
        child_id: int,
        user: User = Depends(get_current_user),
        amount: Annotated[str, Form()] = "",
        memo: Annotated[str, Form()] = "",
    ):
        try:
            deposit(child_id, amount, memo, user)
            flash(request, "콩이 지급되었습니다.", "success")
        except InvalidAmountError as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(url=f"/children/{child_id}/points/deposit", status_code=303)
        except ChildAccessDeniedError as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(url="/classes/manage", status_code=303)
        except Exception as exc:
            flash(request, f"지급 처리 중 오류가 발생했습니다: {exc}", "error")
            return RedirectResponse(url=f"/children/{child_id}/points/deposit", status_code=303)

        return RedirectResponse(url="/classes/manage", status_code=303)

    @router.get("/children/{child_id}/points/withdraw", response_class=HTMLResponse)
    def withdraw_page(request: Request, child_id: int, user: User = Depends(get_current_user)):
        try:
            child = get_child_for_teacher(child_id, user)
            balance = get_child_balance(child_id, user)
            school_class = get_class_by_teacher(user.id)
        except ChildAccessDeniedError:
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/classes/manage", status_code=303)

        return templates.TemplateResponse(
            request,
            "point_withdraw.html",
            {
                "user": user,
                "child": child,
                "balance": balance,
                "currency_name": resolve_class_currency_name(school_class),
                "flashes": pop_flashes(request),
            },
        )

    @router.post("/children/{child_id}/points/withdraw")
    def withdraw_submit(
        request: Request,
        child_id: int,
        user: User = Depends(get_current_user),
        amount: Annotated[str, Form()] = "",
        memo: Annotated[str, Form()] = "",
    ):
        try:
            withdraw(child_id, amount, memo, user)
            flash(request, "콩이 차감되었습니다.", "success")
        except (InsufficientBalanceError, InvalidAmountError) as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(url=f"/children/{child_id}/points/withdraw", status_code=303)
        except ChildAccessDeniedError as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(url="/classes/manage", status_code=303)
        except Exception as exc:
            flash(request, f"차감 처리 중 오류가 발생했습니다: {exc}", "error")
            return RedirectResponse(url=f"/children/{child_id}/points/withdraw", status_code=303)

        return RedirectResponse(url="/classes/manage", status_code=303)

    @router.get("/children/{child_id}/transactions", response_class=HTMLResponse)
    def child_transactions_page(
        request: Request, child_id: int, user: User = Depends(get_current_user)
    ):
        try:
            child = get_child_for_teacher(child_id, user)
            balance = get_child_balance(child_id, user)
            transactions = get_child_transactions_for_teacher(child_id, user)
            school_class = get_class_by_teacher(user.id)
        except ChildAccessDeniedError:
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/classes/manage", status_code=303)

        tx_rows = [
            {**tx.__dict__, "type_label": transaction_type_label(tx.transaction_type)}
            for tx in transactions
        ]

        return templates.TemplateResponse(
            request,
            "child_transactions.html",
            {
                "user": user,
                "child": child,
                "balance": balance,
                "currency_name": resolve_class_currency_name(school_class),
                "transactions": tx_rows,
                "flashes": pop_flashes(request),
            },
        )

    @router.get("/classes/my/transactions", response_class=HTMLResponse)
    def class_transactions_page(request: Request, user: User = Depends(get_current_user)):
        school_class = get_class_by_teacher(user.id)
        if school_class is None or not verify_class_owner(school_class, user):
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/", status_code=303)

        try:
            transactions = get_class_transactions_for_teacher(user)
        except ChildAccessDeniedError:
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/", status_code=303)

        tx_rows = [
            {**tx.__dict__, "type_label": transaction_type_label(tx.transaction_type)}
            for tx in transactions
        ]

        return templates.TemplateResponse(
            request,
            "class_transactions.html",
            {
                "user": user,
                "school_class": school_class,
                "currency_name": resolve_class_currency_name(school_class),
                "transactions": tx_rows,
                "flashes": pop_flashes(request),
            },
        )

    @router.get("/class/my")
    def class_my_alias():
        return RedirectResponse(url="/classes/manage", status_code=303)

    return router
