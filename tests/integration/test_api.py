from io import BytesIO

from apps.worker.worker import process_pending_import_jobs


def _bootstrap_household(client, headers, *, household_name: str) -> dict:
    response = client.post(
        "/households/bootstrap",
        json={"household_name": household_name},
        headers=headers,
    )
    response.raise_for_status()
    return response.json()


def test_api_bootstrap_to_analytics_flow(client, auth_headers_factory) -> None:
    headers, user = auth_headers_factory(email="owner@example.com", display_name="Owner")
    me = client.get("/auth/me", headers=headers)
    me.raise_for_status()
    assert me.json()["email"] == user["email"]

    payload = _bootstrap_household(client, headers, household_name="Family A")
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
        headers=headers,
    )
    account.raise_for_status()
    account_id = account.json()["id"]

    client.post("/categories", json={"household_id": household_id, "name": "Food"}, headers=headers).raise_for_status()
    client.post(
        "/budgets",
        json={"household_id": household_id, "month": "2026-03", "limit_amount": "500"},
        headers=headers,
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
        headers=headers,
    ).raise_for_status()

    summary = client.get("/analytics/monthly-summary", params={"household_id": household_id, "month": "2026-03"}, headers=headers)
    summary.raise_for_status()
    budget = client.get("/analytics/budget-status", params={"household_id": household_id, "month": "2026-03"}, headers=headers)
    budget.raise_for_status()

    assert summary.json()["expense"] == "88.80"
    assert budget.json()["remaining"] == "411.20"


def test_import_route_enqueues_and_worker_processes_jobs_without_openclaw_runtime(client, auth_headers_factory, monkeypatch) -> None:
    headers, _ = auth_headers_factory(email="owner2@example.com", display_name="Owner2")
    bootstrap = _bootstrap_household(client, headers, household_name="Family B")
    household_id = bootstrap["household_id"]
    member_id = bootstrap["member_id"]
    account = client.post(
        "/accounts",
        json={
            "household_id": household_id,
            "member_id": member_id,
            "name": "WeChat",
            "type": "ewallet",
            "balance": "0",
        },
        headers=headers,
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
        headers=headers,
    )
    response.raise_for_status()
    initial_job = client.get(
        f"/imports/jobs/{response.json()['job_id']}",
        params={"household_id": household_id},
        headers=headers,
    )
    initial_job.raise_for_status()

    def fake_run(*args, **kwargs):
        raise FileNotFoundError("openclaw")

    monkeypatch.setattr("subprocess.run", fake_run)
    processed = process_pending_import_jobs()

    job = client.get(
        f"/imports/jobs/{response.json()['job_id']}",
        params={"household_id": household_id},
        headers=headers,
    )
    job.raise_for_status()
    transactions = client.get("/transactions", params={"household_id": household_id}, headers=headers)
    transactions.raise_for_status()

    assert processed == [response.json()["job_id"]]
    assert response.json()["status"] == "pending"
    assert response.json()["imported_count"] == 0
    assert initial_job.json()["status"] == "pending"
    assert job.json()["status"] == "completed"
    assert job.json()["record_count"] == 1
    assert len(transactions.json()) == 1


def test_import_route_returns_failed_job_state_after_worker_parse_error(client, auth_headers_factory, monkeypatch) -> None:
    headers, _ = auth_headers_factory(email="owner3@example.com", display_name="Owner3")
    bootstrap = _bootstrap_household(client, headers, household_name="Family C")
    household_id = bootstrap["household_id"]
    member_id = bootstrap["member_id"]
    account = client.post(
        "/accounts",
        json={
            "household_id": household_id,
            "member_id": member_id,
            "name": "WeChat",
            "type": "ewallet",
            "balance": "0",
        },
        headers=headers,
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
        headers=headers,
    )
    response.raise_for_status()

    def fake_run(*args, **kwargs):
        raise FileNotFoundError("openclaw")

    monkeypatch.setattr("subprocess.run", fake_run)
    process_pending_import_jobs()

    job = client.get(
        f"/imports/jobs/{response.json()['job_id']}",
        params={"household_id": household_id},
        headers=headers,
    )
    job.raise_for_status()

    assert response.json()["status"] == "pending"
    assert job.json()["status"] == "failed"
    assert job.json()["error_message"] is not None


def test_chat_route_returns_503_when_openclaw_cli_missing(client, auth_headers_factory, monkeypatch) -> None:
    headers, _ = auth_headers_factory(email="owner4@example.com", display_name="Owner4")
    bootstrap = _bootstrap_household(client, headers, household_name="Family D")

    def fake_run(*args, **kwargs):
        raise FileNotFoundError("openclaw")

    monkeypatch.setattr("subprocess.run", fake_run)
    response = client.post(
        "/chat/messages",
        json={
            "household_id": bootstrap["household_id"],
            "session_key": "agent:homefin:test:wechat:actor",
            "message": "hello",
        },
        headers=headers,
    )

    assert response.status_code == 503
    assert response.json()["error_code"] == "openclaw_cli_not_found"
