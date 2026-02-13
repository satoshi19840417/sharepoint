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
        self.execution_id = "test-run-mig"

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


class DedupeMigrationTests(unittest.TestCase):
    def test_v1_history_blocks_v2_send_within_24h(self):
        with _KeyringPatch():
            with tempfile.TemporaryDirectory() as tmp:
                skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
                skill.audit_logger = _AuditStub()
                original_ledger = skill.send_ledger
                skill.send_ledger = SendLedger(str(Path(tmp) / "send_ledger.sqlite3"))
                original_ledger.close()
                skill.config.update(
                    {
                        "dedupe_key_version": "v2",
                        "rerun_scope": "global",
                        "rerun_policy_default": "auto_skip",
                        "rerun_window_hours": 24,
                    }
                )

                record = ContactRecord(company_name="A社", email="a@example.com", contact_name="担当")
                legacy_v1 = skill._build_legacy_v1_key(
                    email=record.email,
                    subject="TC-MIG",
                    template_content="fixed body",
                )
                skill.send_ledger.append_entry(
                    dedupe_key=legacy_v1,
                    recipient=record.email,
                    message_id="MID-V1",
                    run_id="legacy-run",
                    sent_at=dt.datetime.now(),
                )

                with mock.patch.object(
                    skill.mail_sender,
                    "send_mail",
                    return_value=SendResult(
                        success=True,
                        email=record.email,
                        company_name="A社",
                        message_id="MID-V2",
                        sent_at=dt.datetime.now(),
                    ),
                ) as send_mock:
                    result = skill.send_bulk(
                        records=[record],
                        subject="TC-MIG",
                        template_content="fixed body",
                        product_name="P",
                        product_features="F",
                        product_url="https://example.com/product?a=1",
                        maker_code="CODE-1",
                        input_file="tc_mig.csv",
                    )
                skill.send_ledger.close()

        self.assertEqual(send_mock.call_count, 0)
        self.assertEqual(result["skipped_rerun_count"], 1)


if __name__ == "__main__":
    unittest.main()
