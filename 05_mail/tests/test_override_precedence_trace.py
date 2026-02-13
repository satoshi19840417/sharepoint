import datetime as dt
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.csv_handler import ContactRecord
from scripts.main import QuoteRequestSkill
from scripts.mail_sender import SendResult
from scripts.send_ledger import SendLedger


class _AuditStub:
    def __init__(self) -> None:
        self.execution_id = "test-run-override"

    def write_audit_log(self, input_file, results, product_info=None):
        return "audit.json"

    def write_sent_list(self, results):
        return "sent.csv"

    def write_unsent_list(self, results):
        return "unsent.csv"

    def format_screen_output(self, results):
        return "screen"


class _KeyringPatch:
    def __init__(self):
        self._store = {}
        self._patchers = []

    def __enter__(self):
        self._patchers = [
            mock.patch(
                "scripts.send_ledger.keyring.get_password",
                side_effect=lambda service, key: self._store.get((service, key)),
            ),
            mock.patch(
                "scripts.send_ledger.keyring.set_password",
                side_effect=lambda service, key, val: self._store.__setitem__((service, key), val),
            ),
        ]
        for p in self._patchers:
            p.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        for p in reversed(self._patchers):
            p.stop()


class OverridePrecedenceTests(unittest.TestCase):
    def test_request_key_override_has_priority_and_trace(self):
        with _KeyringPatch():
            with tempfile.TemporaryDirectory() as tmp:
                skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
                skill.audit_logger = _AuditStub()
                original_ledger = skill.send_ledger
                skill.send_ledger = SendLedger(str(Path(tmp) / "send_ledger.sqlite3"))
                original_ledger.close()
                skill.config.update(
                    {
                        "rerun_policy_default": "auto_skip",
                        "rerun_scope": "global",
                        "dedupe_key_version": "v2",
                    }
                )
                record = ContactRecord(company_name="A社", email="a@example.com", contact_name="担当")
                recipient_norm = skill._normalize_email(record.email)
                canonical_url = skill._normalize_input_url("https://example.com/item")
                request_key = skill._build_request_key(recipient_norm, "code-1", canonical_url, "", "v2")
                recipient_hash = skill.send_ledger.hash_recipient(recipient_norm)

                skill.send_ledger.add_override(
                    kind="recipient",
                    target_hash=recipient_hash,
                    ttl_min=30,
                    reason="recipient override",
                    operator="tester",
                    host="host",
                    command_summary_redacted="recipient",
                )
                skill.send_ledger.add_override(
                    kind="request_key",
                    target_hash=request_key,
                    ttl_min=30,
                    reason="request override",
                    operator="tester",
                    host="host",
                    command_summary_redacted="request_key",
                )

                skill.send_ledger.mark_sent(
                    request_key=request_key,
                    v1_key="legacy",
                    key_version="v2",
                    run_id="previous",
                    mail_key="mk:v2:prev",
                    recipient_hash=recipient_hash,
                    message_id="MID-PREV",
                    message_id_source="direct",
                    idempotency_token="token-prev",
                    idempotency_secret_version="v1",
                    subject_norm="TC-OVR",
                    decision_trace=["seed"],
                    sent_at=dt.datetime.now(),
                )

                with mock.patch.object(
                    skill.mail_sender,
                    "send_mail",
                    return_value=SendResult(
                        success=True,
                        email=record.email,
                        company_name="A社",
                        message_id="MID-NEW",
                        sent_at=dt.datetime.now(),
                        message_id_source="direct",
                    ),
                ):
                    result = skill.send_bulk(
                        records=[record],
                        subject="TC-OVR",
                        template_content="fixed",
                        product_name="P",
                        product_features="F",
                        product_url="https://example.com/item",
                        maker_code="CODE-1",
                        input_file="tc_ovr.csv",
                    )
                skill.send_ledger.close()

        self.assertEqual(result["success_count"], 1)
        trace = result["results"][0].get("decision_trace", [])
        self.assertTrue(any("override_applied:request_key" in str(t) for t in trace))


if __name__ == "__main__":
    unittest.main()
