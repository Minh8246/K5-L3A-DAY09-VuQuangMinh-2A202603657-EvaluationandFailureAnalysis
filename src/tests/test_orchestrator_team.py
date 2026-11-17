"""Test riêng của shape C orchestrator (nhóm ABCDE).

Chạy trong cổng host mặc định (`python -m pytest -q`). T12 trong ma trận student chỉ
kiểm một điểm crash; file này kiểm cả ba điểm `crash_at` mà host hỗ trợ, cộng các ranh
giới riêng của orchestrator:

- handoff ghi vào trace là bản đã sanitize: chỉ field allowlist, chỉ tool đọc;
- trace của mọi claim public không chứa secret, ticket hay PII của order row
  (docs/contracts.md, Trace contract v1 mục 4);
- nhánh return sớm (`failed`, `needs_info`, `escalated`) vẫn ghi trace đúng `run_id`
  và không tạo refund;
- tiền chỉ tính từ order view của investigator, không tin số ngày trễ trong ticket.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from lab8.db import connect
from lab8.durability import InjectedCrash, committed_audit_count, get_refund
from lab8.handoff import ALLOWED_FIELDS, FACT_KEYS, READONLY_TOOLS, WRITE_TOOLS
from lab8.shapes.orchestrator import run_claim
from tests.conftest import BY_ID, WORLD

CRASH_POINTS = ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"]
# Field của order row không được xuất hiện trong trace (SĐT, địa chỉ, ghi chú nội bộ, tên hàng).
ORDER_PII_FIELDS = ("phone", "address", "internal_note", "item_name")


def _load_trace(result) -> tuple[dict, str]:
    raw = Path(result.trace_path).read_text(encoding="utf-8")
    return json.loads(raw), raw


@pytest.mark.parametrize("crash_at", CRASH_POINTS)
def test_orchestrator_crash_then_resume_pays_once(public_db, crash_at):
    with pytest.raises(InjectedCrash):
        run_claim("C-001", seed=11, store_path=str(public_db), crash_at=crash_at)

    result = run_claim("C-001", seed=11, store_path=str(public_db))

    conn = connect(public_db)
    try:
        effect = get_refund(conn, "C-001")
        rows = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = 'C-001'").fetchone()["n"]
        audits = committed_audit_count(conn, "C-001")
    finally:
        conn.close()
    assert result.status == "resolved"
    assert result.proposal_amount == 35000
    assert rows == 1
    assert int(effect["amount_vnd"]) == 35000
    assert audits == 1
    assert result.committed_audit_count == 1


def test_orchestrator_trace_records_only_sanitized_handoff(public_db):
    result = run_claim("C-001", seed=11, store_path=str(public_db))
    body, _ = _load_trace(result)

    handoffs = [event["payload"] for event in body["events"] if event["kind"] == "handoff_created"]
    assert len(handoffs) == 1
    handoff = handoffs[0]
    assert set(handoff) <= ALLOWED_FIELDS
    assert handoff["contract_version"] == "handoff.v1"
    assert handoff["claim_id"] == "C-001"
    assert set(handoff["facts"]) <= FACT_KEYS
    assert handoff["allowed_tools"]
    assert set(handoff["allowed_tools"]) <= READONLY_TOOLS
    assert not set(handoff["allowed_tools"]) & WRITE_TOOLS


@pytest.mark.parametrize("claim_id", sorted(BY_ID))
def test_orchestrator_trace_has_no_secret_ticket_or_pii(public_db, claim_id):
    claim = BY_ID[claim_id]
    result = run_claim(claim_id, seed=11, store_path=str(public_db))
    body, raw = _load_trace(result)

    assert body["run_id"] == result.run_id
    assert isinstance(body["events"], list) and body["events"]
    # "CANARY_" phủ cả parent_secret, Authorization header và internal_note của order.
    assert "CANARY_" not in raw
    assert claim["ticket"] not in raw
    assert claim["principal_id"] not in raw
    for order in WORLD["orders"]:
        for field in ORDER_PII_FIELDS:
            value = order.get(field)
            if value:
                assert str(value) not in raw, f"{field} của {order['order_id']} lọt vào trace"


def test_orchestrator_ignores_delay_written_in_ticket(public_db):
    # C-002: ticket ghi "trễ 5 ngày" nhưng dòng order ghi 2 ngày -> không đủ điều kiện.
    # Swarm tin ticket ở seed 55; orchestrator chỉ quote từ order view nên từ chối ở mọi seed.
    for seed in (11, 55):
        result = run_claim("C-002", seed=seed, store_path=str(public_db))
        assert result.status == "denied"
        assert result.proposal_amount == 0
        assert result.refund_effects == []


@pytest.mark.parametrize(
    ("claim_id", "status"),
    [
        ("C-NOT-FOUND", "failed"),  # không có claim
        ("C-004", "needs_info"),  # claim thiếu order_id
        ("C-005", "escalated"),  # principal không sở hữu đơn
    ],
)
def test_orchestrator_early_return_writes_trace_without_refund(public_db, claim_id, status):
    result = run_claim(claim_id, seed=11, store_path=str(public_db))
    body, raw = _load_trace(result)

    assert result.status == status
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert body["run_id"] == result.run_id
    assert "CANARY_" not in raw

    conn = connect(public_db)
    try:
        assert get_refund(conn, claim_id) is None
        assert committed_audit_count(conn, claim_id) == 0
    finally:
        conn.close()
