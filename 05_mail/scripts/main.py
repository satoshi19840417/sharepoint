"""
main.py - 見積依頼スキル メインエントリポイント

要件定義書 v11 §5 に基づくワークフローを実装。
1. 設定ファイル読み込み
2. CSV読み込み・バリデーション
3. ドメインフィルタリング
4. テスト送信 → 本番送信
5. 監査ログ出力
"""

import datetime as dt
import json
import re
import sys
import hashlib
import urllib.parse
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from dataclasses import asdict

from .csv_handler import CSVHandler, ContactRecord
from .domain_filter import DomainFilter
from .pii_detector import PIIDetector
from .template_processor import TemplateProcessor, get_default_template
from .url_validator import URLValidator
from .mail_sender import OutlookMailSender
from .audit_logger import AuditLogger
from .encryption import EncryptionManager
from .send_ledger import (
    SendLedger,
    STATUS_SKIPPED_DUPLICATE_IN_RUN,
    STATUS_SKIPPED_CONFIRM_REQUIRED,
    STATUS_SKIPPED_AUTO,
)

EXIT_CODE_OK = 0
EXIT_CODE_CONFIRM_REQUIRED = 3
EXIT_CODE_INVALID_INPUT = 4

TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_KEYS = {
    "gclid",
    "fbclid",
    "msclkid",
    "mc_cid",
    "mc_eid",
    "_ga",
    "_gl",
    "yclid",
}


