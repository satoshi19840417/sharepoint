# wild-wobbling-pine 指摘まとめ

## 2026-02-13
- 対象ファイル: `plans/wild-wobbling-pine.md`
- 最終更新日: 2026-02-13 10:53:38

### 指摘事項
1. [重大] 互換性要件と移行手順が矛盾しています。計画では `05_mail/scripts` 配下3ファイルの移動・改名を前提にしていますが、Notesでは従来実行の互換性維持を宣言しています。現行の `05_mail/scripts/convert_manual_to_ppt.py` は同ディレクトリの `parse_manual.py` と `generate_ppt.py` を直接 import しているため、単純移動すると従来実行は壊れます（`plans/wild-wobbling-pine.md:57`, `plans/wild-wobbling-pine.md:68`, `plans/wild-wobbling-pine.md:283`, `05_mail/scripts/convert_manual_to_ppt.py:25`）。
2. [重大] import 方針の実行条件が未定義です。`converter.py` の import を `from scripts.parse_manual ...` へ変更する指示はありますが、どの実行形態で保証するか（`python skills/manual-to-ppt/main.py` 固定か、`-m` 実行か）が決まっていません。呼び出し方次第で `ModuleNotFoundError` のリスクがあります（`plans/wild-wobbling-pine.md:152`, `plans/wild-wobbling-pine.md:185`）。
3. [中] 出力先のデフォルト仕様が不整合です。`main.py` の説明では「入力ファイルと同じディレクトリ出力」、`config_template.json` では `./output` がデフォルトになっており、優先順位が未定義です（`plans/wild-wobbling-pine.md:94`, `plans/wild-wobbling-pine.md:127`, `plans/wild-wobbling-pine.md:234`）。
4. [中] `config_template.json` を作る計画はあるものの、読み込み・適用フローが明記されていません。現状の手順だと設定ファイルが実質未使用で終わる可能性があります（`plans/wild-wobbling-pine.md:108`, `plans/wild-wobbling-pine.md:131`, `plans/wild-wobbling-pine.md:157`）。
5. [中] 検証計画が手動確認中心で、回帰検知が弱いです。期待値が見た目ベースに寄っており、ステップ抽出数・生成スライド数・失敗時終了コードなど機械判定できる合格条件が不足しています（`plans/wild-wobbling-pine.md:248`, `plans/wild-wobbling-pine.md:254`）。

### 推奨対応
1. 「移動」ではなく「共通モジュール化 + 既存側は薄いラッパー化」に変更し、旧パス互換を明示してください。
2. 実行方式を1つに固定し、import 方式（相対/絶対）と起動コマンドをセットで定義してください。
3. 出力先・ロゴ・配色の設定優先順位（CLI > config > default）を仕様として明文化してください。
4. `config_template.json` のロード処理をステップ4または7に追加し、未設定時フォールバックも記載してください。
5. 最低限の自動テスト（正常系1件、異常系2件）を検証計画へ追加してください。

## 2026-02-13（再レビュー）
- 対象ファイル: `plans/wild-wobbling-pine.md`
- 最終更新日: 2026-02-13 10:53:38

### 指摘事項
1. [重大] 前回レビューからの修正差分を確認できません。計画本文に、前回の重大指摘（互換性矛盾・import実行条件未定義）を解消する記述追加が見当たりません（`plans/wild-wobbling-pine.md:57`, `plans/wild-wobbling-pine.md:68`, `plans/wild-wobbling-pine.md:152`, `plans/wild-wobbling-pine.md:283`）。
2. [中] 中優先度指摘（出力先デフォルト不整合、config適用フロー未定義、検証の機械判定不足）も未解消です（`plans/wild-wobbling-pine.md:94`, `plans/wild-wobbling-pine.md:108`, `plans/wild-wobbling-pine.md:127`, `plans/wild-wobbling-pine.md:248`）。

### 推奨対応
1. 前回指摘の5項目を計画本文へ直接反映し、該当箇所に「方針」「実行コマンド」「優先順位ルール」「合格基準」を明記してください。
2. 次回レビュー依頼時は、修正した章タイトルまたは行番号帯を併記してください（差分確認が速くなります）。

## 2026-02-13（再レビュー2）
- 対象ファイル: `plans/wild-wobbling-pine.md`
- 最終更新日: 2026-02-13 10:53:38

### 指摘事項
1. [重大] 対象計画書の更新差分を確認できません。前回と同一更新時刻・同一内容のため、重大指摘2件（互換性矛盾、import実行条件未定義）は未解消のままです（`plans/wild-wobbling-pine.md:57`, `plans/wild-wobbling-pine.md:68`, `plans/wild-wobbling-pine.md:152`, `plans/wild-wobbling-pine.md:283`）。
2. [中] 中優先度の3件（出力先デフォルト整合、config適用フロー、検証の機械判定基準）も未反映です（`plans/wild-wobbling-pine.md:94`, `plans/wild-wobbling-pine.md:108`, `plans/wild-wobbling-pine.md:127`, `plans/wild-wobbling-pine.md:248`）。

### 推奨対応
1. 修正対象が別ファイルの場合は正しいパスを指定してください。
2. `plans/wild-wobbling-pine.md` を修正した場合は保存後に再レビューを依頼してください（更新時刻が変わることを確認）。

## 2026-02-13（再レビュー3）
- 対象ファイル: `plans/wild-wobbling-pine.md`
- 最終更新日: 2026-02-13 11:19:40

### 指摘事項
1. [中] 互換import検証コマンドの実行前提が不足しています。計画記載の `python -c "from convert_manual_to_ppt import ..."` はプロジェクトルート実行では `ModuleNotFoundError` となり、`05_mail/scripts` での実行時のみ成立します。検証手順に作業ディレクトリまたは `PYTHONPATH` 条件を明記してください（`plans/wild-wobbling-pine.md:216`）。
2. [軽微] 正常系の合格条件 `steps_count` / `slides_count` の取得方法が未定義です。観測方法（ログ出力、戻り値、生成物解析スクリプト等）を1行でよいので追記すると、実装者の判断ブレを防げます（`plans/wild-wobbling-pine.md:188`, `plans/wild-wobbling-pine.md:189`）。

### 推奨対応
1. 互換import回帰テストを以下のように明示してください。例: `cd 05_mail/scripts && python -c "from convert_manual_to_ppt import convert_excel_to_ppt; print(callable(convert_excel_to_ppt))"`。
2. `steps_count` と `slides_count` の算出元（例: converterのサマリーJSON）を Verification Plan に追記してください。

## 2026-02-13（再レビュー4）
- 対象ファイル: `plans/wild-wobbling-pine.md`
- 最終更新日: 2026-02-13 11:23:43

### 指摘事項
1. 新規指摘なし（前回の未解消2件は反映確認済み）。

### 推奨対応
1. 計画書レビューは完了。次フェーズで実装に着手して問題ありません。
