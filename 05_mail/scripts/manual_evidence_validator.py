"""
manual_evidence_validator.py - 手動送信証跡ファイル検証
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


@dataclass
class ManualEvidenceValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)
    normalized_recipients: Set[str] = field(default_factory=set)


class ManualEvidenceValidator:
    @staticmethod
    def normalize_email(value: str) -> str:
        return str(value or "").strip().lower()

    @staticmethod
    def _require_fields(payload: Dict[str, Any], required: Iterable[str], errors: List[str]) -> None:
        for field_name in required:
            if field_name not in payload:
                errors.append(f"必須項目不足: {field_name}")

    def validate(
        self,
        evidence_path: Path,
        *,
        expected_request_id: str,
        expected_run_id: str,
        expected_recipients: Iterable[str],
    ) -> ManualEvidenceValidationResult:
        errors: List[str] = []
        path = Path(evidence_path)
        if not path.exists():
            return ManualEvidenceValidationResult(False, [f"証跡ファイルが存在しません: {path}"])

        expected_filename = f"manual_send_evidence_{expected_run_id}.json"
        if path.name != expected_filename:
            errors.append(
                f"証跡ファイル名不正: expected={expected_filename}, actual={path.name}"
            )

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return ManualEvidenceValidationResult(False, [f"証跡JSON読込エラー: {exc}"])

        self._require_fields(
            payload,
            ("request_id", "run_id", "operator", "confirmed_at", "recipients"),
            errors,
        )

        if str(payload.get("request_id", "")) != expected_request_id:
            errors.append("request_id が一致しません。")
        if str(payload.get("run_id", "")) != expected_run_id:
            errors.append("run_id が一致しません。")

        recipients_raw = payload.get("recipients")
        if not isinstance(recipients_raw, list) or not recipients_raw:
            errors.append("recipients[] は必須です。")
            return ManualEvidenceValidationResult(False, errors)

        normalized_expected = {self.normalize_email(v) for v in expected_recipients}
        normalized_actual: Set[str] = set()
        message_ids: Set[str] = set()

        for idx, recipient in enumerate(recipients_raw):
            if not isinstance(recipient, dict):
                errors.append(f"recipients[{idx}] がオブジェクトではありません。")
                continue
            for key in ("email", "message_id", "sent_at"):
                if not recipient.get(key):
                    errors.append(f"recipients[{idx}].{key} は必須です。")

            email_norm = self.normalize_email(recipient.get("email", ""))
            if email_norm:
                normalized_actual.add(email_norm)

            message_id = str(recipient.get("message_id", "")).strip()
            if message_id:
                if message_id in message_ids:
                    errors.append(f"message_id 重複: {message_id}")
                message_ids.add(message_id)

        if normalized_actual != normalized_expected:
            errors.append(
                "証跡宛先集合が最終送信先集合と一致しません。"
            )

        return ManualEvidenceValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            normalized_recipients=normalized_actual,
        )

