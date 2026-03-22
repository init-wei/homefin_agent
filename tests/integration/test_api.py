from io import BytesIO


def test_api_bootstrap_to_analytics_flow(client) -> None:
    bootstrap = client.post(
        "/households/bootstrap",
        json={
            "household_name": "Family A",
            "owner_email": "owner@example.com",
            "owner_display_name": "Owner",
        },
    )
    bootstrap.raise_for_status()
    payload = bootstrap.json()
    household_id = payload["household_id"]
    member_id = payload["member_id"]

    account = client.post(
        "/accounts",
        json={
            "household_id": household_id,
            "member_id": member_id,
            "name": "Main Card",
            "type": "bank",
            "balance": "0",
        },
    )
    account.raise_for_status()
    account_id = account.json()["id"]

    client.post("/categories", json={"household_id": household_id, "name": "Food"}).raise_for_status()
    client.post(
        "/budgets",
        json={"household_id": household_id, "month": "2026-03", "limit_amount": "500"},
    ).raise_for_status()
    client.post(
        "/transactions",
        json={
            "household_id": household_id,
            "account_id": account_id,
            "member_id": member_id,
            "direction": "expense",
            "amount": "88.80",
            "txn_time": "2026-03-20T08:30:00+00:00",
            "description": "Groceries",
        },
    ).raise_for_status()

    summary = client.get("/analytics/monthly-summary", params={"household_id": household_id, "month": "2026-03"})
    summary.raise_for_status()
    budget = client.get("/analytics/budget-status", params={"household_id": household_id, "month": "2026-03"})
    budget.raise_for_status()

    assert summary.json()["expense"] == "88.80"
    assert budget.json()["remaining"] == "411.20"


def test_import_route_tracks_job_and_dedupes(client) -> None:
    bootstrap = client.post(
        "/households/bootstrap",
        json={
            "household_name": "Family B",
            "owner_email": "owner2@example.com",
            "owner_display_name": "Owner2",
        },
    )
    bootstrap.raise_for_status()
    household_id = bootstrap.json()["household_id"]
    member_id = bootstrap.json()["member_id"]
    account = client.post(
        "/accounts",
        json={
            "household_id": household_id,
            "member_id": member_id,
            "name": "WeChat",
            "type": "ewallet",
            "balance": "0",
        },
    )
    account.raise_for_status()
    account_id = account.json()["id"]
    payload = (
        "交易时间,收/支,交易对方,商品,金额(元),交易单号\n"
        "2026-03-20 08:30:00,支出,楼下超市,早餐,12.50,wx-001\n"
        "2026-03-20 08:30:00,支出,楼下超市,早餐,12.50,wx-001\n"
    )
    response = client.post(
        "/imports/statements",
        data={"household_id": household_id, "account_id": account_id},
        files={"file": ("wechat.csv", BytesIO(payload.encode("utf-8")), "text/csv")},
    )
    response.raise_for_status()
    job = client.get(f"/imports/jobs/{response.json()['job_id']}")
    job.raise_for_status()
    transactions = client.get("/transactions", params={"household_id": household_id})
    transactions.raise_for_status()

    assert response.json()["status"] == "completed"
    assert response.json()["imported_count"] == 1
    assert job.json()["record_count"] == 1
    assert len(transactions.json()) == 1


def test_import_route_returns_failed_job_state_on_parse_error(client) -> None:
    bootstrap = client.post(
        "/households/bootstrap",
        json={
            "household_name": "Family C",
            "owner_email": "owner3@example.com",
            "owner_display_name": "Owner3",
        },
    )
    bootstrap.raise_for_status()
    household_id = bootstrap.json()["household_id"]
    member_id = bootstrap.json()["member_id"]
    account = client.post(
        "/accounts",
        json={
            "household_id": household_id,
            "member_id": member_id,
            "name": "WeChat",
            "type": "ewallet",
            "balance": "0",
        },
    )
    account.raise_for_status()
    account_id = account.json()["id"]
    payload = (
        "交易时间,收/支,交易对方,商品,金额(元),交易单号\n"
        "not-a-date,支出,楼下超市,早餐,12.50,wx-001\n"
    )
    response = client.post(
        "/imports/statements",
        data={"household_id": household_id, "account_id": account_id},
        files={"file": ("wechat.csv", BytesIO(payload.encode("utf-8")), "text/csv")},
    )
    response.raise_for_status()

    assert response.json()["status"] == "failed"
    assert response.json()["error_message"] is not None


def test_chat_route_returns_503_when_openclaw_cli_missing(client, monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise FileNotFoundError("openclaw")

    monkeypatch.setattr("subprocess.run", fake_run)
    response = client.post(
        "/chat/messages",
        json={
            "session_key": "agent:homefin:test:wechat:actor",
            "message": "hello",
        },
    )

    assert response.status_code == 503
    assert response.json()["error_code"] == "openclaw_cli_not_found"
