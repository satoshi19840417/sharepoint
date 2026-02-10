"""
テスト送信スクリプト
test_mode=trueの場合、設定されたtest_emailにテストメールを送信
"""
import sys
from pathlib import Path

# scriptsディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from scripts.main import QuoteRequestSkill


def main():
    print("=" * 60)
    print("見積依頼スキル - テスト送信")
    print("=" * 60)
    print()

    # スキル初期化
    skill = QuoteRequestSkill()

    # 設定確認
    test_email = skill.config.get("test_email", "")
    test_mode = skill.config.get("test_mode", False)
    dry_run = skill.config.get("dry_run", False)

    print(f"設定確認:")
    print(f"  test_mode: {test_mode}")
    print(f"  dry_run: {dry_run}")
    print(f"  test_email: {test_email}")
    print()

    if not test_email:
        print("エラー: test_emailが設定されていません。")
        print("config.jsonでtest_emailを設定してください。")
        sys.exit(1)

    # 暗号化鍵確認
    if not skill.ensure_encryption_key():
        print("エラー: 暗号化鍵の準備に失敗しました。")
        sys.exit(1)

    # Outlook接続確認
    outlook_check = skill.check_outlook_connection()
    if not outlook_check["connected"]:
        print(f"エラー: {outlook_check['message']}")
        sys.exit(1)

    print("[OK] Outlook接続確認: OK")
    print()

    # テストメール内容
    subject = "【テスト送信】見積依頼スキル動作確認"
    body = """お世話になっております。

こちらは見積依頼スキルのテスト送信です。

【テスト内容】
- Outlook連携の動作確認
- メール送信機能の確認
- 監査ログ機能の確認

このメールを受信できている場合、見積依頼スキルは正常に動作しています。

--
セルジェンテック株式会社
"""

    print("テストメール送信中...")
    print(f"  宛先: {test_email}")
    print(f"  件名: {subject}")
    print()

    # テスト送信実行
    result = skill.send_test(
        test_email=test_email,
        subject=subject,
        body=body
    )

    print()
    print("=" * 60)
    if result["success"]:
        print("[SUCCESS] テスト送信成功")
        print(f"  Message-ID: {result.get('message_id', 'N/A')}")
        print()
        print("受信トレイを確認してください。")
    else:
        print("[FAILED] テスト送信失敗")
        print(f"  エラー: {result.get('error', '不明なエラー')}")
    print("=" * 60)

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
