from hashlib import sha256


def _normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.lower().strip().split())


def build_dedupe_key(
    *,
    household_id: str,
    account_id: str,
    txn_time: str,
    amount: str,
    counterparty: str | None,
    description: str | None,
    source_txn_id: str | None,
) -> str:
    payload = "|".join(
        [
            household_id,
            account_id,
            txn_time,
            amount,
            _normalize_text(counterparty),
            _normalize_text(description),
            source_txn_id or "",
        ]
    )
    return sha256(payload.encode("utf-8")).hexdigest()

