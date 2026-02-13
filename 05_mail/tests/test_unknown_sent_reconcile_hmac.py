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
        self.execution_id = "test-run-unknown"

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


class UnknownSentReconcileTests(unittest.TestCase):
    def test_unknown_sent_is_reconciled_and_not_resent(self):
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
                send_ok = SendResult(
                    success=True,
                    email=record.email,
                    company_name="A社",
                    message_id="MID-1",
                    sent_at=dt.datetime.now(),
                    message_id_source="direct",
                )

                with mock.patch.object(skill.mail_sender, "send_mail", return_value=send_ok):
                    with mock.patch.object(skill.send_ledger, "mark_sent", side_effect=RuntimeError("commit failed")):
                        first = skill.send_bulk(
                            records=[record],
                            subject="TC-UNK",
                            template_content="fixed",
                            product_name="P",
                            product_features="F",
                            product_url="https://example.com/p",
                            maker_code="CODE-1",
                            input_file="tc_unknown_1.csv",
                        )
                self.assertEqual(first["confirmation_required_count"], 1)

                with mock.patch.object(
                    skill.mail_sender,
                    "reconcile_unknown_send",
                    return_value={"matched": True, "method": "header", "message_id": "MID-1"},
                ), mock.patch.object(skill.mail_sender, "send_mail") as send_mock_2:
                    second = skill.send_bulk(
                        records=[record],
                        subject="TC-UNK",
                        template_content="fixed",
                        product_name="P",
                        product_features="F",
                        product_url="https://example.com/p",
                        maker_code="CODE-1",
                        input_file="tc_unknown_2.csv",
                    )
                skill.send_ledger.close()

        self.assertEqual(send_mock_2.call_count, 0)
        self.assertTrue(any(r.get("action") == "skip_reconciled_sent" for r in second["results"]))


if __name__ == "__main__":
    unittest.main()
