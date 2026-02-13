from pathlib import Path
import sys
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.main import QuoteRequestSkill


class RequestKeyStabilityTests(unittest.TestCase):
    def test_request_key_is_stable_for_input_url_variants(self):
        skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
        try:
            u1 = "https://example.com/item?utm_source=a&b=2&a=1"
            u2 = "https://example.com/item?a=1&b=2&utm_source=z"
            c1 = skill._normalize_input_url(u1)
            c2 = skill._normalize_input_url(u2)
            self.assertEqual(c1, c2)

            key1 = skill._build_request_key(
                recipient_email_norm="user@example.com",
                maker_code_norm="code-1",
                canonical_input_url_norm=c1,
                quantity_norm="1",
                key_version="v2",
            )
            key2 = skill._build_request_key(
                recipient_email_norm="user@example.com",
                maker_code_norm="code-1",
                canonical_input_url_norm=c2,
                quantity_norm="1",
                key_version="v2",
            )
            self.assertEqual(key1, key2)
        finally:
            skill.send_ledger.close()

    def test_request_key_changes_when_sku_query_changes(self):
        skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
        try:
            c1 = skill._normalize_input_url("https://example.com/item?sku=abc")
            c2 = skill._normalize_input_url("https://example.com/item?sku=xyz")

            key1 = skill._build_request_key("user@example.com", "code-1", c1, "1", "v2")
            key2 = skill._build_request_key("user@example.com", "code-1", c2, "1", "v2")
            self.assertNotEqual(key1, key2)
        finally:
            skill.send_ledger.close()


if __name__ == "__main__":
    unittest.main()
