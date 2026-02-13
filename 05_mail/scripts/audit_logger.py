"""
audit_logger.py - 監査ログ出力モジュール

要件定義書 v11 §7.3, §7.4, §9.2 に基づくログ機能を提供する。
- 画面表示用マスキング
- 監査ログ暗号化保存
- 送信済み/未送信リスト出力
"""

import os
import json
import csv
import datetime
import uuid
import getpass
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict

from .encryption import EncryptionManager


@dataclass
class AuditLogEntry:
    """監査ログエントリ"""
    execution_id: str
    start_time: str
    end_time: str
    operator: str
    input_file: str
    total_count: int
    success_count: int
    failure_count: int
    details: List[Dict[str, Any]]  # 暗号化対象
    errors: List[Dict[str, str]]


class AuditLogger:
    """監査ログ出力クラス"""

    def __init__(
        self,
        log_dir: str,
        encryption_manager: Optional[EncryptionManager] = None
    ):
        """
        Args:
            log_dir: ログ出力ディレクトリ
            encryption_manager: 暗号化マネージャー
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.encryption_manager = encryption_manager or EncryptionManager()

        self.execution_id = str(uuid.uuid4())
        self.start_time = datetime.datetime.now()
        self.operator = getpass.getuser()

    def write_audit_log(
        self,
        input_file: str,
        results: List[Dict[str, Any]],
        product_info: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        監査ログを書き込む。

        Args:
            input_file: 入力ファイル名
            results: 送信結果リスト
            product_info: 製品情報（任意）

        Returns:
            ログファイルパス
        """
        end_time = datetime.datetime.now()

        # 集計
        success_count = sum(1 for r in results if r.get("success"))
        failure_count = len(results) - success_count

        # 詳細情報を暗号化
        encrypted_details = []
        for result in results:
            detail = {
                "email_enc": self._encrypt_if_available(result.get("email", "")),
                "company_name": result.get("company_name", ""),
                "success": result.get("success", False),
                "message_id": result.get("message_id", ""),
                "sent_at": result.get("sent_at", ""),
                "request_key": result.get("request_key", result.get("dedupe_key", "")),
                "mail_key": result.get("mail_key", ""),
                "dedupe_key_version": result.get("dedupe_key_version", ""),
                "decision_trace": result.get("decision_trace", []),
                "action": result.get("action", ""),
            }
            encrypted_details.append(detail)

        # エラー情報（メールアドレスはマスク）
        errors = []
        for result in results:
            if not result.get("success"):
                error_payload = result.get("error_details")
                if error_payload in (None, ""):
                    error_payload = result.get("error", "")
                errors.append({
                    "email_masked": self.mask_email_domain_only(result.get("email", "")),
                    "error": self._mask_error_details(error_payload),
                })

        # ログエントリ作成
        entry = AuditLogEntry(
            execution_id=self.execution_id,
            start_time=self.start_time.isoformat(),
            end_time=end_time.isoformat(),
            operator=self.operator,
            input_file=Path(input_file).name,
            total_count=len(results),
            success_count=success_count,
            failure_count=failure_count,
            details=encrypted_details,
            errors=errors,
        )

        # ファイル書き込み
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"audit_{timestamp}_{self.execution_id[:8]}.json"

        entry_dict = asdict(entry)
        if product_info:
            entry_dict["product_info"] = product_info

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(entry_dict, f, ensure_ascii=False, indent=2)

        return str(log_file)

    def write_sent_list(
        self,
        results: List[Dict[str, Any]],
        success_only: bool = True
    ) -> str:
        """
        送信済みリストを書き込む（メールアドレス暗号化）。

        Args:
            results: 送信結果リスト
            success_only: Trueなら成功分のみ

        Returns:
            ファイルパス
        """
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"sent_list_{timestamp}.csv"
        filepath = self.log_dir / filename

        filtered = [r for r in results if r.get("success")] if success_only else results

        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "メールアドレス_enc",
                "会社名",
                "送信日時",
                "Message-ID"
            ])

            for result in filtered:
                writer.writerow([
                    self._encrypt_if_available(result.get("email", "")),
                    result.get("company_name", ""),
                    result.get("sent_at", ""),
                    result.get("message_id", ""),
                ])

        return str(filepath)

    def write_unsent_list(
        self,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        未送信リストを書き込む（メールアドレス暗号化）。

        Args:
            results: 送信結果リスト（失敗分）

        Returns:
            ファイルパス
        """
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"unsent_list_{timestamp}.csv"
        filepath = self.log_dir / filename

        failed = [r for r in results if not r.get("success")]

        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "メールアドレス_enc",
                "会社名",
                "エラー内容"
            ])

            for result in failed:
                writer.writerow([
                    self._encrypt_if_available(result.get("email", "")),
                    result.get("company_name", ""),
                    result.get("error", ""),
                ])

        return str(filepath)

    def _encrypt_if_available(self, value: str) -> str:
        """暗号化マネージャーが利用可能なら暗号化する"""
        if not value:
            return ""

        try:
            return self.encryption_manager.encrypt(value)
        except Exception:
            # 鍵がない場合等はマスク表示
            return self.mask_email(value) if "@" in value else "***"

    def _mask_error_details(self, value: Any) -> Any:
        """エラー詳細内のメールアドレスを ***@domain 形式でマスクする。"""
        if isinstance(value, dict):
            return {k: self._mask_error_details(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._mask_error_details(v) for v in value]
        if isinstance(value, str):
            return self._mask_emails_in_text(value)
        return value

    def _mask_emails_in_text(self, text: str) -> str:
        """文字列内に含まれるメールアドレスをマスクする。"""
        if not text:
            return text

        email_pattern = re.compile(
            r'([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})'
        )
        return email_pattern.sub(
            lambda m: self.mask_email_domain_only(m.group(1)),
            text,
        )

    @staticmethod
    def mask_email(email: str) -> str:
        """
        メールアドレスをマスクする（画面表示用）。

        例: tanaka@example.com → tan***@example.com
        """
        if "@" not in email:
            return "***"

        local, domain = email.split("@", 1)
        if len(local) <= 3:
            masked_local = local[0] + "***"
        else:
            masked_local = local[:3] + "***"

        return f"{masked_local}@{domain}"

    @staticmethod
    def mask_email_domain_only(email: str) -> str:
        """
        メールアドレスをドメイン部分のみ表示する（エラーログ用）。

        例: tanaka@example.com → ***@example.com
        """
        if "@" not in email:
            return "***"

        _, domain = email.split("@", 1)
        return f"***@{domain}"

    def format_screen_output(self, results: List[Dict[str, Any]]) -> str:
        """
        画面表示用の出力を生成する。

        Args:
            results: 送信結果リスト

        Returns:
            フォーマット済み文字列
        """
        lines = ["=" * 50]
        lines.append("送信結果サマリ")
        lines.append("=" * 50)

        success_count = sum(1 for r in results if r.get("success"))
        failure_count = len(results) - success_count

        lines.append(f"総件数: {len(results)}")
        lines.append(f"成功: {success_count}")
        lines.append(f"失敗: {failure_count}")
        lines.append("")

        lines.append("-" * 50)
        lines.append("詳細:")
        lines.append("-" * 50)

        for result in results:
            status = "✓" if result.get("success") else "✗"
            email_masked = self.mask_email(result.get("email", ""))
            company = result.get("company_name", "")
            sent_at = result.get("sent_at", "")

            line = f"{status} {company} ({email_masked})"
            if sent_at:
                if isinstance(sent_at, datetime.datetime):
                    line += f" - {sent_at.strftime('%H:%M:%S')}"
                else:
                    line += f" - {sent_at}"

            if not result.get("success"):
                line += f" [エラー: {result.get('error', '不明')}]"

            lines.append(line)

        lines.append("=" * 50)
        return "\n".join(lines)
