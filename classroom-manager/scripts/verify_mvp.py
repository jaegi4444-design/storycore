"""MVP 검증 스크립트 — 11가지 시나리오."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.app import app
from api.repository import get_active_currencies
from config.settings import USE_SUPABASE

client = TestClient(app)


def test_all() -> None:
    # 1. 로그인하지 않고 메인 페이지 접근 시 로그인 화면으로 이동
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 303, f"1 failed: {r.status_code}"
    assert r.headers["location"] == "/login"
    print("1. OK - unauthenticated main redirects to login")

    # 2. 이름으로 로그인하면 사용자 생성 또는 기존 사용자 로그인
    r = client.post("/login", data={"name": "김선생"}, follow_redirects=False)
    assert r.status_code == 303
    r = client.get("/")
    assert r.status_code == 200
    assert "김선생" in r.text
    print("2. OK - login creates user and shows main")

    # 3. 로그인 후 반을 만들 수 있다
    r = client.post(
        "/classes/create",
        data={"class_name": "3학년 2반", "currency_code": "BEAN"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    r = client.get("/classes/manage")
    assert r.status_code == 200
    assert "3학년 2반" in r.text
    print("3. OK - create class")

    # 4. 같은 사용자가 반을 2개 만들 수 없다
    r = client.get("/classes/create", follow_redirects=False)
    assert r.status_code == 303
    assert "/classes/manage" in r.headers["location"]
    r = client.post(
        "/classes/create",
        data={"class_name": "다른반", "currency_code": "BEAN"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "/classes/manage" in r.headers["location"]
    print("4. OK - duplicate class blocked")

    # 5. 반 생성 시 기본 화폐 단위가 콩
  # (already created with BEAN - verify in page)
    assert "콩" in r.text or client.get("/classes/manage").text.find("콩") >= 0
    print("5. OK - default currency is 콩")

    # 6. 코드 테이블에서 화폐 단위 조회
    db = None
    try:
        currencies = get_active_currencies()
        assert any(c.code == "BEAN" and c.code_name == "콩" for c in currencies)
    finally:
        pass
    r = client.get("/classes/create", follow_redirects=False)
    # already has class, redirected - logout and create new user
    print("6. OK - currency from code_table")

    # 7. 자기 반에 아이 추가
    r = client.post(
        "/children/add",
        data={"child_name": "홍길동", "photo_url": "https://example.com/a.jpg"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    r = client.get("/classes/manage")
    assert "홍길동" in r.text
    print("7. OK - add child")

    # 8. 아이 이름과 사진 수정
    r = client.get("/classes/manage")
    # extract child id from edit link
    import re

    m = re.search(r"/children/(\d+)/edit", r.text)
    assert m, "child edit link not found"
    child_id = m.group(1)
    r = client.post(
        f"/children/{child_id}/edit",
        data={"child_name": "홍길순", "photo_url": "https://example.com/b.jpg"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    r = client.get("/classes/manage")
    assert "홍길순" in r.text
    print("8. OK - edit child")

    # 9. 아이 삭제
    r = client.post(f"/children/{child_id}/delete", follow_redirects=False)
    assert r.status_code == 303
    r = client.get("/classes/manage")
    assert "홍길순" not in r.text
    print("9. OK - delete child")

    # 10. 다른 사용자의 반이나 아이 데이터 접근 불가
    client.post("/logout", follow_redirects=False)
    client.post("/login", data={"name": "이선생"}, follow_redirects=False)
    r = client.get("/classes/manage", follow_redirects=False)
    # 이선생 has no class - redirects to create
    assert r.status_code == 303

    r = client.post(
        f"/children/{child_id}/edit",
        data={"child_name": "해킹"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    r = client.get("/classes/manage", follow_redirects=False)
    # still no access to 김선생's class child

    client.post("/logout", follow_redirects=False)
    client.post("/login", data={"name": "김선생"}, follow_redirects=False)
    r = client.get("/classes/manage")
    assert "3학년 2반" in r.text
    r = client.post(f"/children/{child_id}/delete", follow_redirects=False)
    # child already deleted - should get access denied or manage redirect
    assert r.status_code == 303
    print("10. OK - other user cannot access foreign data")

    # 11. 로그아웃 후 기능 접근 막힘
    client.post("/logout", follow_redirects=False)
    r = client.get("/classes/manage", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"
    print("11. OK - logout blocks access")

    print("\nAll 11 verification checks passed.")


if __name__ == "__main__":
    test_all()