class QuoteRequestSkill:
    """見積依頼スキル メインクラス"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: 設定ファイルパス。Noneの場合はデフォルトパスを使用。
        """
        self.base_dir = Path(__file__).parent.parent
        self.config_path = config_path or str(self.base_dir / "config.json")
        self.config = self._load_config()

        # モジュール初期化
        self.encryption_manager = EncryptionManager(
            self.config.get("credential_target_name")
        )
        self.csv_handler = CSVHandler(self.encryption_manager)
        self.domain_filter = DomainFilter(
            self.config.get("domain_whitelist", []),
            self.config.get("domain_blacklist", [])
        )
        self.pii_detector = PIIDetector()
        self.template_processor = TemplateProcessor()
        self.url_validator = URLValidator(
            timeout=self.config.get("url_timeout_sec", 10),
            retry_count=self.config.get("url_retry_count", 2),
            retry_interval=self.config.get("url_retry_interval_sec", 3.0)
        )
        self.mail_sender = OutlookMailSender(
            send_interval_sec=self.config.get("send_interval_sec", 3.0),
            dry_run=self.config.get("dry_run", False)
        )
        self.audit_logger = AuditLogger(
            str(self.base_dir / "logs"),
            self.encryption_manager
        )
        ledger_path_cfg = str(
            self.config.get("ledger_sqlite_path", "./logs/send_ledger.sqlite3")
        )
        ledger_path = (
            self.base_dir / ledger_path_cfg
            if not Path(ledger_path_cfg).is_absolute()
            else Path(ledger_path_cfg)
        )
        self.send_ledger = SendLedger(
            str(ledger_path),
            retention_days=self.config.get("log_retention_days", 90),
            busy_timeout_ms=self.config.get("dedupe_busy_timeout_ms", 15000),
            backoff_attempts=self.config.get("dedupe_retry_attempts", 5),
            credential_target_name=self.config.get("credential_target_name"),
        )

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルを読み込む"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"警告: 設定ファイルが見つかりません: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"警告: 設定ファイルの形式エラー: {e}")
            return {}

    def load_contacts(self, csv_path: str) -> Dict[str, Any]:
        """
        連絡先CSVを読み込む。

        Returns:
            {"success": bool, "records": List[ContactRecord], "warnings": [], "errors": []}
        """
        result = self.csv_handler.load_csv(csv_path)

        return {
            "success": len(result.errors) == 0,
            "records": result.records,
            "warnings": result.warnings,
            "errors": result.errors,
            "duplicate_emails": result.duplicate_emails,
            "skipped_rows": result.skipped_rows,
        }

    def filter_by_domain(self, records: List[ContactRecord]) -> Dict[str, Any]:
        """
        ドメインフィルタリングを適用する。

        Returns:
            {"allowed": List[ContactRecord], "rejected": List[...]}
        """
        allowed = []
        rejected = []

        for record in records:
            result = self.domain_filter.check(record.email)
            if result.allowed:
                allowed.append(record)
            else:
                rejected.append({
                    "record": record,
                    "reason": result.reason,
                })

        return {"allowed": allowed, "rejected": rejected}

    def check_pii(self, query: str, company_names: List[str] = None) -> Dict[str, Any]:
        """
        製品検索クエリのPIIチェック。

        Returns:
            {"blocked": bool, "warning": bool, "message": str}
        """
        if company_names:
            self.pii_detector.set_company_names(set(company_names))

        result = self.pii_detector.detect(query)

        return {
            "blocked": result.has_blocking_pii,
            "warning": result.has_warning_pii,
            "message": result.message,
            "emails_found": result.emails_found,
            "phones_found": result.phones_found,
            "companies_found": result.companies_found,
        }

    @staticmethod
    def _normalize_text(value: str) -> str:
        normalized = unicodedata.normalize("NFKC", str(value or ""))
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.strip()

    @staticmethod
    def _normalize_email(value: str) -> str:
        raw = QuoteRequestSkill._normalize_text(value).lower()
        match = re.search(
            r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
            raw,
        )
        return match.group(1) if match else raw

    @staticmethod
    def _normalize_maker_code(value: str) -> str:
        return QuoteRequestSkill._normalize_text(value).lower()

    @staticmethod
    def _normalize_subject(value: str) -> str:
        normalized = QuoteRequestSkill._normalize_text(value)
        return re.sub(r"\s+", " ", normalized)

    @staticmethod
    def _normalize_quantity(value: str) -> str:
        normalized = QuoteRequestSkill._normalize_text(value)
        if not normalized:
            return ""
        compact = normalized.replace(",", "")
        try:
            parsed = Decimal(compact)
            canonical = parsed.normalize()
            if canonical == canonical.to_integral():
                return str(canonical.quantize(Decimal("1")))
            return format(canonical, "f").rstrip("0").rstrip(".")
        except (InvalidOperation, ValueError):
            return normalized.lower()

    @staticmethod
    def _is_tracking_query_key(key: str) -> bool:
        key_lower = str(key or "").strip().lower()
        if key_lower in TRACKING_QUERY_KEYS:
            return True
        return any(key_lower.startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES)

    @staticmethod
    def _normalize_input_url(url: str) -> str:
        raw = QuoteRequestSkill._normalize_text(url)
        if not raw:
            return ""
        parsed = urllib.parse.urlsplit(raw)
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower().strip()
        if ":" in netloc:
            host, port = netloc.rsplit(":", 1)
            if (scheme == "https" and port == "443") or (scheme == "http" and port == "80"):
                netloc = host
        path = parsed.path or "/"
        try:
            path = urllib.parse.quote(urllib.parse.unquote(path), safe="/:@-._~!$&'()*+,;=")
        except Exception:
            pass
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        filtered = [
            (k, v) for (k, v) in query_pairs
            if not QuoteRequestSkill._is_tracking_query_key(k)
        ]
        filtered.sort(key=lambda pair: (pair[0], pair[1]))
        normalized_query = urllib.parse.urlencode(filtered, doseq=True)
        return urllib.parse.urlunsplit((scheme, netloc, path, normalized_query, ""))

    @staticmethod
    def _build_request_key(
        recipient_email_norm: str,
        maker_code_norm: str,
        canonical_input_url_norm: str,
        quantity_norm: str,
        key_version: str,
    ) -> str:
        payload = "\n".join([
            recipient_email_norm,
            maker_code_norm,
            canonical_input_url_norm,
            quantity_norm,
        ])
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"rq:{key_version}:{digest}"

    @staticmethod
    def _build_mail_key(
        recipient_email_norm: str,
        subject_norm: str,
        body_fingerprint_norm: str,
    ) -> str:
        payload = "\n".join([recipient_email_norm, subject_norm, body_fingerprint_norm])
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"mk:v2:{digest}"

    @staticmethod
    def _build_legacy_v1_key(email: str, subject: str, template_content: str) -> str:
        normalized_email = str(email or "").strip().lower()
        payload = f"{subject}\n{template_content}"
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"{normalized_email}:{payload_hash}"

    @staticmethod
    def _build_body_fingerprint(value: str) -> str:
        normalized = QuoteRequestSkill._normalize_text(value)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def validate_url(self, url: str) -> Dict[str, Any]:
        """
        URLの有効性をチェックする。

        Returns:
            {"valid": bool, "error": str, "warning": str}
        """
        result = self.url_validator.validate(url)
        canonical_input_url = self._normalize_input_url(url)
        final_url = str(result.final_url or "")
        final_host = ""
        if final_url:
            try:
                final_host = urllib.parse.urlsplit(final_url).netloc.lower()
            except Exception:
                final_host = ""
        fingerprint = hashlib.sha256(final_url.encode("utf-8")).hexdigest() if final_url else ""
        resolve_status = "valid" if result.valid else "invalid"
        try:
            self.send_ledger.record_url_alias(
                canonical_input_url=canonical_input_url,
                last_final_url=final_url,
                final_host=final_host,
                redirect_hops=0,
                final_url_fingerprint=fingerprint,
                resolve_status=resolve_status,
            )
        except Exception:
            pass

        return {
            "valid": result.valid,
            "error": result.error,
            "warning": result.warning,
            "final_url": result.final_url,
            "status_code": result.status_code,
        }

    def load_template(self, template_path: Optional[str] = None) -> Dict[str, Any]:
        """
        テンプレートを読み込む。

        Returns:
            {"success": bool, "content": str, "error": str}
        """
        if template_path:
            result = self.template_processor.load_template(template_path)
            return {
                "success": result.success,
                "content": result.content,
                "error": result.error,
            }
        else:
            return {
                "success": True,
                "content": get_default_template(),
                "error": "",
            }

    def render_email(
        self,
        template_content: str,
        record: ContactRecord,
        product_name: str,
        product_features: str,
        product_url: str,
        maker_name: str = "",
        maker_code: str = "",
        quantity: str = "",
    ) -> str:
        """
        メール本文をレンダリングする。
        """
        result = self.template_processor.create_email_body(
            template_content=template_content,
            company_name=record.company_name,
            contact_name=record.contact_name,
            product_name=product_name,
            product_features=product_features,
            product_url=product_url,
            maker_name=maker_name,
            maker_code=maker_code,
            quantity=quantity,
        )
        return result.content

    def check_outlook_connection(self) -> Dict[str, Any]:
        """
        Outlook接続を確認する。

        Returns:
            {"connected": bool, "message": str}
        """
        connected, message = self.mail_sender.check_outlook_connection()
        return {"connected": connected, "message": message}

    def send_test(
        self,
        test_email: str,
        subject: str,
        body: str
    ) -> Dict[str, Any]:
        """
        テスト送信を実行する。

        Returns:
            {"success": bool, "error": str}
        """
        result = self.mail_sender.send_test_mail(test_email, subject, body)

        return {
            "success": result.success,
            "error": result.error,
            "message_id": result.message_id,
            "message_id_source": result.message_id_source,
        }

    @staticmethod
    def _build_dedupe_key(email: str, subject: str, body: str) -> str:
        """互換API: v1 dedupe keyを生成する。"""
        return QuoteRequestSkill._build_legacy_v1_key(email, subject, body)

    def send_bulk(
        self,
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
        confirm_rerun_callback: Optional[Callable[[ContactRecord, Dict[str, Any]], bool]] = None,
        confirm_bulk_send_callback: Optional[Callable[[int], bool]] = None,
    ) -> Dict[str, Any]:
        max_recipients = self.config.get("max_recipients", 50)
        if len(records) > max_recipients:
            return {
                "success": False,
                "error": f"送信件数が上限を超えています: {len(records)} > {max_recipients}",
                "exit_code": EXIT_CODE_INVALID_INPUT,
            }

        maker_code_norm = self._normalize_maker_code(maker_code)
        canonical_input_url = self._normalize_input_url(product_url)
        if not maker_code_norm:
            return {"success": False, "error": "maker_code は必須です。", "exit_code": EXIT_CODE_INVALID_INPUT}
        if not canonical_input_url:
            return {"success": False, "error": "product_url は必須です。", "exit_code": EXIT_CODE_INVALID_INPUT}

        dedupe_key_version = str(self.config.get("dedupe_key_version", "v2"))
        rerun_policy_default = str(self.config.get("rerun_policy_default", "auto_skip"))
        rerun_scope = str(self.config.get("rerun_scope", "global"))
        rerun_window_hours = int(self.config.get("rerun_window_hours", 24))
        in_progress_ttl_sec = int(self.config.get("dedupe_in_progress_ttl_sec", 2700))
        dedupe_heartbeat_sec = int(self.config.get("dedupe_heartbeat_sec", 30))
        unknown_sent_hold_sec = int(self.config.get("unknown_sent_hold_sec", 1800))
        idempotency_secret_version = str(self.config.get("idempotency_secret_version", "v1"))

        self.send_ledger.cleanup_on_batch_start(rerun_window_hours, unknown_sent_hold_sec)
        self.send_ledger.record_url_alias(
            canonical_input_url=canonical_input_url,
            last_final_url="",
            final_host=urllib.parse.urlsplit(canonical_input_url).netloc.lower(),
            redirect_hops=0,
            final_url_fingerprint="",
            resolve_status="input_only",
        )

        confirmation_threshold = self.config.get("confirmation_threshold", 5)
        if len(records) >= confirmation_threshold and confirm_bulk_send_callback is not None:
            try:
                if not bool(confirm_bulk_send_callback(len(records))):
                    return {
                        "success": False,
                        "error": f"{len(records)}件の送信は確認によりキャンセルされました。",
                        "results": [],
                        "warnings": [],
                        "warning": "",
                        "exit_code": EXIT_CODE_CONFIRM_REQUIRED,
                    }
            except Exception as callback_error:
                return {
                    "success": False,
                    "error": f"送信前確認コールバックエラー: {callback_error}",
                    "results": [],
                    "warnings": [],
                    "warning": "",
                    "exit_code": EXIT_CODE_CONFIRM_REQUIRED,
                }

        run_id = getattr(self.audit_logger, "execution_id", "")
        run_scope = run_id if rerun_scope == "same_run" else None
        quantity_norm = self._normalize_quantity(quantity)
        subject_norm = self._normalize_subject(subject)
        non_interactive = confirm_rerun_callback is None

        results: List[Dict[str, Any]] = []
        warnings: List[str] = []
        seen_request_keys = set()
        skipped_duplicate_count = 0
        skipped_rerun_count = 0
        confirmation_required_count = 0

        def add_skip(
            *,
            record: ContactRecord,
            request_key: str,
            mail_key: str,
            v1_key: str,
            recipient_hash: str,
            idempotency_token: str,
            decision_trace: List[str],
            message: str,
            action: str,
            status: str,
            confirmation_required: bool,
            count_as_rerun: bool = True,
        ) -> None:
            nonlocal skipped_rerun_count, confirmation_required_count
            if count_as_rerun:
                skipped_rerun_count += 1
            if confirmation_required:
                confirmation_required_count += 1
            warnings.append(message)
            self.send_ledger.mark_skipped(
                request_key=request_key,
                v1_key=v1_key,
                key_version=dedupe_key_version,
                run_id=run_id,
                mail_key=mail_key,
                recipient_hash=recipient_hash,
                idempotency_token=idempotency_token,
                idempotency_secret_version=idempotency_secret_version,
                subject_norm=subject_norm,
                status=status,
                decision_trace=decision_trace,
                error=message,
            )
            results.append({
                "email": record.email,
                "company_name": record.company_name,
                "success": False,
                "message_id": "",
                "error": message,
                "sent_at": "",
                "is_fallback_id": False,
                "message_id_source": "",
                "dedupe_key": request_key,
                "request_key": request_key,
                "mail_key": mail_key,
                "dedupe_key_version": dedupe_key_version,
                "decision_trace": list(decision_trace),
                "skipped": True,
                "action": action,
                "skip_duplicate_in_run": action == "skip_duplicate_in_run",
                "confirmation_required": confirmation_required,
            })

        for record in records:
            body = self.render_email(
                template_content=template_content,
                record=record,
                product_name=product_name,
                product_features=product_features,
                product_url=product_url,
                maker_name=maker_name,
                maker_code=maker_code,
                quantity=quantity,
            )
            recipient_email_norm = self._normalize_email(record.email)
            request_key = self._build_request_key(
                recipient_email_norm,
                maker_code_norm,
                canonical_input_url,
                quantity_norm,
                dedupe_key_version,
            )
            mail_key = self._build_mail_key(
                recipient_email_norm,
                subject_norm,
                self._build_body_fingerprint(body),
            )
            v1_key = self._build_legacy_v1_key(record.email, subject, template_content)
            recipient_hash = self.send_ledger.hash_recipient(recipient_email_norm)
            idempotency_token = self.send_ledger.build_idempotency_token(
                request_key,
                idempotency_secret_version,
            )
            body_marker = f"[IDEMP:{idempotency_token[:24]}]"
            decision_trace = [f"request_key={request_key}", f"mail_key={mail_key}"]

            if request_key in seen_request_keys:
                skipped_duplicate_count += 1
                add_skip(
                    record=record,
                    request_key=request_key,
                    mail_key=mail_key,
                    v1_key=v1_key,
                    recipient_hash=recipient_hash,
                    idempotency_token=idempotency_token,
                    decision_trace=decision_trace + ["duplicate_in_run=true"],
                    message=f"同一実行内の重複送信をスキップしました: {record.email}",
                    action="skip_duplicate_in_run",
                    status=STATUS_SKIPPED_DUPLICATE_IN_RUN,
                    confirmation_required=False,
                    count_as_rerun=False,
                )
                continue
            seen_request_keys.add(request_key)

            override_decision = self.send_ledger.evaluate_override(request_key, recipient_hash)
            decision_trace.extend(override_decision.trace)

            unknown_lock = self.send_ledger.get_unknown_lock(request_key)
            if unknown_lock:
                matched = False
                method = ""
                message_id = ""
                try:
                    reconcile = self.mail_sender.reconcile_unknown_send(
                        token=idempotency_token,
                        body_marker=body_marker,
                        message_id=str(unknown_lock.get("last_message_id", "")),
                        subject=subject_norm,
                        recipient=record.email,
                    )
                    matched = bool(reconcile.get("matched"))
                    method = str(reconcile.get("method", ""))
                    message_id = str(reconcile.get("message_id", ""))
                except Exception:
                    matched = False
                if matched:
                    self.send_ledger.mark_reconciled_sent(
                        request_key=request_key,
                        run_id=run_id,
                        decision_trace=decision_trace + [f"unknown_reconciled={method}"],
                        reconciled_message_id=message_id,
                        reconciled_source=method or "reconcile",
                    )
                    add_skip(
                        record=record,
                        request_key=request_key,
                        mail_key=mail_key,
                        v1_key=v1_key,
                        recipient_hash=recipient_hash,
                        idempotency_token=idempotency_token,
                        decision_trace=decision_trace + [f"unknown_reconciled={method}"],
                        message="UNKNOWN_SENTを照合してSENTへ昇格したため送信をスキップしました。",
                        action="skip_reconciled_sent",
                        status=STATUS_SKIPPED_AUTO,
                        confirmation_required=False,
                    )
                    continue

                should_send_unknown = False
                if confirm_rerun_callback is not None:
                    try:
                        should_send_unknown = bool(confirm_rerun_callback(record, {"status": STATUS_UNKNOWN_SENT}))
                    except Exception:
                        should_send_unknown = False
                if not should_send_unknown:
                    add_skip(
                        record=record,
                        request_key=request_key,
                        mail_key=mail_key,
                        v1_key=v1_key,
                        recipient_hash=recipient_hash,
                        idempotency_token=idempotency_token,
                        decision_trace=decision_trace + ["unknown_sent_unresolved=true"],
                        message=f"UNKNOWN_SENT未回復のため送信をスキップしました: {record.email}",
                        action="skip_unknown_sent_confirm_required",
                        status=STATUS_SKIPPED_CONFIRM_REQUIRED,
                        confirmation_required=True,
                    )
                    continue
                self.send_ledger.clear_unknown_lock_for_manual_override(request_key)

            recent_entry = self.send_ledger.find_recent_sent(
                request_key=request_key,
                v1_key=v1_key,
                window_hours=rerun_window_hours,
                run_id=run_scope,
            )
            if recent_entry and not override_decision.allowed:
                should_send = False
                if rerun_policy_default == "confirm" and confirm_rerun_callback is not None:
                    try:
                        should_send = bool(confirm_rerun_callback(record, recent_entry))
                    except Exception:
                        should_send = False
                if rerun_policy_default == "auto_skip" or not should_send:
                    add_skip(
                        record=record,
                        request_key=request_key,
                        mail_key=mail_key,
                        v1_key=v1_key,
                        recipient_hash=recipient_hash,
                        idempotency_token=idempotency_token,
                        decision_trace=decision_trace + ["recent_sent_detected=true"],
                        message=f"24時間以内の再実行を検知したため送信をスキップしました: {record.email}",
                        action="skip_rerun_auto_skip" if rerun_policy_default == "auto_skip" else "skip_rerun_confirmation_required",
                        status=STATUS_SKIPPED_AUTO if rerun_policy_default == "auto_skip" else STATUS_SKIPPED_CONFIRM_REQUIRED,
                        confirmation_required=rerun_policy_default != "auto_skip",
                    )
                    continue

            reservation = self.send_ledger.reserve_send(
                request_key=request_key,
                v1_key=v1_key,
                key_version=dedupe_key_version,
                run_id=run_id,
                mail_key=mail_key,
                recipient_hash=recipient_hash,
                idempotency_token=idempotency_token,
                idempotency_secret_version=idempotency_secret_version,
                subject_norm=subject_norm,
                ttl_sec=in_progress_ttl_sec,
                decision_trace=decision_trace,
            )
            if not reservation.acquired:
                add_skip(
                    record=record,
                    request_key=request_key,
                    mail_key=mail_key,
                    v1_key=v1_key,
                    recipient_hash=recipient_hash,
                    idempotency_token=idempotency_token,
                    decision_trace=decision_trace + [f"reservation={reservation.reason}"],
                    message=f"送信ロックを確保できなかったため送信をスキップしました: {record.email}",
                    action="skip_lock_conflict",
                    status=STATUS_SKIPPED_CONFIRM_REQUIRED,
                    confirmation_required=True,
                )
                continue

            self.send_ledger.heartbeat(request_key, dedupe_heartbeat_sec)
            send_result = self.mail_sender.send_mail(
                to=record.email,
                subject=subject,
                body=body,
                company_name=record.company_name,
                idempotency_token=idempotency_token,
                body_reconcile_marker=body_marker,
            )
            if send_result.success:
                try:
                    self.send_ledger.mark_sent(
                        request_key=request_key,
                        v1_key=v1_key,
                        key_version=dedupe_key_version,
                        run_id=run_id,
                        mail_key=mail_key,
                        recipient_hash=recipient_hash,
                        message_id=send_result.message_id,
                        message_id_source=send_result.message_id_source,
                        idempotency_token=idempotency_token,
                        idempotency_secret_version=idempotency_secret_version,
                        subject_norm=subject_norm,
                        decision_trace=decision_trace,
                        sent_at=send_result.sent_at,
                    )
                    send_success = True
                    send_error = ""
                    action = "sent"
                    confirmation_required = False
                except Exception as ledger_error:
                    send_success = False
                    send_error = f"送信後のSENT確定に失敗したためUNKNOWN_SENTとして保留: {ledger_error}"
                    action = "unknown_sent_pending"
                    confirmation_required = True
                    confirmation_required_count += 1
                    warnings.append(send_error)
                    self.send_ledger.mark_unknown_sent(
                        request_key=request_key,
                        v1_key=v1_key,
                        key_version=dedupe_key_version,
                        run_id=run_id,
                        mail_key=mail_key,
                        recipient_hash=recipient_hash,
                        idempotency_token=idempotency_token,
                        idempotency_secret_version=idempotency_secret_version,
                        subject_norm=subject_norm,
                        decision_trace=decision_trace + ["sent_commit=unknown"],
                        error=send_error,
                        hold_sec=unknown_sent_hold_sec,
                        message_id=send_result.message_id,
                        message_id_source=send_result.message_id_source,
                    )
                results.append({
                    "email": record.email,
                    "company_name": record.company_name,
                    "success": send_success,
                    "message_id": send_result.message_id,
                    "error": send_error,
                    "sent_at": send_result.sent_at.isoformat() if send_result.sent_at else "",
                    "is_fallback_id": send_result.is_fallback_id,
                    "message_id_source": send_result.message_id_source,
                    "dedupe_key": request_key,
                    "request_key": request_key,
                    "mail_key": mail_key,
                    "dedupe_key_version": dedupe_key_version,
                    "decision_trace": decision_trace,
                    "skipped": False,
                    "action": action,
                    "skip_duplicate_in_run": False,
                    "confirmation_required": confirmation_required,
                })
                continue

            self.send_ledger.mark_failed_pre_send(
                request_key=request_key,
                v1_key=v1_key,
                key_version=dedupe_key_version,
                run_id=run_id,
                mail_key=mail_key,
                recipient_hash=recipient_hash,
                idempotency_token=idempotency_token,
                idempotency_secret_version=idempotency_secret_version,
                subject_norm=subject_norm,
                decision_trace=decision_trace,
                error=send_result.error,
            )
            results.append({
                "email": record.email,
                "company_name": record.company_name,
                "success": False,
                "message_id": send_result.message_id,
                "error": send_result.error,
                "sent_at": send_result.sent_at.isoformat() if send_result.sent_at else "",
                "is_fallback_id": send_result.is_fallback_id,
                "message_id_source": send_result.message_id_source,
                "dedupe_key": request_key,
                "request_key": request_key,
                "mail_key": mail_key,
                "dedupe_key_version": dedupe_key_version,
                "decision_trace": decision_trace,
                "skipped": False,
                "action": "failed_pre_send",
                "skip_duplicate_in_run": False,
                "confirmation_required": False,
            })

        product_info = None
        if product_name or maker_name or maker_code or quantity or product_url:
            product_info = {
                "product_name": product_name,
                "maker_name": maker_name,
                "maker_code": maker_code,
                "quantity": quantity,
                "product_url": product_url,
            }
        audit_log_path = self.audit_logger.write_audit_log(input_file, results, product_info=product_info)
        sent_list_path = self.audit_logger.write_sent_list(results)
        unsent_list_path = ""
        if any(not r["success"] for r in results):
            unsent_list_path = self.audit_logger.write_unsent_list(results)

        screen_output = self.audit_logger.format_screen_output(results)
        attempted_results = [r for r in results if not r.get("skipped")]
        success_count = sum(1 for r in attempted_results if r["success"])
        failure_count = sum(1 for r in attempted_results if not r["success"])
        warning_text = "; ".join(warnings)

        exit_code = EXIT_CODE_OK
        if confirmation_required_count > 0 and non_interactive:
            exit_code = EXIT_CODE_CONFIRM_REQUIRED
        return {
            "success": failure_count == 0 and confirmation_required_count == 0,
            "total": len(results),
            "attempted_count": len(attempted_results),
            "success_count": success_count,
            "failure_count": failure_count,
            "skipped_duplicate_count": skipped_duplicate_count,
            "skipped_rerun_count": skipped_rerun_count,
            "confirmation_required_count": confirmation_required_count,
            "audit_log_path": audit_log_path,
            "sent_list_path": sent_list_path,
            "unsent_list_path": unsent_list_path,
            "screen_output": screen_output,
            "warning": warning_text,
            "warnings": warnings,
            "results": results,
            "dedupe_key_version": dedupe_key_version,
            "exit_code": exit_code,
        }

    def ensure_encryption_key(self) -> bool:
        """
        暗号化鍵が存在しない場合は生成する。

        Returns:
            鍵が利用可能ならTrue
        """
        if self.encryption_manager.get_key() is None:
            try:
                self.encryption_manager.generate_key()
                print("暗号化鍵を生成しました。")
                return True
            except Exception as e:
                print(f"暗号化鍵の生成に失敗しました: {e}")
                return False
        return True


def main():
    """コマンドライン実行用エントリポイント"""
    print("見積依頼スキル")
    print("=" * 40)

    skill = QuoteRequestSkill()

    # 暗号化鍵確認
    if not skill.ensure_encryption_key():
        print("エラー: 暗号化鍵の準備に失敗しました。")
        sys.exit(1)

    # Outlook接続確認
    outlook_check = skill.check_outlook_connection()
    if not outlook_check["connected"]:
        print(f"エラー: {outlook_check['message']}")
        sys.exit(1)

    print("Outlook接続: OK")
    print()
    print("このスキルはAIチャット経由で実行してください。")
    print("詳細は SKILL.md を参照してください。")


if __name__ == "__main__":
    main()
