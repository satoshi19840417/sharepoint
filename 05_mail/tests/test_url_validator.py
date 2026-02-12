from pathlib import Path
import sys
import unittest
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.url_validator import URLValidator


class _Resp:
    def __init__(self, status_code: int, url: str, history_count: int = 0):
        self.status_code = status_code
        self.url = url
        self.history = [object() for _ in range(history_count)]

    def close(self) -> None:
        return None


class URLValidatorTests(unittest.TestCase):
    def test_redirect_depth_over_limit_is_blocked(self):
        validator = URLValidator(max_redirects=5, retry_count=0)
        with mock.patch(
            "scripts.url_validator.requests.head",
            return_value=_Resp(200, "https://example.com/final", history_count=6),
        ):
            res = validator.validate("https://example.com")

        self.assertFalse(res.valid)
        self.assertIn("リダイレクト回数が上限を超えています", res.error)

    def test_http_warning_is_preserved_in_result(self):
        validator = URLValidator(retry_count=0)
        with mock.patch(
            "scripts.url_validator.requests.head",
            return_value=_Resp(200, "http://example.com/status/200"),
        ):
            res = validator.validate("http://example.com/status/200")

        self.assertTrue(res.warning)
        self.assertIn("HTTPスキーム", res.warning)


if __name__ == "__main__":
    unittest.main()
