"""
main.py - 見積依頼スキル メインエントリポイント

要件定義書 v11 §5 に基づくワークフローを実装。
1. 設定ファイル読み込み
2. CSV読み込み・バリデーション
3. ドメインフィルタリング
4. テスト送信 → 本番送信
5. 監査ログ出力
"""

import json
import sys
import hashlib
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
from .send_ledger import SendLedger


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
        self.send_ledger = SendLedger(str(self.base_dir / "logs" / "send_ledger.jsonl"))

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

    def validate_url(self, url: str) -> Dict[str, Any]:
        """
        URLの有効性をチェックする。

        Returns:
            {"valid": bool, "error": str, "warning": str}
        """
        result = self.url_validator.validate(url)

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
        """同一送信判定キーを生成する。"""
        normalized_email = str(email or "").strip().lower()
        payload = f"{subject}\n{body}"
        payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"{normalized_email}:{payload_hash}"

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
    ) -> Dict[str, Any]:
        """
        一斉送信を実行する。

        Returns:
            送信結果サマリ
        """
        # 件数上限チェック
        max_recipients = self.config.get("max_recipients", 50)
        if len(records) > max_recipients:
            return {
                "success": False,
                "error": f"送信件数が上限を超えています: {len(records)} > {max_recipients}",
            }

        # 確認閾値チェック
        confirmation_threshold = self.config.get("confirmation_threshold", 5)
        if len(records) >= confirmation_threshold:
            print(f"警告: {len(records)}件のメールを送信します。")
            # 実際の運用ではここでユーザー確認を挟む

        results = []
        warnings: List[str] = []
        seen_dedupe_keys = set()
        skipped_duplicate_count = 0
        skipped_rerun_count = 0
        run_id = getattr(self.audit_logger, "execution_id", "")
        rerun_scope_run_id = run_id if self.config.get("test_mode", False) else None

        for record in records:
            # 本文生成
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
            dedupe_key = self._build_dedupe_key(record.email, subject, template_content)

            # 同一実行内重複チェック
            if dedupe_key in seen_dedupe_keys:
                skipped_duplicate_count += 1
                warning_message = (
                    f"同一実行内の重複送信をスキップしました: {record.email}"
                )
                warnings.append(warning_message)
                results.append({
                    "email": record.email,
                    "company_name": record.company_name,
                    "success": False,
                    "message_id": "",
                    "error": warning_message,
                    "sent_at": "",
                    "is_fallback_id": False,
                    "message_id_source": "",
                    "dedupe_key": dedupe_key,
                    "skipped": True,
                    "action": "skip_duplicate_in_run",
                    "skip_duplicate_in_run": True,
                    "confirmation_required": False,
                })
                continue
            seen_dedupe_keys.add(dedupe_key)

            # 24時間以内再実行チェック
            recent_entry = self.send_ledger.find_recent(
                dedupe_key,
                window_hours=24,
                run_id=rerun_scope_run_id,
            )
            if recent_entry:
                should_send = False
                if confirm_rerun_callback is not None:
                    try:
                        should_send = bool(confirm_rerun_callback(record, recent_entry))
                    except Exception as callback_error:
                        warnings.append(
                            f"再実行確認コールバックエラー: {callback_error}"
                        )
                        should_send = False

                if not should_send:
                    skipped_rerun_count += 1
                    warning_message = (
                        "24時間以内の再実行を検知しました。"
                        f"確認未実施のため送信をスキップ: {record.email}"
                    )
                    warnings.append(warning_message)
                    results.append({
                        "email": record.email,
                        "company_name": record.company_name,
                        "success": False,
                        "message_id": "",
                        "error": warning_message,
                        "error_details": {
                            "confirmation_required": True,
                            "previous_send": {
                                "timestamp": recent_entry.get("timestamp", ""),
                                "message_id": recent_entry.get("message_id", ""),
                                "run_id": recent_entry.get("run_id", ""),
                            },
                        },
                        "sent_at": "",
                        "is_fallback_id": False,
                        "message_id_source": "",
                        "dedupe_key": dedupe_key,
                        "skipped": True,
                        "action": "skip_rerun_confirmation_required",
                        "skip_duplicate_in_run": False,
                        "confirmation_required": True,
                    })
                    continue

            # 送信
            send_result = self.mail_sender.send_mail(
                to=record.email,
                subject=subject,
                body=body,
                company_name=record.company_name,
            )

            results.append({
                "email": record.email,
                "company_name": record.company_name,
                "success": send_result.success,
                "message_id": send_result.message_id,
                "error": send_result.error,
                "sent_at": send_result.sent_at.isoformat() if send_result.sent_at else "",
                "is_fallback_id": send_result.is_fallback_id,
                "message_id_source": send_result.message_id_source,
                "dedupe_key": dedupe_key,
                "skipped": False,
                "action": "sent",
                "skip_duplicate_in_run": False,
                "confirmation_required": False,
            })

            if send_result.success:
                self.send_ledger.append_entry(
                    dedupe_key=dedupe_key,
                    recipient=record.email,
                    message_id=send_result.message_id,
                    run_id=run_id,
                    sent_at=send_result.sent_at,
                )

        # 監査ログ出力
        product_info = None
        if product_name or maker_name or maker_code or quantity or product_url:
            product_info = {
                "product_name": product_name,
                "maker_name": maker_name,
                "maker_code": maker_code,
                "quantity": quantity,
                "product_url": product_url,
            }
        audit_log_path = self.audit_logger.write_audit_log(
            input_file,
            results,
            product_info=product_info,
        )

        # 送信済み/未送信リスト出力
        sent_list_path = self.audit_logger.write_sent_list(results)
        unsent_list_path = ""
        if any(not r["success"] for r in results):
            unsent_list_path = self.audit_logger.write_unsent_list(results)

        # 画面表示用出力
        screen_output = self.audit_logger.format_screen_output(results)

        attempted_results = [r for r in results if not r.get("skipped")]
        success_count = sum(1 for r in attempted_results if r["success"])
        failure_count = sum(1 for r in attempted_results if not r["success"])
        warning_text = "; ".join(warnings)

        return {
            "success": failure_count == 0,
            "total": len(results),
            "attempted_count": len(attempted_results),
            "success_count": success_count,
            "failure_count": failure_count,
            "skipped_duplicate_count": skipped_duplicate_count,
            "skipped_rerun_count": skipped_rerun_count,
            "audit_log_path": audit_log_path,
            "sent_list_path": sent_list_path,
            "unsent_list_path": unsent_list_path,
            "screen_output": screen_output,
            "warning": warning_text,
            "warnings": warnings,
            "results": results,
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
