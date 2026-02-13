# マニュアルスライド化スキル作成計画（再レビュー反映版）

## Context

ユーザー要望に基づき、ExcelマニュアルをPowerPointへ変換する機能を「マニュアルスライド化スキル」として整備する。
本計画は 2026-02-13 の再レビュー指摘（重大2件・中3件）を反映した決定版である。

### 背景
- 既存の変換処理は `05_mail/scripts/convert_manual_to_ppt.py` を起点に実装済み
- 既存処理は `05_mail/scripts/parse_manual.py` と `05_mail/scripts/generate_ppt.py` に依存
- 今回はスキル化しつつ、既存利用者を壊さない互換運用が必要

### 要件
- スキル名: マニュアルスライド化スキル
- 正式実行方式: `python skills/manual-to-ppt/main.py <excel_path>`
- 実行モード: 簡易実行 + 対話形式
- 配置先: `skills/manual-to-ppt/`
- 変換対象: Excelマニュアル（テキスト + 埋め込み画像）
- 出力: CellGenTechデザインのPowerPoint

---

## Implementation Plan

### ステップ1: スキル構成のパッケージ化

`skills/manual-to-ppt/` は `manual_to_ppt` パッケージを中心に構成する。

```text
skills/manual-to-ppt/
├── SKILL.md
├── main.py
├── requirements.txt
├── config/
│   └── config_template.json
└── manual_to_ppt/
    ├── __init__.py
    ├── parse_manual.py
    ├── generate_ppt.py
    ├── converter.py
    └── config_loader.py
```

実装責務:
- `main.py`: 正式CLI入口（引数処理、対話入力、終了コード制御）
- `manual_to_ppt/converter.py`: 変換フロー本体
- `manual_to_ppt/config_loader.py`: 設定読込と優先順位解決

### ステップ2: 共通モジュール化 + 互換ラッパー化

方針を「移動・改名」から「共通化 + 互換維持」へ変更する。

1. 共通実装は `skills/manual-to-ppt/manual_to_ppt/` に集約する。
2. 既存導線 `05_mail/scripts/` は削除しない。
3. `05_mail/scripts/convert_manual_to_ppt.py` は薄いラッパーとして保持し、以下を維持する。
- 旧CLI実行: `python 05_mail/scripts/convert_manual_to_ppt.py`
- 旧import: `from convert_manual_to_ppt import convert_excel_to_ppt`
4. 必要に応じて `05_mail/scripts/parse_manual.py` と `05_mail/scripts/generate_ppt.py` も薄いラッパー化し、既存import互換を維持する。

### ステップ3: SKILL.md の整備

`skills/manual-to-ppt/SKILL.md` に以下を明記する。
- 概要と対象入力
- 正式コマンド（`main.py` 固定）
- 対話モードの使い方
- 設定ファイル利用方法（`--config`）
- 旧導線互換の扱い（非推奨だが維持）

### ステップ4: main.py（正式エントリーポイント）

`main.py` は唯一の正式入口とする。

必須仕様:
1. 正式起動:
- `python skills/manual-to-ppt/main.py <excel_path>`
2. 対話起動:
- `python skills/manual-to-ppt/main.py --interactive`
3. サポート引数:
- `--output <pptx>`
- `--output-dir <dir>`
- `--logo <path>`
- `--config <json>`
- `--interactive`
4. エラー制御:
- 入力/設定不備は終了コード `2`
- 変換処理失敗は終了コード `1`
- 成功時は終了コード `0`

注記:
- `converter.py` の直実行はサポート外と明記する。

### ステップ5: config_template.json の読込・適用フロー定義

`config/config_template.json` は雛形として作成し、実運用では `--config` または既定配置設定を読む。

優先順位（固定）:
- `output_path`: `--output` > `--output-dir` > `config.default_output_dir` > 入力Excelと同じディレクトリ
- `logo_path`: `--logo` > `config.logo_path` > 自動探索 > なし
- `color_scheme`: `config.color_scheme` > 内部デフォルト

フォールバック規則:
- config未指定: デフォルト値で継続
- config不正JSON/型不正: エラー終了（終了コード `2`）

### ステップ6: requirements.txt の明確化

`skills/manual-to-ppt/requirements.txt`:

```text
openpyxl>=3.1.0
python-pptx>=1.0.0
Pillow>=10.0.0
```

### ステップ7: import 方針の固定

`ModuleNotFoundError` 回避のため、import規約を固定する。

- `main.py` / `converter.py` は `manual_to_ppt` 絶対importを使用
- `from scripts.parse_manual ...` / `from scripts.generate_ppt ...` は新構成側で使用しない
- 実行保証範囲は `main.py` 起動時に限定して明記

### ステップ8: ドキュメント整備

- `SKILL.md` にトラブルシューティングを追加
- 使用例を正式コマンドに統一
- 互換導線は「維持対象だが推奨入口ではない」と明記

### ステップ9: レビュー容易化のための改訂履歴追記

本文末に `## Revision Scope (2026-02-13 再レビュー反映)` を追加し、今回変更した章を列挙する。

