"""M1 trace case (docs/trace_case.md): FM-03 ticket_trust on C-002@11.

The first wrong step is event #3 `model_override`: the ticket's "5 days late" replaces
the DB's delay_days=2, so a claim that must be denied gets a 20.000đ refund.
"""
import pytest

pytestmark = pytest.mark.student


def test_c002_ticket_trust_is_caught():
    from lab9.trace_case import investigate

    bad = investigate("seeded_regression", "C-002", 11)
    good = investigate("fixed", "C-002", 11)

    # The buggy variant overrides a DB fact and the ledger no longer matches the label.
    assert any(e.get("kind") == "model_override" for e in bad["trial"]["events"])
    assert bad["trial"]["snapshot"]["refund_vnd"] != bad["label"]["refund_vnd"]

    # The fixed shape keeps the DB fact and the ledger matches the label.
    assert not any(e.get("kind") == "model_override" for e in good["trial"]["events"])
    assert good["trial"]["snapshot"]["refund_vnd"] == good["label"]["refund_vnd"]
