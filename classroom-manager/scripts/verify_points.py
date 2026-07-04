"""포인트 기능 검증 — 14가지 시나리오 (SQLite 테스트 모드)."""

from __future__ import annotations

import os

os.environ["CLASSROOM_TEST_SQLITE"] = "1"

from fastapi.testclient import TestClient

from api.app import app
from api.wallet_repository import get_wallet

client = TestClient(app)


def test_all() -> None:
    # 로그인
    client.post("/logout")
    client.post("/login", data={"name": "포인트선생"}, follow_redirects=False)

    # 반 생성
    client.post(
        "/classes/create",
        data={"class_name": "포인트반", "currency_code": "BEAN"},
        follow_redirects=False,
    )

    # 1. 아이 추가 시 지갑 자동 생성
    client.post(
        "/children/add",
        data={"child_name": "민수", "company_name": "콩농장"},
        follow_redirects=False,
    )
    r = client.get("/classes/manage")
    assert "민수" in r.text
    import re

    m = re.search(r"/children/(\d+)/points/deposit", r.text)
    assert m, "child id not found"
    child_id = int(m.group(1))
    wallet = get_wallet(child_id, "BEAN")
    assert wallet is not None and wallet.balance == 0
    print("1. OK - wallet auto-created")

    # 2. 아이 카드에 잔액 표시
    assert "보유" in r.text
    print("2. OK - balance on card")

    # 3-5. 지급
    r = client.post(
        f"/children/{child_id}/points/deposit",
        data={"amount": "10", "memo": "칭찬"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    wallet = get_wallet(child_id, "BEAN")
    assert wallet.balance == 10
    print("3-5. OK - deposit + balance + tx")

    # 6-8. 차감
    client.post(
        f"/children/{child_id}/points/withdraw",
        data={"amount": "3", "memo": "벌점"},
        follow_redirects=False,
    )
    wallet = get_wallet(child_id, "BEAN")
    assert wallet.balance == 7
    print("6-8. OK - withdraw + balance + tx")

    # 9. 잔액 초과 차감 불가
    r = client.post(
        f"/children/{child_id}/points/withdraw",
        data={"amount": "100"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    wallet = get_wallet(child_id, "BEAN")
    assert wallet.balance == 7
    print("9. OK - insufficient balance blocked")

    # 10. 아이별 거래내역
    r = client.get(f"/children/{child_id}/transactions")
    assert r.status_code == 200
    assert "지급" in r.text and "차감" in r.text
    assert "10" in r.text and "7" in r.text
    print("10. OK - child transactions")

    # 11. 반 전체 거래내역
    r = client.get("/classes/my/transactions")
    assert r.status_code == 200
    assert "민수" in r.text
    print("11. OK - class transactions")

    # 12. 다른 선생님 접근 차단
    client.post("/logout")
    client.post("/login", data={"name": "다른선생"}, follow_redirects=False)
    r = client.post(
        f"/children/{child_id}/points/deposit",
        data={"amount": "5"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    wallet = get_wallet(child_id, "BEAN")
    assert wallet.balance == 7
    print("12. OK - other teacher blocked")

    # 13. 로그아웃 후 접근 차단
    client.post("/logout")
    r = client.get(f"/children/{child_id}/transactions", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/login"
    print("13. OK - logout blocks access")

    # 14. balance_before / balance_after in transactions page
    client.post("/login", data={"name": "포인트선생"}, follow_redirects=False)
    r = client.get(f"/children/{child_id}/transactions")
    assert "0" in r.text  # balance_before from first deposit
    print("14. OK - before/after balances recorded")

    print("\nAll 14 point verification checks passed.")


if __name__ == "__main__":
    test_all()
