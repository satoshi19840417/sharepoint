"""
workflow_service.py - 相見積改良フロー実行サービス
"""

from __future__ import annotations

import copy
import datetime as dt
import json
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .csv_handler import ContactRecord
from .draft_repository import DraftRepository
from .hmac_key_manager import HmacKeyManager
from .manual_evidence_validator import ManualEvidenceValidator
from .request_history_store import RequestHistoryStore
from .workflow_types import HearingInput, SendMode, WorkflowMode, WorkflowResult

VALID_WORKFLOW_MODES = {"enhanced", "legacy"}
VALID_SEND_MODES = {"auto", "manual", "draft_only"}


class WorkflowService:
    def __init__(self, skill: Any):
        self.skill = skill
        self.base_dir = Path(self.skill.base_dir)
        self.config = self.skill.config
        self.draft_repo = DraftRepository(self.base_dir)
        credential_service = str(
            self.config.get("hmac_credential_service")
            or self.config.get("credential_target_name")
            or "見積依頼スキル"
        )
        registry_path = (
            self.base_dir / "logs" / "request_history" / "hmac_key_registry.json"
        )
        self.hmac_key_manager = HmacKeyManager(
            credential_service=credential_service,
            registry_path=registry_path,
            rotation_days=int(self.config.get("hmac_rotation_days", 180)),
        )
        self.history_store = RequestHistoryStore(
            base_dir=self.base_dir,
            key_manager=self.hmac_key_manager,
            retention_days=int(self.config.get("request_history_retention_days", 365)),
        )
        self.manual_validator = ManualEvidenceValidator()

    @staticmethod
    def _new_uuid_v7() -> str:
        if hasattr(uuid, "uuid7"):
            return str(uuid.uuid7())
        return str(uuid.uuid4())

    def resolve_workflow_mode(self, cli_mode: Optional[str]) -> WorkflowMode:
        if cli_mode:
            mode = str(cli_mode).strip().lower()
            if mode not in VALID_WORKFLOW_MODES:
                raise ValueError(f"workflow_mode 不正: {cli_mode}")
            return mode  # type: ignore[return-value]
        cfg = str(self.config.get("workflow_mode_default", "legacy")).strip().lower()
        if cfg not in VALID_WORKFLOW_MODES:
            cfg = "legacy"
        return cfg  # type: ignore[return-value]

    def resolve_send_mode(
        self,
        cli_mode: Optional[str],
        hearing: HearingInput,
    ) -> SendMode:
        candidate = cli_mode or hearing.send_mode or self.config.get("send_mode_default", "auto")
        mode = str(candidate).strip().lower()
        if mode not in VALID_SEND_MODES:
            raise ValueError(f"send_mode 不正: {candidate}")
        return mode  # type: ignore[return-value]

    def _normalize_email(self, email: str) -> str:
        return self.skill._normalize_email(email)

    def _build_recipient_records(
        self,
        base_records: Iterable[ContactRecord],
        final_recipients: Iterable[str],
    ) -> List[ContactRecord]:
        base_map: Dict[str, ContactRecord] = {}
        for rec in base_records:
            base_map[self._normalize_email(rec.email)] = rec

        result: List[ContactRecord] = []
        for raw_email in final_recipients:
            email_norm = self._normalize_email(raw_email)
            if not email_norm:
                continue
            source = base_map.get(email_norm)
            if source:
                result.append(copy.deepcopy(source))
                continue
            company = email_norm.split("@", 1)[0] if "@" in email_norm else "Unknown"
            result.append(
                ContactRecord(
                    company_name=company,
                    email=email_norm,
                    contact_name="ご担当者様",
                )
            )
        return result

    def _re_evaluate_safety(
        self,
        *,
        records: Iterable[ContactRecord],
        subject: str,
        product_url: str,
        maker_code: str,
        quantity: str,
        run_id: str,
    ) -> List[str]:
        blocked_reasons: List[str] = []
        records_list = list(records)
        if not records_list:
            blocked_reasons.append("送信先が0件です。")
            return blocked_reasons

        domain_result = self.skill.filter_by_domain(records_list)
        for rejected in domain_result.get("rejected", []):
            rec = rejected.get("record")
            reason = rejected.get("reason", "")
            email = getattr(rec, "email", "")
            blocked_reasons.append(f"ドメイン制限NG: {email} ({reason})")

        maker_code_norm = self.skill._normalize_maker_code(maker_code or "unknown")
        canonical_url = self.skill._normalize_input_url(product_url or "")
        quantity_norm = self.skill._normalize_quantity(quantity or "")
        subject_norm = self.skill._normalize_subject(subject)
        dedupe_key_version = str(self.config.get("dedupe_key_version", "v2"))
        rerun_window_hours = int(self.config.get("rerun_window_hours", 24))
        run_scope = run_id if str(self.config.get("rerun_scope", "global")) == "same_run" else None

        for record in records_list:
            recipient_norm = self._normalize_email(record.email)
            request_key = self.skill._build_request_key(
                recipient_norm,
                maker_code_norm,
                canonical_url,
                quantity_norm,
                dedupe_key_version,
            )
            v1_key = self.skill._build_legacy_v1_key(record.email, subject_norm, "workflow_safety")
            blocked, reason = self.skill.send_ledger.is_send_blocked_precheck(
                request_key=request_key,
                v1_key=v1_key,
                rerun_window_hours=rerun_window_hours,
                run_id=run_scope,
            )
            if blocked:
                blocked_reasons.append(f"重複送信防止NG: {record.email} ({reason})")

        return blocked_reasons

    @staticmethod
    def _build_markdown_content(
        *,
        request_id: str,
        run_id: str,
        workflow_mode: WorkflowMode,
        send_mode: SendMode,
        subject: str,
        body_preview: str,
        recipients: Iterable[str],
        product_name: str,
        product_features: str,
        product_url: str,
        other_requests: str,
        user_approved: bool,
    ) -> str:
        lines = [
            f"# 見積依頼メール案 ({run_id})",
            "",
            f"- request_id: `{request_id}`",
            f"- run_id: `{run_id}`",
            f"- workflow_mode: `{workflow_mode}`",
            f"- send_mode: `{send_mode}`",
            f"- user_approved: `{str(user_approved).lower()}`",
            "",
            "## 製品情報",
            f"- 製品名: {product_name}",
            f"- 特徴: {product_features}",
            f"- 製品URL: {product_url}",
            "",
            "## 送信対象",
        ]
        for email in recipients:
            lines.append(f"- {email}")
        lines.extend(
            [
                "",
                "## その他要望",
                other_requests or "(なし)",
                "",
                "## 件名",
                subject,
                "",
                "## 本文（プレビュー）",
                body_preview,
                "",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _record_emails(records: Iterable[ContactRecord]) -> List[str]:
        return [str(r.email) for r in records]

    def execute(
        self,
        *,
        workflow_mode: Optional[str],
        send_mode: Optional[str],
        hearing_input: Optional[Dict[str, Any]],
        records: List[ContactRecord],
        subject: str,
        template_content: str,
        product_name: str,
        product_features: str,
        product_url: str,
        maker_name: str = "",
        maker_code: str = "",
        quantity: str = "",
        input_file: str = "",
        request_id: str = "",
        rerun_of_run_id: str = "",
        user_approved: Optional[bool] = None,
    ) -> Dict[str, Any]:
        run_started_at = dt.datetime.now(dt.timezone.utc)
        resolved_workflow_mode = self.resolve_workflow_mode(workflow_mode)
        hearing = HearingInput.from_dict(hearing_input)
        resolved_send_mode = self.resolve_send_mode(send_mode, hearing)
        resolved_request_id = request_id or self._new_uuid_v7()
        run_id = self._new_uuid_v7()
        final_user_approved = hearing.user_approved if user_approved is None else bool(user_approved)

        blocked_reasons: List[str] = []

        if resolved_workflow_mode == "enhanced" and hearing_input is None:
            blocked_reasons.append("workflow_mode=enhanced では hearing_input が必須です。")

        recipient_emails: List[str]
        recipients_changed = hearing.recipients_changed
        if recipients_changed:
            if not hearing.final_recipients:
                blocked_reasons.append("recipients_changed=true では final_recipients が必須です。")
                recipient_emails = []
            else:
                recipient_emails = list(hearing.final_recipients)
        else:
            recipient_emails = [r.email for r in records]

        final_records = self._build_recipient_records(records, recipient_emails)

        if recipients_changed:
            blocked_reasons.extend(
                self._re_evaluate_safety(
                    records=final_records,
                    subject=subject,
                    product_url=product_url,
                    maker_code=maker_code,
                    quantity=quantity,
                    run_id=run_id,
                )
            )

        blocked_reasons.extend(
            self._re_evaluate_safety(
                records=final_records,
                subject=subject,
                product_url=product_url,
                maker_code=maker_code,
                quantity=quantity,
                run_id=run_id,
            )
        )

        preview_body = ""
        if final_records:
            preview_body = self.skill.render_email(
                template_content=template_content,
                record=final_records[0],
                product_name=product_name,
                product_features=product_features,
                product_url=product_url,
                maker_name=maker_name,
                maker_code=maker_code,
                quantity=quantity,
            )

        draft_content = self._build_markdown_content(
            request_id=resolved_request_id,
            run_id=run_id,
            workflow_mode=resolved_workflow_mode,
            send_mode=resolved_send_mode,
            subject=subject,
            body_preview=preview_body,
            recipients=[r.email for r in final_records],
            product_name=product_name,
            product_features=product_features,
            product_url=product_url,
            other_requests=hearing.other_requests,
            user_approved=final_user_approved,
        )
        draft_path = self.draft_repo.save_draft(
            content=draft_content,
            run_started_at=run_started_at,
            product_name=product_name,
            request_id=resolved_request_id,
            run_id=run_id,
        )

        state: str = "blocked" if blocked_reasons else "pending"
        completed_path = ""
        error_path = ""
        audit_log_path = ""

        workflow_context = {
            "request_id": resolved_request_id,
            "run_id": run_id,
            "workflow_mode": resolved_workflow_mode,
            "send_mode": resolved_send_mode,
        }
        product_info = {
            "product_name": product_name,
            "maker_name": maker_name,
            "maker_code": maker_code,
            "quantity": quantity,
            "product_url": product_url,
        }

        if blocked_reasons:
            audit_log_path = self.skill.audit_logger.write_audit_log(
                input_file=input_file,
                results=[],
                product_info=product_info,
                workflow_context=workflow_context,
            )
            error_path = str(self.draft_repo.move_to_error(draft_path))
            state = "blocked"
        else:
            if resolved_send_mode == "auto":
                if not final_user_approved:
                    blocked_reasons.append("auto モードは最終承認が必要です。")
                    audit_log_path = self.skill.audit_logger.write_audit_log(
                        input_file=input_file,
                        results=[],
                        product_info=product_info,
                        workflow_context=workflow_context,
                    )
                    state = "pending"
                else:
                    send_result = self.skill.send_bulk(
                        records=final_records,
                        subject=subject,
                        template_content=template_content,
                        product_name=product_name,
                        product_features=product_features,
                        product_url=product_url,
                        maker_name=maker_name,
                        maker_code=maker_code,
                        quantity=quantity,
                        input_file=input_file,
                        workflow_context=workflow_context,
                    )
                    audit_log_path = str(send_result.get("audit_log_path", ""))
                    if bool(send_result.get("success")) and audit_log_path:
                        state = "completed"
                    else:
                        state = "failed"
                        blocked_reasons.append(
                            "auto モード完了条件未達（全送信成功 + 監査ログ永続化成功）。"
                        )
            elif resolved_send_mode == "manual":
                evidence_path = (
                    self.base_dir
                    / "outputs"
                    / "manual_evidence"
                    / resolved_request_id
                    / f"manual_send_evidence_{run_id}.json"
                )
                validation = self.manual_validator.validate(
                    evidence_path,
                    expected_request_id=resolved_request_id,
                    expected_run_id=run_id,
                    expected_recipients=self._record_emails(final_records),
                )
                audit_log_path = self.skill.audit_logger.write_audit_log(
                    input_file=input_file,
                    results=[],
                    product_info=product_info,
                    workflow_context=workflow_context,
                )
                if validation.valid:
                    state = "completed"
                else:
                    state = "blocked"
                    blocked_reasons.extend(validation.errors)
            else:
                audit_log_path = self.skill.audit_logger.write_audit_log(
                    input_file=input_file,
                    results=[],
                    product_info=product_info,
                    workflow_context=workflow_context,
                )
                if final_user_approved:
                    state = "completed"
                else:
                    state = "pending"
                    blocked_reasons.append("draft_only モードは user_approved=true が必要です。")

            if state == "completed":
                completed_path = str(self.draft_repo.move_to_completed(draft_path))
            elif state in {"blocked", "failed"}:
                error_path = str(self.draft_repo.move_to_error(draft_path))

        history_payload = self.history_store.build_history_payload(
            request_id=resolved_request_id,
            run_id=run_id,
            workflow_mode=resolved_workflow_mode,
            send_mode=resolved_send_mode,
            state=state,
            final_recipients=self._record_emails(final_records),
            blocked_reasons=blocked_reasons,
            rerun_of_run_id=rerun_of_run_id,
            metadata={
                "draft_path": str(draft_path),
                "completed_path": completed_path,
                "error_path": error_path,
                "audit_log_path": audit_log_path,
            },
            now=run_started_at,
        )
        history_path = self.history_store.save_history(
            request_id=resolved_request_id,
            run_id=run_id,
            payload=history_payload,
        )

        result = WorkflowResult(
            request_id=resolved_request_id,
            run_id=run_id,
            workflow_mode=resolved_workflow_mode,
            send_mode=resolved_send_mode,
            state=state,  # type: ignore[arg-type]
            draft_path=str(draft_path),
            completed_path=completed_path,
            error_path=error_path,
            history_path=str(history_path),
            blocked_reasons=blocked_reasons,
            audit_log_path=audit_log_path,
        )
        payload = result.to_dict()
        payload["history"] = history_payload
        return payload

    @staticmethod
    def load_hearing_input(hearing_input_path: Optional[str]) -> Optional[Dict[str, Any]]:
        if not hearing_input_path:
            return None
        path = Path(hearing_input_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError("hearing_input JSON はオブジェクトである必要があります。")
        return data

