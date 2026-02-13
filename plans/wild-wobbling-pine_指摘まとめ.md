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
