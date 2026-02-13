# 相見積自動送信プロジェクト改良 実装計画書（要件定義書 v4 準拠）

本計画書は `05_mail/相見積自動送信プロジェクト改良_要件定義書.md` に基づく実装・試験・移行の実施方針を示す。

## 対象
- `workflow_mode` 判定（`enhanced`/`legacy`）
- `send_mode` 分岐（`auto`/`manual`/`draft_only`）
- Markdown草案出力・命名・保管
- 安全機能再評価（送信先確定時 / 送信直前）
- 完了判定・フォルダ移動制御
- 手動証跡検証
- `request_id` / `run_id`・実行履歴・HMAC鍵管理
- AC-01..AC-10 受入試験

## 実装方針
1. 既存 `send_bulk` API は後方互換維持。
2. 新規ワークフローは `run_aimitsu_workflow.py` と `workflow_service.py` に分離。
3. 履歴保存は `logs/request_history/{request_id}/{run_id}.json` の 1 実行 1 ファイル。
4. `workflow_mode_default` は `legacy` 固定。
5. 非完了状態は `outputs/completed` へ移動しない。

## 主要成果物
- `05_mail/scripts/run_aimitsu_workflow.py`
- `05_mail/scripts/workflow_service.py`
- `05_mail/scripts/workflow_types.py`
- `05_mail/scripts/draft_repository.py`
- `05_mail/scripts/manual_evidence_validator.py`
- `05_mail/scripts/request_history_store.py`
- `05_mail/scripts/hmac_key_manager.py`
- `05_mail/tests/run_aimitsu_acceptance.py`

## 試験
- 単体: `python -m pytest 05_mail/tests -q`
- 回帰: `python 05_mail/tests/run_tc_suite.py --stage all`
- 受入: `python 05_mail/tests/run_aimitsu_acceptance.py`

## 移行
1. 初期リリースは `workflow_mode_default=legacy`。
2. `enhanced` は `--workflow-mode enhanced` 指定時のみ有効。
3. 問題時は `legacy` に切替え、生成物は `outputs/error` へ隔離。

