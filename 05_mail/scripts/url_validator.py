"""
url_validator.py - URL有効性チェックモジュール

要件定義書 v11 §3.2 に基づくURL検証機能を提供する。
- HTTPSスキームのみ許可（HTTPは警告）
- 内部アドレス（ローカルホスト、プライベートIP）遮断
- HEAD → GET フォールバック
- リダイレクト追従（最大5回）
- タイムアウト10秒、リトライ2回
"""

import re
import socket
from typing import Tuple, Optional
from urllib.parse import urlparse
from dataclasses import dataclass
import requests
from requests.exceptions import RequestException, Timeout


@dataclass
class URLValidationResult:
    """URL検証結果"""
    valid: bool
    url: str
    final_url: str = ""
    status_code: int = 0
    error: str = ""
    warning: str = ""


class URLValidator:
    """URL有効性チェッククラス"""

    # プライベートIPレンジ
    PRIVATE_IP_PATTERNS = [
        r'^127\.',                          # ローカルホスト
        r'^10\.',                           # クラスA
        r'^172\.(1[6-9]|2[0-9]|3[01])\.',  # クラスB
        r'^192\.168\.',                     # クラスC
        r'^0\.',                            # 特殊
        r'^localhost$',
    ]

    # ブラウザ相当のUser-Agent
    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        timeout: int = 10,
        retry_count: int = 2,
        retry_interval: float = 3.0,
        max_redirects: int = 5
    ):
        """
        Args:
            timeout: タイムアウト秒数
            retry_count: リトライ回数
            retry_interval: リトライ間隔（秒）
            max_redirects: 最大リダイレクト回数
        """
        self.timeout = timeout
        self.retry_count = retry_count
        self.retry_interval = retry_interval
        self.max_redirects = max_redirects

    def validate(self, url: str) -> URLValidationResult:
        """
        URLの有効性をチェックする。

        Args:
            url: 検証対象URL

        Returns:
            URLValidationResult
        """
        result = URLValidationResult(valid=False, url=url)

        # スキームチェック
        scheme_check = self._check_scheme(url)
        if scheme_check[0] is False:
            result.error = scheme_check[1]
            return result
        if scheme_check[1]:  # 警告がある場合
            result.warning = scheme_check[1]

        # 内部アドレスチェック
        internal_check = self._check_internal_address(url)
        if not internal_check[0]:
            result.error = internal_check[1]
            return result

        # HTTP検証
        return self._perform_request(url, warning=result.warning)

    def _check_scheme(self, url: str) -> Tuple[Optional[bool], str]:
        """
        スキームをチェックする。

        Returns:
            (結果, メッセージ) - 結果がNoneの場合は継続、Falseはブロック
        """
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        if scheme == "https":
            return None, ""
        elif scheme == "http":
            return None, "HTTPスキームです。セキュリティ上のリスクがあります。"
        else:
            return False, f"許可されていないスキームです: {scheme}"

    def _check_internal_address(self, url: str) -> Tuple[bool, str]:
        """
        内部アドレスかどうかをチェックする。

        Returns:
            (許可するか, エラーメッセージ)
        """
        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return False, "ホスト名を取得できません"

        # ローカルホストチェック
        if hostname.lower() in ("localhost", "127.0.0.1", "::1"):
            return False, "ローカルホストへのアクセスはブロックされています"

        # プライベートIPチェック
        for pattern in self.PRIVATE_IP_PATTERNS:
            if re.match(pattern, hostname, re.IGNORECASE):
                return False, f"プライベートIPへのアクセスはブロックされています: {hostname}"

        # DNS解決してプライベートIPチェック
        try:
            ip = socket.gethostbyname(hostname)
            for pattern in self.PRIVATE_IP_PATTERNS:
                if re.match(pattern, ip):
                    return False, f"解決先がプライベートIPです: {hostname} → {ip}"
        except socket.gaierror:
            # DNS解決失敗は後続のHTTPリクエストで検出される
            pass

        return True, ""

    def _perform_request(self, url: str, warning: str = "") -> URLValidationResult:
        """
        HTTP(S)リクエストを実行して有効性を確認する。
        """
        result = URLValidationResult(valid=False, url=url, warning=warning)
        headers = {"User-Agent": self.DEFAULT_USER_AGENT}

        for attempt in range(self.retry_count + 1):
            try:
                # まずHEADリクエスト
                response = requests.head(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    allow_redirects=True,
                    verify=True
                )

                # HEADが失敗（405 Method Not Allowed等）ならGETで再試行
                if response.status_code == 405:
                    response = requests.get(
                        url,
                        headers=headers,
                        timeout=self.timeout,
                        allow_redirects=True,
                        verify=True,
                        stream=True  # ボディは読まない
                    )
                    response.close()

                result.status_code = response.status_code
                result.final_url = response.url

                redirect_count = len(getattr(response, "history", []) or [])
                if redirect_count > self.max_redirects:
                    result.error = (
                        f"リダイレクト回数が上限を超えています: "
                        f"{redirect_count} > {self.max_redirects}"
                    )
                    return result

                # 2xx/3xxは成功
                if 200 <= response.status_code < 400:
                    result.valid = True
                    return result
                else:
                    result.error = f"HTTPステータス {response.status_code}"
                    return result

            except Timeout:
                result.error = f"タイムアウト（{self.timeout}秒）"
                if attempt < self.retry_count:
                    import time
                    time.sleep(self.retry_interval)
                    continue
            except RequestException as e:
                result.error = f"接続エラー: {str(e)}"
                if attempt < self.retry_count:
                    import time
                    time.sleep(self.retry_interval)
                    continue

        return result

    def validate_multiple(self, urls: list) -> list:
        """
        複数URLを検証する。

        Args:
            urls: URLリスト

        Returns:
            URLValidationResultのリスト
        """
        return [self.validate(url) for url in urls]
