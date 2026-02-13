"""
request_history_store.py - request_historyの保存
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .hmac_key_manager import HmacKeyManager


class RequestHistoryStore:
    def __init__(
        self,
        *,
        base_dir: Path,
        key_manager: HmacKeyManager,
        retention_days: int = 365,
    ):
        self.base_dir = Path(base_dir)
        self.history_root = self.base_dir / "logs" / "request_history"
        self.history_root.mkdir(parents=True, exist_ok=True)
        self.key_manager = key_manager
        self.retention_days = max(1, int(retention_days))

    def _request_dir(self, request_id: str) -> Path:
        path = self.history_root / request_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _normalize_emails(values: Iterable[str]) -> List[str]:
        normalized: List[str] = []
        for value in values:
            v = str(value or "").strip().lower()
            if v:
                normalized.append(v)
        return sorted(set(normalized))

    def build_history_payload(
        self,
        *,
        request_id: str,
        run_id: str,
        workflow_mode: str,
        send_mode: str,
        state: str,
        final_recipients: Iterable[str],
        blocked_reasons: Optional[List[str]] = None,
        rerun_of_run_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        now: Optional[dt.datetime] = None,
    ) -> Dict[str, Any]:
        timestamp = (now or dt.datetime.now(dt.timezone.utc)).astimezone(dt.timezone.utc)
        recipients = self._normalize_emails(final_recipients)
        key_version, _ = self.key_manager.ensure_active_key(now=timestamp)
        recipient_hashes = []
        for email in recipients:
            _, digest = self.key_manager.hash_email(email, key_version)
            recipient_hashes.append({"email_hmac": digest})

        payload: Dict[str, Any] = {
            "request_id": request_id,
            "run_id": run_id,
            "workflow_mode": workflow_mode,
            "send_mode": send_mode,
            "state": state,
            "final_recipients": recipients,
            "recipient_hashes": recipient_hashes,
            "blocked_reasons": list(blocked_reasons or []),
            "rerun_of_run_id": rerun_of_run_id or "",
            "hmac_key_version": key_version,
            "verification_status": self.key_manager.verification_status_for_version(key_version),
            "recorded_at_utc": timestamp.isoformat(),
        }
        if metadata:
            payload["metadata"] = dict(metadata)
        return payload

    def save_history(
        self,
        *,
        request_id: str,
        run_id: str,
        payload: Dict[str, Any],
    ) -> Path:
        request_dir = self._request_dir(request_id)
        history_path = request_dir / f"{run_id}.json"
        if history_path.exists():
            raise FileExistsError(f"履歴ファイルは上書きできません: {history_path}")
        history_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return history_path

    def annotate_existing_record_status(self, record: Dict[str, Any]) -> Dict[str, Any]:
        cloned = dict(record)
        version = str(cloned.get("hmac_key_version", ""))
        cloned["verification_status"] = self.key_manager.verification_status_for_version(version)
        return cloned

