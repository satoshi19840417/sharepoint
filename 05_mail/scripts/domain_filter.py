"""
domain_filter.py - ドメイン制限モジュール

要件定義書 v11 §4 に基づくドメイン制限機能を提供する。

優先順位:
1. ブラックリストに一致 → 拒否（ホワイトリストより優先）
2. ホワイトリストが空 → 許可
3. ホワイトリストに一致 → 許可
4. 上記以外 → 拒否
"""

from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class DomainFilterResult:
    """ドメインフィルタ結果"""
    allowed: bool
    reason: str
    domain: str


class DomainFilter:
    """ドメイン制限フィルタクラス"""

    def __init__(self, whitelist: List[str] = None, blacklist: List[str] = None):
        """
        Args:
            whitelist: 許可ドメインリスト（空の場合は全許可）
            blacklist: 拒否ドメインリスト（ホワイトリストより優先）
        """
        self.whitelist = [d.lower().strip() for d in (whitelist or [])]
        self.blacklist = [d.lower().strip() for d in (blacklist or [])]

    def check(self, email: str) -> DomainFilterResult:
        """
        メールアドレスのドメインをチェックする。

        Args:
            email: メールアドレス

        Returns:
            DomainFilterResult
        """
        domain = self._extract_domain(email)

        # 1. ブラックリストチェック（最優先）
        if self._matches_list(domain, self.blacklist):
            return DomainFilterResult(
                allowed=False,
                reason=f"ブラックリストに一致: {domain}",
                domain=domain
            )

        # 2. ホワイトリストが空 → 許可
        if not self.whitelist:
            return DomainFilterResult(
                allowed=True,
                reason="ホワイトリスト未設定のため許可",
                domain=domain
            )

        # 3. ホワイトリストに一致 → 許可
        if self._matches_list(domain, self.whitelist):
            return DomainFilterResult(
                allowed=True,
                reason=f"ホワイトリストに一致: {domain}",
                domain=domain
            )

        # 4. 上記以外 → 拒否
        return DomainFilterResult(
            allowed=False,
            reason=f"ホワイトリストに含まれません: {domain}",
            domain=domain
        )

    def _extract_domain(self, email: str) -> str:
        """メールアドレスからドメインを抽出する"""
        if "@" not in email:
            return ""
        return email.split("@", 1)[1].lower().strip()

    def _matches_list(self, domain: str, domain_list: List[str]) -> bool:
        """
        ドメインがリストに一致するかチェックする。
        サブドメインも含めてマッチング。
        """
        for pattern in domain_list:
            if domain == pattern:
                return True
            # サブドメインマッチング（例: sub.example.com は example.com にマッチ）
            if domain.endswith("." + pattern):
                return True
        return False

    def filter_emails(self, emails: List[str]) -> Tuple[List[str], List[DomainFilterResult]]:
        """
        メールアドレスリストをフィルタリングする。

        Args:
            emails: メールアドレスリスト

        Returns:
            (許可されたメールリスト, 拒否結果リスト)
        """
        allowed = []
        rejected = []

        for email in emails:
            result = self.check(email)
            if result.allowed:
                allowed.append(email)
            else:
                rejected.append(result)

        return allowed, rejected