---

## Public APIs / Interfaces

### 正式CLI

```bash
python skills/manual-to-ppt/main.py <excel_path> [--output <pptx>] [--output-dir <dir>] [--logo <path>] [--config <json>] [--interactive]
```

### 終了コード
- `0`: 成功
- `1`: 変換処理失敗
- `2`: 入力/設定バリデーション失敗

### 互換保証
- 旧CLIは継続実行可能: `python 05_mail/scripts/convert_manual_to_ppt.py`
- 旧importは継続利用可能: `from convert_manual_to_ppt import convert_excel_to_ppt`

---

## Critical Files

### 新規作成
- `skills/manual-to-ppt/SKILL.md`
- `skills/manual-to-ppt/main.py`
- `skills/manual-to-ppt/requirements.txt`
- `skills/manual-to-ppt/config/config_template.json`
- `skills/manual-to-ppt/manual_to_ppt/__init__.py`
- `skills/manual-to-ppt/manual_to_ppt/parse_manual.py`
- `skills/manual-to-ppt/manual_to_ppt/generate_ppt.py`
- `skills/manual-to-ppt/manual_to_ppt/converter.py`
- `skills/manual-to-ppt/manual_to_ppt/config_loader.py`

### 互換ラッパーとして更新
- `05_mail/scripts/convert_manual_to_ppt.py`
- `05_mail/scripts/parse_manual.py`（必要時）
- `05_mail/scripts/generate_ppt.py`（必要時）

### 既存参照のみ
- `05_mail/相見積操作マニュアル.xlsx`
- `05_mail/CellGenTech_Logo_20221203_Blue_Horizontal.png`

---

## Verification Plan

### 1. 正常系: 変換成功

```bash
python skills/manual-to-ppt/main.py 05_mail/相見積操作マニュアル.xlsx
```

合格条件:
- 終了コード `0`
- `steps_count > 0`
- `slides_count == steps_count + 1`
- 出力 `.pptx` が存在
- `steps_count` / `slides_count` は `main.py` のサマリーJSONログ（例: `{"steps_count":3,"slides_count":4}`）を算出元として判定する

### 2. 異常系: 入力ファイル不存在

```bash
python skills/manual-to-ppt/main.py 05_mail/not_found.xlsx
```

合格条件:
- 終了コード `2`
- 入力ファイル不正を示すエラーメッセージが出力される

### 3. 異常系: config不正

```bash
python skills/manual-to-ppt/main.py 05_mail/相見積操作マニュアル.xlsx --config skills/manual-to-ppt/config/invalid.json
```

合格条件:
- 終了コード `2`
- 設定読込失敗を示すエラーメッセージが出力される

### 4. 回帰系: 旧CLI + 旧import互換

```bash
python 05_mail/scripts/convert_manual_to_ppt.py
cd 05_mail/scripts && python -c "from convert_manual_to_ppt import convert_excel_to_ppt; print(callable(convert_excel_to_ppt))"
```

合格条件:
- `ModuleNotFoundError` が発生しない
- 旧CLI実行が継続可能
- 旧importが成功する

---

## Notes

1. 既存利用者保護を優先し、`05_mail/scripts` 導線は廃止しない。
2. 新規開発・運用の入口は `skills/manual-to-ppt/main.py` に一本化する。
3. デフォルト出力先は「入力Excelと同一ディレクトリ」で統一する。
4. 設定優先順位は `CLI > config > default` を厳守する。
5. 検証は機械判定を必須化し、目視確認は補助扱いとする。

---

## Acceptance Criteria

- 重大2件・中3件に対応する仕様が本文へ明示されている。
- 旧記述の矛盾（移動前提と互換維持の同居、import条件未定義、設定優先順位未定義）が解消されている。
- 実装者が本計画のみで追加判断なく着手できる。

---

## Assumptions and Defaults

- 既存導線互換（旧CLI + 旧import）は維持する。
- config指定は任意で、未指定時はフォールバックで実行可能とする。
- 本計画の対象は計画文書更新であり、コード変更は次フェーズとする。

---

## Summary

### スキル化の流れ

1. `manual_to_ppt` パッケージ構成を作成
2. 共通モジュール化と互換ラッパー化を実施
3. `main.py` 正式入口を固定
4. config読込フローと優先順位を明文化
5. 機械判定ベースの検証計画へ更新
6. ドキュメントと改訂履歴を整備

### スキルの特徴

- 正式入口が明確で実行条件がぶれない
- 旧運用を壊さずに新構成へ移行できる
- 設定解決ルールが明文化され運用判断が不要
- 回帰検知可能な検証基準を持つ

---

## Revision Scope (2026-02-13 再レビュー反映)

今回更新した章:
- `## Implementation Plan`（ステップ1-9）
- `## Public APIs / Interfaces`（新設）
- `## Critical Files`（全面更新）
- `## Verification Plan`（全面更新）
- `## Notes`（整合更新）
- `## Acceptance Criteria`（新設）
- `## Assumptions and Defaults`（整合更新）
- `## Summary`（全面更新）


