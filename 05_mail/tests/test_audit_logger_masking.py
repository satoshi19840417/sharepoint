import json
from pathlib import Path
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.audit_logger import AuditLogger


class _DummyEncryptionManager:
    def encrypt(self, value: str) -> str:
        return f"enc:v1:{value}"


class AuditLoggerMaskingTests(unittest.TestCase):
    def test_error_log_masks_email_as_domain_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = AuditLogger(str(Path(tmp)), _DummyEncryptionManager())
            results = [
                {
                    "email": "user@example.com",
                    "company_name": "A社",
                    "success": False,
                    "error_details": {
                        "contact": "user@example.com",
                        "message": "通知先 user@example.com で失敗",
                    },
                }
            ]

            path = logger.write_audit_log("input.csv", results)
            data = json.loads(Path(path).read_text(encoding="utf-8"))

        self.assertEqual(data["errors"][0]["email_masked"], "***@example.com")
        self.assertEqual(data["errors"][0]["error"]["contact"], "***@example.com")
        self.assertIn("***@example.com", data["errors"][0]["error"]["message"])


if __name__ == "__main__":
    unittest.main()
