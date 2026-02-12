# AGENT.md

## 目的
このリポジトリは、SharePointリスト化プロジェクトの設計資料・運用資料・自動化スクリプトを管理する。
主要対象は `01_Documents` と `02_Scripts`、補助的に `05_mail`（見積依頼スキル）と `04_AI_Study_Promo`（Remotion動画）。

## まず確認するファイル
1. `01_Documents/README.md`（全体導線）
2. `01_Documents/00_Overview/SharePointリスト化全体計画.md`（フェーズ状況）
3. `01_Documents/00_Overview/実施済み作業一覧.md`（完了履歴・次タスク）
4. `01_Documents/00_Overview/計画書レビュー運用ルール.md`（指摘まとめ運用）
5. `plans/precious-whistling-puddle.md`（Phase5準備の実装計画）

## ディレクトリ要約
- `01_Documents/`
  - `00_Overview/`: 全体計画、進捗、運用ルール
  - `01_Phases/`: Phase5〜8の計画書・手順書・指摘まとめ
  - `02_Templates/`: Word/Excel/CSVテンプレート
  - `03_DataSamples/`: サンプルデータ
  - `04_Reference/`: 列定義や参照メモ
- `02_Scripts/`
  - SharePoint操作用PowerShell（PnP.PowerShell）
- `03_Release/`
  - 配布用zip（現行: `automation_1_1_0_2.zip`）
- `04_AI_Study_Promo/`
  - Remotion/React の独立したNodeプロジェクト
- `05_mail/`
  - 見積依頼スキル（Python、Outlook連携、testsあり）
- `99_Archive/`
  - 過去資料（原則、明示依頼がない限り編集しない）

## 作業ルール（このリポジトリ固有）
- Phase計画書のレビュー指摘は、同一フォルダ内の `*_指摘まとめ.md` に記録する。
- 指摘まとめには最低限「日付」「対象ファイル」「指摘事項」「推奨対応」を含める。
- ドキュメント移動・改名時は相対リンクの整合を必ず確認する。
- 状況確認依頼（例: 「次のタスク」）では `01_Documents/README.md` と `00_Overview` を優先参照する。

## タスク別の主作業場所
- SharePoint列・リスト作成/更新: `02_Scripts/*.ps1`
- Phase計画・手順の更新: `01_Documents/01_Phases/*`
- 見積依頼メール機能: `05_mail/scripts/*` と `05_mail/tests/*`
- 動画・プレゼン生成: `04_AI_Study_Promo/*`

## 実行コマンド（代表）
- Pythonテスト（見積依頼スキル）:
  - `python -m pytest 05_mail/tests`
  - `python 05_mail/tests/run_tc_suite.py`
- テスト送信:
  - `python 05_mail/test_send.py`
- Remotion:
  - `cd 04_AI_Study_Promo && npm run start`
  - `cd 04_AI_Study_Promo && npm run build`

## 前提環境
- Windows + PowerShell
- SharePoint操作時: `PnP.PowerShell` と認証（Interactive / DeviceLogin）
- 見積依頼スキル: Outlookクライアント、Python依存 (`05_mail/requirements.txt`)
- Remotion: Node.js + npm

## 触らない/慎重に扱う領域
- 生成物・大容量ディレクトリは不要な差分を出さない:
  - `04_AI_Study_Promo/node_modules/`
  - `04_AI_Study_Promo/out/`
  - `05_mail/logs/`
  - `05_mail/test_artifacts/`
- 既存アーカイブ `99_Archive/` は、依頼がない限り変更しない。

## 変更後チェック
- 変更対象のMarkdownリンクが切れていないか
- `git status` で意図しない差分がないか
- 実行したコマンド/検証結果を、必要に応じて関連ドキュメントへ反映したか
