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
            result.message_id_source = "dry_run"
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
                message_id, is_fallback, message_id_source = self._get_message_id_with_source(
                    mail,
                    subject_before_send,
                    recipient_before_send,
                    sent_time_approx
                )

                result.success = True
                result.message_id = message_id
                result.is_fallback_id = is_fallback
                result.message_id_source = message_id_source
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
        互換性維持用: Message-IDとfallback判定のみを返す。
        """
        message_id, is_fallback, _ = self._get_message_id_with_source(
            None,
            subject,
            recipient,
            sent_time_approx,
        )
        return message_id, is_fallback

    def _get_message_id_with_source(
        self,
        mail_item,
        subject: str,
        recipient: str,
        sent_time_approx: datetime.datetime
    ) -> Tuple[str, bool, str]:
        """
        Message-IDを取得する。
        優先順位:
        1. 送信直後のMailItemから直接取得（ポーリング）
        2. 送信済みフォルダ再検索（Subject + SentOn(±180秒) + To）
        3. fallback ID生成

        Returns:
            (message_id, is_fallback, source)
        """
        direct_message_id = self._poll_message_id_from_mail_item(
            mail_item=mail_item,
            timeout_sec=self.DIRECT_MESSAGE_ID_POLL_TIMEOUT_SEC,
            interval_sec=self.DIRECT_MESSAGE_ID_POLL_INTERVAL_SEC,
        )
        if direct_message_id:
            return direct_message_id, False, "direct"

        sent_items_message_id = self._get_message_id_from_sent_items(
            subject=subject,
            recipient=recipient,
            sent_time_approx=sent_time_approx,
            time_window_sec=self.SENT_TIME_WINDOW_SEC,
        )
        if sent_items_message_id:
            return sent_items_message_id, False, "sent_items"

        fallback_id = self._generate_fallback_id(subject, sent_time_approx)
        return fallback_id, True, "fallback"

    def _poll_message_id_from_mail_item(
        self,
        mail_item,
        timeout_sec: float,
        interval_sec: float,
    ) -> str:
        """送信直後のMailItemからMessage-IDをポーリング取得する。"""
        if mail_item is None:
            return ""

        deadline = time.time() + timeout_sec
        while time.time() < deadline:
            message_id = self._extract_message_id_from_item(mail_item)
            if message_id:
                return message_id
            time.sleep(interval_sec)
        return ""

    def _get_message_id_from_sent_items(
        self,
        subject: str,
        recipient: str,
        sent_time_approx: datetime.datetime,
        time_window_sec: int = 180,
    ) -> str:
        """送信済みフォルダからMessage-IDを再検索する。"""
        recipient_expected = self._normalize_recipients(recipient)
        for attempt in range(self.message_id_retry_count):
            try:
                outlook = self._get_outlook()
                namespace = outlook.GetNamespace("MAPI")
                sent_folder = namespace.GetDefaultFolder(self.SENT_FOLDER_ID)
                items = sent_folder.Items
                items.Sort("[SentOn]", True)  # 降順

                scanned = 0
                min_allowed_time = sent_time_approx - datetime.timedelta(seconds=time_window_sec)
                max_allowed_time = sent_time_approx + datetime.timedelta(seconds=time_window_sec)

                for item in items:
                    scanned += 1
                    if scanned > self.MAX_SENT_ITEMS_SCAN:
                        break

                    try:
                        item_subject = str(getattr(item, "Subject", "")).strip()
                        if item_subject != str(subject).strip():
                            continue

                        item_sent_on = getattr(item, "SentOn", None)
                        if not isinstance(item_sent_on, datetime.datetime):
                            continue

                        if item_sent_on < min_allowed_time:
                            break
                        if item_sent_on > max_allowed_time:
                            continue

                        if not self._recipient_matches(
                            recipient_expected,
                            self._normalize_recipients(str(getattr(item, "To", ""))),
                        ):
                            continue

                        message_id = self._extract_message_id_from_item(item)
                        if message_id:
                            return message_id
                    except Exception:
                        continue
            except Exception:
                pass

            if attempt < self.message_id_retry_count - 1:
                time.sleep(self.message_id_retry_interval_sec)

        return ""

    def _extract_message_id_from_item(self, item) -> str:
        """MailItemからMessage-IDを抽出する。"""
        if item is None:
            return ""

        try:
            message_id = item.PropertyAccessor.GetProperty(self.MESSAGE_ID_PROPERTY)
            if message_id:
                return str(message_id).strip()
        except Exception:
            pass

        try:
            headers = item.PropertyAccessor.GetProperty(self.MESSAGE_HEADER_PROPERTY)
            return self._extract_message_id_from_headers(headers)
        except Exception:
            pass

        return ""

    @staticmethod
    def _extract_message_id_from_headers(headers: str) -> str:
        """メールヘッダ文字列からMessage-IDを抽出する。"""
        if not headers:
            return ""

        match = re.search(
            r"^Message-ID:\s*(<[^>]+>|[^\r\n]+)",
            str(headers),
            re.IGNORECASE | re.MULTILINE,
        )
        if not match:
            return ""
        return match.group(1).strip()

    @staticmethod
    def _normalize_recipients(recipients: str) -> List[str]:
        """宛先文字列を正規化してアドレス配列にする。"""
        if not recipients:
            return []

        normalized: List[str] = []
        parts = re.split(r"[;,]", recipients)
        for part in parts:
            token = part.strip()
            if not token:
                continue

            email_match = re.search(
                r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
                token,
            )
            if email_match:
                normalized.append(email_match.group(1).lower())
            else:
                normalized.append(token.lower())

        return normalized

    @staticmethod
    def _recipient_matches(expected: List[str], actual: List[str]) -> bool:
        """宛先候補が一致するかを判定する。"""
        if not expected or not actual:
            return False

        expected_set = set(expected)
        actual_set = set(actual)
        return bool(expected_set & actual_set)

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
