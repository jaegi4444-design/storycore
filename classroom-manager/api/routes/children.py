"""아이 관리 라우트."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from api.deps import flash, get_current_user, pop_flashes
from api.entities import User
from api.services.child_service import (
    ChildAccessDeniedError,
    create_child,
    delete_child,
    get_child_for_teacher,
    resolve_photo_display,
    save_photo_upload,
)
from api.services.class_service import get_class_by_teacher, verify_class_owner

router = APIRouter(prefix="/children", tags=["children"])


def register_children_routes(templates: Jinja2Templates) -> APIRouter:
    def _require_own_class(user: User):
        school_class = get_class_by_teacher(user.id)
        if school_class is None or not verify_class_owner(school_class, user):
            return None
        return school_class

    @router.get("/add", response_class=HTMLResponse)
    def child_add_page(
        request: Request,
        user: User = Depends(get_current_user),
    ):
        school_class = _require_own_class(user)
        if school_class is None:
            flash(request, "먼저 반을 만들어 주세요.", "error")
            return RedirectResponse(url="/", status_code=303)

        return templates.TemplateResponse(
            request,
            "child_form.html",
            {
                "user": user,
                "school_class": school_class,
                "child": None,
                "photo_display": "/static/images/default-profile.svg",
                "form_action": "/children/add",
                "page_title": "아이 추가",
                "flashes": pop_flashes(request),
            },
        )

    @router.post("/add")
    async def child_add_submit(
        request: Request,
        user: User = Depends(get_current_user),
        child_name: Annotated[str, Form()] = "",
        company_name: Annotated[str, Form()] = "",
        photo_url: Annotated[str, Form()] = "",
        photo_file: UploadFile | None = File(None),
    ):
        school_class = _require_own_class(user)
        if school_class is None:
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/", status_code=303)

        try:
            photo_path, uploaded_url = await save_photo_upload(photo_file)
            merged_url = uploaded_url or photo_url or None
            create_child(
                school_class,
                child_name,
                photo_path=photo_path,
                photo_url=merged_url,
                company_name=company_name,
            )
            flash(request, "아이가 등록되었습니다.", "success")
        except ValueError as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(url="/children/add", status_code=303)

        return RedirectResponse(url="/classes/manage", status_code=303)

    @router.get("/{child_id}/edit", response_class=HTMLResponse)
    def child_edit_page(
        request: Request,
        child_id: int,
        user: User = Depends(get_current_user),
    ):
        school_class = _require_own_class(user)
        if school_class is None:
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/", status_code=303)

        try:
            child = get_child_for_teacher(child_id, user)
        except ChildAccessDeniedError:
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/classes/manage", status_code=303)

        return templates.TemplateResponse(
            request,
            "child_form.html",
            {
                "user": user,
                "school_class": school_class,
                "child": child,
                "photo_display": resolve_photo_display(child),
                "form_action": f"/children/{child_id}/edit",
                "page_title": "아이 수정",
                "flashes": pop_flashes(request),
            },
        )

    @router.post("/{child_id}/edit")
    async def child_edit_submit(
        request: Request,
        child_id: int,
        user: User = Depends(get_current_user),
        child_name: Annotated[str, Form()] = "",
        company_name: Annotated[str, Form()] = "",
        photo_url: Annotated[str, Form()] = "",
        photo_file: UploadFile | None = File(None),
        remove_photo: Annotated[str, Form()] = "",
    ):
        try:
            child = get_child_for_teacher(child_id, user)
        except ChildAccessDeniedError:
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/classes/manage", status_code=303)

        try:
            photo_path, uploaded_url = await save_photo_upload(photo_file)
            merged_url = uploaded_url if uploaded_url else photo_url
            update_child(
                child,
                child_name,
                photo_path=photo_path,
                photo_url=merged_url,
                company_name=company_name,
                clear_upload=remove_photo == "1" and photo_path is None and not uploaded_url,
            )
            flash(request, "아이 정보가 수정되었습니다.", "success")
        except ValueError as exc:
            flash(request, str(exc), "error")
            return RedirectResponse(url=f"/children/{child_id}/edit", status_code=303)

        return RedirectResponse(url="/classes/manage", status_code=303)

    @router.post("/{child_id}/delete")
    def child_delete_submit(
        request: Request,
        child_id: int,
        user: User = Depends(get_current_user),
    ):
        try:
            child = get_child_for_teacher(child_id, user)
        except ChildAccessDeniedError:
            flash(request, "접근 권한이 없습니다.", "error")
            return RedirectResponse(url="/classes/manage", status_code=303)

        delete_child(child)
        flash(request, "아이가 삭제되었습니다.", "success")
        return RedirectResponse(url="/classes/manage", status_code=303)

    return router
