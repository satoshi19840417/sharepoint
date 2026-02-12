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


class RerunDetectionTests(unittest.TestCase):
    def test_rerun_within_24h_requires_confirmation_and_skips_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
            skill.audit_logger = _AuditStub()
            skill.send_ledger = SendLedger(str(Path(tmp) / "send_ledger.jsonl"))

            records = [ContactRecord(company_name="A社", email="a91@example.com", contact_name="A")]

            with mock.patch.object(
                skill.mail_sender,
                "send_mail",
                return_value=SendResult(
                    success=True,
                    email="a91@example.com",
                    company_name="A社",
                    message_id="MID-91",
                    sent_at=dt.datetime.now(),
                ),
            ) as send_mock:
                first = skill.send_bulk(
                    records=records,
                    subject="TC91",
                    template_content="fixed template body",
                    product_name="P",
                    product_features="F",
                    product_url="https://example.com",
                    input_file="tc91_first.csv",
                )
                second = skill.send_bulk(
                    records=records,
                    subject="TC91",
                    template_content="fixed template body",
                    product_name="P",
                    product_features="F",
                    product_url="https://example.com",
                    input_file="tc91_second.csv",
                )

        self.assertEqual(first["success_count"], 1)
        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(second["skipped_rerun_count"], 1)
        self.assertTrue(second["warning"])
        self.assertTrue(any(r.get("confirmation_required") for r in second["results"]))


if __name__ == "__main__":
    unittest.main()
