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
from scripts.send_ledger import SendLedger
from scripts.workflow_service import WorkflowService


class _AuditStub:
    def write_audit_log(self, input_file, results, product_info=None, workflow_context=None):
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
                "scripts.hmac_key_manager.keyring.get_password",
                side_effect=lambda service, key: self._store.get((service, key)),
            ),
            mock.patch(
                "scripts.hmac_key_manager.keyring.set_password",
                side_effect=lambda service, key, value: self._store.__setitem__((service, key), value),
            ),
            mock.patch(
                "scripts.send_ledger.keyring.get_password",
                side_effect=lambda service, key: self._store.get((service, key)),
            ),
            mock.patch(
                "scripts.send_ledger.keyring.set_password",
                side_effect=lambda service, key, value: self._store.__setitem__((service, key), value),
            ),
        ]
        for p in self._patchers:
            p.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        for p in reversed(self._patchers):
            p.stop()


class SendModeBranchingTests(unittest.TestCase):
    def _make_service(self, tmp: str) -> WorkflowService:
        skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
        skill.base_dir = Path(tmp)
        skill.audit_logger = _AuditStub()
        original_ledger = skill.send_ledger
        skill.send_ledger = SendLedger(str(Path(tmp) / "send_ledger.sqlite3"))
        original_ledger.close()
        return WorkflowService(skill)

    def _records(self):
        return [ContactRecord(company_name="A社", email="a@example.com", contact_name="A")]

    def test_auto_mode_completed_when_approved_and_send_success(self):
        with _KeyringPatch():
            with tempfile.TemporaryDirectory() as tmp:
                service = self._make_service(tmp)
                with mock.patch.object(
                    service.skill,
                    "send_bulk",
                    return_value={"success": True, "audit_log_path": "audit.json"},
                ) as send_mock:
                    result = service.execute(
                        workflow_mode="enhanced",
                        send_mode="auto",
                        hearing_input={
                            "recipients_changed": False,
                            "send_mode": "auto",
                            "user_approved": True,
                        },
                        records=self._records(),
                        subject="subject",
                        template_content="本文",
                        product_name="製品A",
                        product_features="特徴",
                        product_url="https://example.com/item",
                        maker_code="CODE-1",
                        input_file="input.csv",
                    )
                service.skill.send_ledger.close()

        self.assertEqual(send_mock.call_count, 1)
        self.assertEqual(result["state"], "completed")
        self.assertTrue(result["completed_path"])

    def test_draft_only_requires_user_approval(self):
        with _KeyringPatch():
            with tempfile.TemporaryDirectory() as tmp:
                service = self._make_service(tmp)
                result = service.execute(
                    workflow_mode="enhanced",
                    send_mode="draft_only",
                    hearing_input={
                        "recipients_changed": False,
                        "send_mode": "draft_only",
                        "user_approved": False,
                    },
                    records=self._records(),
                    subject="subject",
                    template_content="本文",
                    product_name="製品A",
                    product_features="特徴",
                    product_url="https://example.com/item",
                    maker_code="CODE-1",
                    input_file="input.csv",
                )
                service.skill.send_ledger.close()

        self.assertEqual(result["state"], "pending")
        self.assertFalse(result["completed_path"])
        self.assertTrue(result["blocked_reasons"])

    def test_non_completed_cases_are_not_moved_to_completed(self):
        with _KeyringPatch():
            with tempfile.TemporaryDirectory() as tmp:
                service = self._make_service(tmp)
                service.skill.config["domain_blacklist"] = ["example.com"]
                service.skill.domain_filter = service.skill.domain_filter.__class__(
                    service.skill.config.get("domain_whitelist", []),
                    service.skill.config.get("domain_blacklist", []),
                )
                result = service.execute(
                    workflow_mode="enhanced",
                    send_mode="auto",
                    hearing_input={
                        "recipients_changed": True,
                        "final_recipients": ["a@example.com"],
                        "send_mode": "auto",
                        "user_approved": True,
                    },
                    records=self._records(),
                    subject="subject",
                    template_content="本文",
                    product_name="製品A",
                    product_features="特徴",
                    product_url="https://example.com/item",
                    maker_code="CODE-1",
                    input_file="input.csv",
                )
                service.skill.send_ledger.close()

        self.assertIn(result["state"], {"blocked", "failed"})
        self.assertFalse(result["completed_path"])


if __name__ == "__main__":
    unittest.main()

