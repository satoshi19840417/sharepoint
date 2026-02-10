"""
encryption.py - 暗号化・復号・鍵管理モジュール

要件定義書 v11 §9.1.1 に基づく暗号化機能を提供する。
- AES-256暗号化（Fernet）
- Windows資格情報マネージャーによる鍵保存
- enc:v{version}:{ciphertext} 形式の暗号化値
"""

import os
import hashlib
import base64
from typing import Optional, Tuple
from cryptography.fernet import Fernet, InvalidToken
import keyring

# 定数
CREDENTIAL_SERVICE = "見積依頼スキル"
CREDENTIAL_KEY_NAME = "encryption_key"
ENCRYPTION_VERSION = "v1"
ENCRYPTION_PREFIX = f"enc:{ENCRYPTION_VERSION}:"


class EncryptionError(Exception):
    """暗号化関連のエラー"""
    pass


class KeyNotFoundError(EncryptionError):
    """鍵が見つからないエラー"""
    pass


class DecryptionError(EncryptionError):
    """復号エラー"""
    pass


class EncryptionManager:
    """暗号化・復号・鍵管理クラス"""

    def __init__(self, credential_target_name: Optional[str] = None):
        """
        Args:
            credential_target_name: Windows資格情報の識別名。Noneの場合はデフォルト値を使用。
        """
        self.service_name = credential_target_name or CREDENTIAL_SERVICE
        self._fernet: Optional[Fernet] = None

    def _get_fernet(self) -> Fernet:
        """Fernetインスタンスを取得（キャッシュ）"""
        if self._fernet is None:
            key = self.get_key()
            if key is None:
                raise KeyNotFoundError(
                    "暗号化鍵が見つかりません。初回実行の場合は generate_key() を呼び出してください。"
                )
            self._fernet = Fernet(key)
        return self._fernet

    def generate_key(self, force: bool = False) -> bytes:
        """
        暗号化鍵を生成し、Windows資格情報マネージャーに保存する。

        Args:
            force: Trueの場合、既存の鍵を上書きする

        Returns:
            生成した鍵（Base64エンコード済み）

        Raises:
            EncryptionError: 既存の鍵がありforceがFalseの場合
        """
        existing_key = self.get_key()
        if existing_key is not None and not force:
            raise EncryptionError(
                "既存の暗号化鍵があります。上書きする場合は force=True を指定してください。"
            )

        # Fernet用の256bit鍵を生成
        key = Fernet.generate_key()

        # Windows資格情報マネージャーに保存
        keyring.set_password(
            self.service_name,
            CREDENTIAL_KEY_NAME,
            key.decode('utf-8')
        )

        # キャッシュをクリア
        self._fernet = None

        return key

    def get_key(self) -> Optional[bytes]:
        """
        Windows資格情報マネージャーから鍵を取得する。

        Returns:
            鍵（Base64エンコード済み）。存在しない場合はNone。
        """
        key_str = keyring.get_password(self.service_name, CREDENTIAL_KEY_NAME)
        if key_str is None:
            return None
        return key_str.encode('utf-8')

    def delete_key(self) -> bool:
        """
        Windows資格情報マネージャーから鍵を削除する。

        Returns:
            削除成功ならTrue
        """
        try:
            keyring.delete_password(self.service_name, CREDENTIAL_KEY_NAME)
            self._fernet = None
            return True
        except keyring.errors.PasswordDeleteError:
            return False

    def encrypt(self, plaintext: str) -> str:
        """
        文字列を暗号化する。

        Args:
            plaintext: 平文

        Returns:
            暗号化済み文字列（enc:v1:{ciphertext} 形式）
        """
        fernet = self._get_fernet()
        ciphertext = fernet.encrypt(plaintext.encode('utf-8'))
        return f"{ENCRYPTION_PREFIX}{ciphertext.decode('utf-8')}"

    def decrypt(self, encrypted_value: str) -> str:
        """
        暗号化された文字列を復号する。

        Args:
            encrypted_value: 暗号化済み文字列（enc:v1:{ciphertext} 形式）

        Returns:
            復号された平文

        Raises:
            DecryptionError: 復号に失敗した場合
        """
        # 形式チェック
        if not self.is_encrypted_value(encrypted_value):
            raise DecryptionError(
                f"暗号化形式が不正です。期待形式: {ENCRYPTION_PREFIX}..."
            )

        # バージョンチェック
        version = self.get_encryption_version(encrypted_value)
        if version != ENCRYPTION_VERSION:
            raise DecryptionError(
                f"暗号化バージョンが不一致です。期待: {ENCRYPTION_VERSION}, 実際: {version}"
            )

        # 暗号文を抽出
        ciphertext = encrypted_value[len(ENCRYPTION_PREFIX):]

        try:
            fernet = self._get_fernet()
            plaintext = fernet.decrypt(ciphertext.encode('utf-8'))
            return plaintext.decode('utf-8')
        except InvalidToken:
            raise DecryptionError(
                "復号に失敗しました。鍵が異なるか、データが破損しています。"
            )

    def export_key(self, filepath: str) -> None:
        """
        鍵をファイルにエクスポートする。

        Args:
            filepath: 出力先ファイルパス

        Raises:
            KeyNotFoundError: 鍵が存在しない場合
        """
        key = self.get_key()
        if key is None:
            raise KeyNotFoundError("エクスポートする鍵が存在しません。")

        with open(filepath, 'wb') as f:
            f.write(key)

    def import_key(self, filepath: str, force: bool = False) -> None:
        """
        ファイルから鍵をインポートする。

        Args:
            filepath: 入力元ファイルパス
            force: Trueの場合、既存の鍵を上書きする

        Raises:
            EncryptionError: 既存の鍵がありforceがFalseの場合
        """
        existing_key = self.get_key()
        if existing_key is not None and not force:
            raise EncryptionError(
                "既存の暗号化鍵があります。上書きする場合は force=True を指定してください。"
            )

        with open(filepath, 'rb') as f:
            key = f.read()

        # 鍵の形式を検証
        try:
            Fernet(key)
        except Exception:
            raise EncryptionError("無効な鍵形式です。")

        keyring.set_password(
            self.service_name,
            CREDENTIAL_KEY_NAME,
            key.decode('utf-8')
        )
        self._fernet = None

    @staticmethod
    def is_encrypted_value(value: str) -> bool:
        """
        値が暗号化形式かどうかを判定する。

        Args:
            value: 判定対象の値

        Returns:
            暗号化形式（enc:v{n}:...）ならTrue
        """
        return value.startswith("enc:v") and ":" in value[5:]

    @staticmethod
    def get_encryption_version(encrypted_value: str) -> Optional[str]:
        """
        暗号化値からバージョンを抽出する。

        Args:
            encrypted_value: 暗号化済み文字列

        Returns:
            バージョン文字列（例: "v1"）。形式が不正ならNone。
        """
        if not encrypted_value.startswith("enc:"):
            return None
        parts = encrypted_value.split(":", 3)
        if len(parts) < 3:
            return None
        return parts[1]

    @staticmethod
    def is_encrypted_column_name(column_name: str) -> bool:
        """
        列名が暗号化列名形式かどうかを判定する。

        Args:
            column_name: 列名

        Returns:
            暗号化列名形式（*_enc）ならTrue
        """
        return column_name.endswith("_enc")

    @staticmethod
    def get_original_column_name(encrypted_column_name: str) -> str:
        """
        暗号化列名から元の列名を取得する。

        Args:
            encrypted_column_name: 暗号化列名（例: "メールアドレス_enc"）

        Returns:
            元の列名（例: "メールアドレス"）
        """
        if encrypted_column_name.endswith("_enc"):
            return encrypted_column_name[:-4]
        return encrypted_column_name

    @staticmethod
    def get_encrypted_column_name(column_name: str) -> str:
        """
        列名を暗号化列名形式に変換する。

        Args:
            column_name: 元の列名（例: "メールアドレス"）

        Returns:
            暗号化列名（例: "メールアドレス_enc"）
        """
        if column_name.endswith("_enc"):
            return column_name
        return f"{column_name}_enc"


