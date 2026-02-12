import datetime as dt
from pathlib import Path
import sys
import unittest
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.csv_handler import ContactRecord
from scripts.mail_sender import SendResult
from scripts.main import QuoteRequestSkill
from scripts.template_processor import TemplateProcessor


class _AuditStub:
    def __init__(self) -> None:
        self.execution_id = "test-run"
        self.product_info = None

    def write_audit_log(self, input_file, results, product_info=None):
        self.product_info = product_info
        return "audit.json"

    def write_sent_list(self, results):
        return "sent.csv"

    def write_unsent_list(self, results):
        return "unsent.csv"

    def format_screen_output(self, results):
        return "screen"


class ProductInfoFieldTests(unittest.TestCase):
    def test_template_processor_renders_new_product_fields(self):
        processor = TemplateProcessor()
        template = (
            "製品名: ≪製品名≫\n"
            "メーカー名: ≪メーカー名≫\n"
            "メーカーコード: ≪メーカーコード≫\n"
            "数量: ≪数量≫\n"
        )
        result = processor.create_email_body(
            template_content=template,
            company_name="A社",
            contact_name="担当者",
            product_name="製品A",
            product_features="",
            product_url="https://example.com",
            maker_name="BIO-RAD",
            maker_code="170-4156",
            quantity="1個",
        )

        self.assertTrue(result.success)
        self.assertIn("製品A", result.content)
        self.assertIn("BIO-RAD", result.content)
        self.assertIn("170-4156", result.content)
        self.assertIn("1個", result.content)

    def test_send_bulk_passes_product_info_to_audit_log(self):
        skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
        skill.audit_logger = _AuditStub()
        skill.send_ledger = mock.Mock()
        skill.send_ledger.find_recent.return_value = None

        records = [
            ContactRecord(company_name="A社", email="a@example.com", contact_name="担当者")
        ]

        with mock.patch.object(
            skill.mail_sender,
            "send_mail",
            return_value=SendResult(
                success=True,
                email="a@example.com",
                company_name="A社",
                message_id="MID-1",
                sent_at=dt.datetime.now(),
            ),
        ):
            result = skill.send_bulk(
                records=records,
                subject="見積依頼",
                template_content="製品名: ≪製品名≫",
                product_name="製品A",
                product_features="",
                product_url="https://example.com",
                maker_name="BIO-RAD",
                maker_code="170-4156",
                quantity="1個",
                input_file="input.csv",
            )

        self.assertTrue(result["success"])
        self.assertEqual(
            skill.audit_logger.product_info,
            {
                "product_name": "製品A",
                "maker_name": "BIO-RAD",
                "maker_code": "170-4156",
                "quantity": "1個",
                "product_url": "https://example.com",
            },
        )


if __name__ == "__main__":
    unittest.main()
