"""
hmac_key_manager.py - request_history向けHMAC鍵管理
"""

from __future__ import annotations

import datetime as dt
import hmac
import hashlib
import json
import secrets
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import keyring

UTC = dt.timezone.utc


class HmacKeyManager:
    def __init__(
        self,
        *,
        credential_service: str,
        registry_path: Path,
        rotation_days: int = 180,
    ):
        self.credential_service = credential_service
        self.registry_path = Path(registry_path)
        self.rotation_days = max(1, int(rotation_days))
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def _utcnow(self) -> dt.datetime:
        return dt.datetime.now(UTC)

    def _load_registry(self) -> Dict[str, Any]:
        if not self.registry_path.exists():
            return {"active_version": "", "keys": {}}
        try:
            data = json.loads(self.registry_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                return {"active_version": "", "keys": {}}
            data.setdefault("active_version", "")
            data.setdefault("keys", {})
            return data
        except Exception:
            return {"active_version": "", "keys": {}}

    def _save_registry(self, registry: Dict[str, Any]) -> None:
        self.registry_path.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def key_name(version: str) -> str:
        return f"aimitsu_hmac_key_{version}"

    @staticmethod
    def _version_number(version: str) -> int:
        text = str(version or "").strip().lower()
        if not text.startswith("v"):
            return 0
        try:
            return int(text[1:])
        except Exception:
            return 0

    def _next_version(self, registry: Dict[str, Any]) -> str:
        max_num = 0
        for version in registry.get("keys", {}).keys():
            max_num = max(max_num, self._version_number(version))
        return f"v{max_num + 1}"

    def _get_key(self, version: str) -> Optional[str]:
        return keyring.get_password(self.credential_service, self.key_name(version))

    def _set_key(self, version: str, value: str) -> None:
        keyring.set_password(self.credential_service, self.key_name(version), value)

    def get_active_version(self) -> str:
        return str(self._load_registry().get("active_version", ""))

    def ensure_active_key(self, now: Optional[dt.datetime] = None) -> Tuple[str, str]:
        registry = self._load_registry()
        current = (now or self._utcnow()).astimezone(UTC)
        active_version = str(registry.get("active_version", ""))
        keys = registry.setdefault("keys", {})

        def activate_new_version() -> Tuple[str, str]:
            version = self._next_version(registry)
            secret = secrets.token_hex(32)
            self._set_key(version, secret)
            keys[version] = {
                "created_at_utc": current.isoformat(),
                "status": "active",
            }
            registry["active_version"] = version
            self._save_registry(registry)
            return version, secret

        if not active_version:
            return activate_new_version()

        active_meta = keys.get(active_version, {})
        created_raw = str(active_meta.get("created_at_utc", ""))
        created_at = None
        if created_raw:
            try:
                created_at = dt.datetime.fromisoformat(created_raw).astimezone(UTC)
            except Exception:
                created_at = None

        status = str(active_meta.get("status", "active"))
        active_secret = self._get_key(active_version)
        needs_rotation = False
        if status != "active" or not active_secret:
            needs_rotation = True
        elif created_at and current >= created_at + dt.timedelta(days=self.rotation_days):
            needs_rotation = True

        if needs_rotation:
            return activate_new_version()
        return active_version, active_secret

    def revoke_version(self, version: str) -> None:
        registry = self._load_registry()
        keys = registry.setdefault("keys", {})
        meta = keys.setdefault(version, {})
        meta["status"] = "revoked"
        meta.setdefault("created_at_utc", self._utcnow().isoformat())
        if registry.get("active_version") == version:
            registry["active_version"] = ""
        self._save_registry(registry)

    def is_revoked(self, version: str) -> bool:
        registry = self._load_registry()
        meta = registry.get("keys", {}).get(version, {})
        return str(meta.get("status", "")).lower() == "revoked"

    @staticmethod
    def normalize_email(value: str) -> str:
        return str(value or "").strip().lower()

    def hash_email(self, email: str, version: Optional[str] = None) -> Tuple[str, str]:
        selected_version = str(version or "").strip()
        if not selected_version:
            selected_version, secret = self.ensure_active_key()
        else:
            secret = self._get_key(selected_version)
            if not secret:
                return selected_version, ""
        payload = self.normalize_email(email).encode("utf-8")
        digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
        return selected_version, digest

    def verification_status_for_version(self, version: str) -> str:
        if not version:
            return "legacy_unverifiable"
        if self.is_revoked(version):
            return "legacy_unverifiable"
        if not self._get_key(version):
            return "legacy_unverifiable"
        return "verifiable"

