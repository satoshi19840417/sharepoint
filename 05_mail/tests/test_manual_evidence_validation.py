import json
from pathlib import Path
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.manual_evidence_validator import ManualEvidenceValidator


class ManualEvidenceValidationTests(unittest.TestCase):
    def setUp(self):
        self.validator = ManualEvidenceValidator()

    def test_valid_evidence_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_id = "run-123"
            request_id = "req-123"
            p = Path(tmp) / f"manual_send_evidence_{run_id}.json"
            payload = {
                "request_id": request_id,
                "run_id": run_id,
                "operator": "tester",
                "confirmed_at": "2026-02-13T09:00:00+09:00",
                "recipients": [
                    {
                        "email": "A@example.com ",
                        "message_id": "MID-1",
                        "sent_at": "2026-02-13T09:00:01+09:00",
                    }
                ],
            }
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.validator.validate(
                p,
                expected_request_id=request_id,
                expected_run_id=run_id,
                expected_recipients=["a@example.com"],
            )
        self.assertTrue(result.valid)
        self.assertEqual(result.errors, [])

    def test_mismatch_recipients_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_id = "run-123"
            request_id = "req-123"
            p = Path(tmp) / f"manual_send_evidence_{run_id}.json"
            payload = {
                "request_id": request_id,
                "run_id": run_id,
                "operator": "tester",
                "confirmed_at": "2026-02-13T09:00:00+09:00",
                "recipients": [
                    {
                        "email": "x@example.com",
                        "message_id": "MID-1",
                        "sent_at": "2026-02-13T09:00:01+09:00",
                    }
                ],
            }
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.validator.validate(
                p,
                expected_request_id=request_id,
                expected_run_id=run_id,
                expected_recipients=["a@example.com"],
            )
        self.assertFalse(result.valid)
        self.assertTrue(any("一致しません" in e for e in result.errors))

    def test_duplicate_message_id_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_id = "run-dup"
            request_id = "req-dup"
            p = Path(tmp) / f"manual_send_evidence_{run_id}.json"
            payload = {
                "request_id": request_id,
                "run_id": run_id,
                "operator": "tester",
                "confirmed_at": "2026-02-13T09:00:00+09:00",
                "recipients": [
                    {"email": "a@example.com", "message_id": "MID-1", "sent_at": "2026-02-13T09:00:01+09:00"},
                    {"email": "b@example.com", "message_id": "MID-1", "sent_at": "2026-02-13T09:00:02+09:00"},
                ],
            }
            p.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            result = self.validator.validate(
                p,
                expected_request_id=request_id,
                expected_run_id=run_id,
                expected_recipients=["a@example.com", "b@example.com"],
            )
        self.assertFalse(result.valid)
        self.assertTrue(any("message_id 重複" in e for e in result.errors))


if __name__ == "__main__":
    unittest.main()

