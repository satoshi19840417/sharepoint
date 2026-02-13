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
from scripts.mail_sender import SendResult
from scripts.main import QuoteRequestSkill
from scripts.send_ledger import SendLedger


class _AuditStub:
    def __init__(self) -> None:
        self.execution_id = "test-run"

    def write_audit_log(self, input_file, results, product_info=None):
        return "audit.json"

    def write_sent_list(self, results):
        return "sent.csv"

    def write_unsent_list(self, results):
        return "unsent.csv"

    def format_screen_output(self, results):
        return "screen"


class SendBulkDedupeTests(unittest.TestCase):
    def test_send_bulk_skips_duplicate_in_same_run(self):
        store = {}
        with tempfile.TemporaryDirectory() as tmp, mock.patch(
            "scripts.send_ledger.keyring.get_password",
            side_effect=lambda service, key: store.get((service, key)),
        ), mock.patch(
            "scripts.send_ledger.keyring.set_password",
            side_effect=lambda service, key, value: store.__setitem__((service, key), value),
        ):
            skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
            skill.audit_logger = _AuditStub()
            original_ledger = skill.send_ledger
            skill.send_ledger = SendLedger(str(Path(tmp) / "send_ledger.jsonl"))
            original_ledger.close()

            records = [
                ContactRecord(company_name="A社", email="dup@example.com", contact_name="A"),
                ContactRecord(company_name="B社", email="dup@example.com", contact_name="B"),
            ]

            with mock.patch.object(
                skill.mail_sender,
                "send_mail",
                return_value=SendResult(
                    success=True,
                    email="dup@example.com",
                    company_name="A社",
                    message_id="MID-1",
                    sent_at=dt.datetime.now(),
                ),
            ) as send_mock:
                result = skill.send_bulk(
                    records=records,
                    subject="TC90",
                    template_content="fixed template body",
                    product_name="P",
                    product_features="F",
                    product_url="https://example.com",
                    maker_code="CODE-90",
                    input_file="tc90.csv",
                )
            skill.send_ledger.close()

        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(result["skipped_duplicate_count"], 1)
        self.assertTrue(any(r.get("action") == "skip_duplicate_in_run" for r in result["results"]))


if __name__ == "__main__":
    unittest.main()
