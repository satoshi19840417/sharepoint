"""
pii_detector.py - PII混入検出モジュール

要件定義書 v11 §9.3 に基づくPII検出機能を提供する。
- メールアドレス形式検出 → 送信ブロック
- 電話番号形式検出 → 送信ブロック
- 会社名一致検出 → 警告表示
"""

import re
from typing import List, Set, Tuple
from dataclasses import dataclass


@dataclass
class PIIDetectionResult:
    """PII検出結果"""
    has_blocking_pii: bool = False
    has_warning_pii: bool = False
    emails_found: List[str] = None
    phones_found: List[str] = None
    companies_found: List[str] = None
    message: str = ""

    def __post_init__(self):
        if self.emails_found is None:
            self.emails_found = []
        if self.phones_found is None:
            self.phones_found = []
        if self.companies_found is None:
            self.companies_found = []


class PIIDetector:
    """PII混入検出クラス"""

    # メールアドレスパターン
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    )

    # 電話番号パターン（ハイフン・空白・括弧を含む形式）
    PHONE_PATTERN = re.compile(
        r'(?:\d[\d\-\s\(\)]{8,}\d)',  # 数字で始まり終わる、間に記号を含む
    )

    def __init__(self, company_names: Set[str] = None):
        """
        Args:
            company_names: 連絡先CSVに含まれる会社名のセット
        """
        self.company_names = company_names or set()

    def detect(self, text: str) -> PIIDetectionResult:
        """
        テキスト内のPIIを検出する。

        Args:
            text: 検査対象のテキスト（製品検索クエリ等）

        Returns:
            PIIDetectionResult
        """
        result = PIIDetectionResult()

        # メールアドレス検出
        emails = self.EMAIL_PATTERN.findall(text)
        if emails:
            result.has_blocking_pii = True
            result.emails_found = emails

        # 電話番号検出
        phones = self._detect_phones(text)
        if phones:
            result.has_blocking_pii = True
            result.phones_found = phones

        # 会社名検出
        companies = self._detect_companies(text)
        if companies:
            result.has_warning_pii = True
            result.companies_found = companies

        # メッセージ生成
        result.message = self._generate_message(result)

        return result

    def _detect_phones(self, text: str) -> List[str]:
        """
        電話番号を検出する。

        要件定義書: ハイフン/空白除去後に連続数字10桁以上を検出
        """
        phones = []
        candidates = self.PHONE_PATTERN.findall(text)

        for candidate in candidates:
            # 数字以外を除去
            digits_only = re.sub(r'\D', '', candidate)
            # 10桁以上なら電話番号として検出
            if len(digits_only) >= 10:
                phones.append(candidate)

        return phones

    def _detect_companies(self, text: str) -> List[str]:
        """
        会社名との完全一致を検出する。
        """
        found = []
        for company in self.company_names:
            if company and company in text:
                found.append(company)
        return found

    def _generate_message(self, result: PIIDetectionResult) -> str:
        """検出結果のメッセージを生成する"""
        if not result.has_blocking_pii and not result.has_warning_pii:
            return ""

        messages = []

        if result.emails_found:
            messages.append(
                f"メールアドレスが検出されました: {', '.join(result.emails_found)}\n"
                "→ 削除してから再実行してください。"
            )

        if result.phones_found:
            messages.append(
                f"電話番号が検出されました: {', '.join(result.phones_found)}\n"
                "→ 削除してから再実行してください。"
            )

        if result.companies_found:
            messages.append(
                f"会社名との一致が検出されました: {', '.join(result.companies_found)}\n"
                "→ 続行する場合は確認してください。"
            )

        return "\n\n".join(messages)

    def set_company_names(self, company_names: Set[str]) -> None:
        """会社名セットを設定する"""
        self.company_names = company_names