def validate_encrypted_column(column_name: str, first_value: str) -> Tuple[bool, Optional[str]]:
    """
    暗号化列の整合性を検証する。

    要件定義書 v11 では「列名と値ヘッダーの両方一致で暗号化列を識別」と定義。
    片方のみ一致の場合はエラー停止。

    Args:
        column_name: 列名
        first_value: 最初の値（ヘッダー値）

    Returns:
        (is_valid, error_message) - 正常ならTrue+None、エラーならFalse+エラーメッセージ
    """
    is_enc_name = EncryptionManager.is_encrypted_column_name(column_name)
    is_enc_value = EncryptionManager.is_encrypted_value(first_value) if first_value else False

    if is_enc_name and is_enc_value:
        # 両方一致: 暗号化列として正常
        return True, None
    elif is_enc_name and not is_enc_value:
        # 列名のみ一致: 不整合エラー
        return False, (
            f"暗号化列検出エラー: 列名 '{column_name}' は暗号化形式ですが、"
            f"値が暗号化形式ではありません。ファイルが破損している可能性があります。"
        )
    elif not is_enc_name and is_enc_value:
        # 値のみ一致: 不整合エラー
        return False, (
            f"暗号化列検出エラー: 列名 '{column_name}' は通常形式ですが、"
            f"値が暗号化形式です。ファイルが破損している可能性があります。"
        )
    else:
        # どちらも不一致: 平文列として正常
        return True, None
