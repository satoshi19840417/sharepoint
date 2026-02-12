"""
mail_sender.py - Outlookメール送信モジュール

要件定義書 v11 §8, §12 に基づくメール送信機能を提供する。
- win32comによるOutlook連携
- Message-ID取得（Subject + SentOn + To 照合）
- リトライ機能（最大3回）
- 代替ID生成（Message-ID取得失敗時）
- 送信間隔制御
"""

import datetime
import re
import time
import uuid
import hashlib
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field

# win32comは実行時にインポート
try:
    import win32com.client
    import pythoncom
    WIN32COM_AVAILABLE = True
except ImportError:
    WIN32COM_AVAILABLE = False


@dataclass
class SendResult:
    """送信結果"""
    success: bool
    email: str
    company_name: str
    message_id: str = ""
    error: str = ""
    is_fallback_id: bool = False
    message_id_source: str = ""
    sent_at: datetime.datetime = None


@dataclass
class SendSummary:
    """送信サマリ"""
    total: int = 0
    success_count: int = 0
    failure_count: int = 0
    results: List[SendResult] = field(default_factory=list)
    start_time: datetime.datetime = None
    end_time: datetime.datetime = None


class OutlookMailSender:
    """Outlookメール送信クラス"""

    # Message-ID取得用MAPIプロパティ
    MESSAGE_ID_PROPERTY = "http://schemas.microsoft.com/mapi/proptag/0x1035001F"
    MESSAGE_HEADER_PROPERTY = "http://schemas.microsoft.com/mapi/proptag/0x007D001F"
    SENT_FOLDER_ID = 5  # olFolderSentMail
    SENT_TIME_WINDOW_SEC = 180
    DIRECT_MESSAGE_ID_POLL_INTERVAL_SEC = 0.5
    DIRECT_MESSAGE_ID_POLL_TIMEOUT_SEC = 5.0
    MAX_SENT_ITEMS_SCAN = 200

    def __init__(
        self,
        send_interval_sec: float = 3.0,
        retry_count: int = 3,
        retry_interval_sec: float = 3.0,
        message_id_retry_count: int = 3,
        message_id_retry_interval_sec: float = 2.0,
        dry_run: bool = False
    ):
        """
        Args:
            send_interval_sec: 送信間隔（秒）
            retry_count: 送信リトライ回数
            retry_interval_sec: 送信リトライ間隔（秒）
            message_id_retry_count: Message-ID取得リトライ回数
            message_id_retry_interval_sec: Message-ID取得リトライ間隔（秒）
            dry_run: ドライランモード（実際には送信しない）
        """
        self.send_interval_sec = send_interval_sec
        self.retry_count = retry_count
        self.retry_interval_sec = retry_interval_sec
        self.message_id_retry_count = message_id_retry_count
        self.message_id_retry_interval_sec = message_id_retry_interval_sec
        self.dry_run = dry_run

        self._outlook = None
        self._last_send_time: Optional[datetime.datetime] = None

    def _get_outlook(self):
        """Outlookアプリケーションを取得"""
        if not WIN32COM_AVAILABLE:
            raise RuntimeError(
                "win32comが利用できません。pywin32をインストールしてください。"
            )

        if self._outlook is None:
            pythoncom.CoInitialize()
            self._outlook = win32com.client.Dispatch("Outlook.Application")

        return self._outlook

    def send_mail(
        self,
        to: str,
        subject: str,
        body: str,
        company_name: str = "",
        html_body: Optional[str] = None
    ) -> SendResult:
        """
        メールを送信する。

        Args:
            to: 宛先メールアドレス
            subject: 件名
            body: 本文（プレーンテキスト）
            company_name: 会社名（ログ用）
            html_body: HTML本文（オプション）

        Returns:
            SendResult
        """
        result = SendResult(
            success=False,
            email=to,
            company_name=company_name
        )

        # 送信間隔を確保
        self._wait_for_interval()

        # ドライランモード
        if self.dry_run:
            result.success = True
            result.message_id = f"DRYRUN:{uuid.uuid4()}"
            result.sent_at = datetime.datetime.now()
            return result

        # 送信実行（リトライ付き）
        for attempt in range(self.retry_count + 1):
            try:
                outlook = self._get_outlook()
                mail = outlook.CreateItem(0)  # 0 = olMailItem
                mail.To = to
                mail.Subject = subject

                if html_body:
                    mail.HTMLBody = html_body
                else:
                    mail.Body = body

                # 送信前に情報を記録
                subject_before_send = mail.Subject
                recipient_before_send = mail.To
                sent_time_approx = datetime.datetime.now()

                mail.Send()
                self._last_send_time = datetime.datetime.now()

                # Message-ID取得
                time.sleep(2)  # Outlook処理待機
                message_id, is_fallback = self._get_message_id(
                    subject_before_send,
                    recipient_before_send,
                    sent_time_approx
                )

                result.success = True
                result.message_id = message_id
                result.is_fallback_id = is_fallback
                result.sent_at = sent_time_approx
                return result

            except Exception as e:
                error_msg = str(e)
                result.error = error_msg

                # リトライ判定
                if self._is_retryable_error(error_msg) and attempt < self.retry_count:
                    time.sleep(self.retry_interval_sec)
                    continue
                else:
                    break

        return result

    def _wait_for_interval(self):
        """送信間隔を確保する"""
        if self._last_send_time is None:
            return

        elapsed = (datetime.datetime.now() - self._last_send_time).total_seconds()
        if elapsed < self.send_interval_sec:
            time.sleep(self.send_interval_sec - elapsed)

    def _get_message_id(
        self,
        subject: str,
        recipient: str,
        sent_time_approx: datetime.datetime
    ) -> Tuple[str, bool]:
        """
        送信済みフォルダからMessage-IDを取得する。

        要件定義書: Subject + SentOn(±60秒) + To で照合

        Returns:
            (message_id, is_fallback)
        """
        for attempt in range(self.message_id_retry_count):
            try:
                outlook = self._get_outlook()
                namespace = outlook.GetNamespace("MAPI")
                sent_folder = namespace.GetDefaultFolder(5)  # 5 = olFolderSentMail
                items = sent_folder.Items
                items.Sort("[SentOn]", True)  # 降順

                for item in items:
                    try:
                        # Subject一致
                        if item.Subject != subject:
                            continue

                        # SentOn一致（±60秒以内）
                        item_sent_on = item.SentOn
                        if isinstance(item_sent_on, datetime.datetime):
                            time_diff = abs((item_sent_on - sent_time_approx).total_seconds())
                            if time_diff > 60:
                                continue
                        else:
                            continue

                        # To一致
                        if item.To != recipient:
                            continue

                        # Message-ID取得
                        message_id = item.PropertyAccessor.GetProperty(
                            self.MESSAGE_ID_PROPERTY
                        )
                        if message_id:
                            return message_id, False

                    except Exception:
                        continue

            except Exception:
                pass

            if attempt < self.message_id_retry_count - 1:
                time.sleep(self.message_id_retry_interval_sec)

        # 代替ID生成
        fallback_id = self._generate_fallback_id(subject, sent_time_approx)
        return fallback_id, True

    def _generate_fallback_id(
        self,
        subject: str,
        timestamp: datetime.datetime
    ) -> str:
        """
        代替一意IDを生成する。

        形式: FALLBACK:{UUID}:{timestamp}:{subject_hash}
        """
        subject_hash = hashlib.sha256(subject.encode('utf-8')).hexdigest()[:8]
        ts = int(timestamp.timestamp())
        return f"FALLBACK:{uuid.uuid4()}:{ts}:{subject_hash}"

    def _is_retryable_error(self, error_msg: str) -> bool:
        """リトライ可能なエラーかどうかを判定"""
        retryable_keywords = [
            "timeout",
            "timed out",
            "connection",
            "temporary",
            "busy",
        ]
        error_lower = error_msg.lower()
        return any(keyword in error_lower for keyword in retryable_keywords)

    def send_test_mail(self, test_email: str, subject: str, body: str) -> SendResult:
        """
        テストメールを送信する。

        Args:
            test_email: テスト送信先（通常は自分のアドレス）
            subject: 件名
            body: 本文

        Returns:
            SendResult
        """
        return self.send_mail(
            to=test_email,
            subject=f"[テスト] {subject}",
            body=body,
            company_name="テスト送信"
        )

    def send_bulk(
        self,
        recipients: List[Dict],
        subject: str,
        body_template: str,
        render_func: callable = None
    ) -> SendSummary:
        """
        一斉送信を実行する。

        Args:
            recipients: 受信者リスト [{"email": ..., "company_name": ..., ...}, ...]
            subject: 件名
            body_template: 本文テンプレート
            render_func: 本文レンダリング関数 (template, recipient) -> body

        Returns:
            SendSummary
        """
        summary = SendSummary(
            total=len(recipients),
            start_time=datetime.datetime.now()
        )

        for recipient in recipients:
            email = recipient.get("email", "")
            company_name = recipient.get("company_name", "")

            # 本文生成
            if render_func:
                body = render_func(body_template, recipient)
            else:
                body = body_template

            # 送信
            result = self.send_mail(
                to=email,
                subject=subject,
                body=body,
                company_name=company_name
            )

            summary.results.append(result)

            if result.success:
                summary.success_count += 1
            else:
                summary.failure_count += 1

        summary.end_time = datetime.datetime.now()
        return summary

    def check_outlook_connection(self) -> Tuple[bool, str]:
        """
        Outlook接続を確認する。

        Returns:
            (接続可否, メッセージ)
        """
        try:
            outlook = self._get_outlook()
            namespace = outlook.GetNamespace("MAPI")
            # 送信済みフォルダにアクセスできるか確認
            sent_folder = namespace.GetDefaultFolder(5)
            _ = sent_folder.Items.Count
            return True, "Outlook接続OK"
        except Exception as e:
            return False, f"Outlook接続エラー: {e}"
