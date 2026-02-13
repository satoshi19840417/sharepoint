from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.send_ledger import SendLedger


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


class SecretRotationTests(unittest.TestCase):
    def test_verify_accepts_current_and_previous_secret_version(self):
        with _KeyringPatch():
            with tempfile.TemporaryDirectory() as tmp:
                ledger = SendLedger(str(Path(tmp) / "ledger.sqlite3"))
                request_key = "rq:v2:abc123"

                token_v1 = ledger.build_idempotency_token(request_key, "v1")
                token_v2 = ledger.build_idempotency_token(request_key, "v2")

                self.assertTrue(ledger.verify_idempotency_token(request_key, token_v2, "v2"))
                self.assertTrue(ledger.verify_idempotency_token(request_key, token_v1, "v2"))
                self.assertFalse(ledger.verify_idempotency_token(request_key, "deadbeef", "v2"))
                ledger.close()


if __name__ == "__main__":
    unittest.main()
