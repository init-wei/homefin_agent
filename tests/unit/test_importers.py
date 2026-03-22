from adapters.importers.registry import default_importer_registry
from adapters.importers.wechat_csv import WechatCSVImporter
from domain.enums.transaction import TransactionDirection
from domain.value_objects.dedupe_key import build_dedupe_key


def test_wechat_importer_normalizes_rows() -> None:
    payload = (
        "交易时间,收/支,交易对方,商品,金额(元),交易单号\n"
        "2026-03-20 08:30:00,支出,楼下超市,早餐,12.50,wx-001\n"
    ).encode("utf-8")
    importer = WechatCSVImporter()

    rows = importer.parse(payload)
    normalized = importer.normalize(rows[0])

    assert len(rows) == 1
    assert normalized.direction == TransactionDirection.EXPENSE
    assert str(normalized.amount) == "12.50"
    assert normalized.counterparty == "楼下超市"
    assert normalized.source_txn_id == "wx-001"


def test_importer_registry_picks_bank_csv() -> None:
    registry = default_importer_registry()
    sample = b"txn_time,amount,direction,description\n2026-03-20T08:30:00,15.00,expense,Coffee\n"

    importer = registry.pick(filename="bank_statement.csv", mime_type="text/csv", sample=sample)

    assert importer.source_type == "bank_csv"


def test_dedupe_key_is_stable() -> None:
    left = build_dedupe_key(
        household_id="h1",
        account_id="a1",
        txn_time="2026-03-20T08:30:00+00:00",
        amount="12.50",
        counterparty="  楼下超市 ",
        description="早餐",
        source_txn_id="wx-001",
    )
    right = build_dedupe_key(
        household_id="h1",
        account_id="a1",
        txn_time="2026-03-20T08:30:00+00:00",
        amount="12.50",
        counterparty="楼下超市",
        description="早餐",
        source_txn_id="wx-001",
    )

    assert left == right

