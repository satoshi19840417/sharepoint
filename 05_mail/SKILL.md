---
name: 見積依頼スキル
description: 業者への見積依頼メール送信を自動化するスキル
---

# 見積依頼スキル

## 概要

業者への見積依頼メール送信を効率化するスキル。AIチャットを活用して最適な製品を検索し、製品情報・ホームページURLを含むメールを自動生成してOutlookから送信する。

## 使用方法

### 1. 基本的な使い方

```
見積依頼スキルを実行してください。
連絡先ファイル: ./業者連絡先_サンプル.csv
製品: 細胞培養用の96ウェルプレート、滅菌済み
```

### 2. テンプレート指定

```
見積依頼スキルを実行してください。
連絡先ファイル: ./業者連絡先.csv
テンプレート: ./見積依頼_サンプル.docx
製品: [製品名]
```

### 3. ドライラン（送信せずに確認）

```
見積依頼スキルをドライランで実行してください。
連絡先ファイル: ./業者連絡先.csv
```

### 4. 相見積改良フロー（CLI）

```bash
python 05_mail/scripts/run_aimitsu_workflow.py \
  --contacts-csv 05_mail/業者連絡先_サンプル.csv \
  --product-name "検証製品A" \
  --product-url "https://example.com/product" \
  --maker-code "TEST-001" \
  --workflow-mode enhanced \
  --send-mode draft_only \
  --hearing-input 05_mail/temp/aimitsu_smoke/hearing_enhanced_draft_only.json
```

## 入力ファイル

| ファイル | 形式 | 説明 |
|----------|------|------|
| 連絡先ファイル | CSV | 必須列: `会社名`, `メールアドレス`（Outlook形式対応） |
| テンプレート | docx/txt | オプション。差し込み変数: `«会社名»` または `{{会社名}}` |

## 設定（config.json）

| 項目 | 説明 | デフォルト |
|------|------|-----------|
| `max_recipients` | 1回の最大送信件数 | 50 |
| `send_interval_sec` | 送信間隔（秒） | 3 |
| `dry_run` | ドライランモード | false |
| `domain_whitelist` | 許可ドメインリスト | [] |
| `domain_blacklist` | 拒否ドメインリスト | [] |
| `dedupe_key_version` | 再実行判定キーのバージョン | `"v2"` |
| `rerun_policy_default` | 再実行検知時の既定動作 | `"auto_skip"` |
| `rerun_scope` | 再実行判定範囲 | `"global"` |
| `rerun_window_hours` | 再実行ブロック時間 | `24` |
| `ledger_sqlite_path` | 送信台帳SQLiteパス | `./logs/send_ledger.sqlite3` |
| `workflow_mode_default` | ワークフロー既定値 | `"legacy"` |
| `send_mode_default` | 送信モード既定値 | `"auto"` |
| `request_history_retention_days` | 実行履歴保持日数 | `365` |
| `hmac_rotation_days` | 履歴HMAC鍵ローテーション日数 | `180` |

## 出力

- **画面表示**: 送信結果サマリ（メールアドレスはマスク表示）
- **監査ログ**: `./logs/` に暗号化保存
- **未送信リスト**: 失敗時に自動生成（再実行に使用可能）
- **草案Markdown**: `./outputs/drafts`（完了時は `./outputs/completed`、失敗/ブロック時は `./outputs/error`）
- **手動証跡**: `./outputs/manual_evidence/{request_id}/manual_send_evidence_{run_id}.json`
- **実行履歴**: `./logs/request_history/{request_id}/{run_id}.json`

## 相見積改良フローの運用注意

- 初期導入は `workflow_mode_default=legacy` のまま運用し、対象ジョブのみ `--workflow-mode enhanced` を付与する。
- `enhanced + manual` は証跡JSONが一致しない限り `completed` に遷移しない。
- `enhanced + draft_only` は `user_approved=true` がないと完了扱いにならない。
- 送信先変更時と送信直前の2回、安全機能（ドメイン制限・重複送信防止）を再評価する。

## 安全機能

- テスト送信モード（初回は自分宛に送信）
- ドメイン制限（ホワイトリスト/ブラックリスト）
- 二重送信防止（`request_key` + SQLite台帳 + 24h判定）
- UNKNOWN_SENT 回復（ヘッダHMAC/本文マーカー照合）
- scoped override（`rerun_override.py` で key/recipient 単位許可）
- PII混入防止（検索クエリのチェック）

## 関連ファイル

- [要件定義書](./見積依頼スキル_要件定義書.md)
- [サンプルテンプレート](./見積依頼_サンプル.docx)
- [サンプル連絡先](./業者連絡先_サンプル.csv)
