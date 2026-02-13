import datetime as dt
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


class SQLiteDualConnectionTests(unittest.TestCase):
    def test_dual_connection_pragmas_and_sent_commit(self):
        with _KeyringPatch():
            with tempfile.TemporaryDirectory() as tmp:
                ledger = SendLedger(str(Path(tmp) / "ledger.sqlite3"))
                main_sync = ledger.conn_main.execute("PRAGMA synchronous;").fetchone()[0]
                sent_sync = ledger.conn_sent.execute("PRAGMA synchronous;").fetchone()[0]
                self.assertEqual(main_sync, 1)  # NORMAL
                self.assertEqual(sent_sync, 2)  # FULL

                reserved = ledger.reserve_send(
                    request_key="rq:v2:abc",
                    v1_key="legacy",
                    key_version="v2",
                    run_id="run-1",
                    mail_key="mk:v2:abc",
                    recipient_hash="hash",
                    idempotency_token="token",
                    idempotency_secret_version="v1",
                    subject_norm="subj",
                    ttl_sec=600,
                    decision_trace=["test"],
                )
                self.assertTrue(reserved.acquired)

                ledger.mark_sent(
                    request_key="rq:v2:abc",
                    v1_key="legacy",
                    key_version="v2",
                    run_id="run-1",
                    mail_key="mk:v2:abc",
                    recipient_hash="hash",
                    message_id="MID-1",
                    message_id_source="direct",
                    idempotency_token="token",
                    idempotency_secret_version="v1",
                    subject_norm="subj",
                    decision_trace=["sent"],
                    sent_at=dt.datetime.now(),
                )
                recent = ledger.find_recent_sent("rq:v2:abc", "legacy", 24)
                self.assertIsNotNone(recent)
                self.assertEqual(recent.get("message_id"), "MID-1")
                ledger.close()


if __name__ == "__main__":
    unittest.main()
