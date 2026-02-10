"""
csv_handler.py - CSV読み込み・エイリアス処理モジュール

要件定義書 v11 §6 に基づくCSV読み込み機能を提供する。
- 文字コード自動判定（BOM → chardet → フォールバック）
- 列名エイリアス正規化
- 担当者名結合ロジック
- バリデーション（メールアドレス形式、重複除外）
- 暗号化列検出・復号
"""

import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from email_validator import validate_email, EmailNotValidError
import chardet

from .encryption import EncryptionManager, validate_encrypted_column, DecryptionError


# 列名エイリアス定義（要件定義書§6.2）
COLUMN_ALIASES: Dict[str, List[str]] = {
    "会社名": ["勤務先", "Company", "会社"],
    "メールアドレス": ["電子メール アドレス", "電子メール", "Email", "E-mail"],
    "部署名": ["部署", "Department"],
    "電話番号": ["会社電話", "電話番号 (会社)", "勤務先電話", "Phone"],
}

# 担当者名エイリアス（優先順位順）
CONTACT_NAME_ALIASES: List[str] = ["担当者名", "氏名"]
CONTACT_NAME_PARTS: Dict[str, List[str]] = {
    "姓": ["姓", "Last Name", "LastName"],
    "名": ["名", "First Name", "FirstName"],
    "ミドル ネーム": ["ミドル ネーム", "Middle Name", "MiddleName"],
}


@dataclass
class ContactRecord:
    """連絡先レコード"""
    company_name: str
    email: str
    contact_name: str = "ご担当者様"
    department: str = ""
    phone: str = ""
    raw_data: Dict[str, str] = field(default_factory=dict)


@dataclass
class CSVLoadResult:
    """CSV読み込み結果"""
    records: List[ContactRecord] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    skipped_rows: List[int] = field(default_factory=list)
    duplicate_emails: List[str] = field(default_factory=list)


