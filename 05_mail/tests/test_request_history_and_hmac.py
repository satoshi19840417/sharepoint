import datetime as dt
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.hmac_key_manager import HmacKeyManager
from scripts.request_history_store import RequestHistoryStore


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
        ]
        for p in self._patchers:
            p.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        for p in reversed(self._patchers):
            p.stop()


class RequestHistoryAndHmacTests(unittest.TestCase):
    def test_history_save_and_key_version(self):
        with _KeyringPatch():
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                manager = HmacKeyManager(
                    credential_service="test-service",
                    registry_path=base / "logs" / "request_history" / "hmac_registry.json",
                    rotation_days=180,
                )
                store = RequestHistoryStore(base_dir=base, key_manager=manager, retention_days=365)
                payload = store.build_history_payload(
                    request_id="req-1",
                    run_id="run-1",
                    workflow_mode="enhanced",
                    send_mode="draft_only",
                    state="completed",
                    final_recipients=["A@example.com", "b@example.com"],
                    blocked_reasons=[],
                )
                path = store.save_history(request_id="req-1", run_id="run-1", payload=payload)
                data = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(data["request_id"], "req-1")
        self.assertEqual(data["run_id"], "run-1")
        self.assertEqual(data["hmac_key_version"], "v1")
        self.assertEqual(data["verification_status"], "verifiable")
        self.assertEqual(len(data["recipient_hashes"]), 2)

    def test_legacy_unverifiable_when_key_revoked(self):
        with _KeyringPatch():
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp)
                manager = HmacKeyManager(
                    credential_service="test-service",
                    registry_path=base / "logs" / "request_history" / "hmac_registry.json",
                    rotation_days=180,
                )
                version, _ = manager.ensure_active_key()
                self.assertEqual(version, "v1")
                manager.revoke_version("v1")
                status = manager.verification_status_for_version("v1")

        self.assertEqual(status, "legacy_unverifiable")


if __name__ == "__main__":
    unittest.main()