class CSVHandler:
    """CSV読み込み・処理クラス"""

    def __init__(self, encryption_manager: Optional[EncryptionManager] = None):
        """
        Args:
            encryption_manager: 暗号化マネージャー（暗号化列復号用）
        """
        self.encryption_manager = encryption_manager or EncryptionManager()

    def load_csv(self, filepath: str, encoding: Optional[str] = None) -> CSVLoadResult:
        """
        CSVファイルを読み込み、連絡先レコードのリストを返す。

        Args:
            filepath: CSVファイルパス
            encoding: 文字コード指定（Noneの場合は自動判定）

        Returns:
            CSVLoadResult
        """
        result = CSVLoadResult()
        path = Path(filepath)

        if not path.exists():
            result.errors.append(f"ファイルが存在しません: {filepath}")
            return result

        # 文字コード判定
        if encoding is None:
            encoding, warning = self._detect_encoding(path)
            if warning:
                result.warnings.append(warning)

        # CSV読み込み
        try:
            with open(path, 'r', encoding=encoding, errors='replace') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            result.errors.append(f"文字コードエラー: {e}")
            return result

        # 文字化けチェック
        if self._has_garbled_chars(content):
            result.warnings.append(
                "文字化けの可能性があります。文字コードを確認してください。"
            )

        # CSVパース
        lines = content.splitlines()
        if not lines:
            result.errors.append("空のファイルです。")
            return result

        reader = csv.DictReader(lines)
        headers = reader.fieldnames or []

        # 列名正規化マップ作成
        column_map = self._create_column_map(headers)

        # 必須列チェック
        if "会社名" not in column_map:
            result.errors.append("必須列 '会社名' が見つかりません。")
        if "メールアドレス" not in column_map:
            result.errors.append("必須列 'メールアドレス' が見つかりません。")

        if result.errors:
            return result

        # 暗号化列チェック
        encrypted_columns = self._detect_encrypted_columns(headers, lines[1] if len(lines) > 1 else "")
        if encrypted_columns.get("errors"):
            result.errors.extend(encrypted_columns["errors"])
            return result

        # レコード読み込み
        seen_emails: set = set()
        for row_num, row in enumerate(reader, start=2):  # ヘッダーが1行目なので2から開始
            # 空行スキップ
            if not any(row.values()):
                continue

            # 暗号化列を復号
            decrypted_row = self._decrypt_row(row, encrypted_columns.get("columns", {}))
            if decrypted_row.get("error"):
                result.errors.append(f"行{row_num}: {decrypted_row['error']}")
                result.skipped_rows.append(row_num)
                continue
            row = decrypted_row.get("row", row)

            # 値取得
            company = self._get_value(row, column_map, "会社名")
            email = self._get_value(row, column_map, "メールアドレス")
            department = self._get_value(row, column_map, "部署名")
            phone = self._get_value(row, column_map, "電話番号")
            contact_name = self._resolve_contact_name(row, headers)

            # 必須項目チェック
            if not company:
                result.errors.append(f"行{row_num}: 会社名が空です。")
                result.skipped_rows.append(row_num)
                continue
            if not email:
                result.errors.append(f"行{row_num}: メールアドレスが空です。")
                result.skipped_rows.append(row_num)
                continue

            # メールアドレス形式チェック
            try:
                validated = validate_email(email, check_deliverability=False)
                email = validated.normalized
            except EmailNotValidError as e:
                result.errors.append(f"行{row_num}: メールアドレス形式エラー - {e}")
                result.skipped_rows.append(row_num)
                continue

            # 重複チェック
            email_lower = email.lower()
            if email_lower in seen_emails:
                result.warnings.append(f"行{row_num}: 重複メールアドレス - {self._mask_email(email)}")
                result.duplicate_emails.append(email)
                result.skipped_rows.append(row_num)
                continue
            seen_emails.add(email_lower)

            # レコード作成
            record = ContactRecord(
                company_name=company,
                email=email,
                contact_name=contact_name,
                department=department,
                phone=phone,
                raw_data=dict(row),
            )
            result.records.append(record)

        return result

    def _detect_encoding(self, path: Path) -> Tuple[str, Optional[str]]:
        """
        文字コードを自動判定する。

        Returns:
            (encoding, warning_message)
        """
        with open(path, 'rb') as f:
            raw_data = f.read()

        # BOM検出
        if raw_data.startswith(b'\xef\xbb\xbf'):
            return 'utf-8-sig', None

        # chardetで推定
        detected = chardet.detect(raw_data)
        if detected['encoding'] and detected['confidence'] > 0.7:
            encoding = detected['encoding']
            # CP932/Shift_JISの正規化
            if encoding.lower() in ('shift_jis', 'shift-jis'):
                encoding = 'cp932'
            return encoding, None

        # フォールバック（要件定義書§6.1）
        fallback_encodings = ['cp932', 'shift_jis', 'utf-8']
        for enc in fallback_encodings:
            try:
                raw_data.decode(enc)
                return enc, f"文字コード自動判定: {enc}（フォールバック使用）"
            except UnicodeDecodeError:
                continue

        # 最終フォールバック
        return 'utf-8', "文字コードを自動判定できませんでした。UTF-8として読み込みます。"

    def _has_garbled_chars(self, content: str) -> bool:
        """文字化けの可能性をチェック"""
        # 置換文字やNULL文字の検出
        garbled_patterns = ['\ufffd', '\u0000', '□']
        return any(p in content for p in garbled_patterns)

    def _create_column_map(self, headers: List[str]) -> Dict[str, str]:
        """
        ヘッダーからエイリアス対応の列名マップを作成する。

        Returns:
            {標準列名: 実際の列名} のマップ
        """
        column_map: Dict[str, str] = {}
        normalized_headers = {h.strip().lower(): h for h in headers}

        for standard_name, aliases in COLUMN_ALIASES.items():
            # 標準名をまずチェック
            if standard_name.lower() in normalized_headers:
                column_map[standard_name] = normalized_headers[standard_name.lower()]
                continue

            # エイリアスをチェック
            for alias in aliases:
                if alias.lower() in normalized_headers:
                    column_map[standard_name] = normalized_headers[alias.lower()]
                    break

        return column_map

    def _get_value(self, row: Dict[str, str], column_map: Dict[str, str], 
                   standard_name: str) -> str:
        """列マップを使用して値を取得"""
        actual_column = column_map.get(standard_name)
        if actual_column is None:
            return ""
        return (row.get(actual_column) or "").strip()

    def _resolve_contact_name(self, row: Dict[str, str], headers: List[str]) -> str:
        """
        担当者名を解決する（要件定義書§6.2の優先順位）。

        1. 担当者名列 → 2. 氏名列 → 3. 姓+名 → 4. 姓のみ → 5. ご担当者様
        """
        normalized_headers = {h.strip().lower(): h for h in headers}

        # 優先順位1-2: 担当者名/氏名列
        for alias in CONTACT_NAME_ALIASES:
            if alias.lower() in normalized_headers:
                value = row.get(normalized_headers[alias.lower()], "").strip()
                if value:
                    return value

        # 優先順位3-4: 姓+名
        sei = ""
        mei = ""
        middle = ""

        for alias in CONTACT_NAME_PARTS["姓"]:
            if alias.lower() in normalized_headers:
                sei = row.get(normalized_headers[alias.lower()], "").strip()
                break

        for alias in CONTACT_NAME_PARTS["名"]:
            if alias.lower() in normalized_headers:
                mei = row.get(normalized_headers[alias.lower()], "").strip()
                break

        for alias in CONTACT_NAME_PARTS["ミドル ネーム"]:
            if alias.lower() in normalized_headers:
                middle = row.get(normalized_headers[alias.lower()], "").strip()
                break

        if sei and mei:
            if middle:
                return f"{sei} {middle} {mei}"
            return f"{sei} {mei}"
        elif sei:
            return sei

        # 優先順位5: デフォルト
        return "ご担当者様"

    def _detect_encrypted_columns(self, headers: List[str], 
                                   first_data_line: str) -> Dict[str, Any]:
        """
        暗号化列を検出する。

        Returns:
            {"columns": {暗号化列名: 元列名}, "errors": [エラーメッセージ]}
        """
        result: Dict[str, Any] = {"columns": {}, "errors": []}

        if not first_data_line:
            return result

        # 1行目のデータをパース
        reader = csv.DictReader([",".join(headers), first_data_line])
        first_row = next(reader, {})

        for header in headers:
            value = first_row.get(header, "")
            is_valid, error_msg = validate_encrypted_column(header, value)

            if not is_valid:
                result["errors"].append(error_msg)
            elif EncryptionManager.is_encrypted_column_name(header):
                original_name = EncryptionManager.get_original_column_name(header)
                result["columns"][header] = original_name

        return result

    def _decrypt_row(self, row: Dict[str, str], 
                     encrypted_columns: Dict[str, str]) -> Dict[str, Any]:
        """
        行内の暗号化列を復号する。

        Returns:
            {"row": 復号後の行, "error": エラーメッセージ（あれば）}
        """
        if not encrypted_columns:
            return {"row": row}

        decrypted_row = dict(row)

        for enc_col, orig_col in encrypted_columns.items():
            if enc_col not in row:
                continue

            encrypted_value = row[enc_col]
            if not encrypted_value:
                continue

            try:
                decrypted_value = self.encryption_manager.decrypt(encrypted_value)
                # 元の列名で値を設定
                decrypted_row[orig_col] = decrypted_value
            except DecryptionError as e:
                return {"error": str(e)}

        return {"row": decrypted_row}

    @staticmethod
    def _mask_email(email: str) -> str:
        """メールアドレスをマスクする"""
        if "@" not in email:
            return "***"
        local, domain = email.split("@", 1)
        if len(local) <= 3:
            masked_local = local[0] + "***"
        else:
            masked_local = local[:3] + "***"
        return f"{masked_local}@{domain}"
