# マニュアルスライド化スキル作成計画

## Context

ユーザーからの要望により、ExcelマニュアルをPowerPointスライドに変換する機能を「マニュアルスライド化スキル」としてスキル化します。

### 背景
- 既に相見積操作マニュアルのPowerPoint変換機能を実装済み
- CellGenTechブランドに最適化されたデザインを適用
- この機能を再利用可能なスキルとして整備

### 要件
- **スキル名**: マニュアルスライド化スキル
- **使用方法**: 簡易実行（Excelファイルパス指定のみ）+ 対話形式（ステップバイステップ）
- **配置場所**: `skills/manual-to-ppt/` ディレクトリに独立配置
- **機能**: Excelマニュアル（テキスト + 画像）→ PowerPointスライド（CellGenTechデザイン）

**変換対象:**
- ファイル: `05_mail\相見積操作マニュアル.xlsx`
- 内容: 見積依頼の作成と送信に関する操作手順
- 構成: 1シートに全体がまとまっている
- 画像: マニュアル内にスクリーンショットが含まれている

**スライド要件:**
- スタイル: スクリーンショット中心の視覚的なデザイン
- 含める要素: 画面イメージ（スクリーンショット）を重視
- ページ数: 必要な情報が伝わる量（制限なし）

---

## Implementation Plan

### ステップ1: スキルディレクトリ構造の作成

`skills/manual-to-ppt/` ディレクトリに以下の構造を作成：

```
skills/manual-to-ppt/
├── SKILL.md                    # スキルドキュメント
├── main.py                     # メインエントリーポイント（対話形式）
├── scripts/
│   ├── parse_manual.py        # Excelマニュアル解析（既存コードを移動）
│   ├── generate_ppt.py        # PowerPoint生成（既存コードを移動）
│   └── converter.py           # 変換ロジック（既存のconvert_manual_to_ppt.pyを改名）
├── config/
│   └── config_template.json   # 設定テンプレート（ロゴパス、カラースキームなど）
└── requirements.txt           # 必要なライブラリ
```

**必要なライブラリ:**
- `openpyxl`: Excelファイルの読み取り、画像の抽出
- `python-pptx`: PowerPointファイルの作成
- `Pillow`: 画像処理

### ステップ2: 既存スクリプトの整理と移動

`05_mail/scripts/` から必要なスクリプトを `skills/manual-to-ppt/scripts/` に移動・整理：

1. **parse_manual.py** - そのまま移動
   - Excelマニュアル解析クラス（ExcelManualParser）
   - テキスト・画像の抽出機能

2. **generate_ppt.py** - そのまま移動
   - PowerPoint生成クラス（PowerPointGenerator）
   - CellGenTechデザイン適用済み
   - ロゴ配置、カラースキーム設定

3. **convert_manual_to_ppt.py** → **converter.py** に改名
   - 統合変換ロジック
   - ステップ情報抽出
   - 画像マッチング機能

### ステップ3: SKILL.md（スキルドキュメント）の作成

`skills/manual-to-ppt/SKILL.md` を作成：

**記載内容:**
1. **概要**: Excelマニュアルを見やすいPowerPointスライドに変換するスキル
2. **使用方法**:
   - 簡易実行: `Excelファイルパスを指定してマニュアルスライド化スキルを実行`
   - 対話形式: 段階的にファイルパスやオプションを入力
3. **入力ファイル**: Excel形式（.xlsx）、画像埋め込み対応
4. **出力**: PowerPointファイル（CellGenTechデザイン、ロゴ付き）
5. **設定オプション**: ロゴパス、カラースキーム、出力先
6. **サンプル**: 使用例のコマンド

### ステップ4: main.py（メインエントリーポイント）の作成

`skills/manual-to-ppt/main.py` を作成：

**機能:**
1. **簡易実行モード**:
   - コマンドライン引数でExcelファイルパスを受け取る
   - デフォルト設定（ロゴ自動検出、出力先同じディレクトリ）で実行

2. **対話形式モード**:
   - ユーザーに質問しながらパラメータを収集
   - Excelファイルパス入力
   - ロゴファイルパス入力（オプション、デフォルトはCellGenTechロゴ）
   - 出力ファイルパス入力（オプション）
   - タイトル・サブタイトルのカスタマイズ（オプション）

3. **エラーハンドリング**:
   - ファイル存在チェック
   - 必要なライブラリのインストール確認
   - わかりやすいエラーメッセージ

### ステップ5: config_template.json（設定テンプレート）の作成

`skills/manual-to-ppt/config/config_template.json` を作成：

**設定項目:**
```json
{
  "logo_path": "CellGenTech_Logo_20221203_Blue_Horizontal.png",
  "color_scheme": {
    "primary": "#0066CC",
    "accent": "#3399FF",
    "dark": "#003366",
    "light_bg": "#F0F8FF"
  },
  "slide_settings": {
    "width_inches": 10,
    "height_inches": 7.5,
    "logo_height_inches": 0.4
  },
  "default_output_dir": "./output"
}
```

**用途:**
- カラースキームのカスタマイズ
- ロゴのデフォルトパス設定
- スライドサイズの調整

### ステップ6: requirements.txt の作成

`skills/manual-to-ppt/requirements.txt` を作成：

```
openpyxl>=3.1.0
python-pptx>=1.0.0
Pillow>=10.0.0
```

**目的:**
- スキル実行に必要なライブラリを明示
- `pip install -r requirements.txt` で一括インストール可能

### ステップ7: スクリプトの統合とテスト

1. **インポートパスの修正**:
   - `converter.py` 内のインポート文を修正
   - `from parse_manual import ...` → `from scripts.parse_manual import ...`
   - `from generate_ppt import ...` → `from scripts.generate_ppt import ...`

2. **main.py での統合**:
   - `converter.py` の機能を呼び出し
   - コマンドライン引数のパース
   - 対話形式のユーザー入力処理

3. **動作確認**:
   - サンプルExcelファイルで変換テスト
   - 簡易実行モードと対話形式モードの両方をテスト

### ステップ8: ドキュメント整備とサンプル作成

1. **SKILL.md の完成**:
   - 使用例を追加
   - トラブルシューティングセクション
   - FAQ（よくある質問）

2. **README.md の作成**（オプション）:
   - スキルの詳細な説明
   - インストール手順
   - 開発者向けの情報

3. **サンプルファイルの配置**:
   - サンプルExcelマニュアル（必要に応じて）
   - サンプル出力PowerPoint

4. **使用例のドキュメント**:
   ```bash
   # 簡易実行
   python skills/manual-to-ppt/main.py path/to/manual.xlsx

   # 対話形式
   python skills/manual-to-ppt/main.py --interactive
   ```

---

## Critical Files

**既存ファイル（移動元）:**
- `05_mail/scripts/parse_manual.py` - Excelマニュアル解析スクリプト
- `05_mail/scripts/generate_ppt.py` - PowerPoint生成スクリプト
- `05_mail/scripts/convert_manual_to_ppt.py` - 統合実行スクリプト
- `05_mail/CellGenTech_Logo_20221203_Blue_Horizontal.png` - CellGenTechロゴ

**作成するファイル（新規）:**
- `skills/manual-to-ppt/SKILL.md` - スキルドキュメント
- `skills/manual-to-ppt/main.py` - メインエントリーポイント
- `skills/manual-to-ppt/requirements.txt` - 必要ライブラリリスト
- `skills/manual-to-ppt/config/config_template.json` - 設定テンプレート

**移動先ファイル:**
- `skills/manual-to-ppt/scripts/parse_manual.py` - 解析スクリプト（移動）
- `skills/manual-to-ppt/scripts/generate_ppt.py` - 生成スクリプト（移動）
- `skills/manual-to-ppt/scripts/converter.py` - 変換スクリプト（convert_manual_to_ppt.pyを改名）

**参考ファイル:**
- `04_AI_Study_Promo/skills/generate-presentation/SKILL.md` - スキル構造の参考
- `05_mail/SKILL.md` - 見積依頼スキルの参考

---

## Verification Plan

### 1. ライブラリのインストール確認
```bash
cd skills/manual-to-ppt
pip install -r requirements.txt
python -c "import openpyxl, pptx, PIL; print('All libraries installed successfully')"
```

### 2. 簡易実行モードのテスト
```bash
python skills/manual-to-ppt/main.py 05_mail/相見積操作マニュアル.xlsx
```
**期待される動作:**
- Excelファイルを読み込み
- 画像を抽出
- PowerPointファイルを生成（同じディレクトリに出力）
- CellGenTechロゴを自動検出して配置

### 3. 対話形式モードのテスト
```bash
python skills/manual-to-ppt/main.py --interactive
```
**期待される動作:**
- Excelファイルパスを入力
- ロゴファイルパス入力（オプション、デフォルト表示）
- 出力先パス入力（オプション）
- タイトル・サブタイトル入力（オプション）
- 変換実行

### 4. 生成されたPowerPointの確認
- タイトルスライド: CellGenTechブランドデザイン適用
- 各ステップスライド: 青のヘッダー、スクリーンショット、ロゴ配置
- カラースキーム: CellGenTechブルー (#0066CC) 統一
- レイアウト: 統一感のあるデザイン

### 5. エラーハンドリングの確認
- 存在しないファイルパスを指定した場合のエラーメッセージ
- 必要なライブラリがない場合のエラーメッセージ
- 画像が含まれないExcelファイルの処理

---

## Notes

1. **スキルの再利用性**:
   - 汎用的なマニュアル変換機能として設計
   - CellGenTechブランド以外にも適用可能（config.jsonで設定変更）

2. **既存コードの活用**:
   - `05_mail/scripts/` の既存スクリプトを最大限活用
   - 大幅な書き換えは不要、構造の整理とラッパーの追加のみ

3. **エンコーディング**:
   - Windows環境でのUnicode対応（既存スクリプトで実装済み）
   - 日本語ファイル名・テキストの完全サポート

4. **ロゴの自動検出**:
   - デフォルトで `CellGenTech_Logo_20221203_Blue_Horizontal.png` を検索
   - プロジェクトルート、スキルディレクトリ、親ディレクトリを順に探索

5. **拡張性**:
   - 将来的にカラースキームのプリセット追加可能
   - テンプレート機能の追加も検討可能（異なるレイアウトパターン）

6. **互換性**:
   - 既存の `05_mail/scripts/convert_manual_to_ppt.py` も保持
   - スキル化後も従来の方法で実行可能

---

## Summary

### スキル化の流れ

1. **ディレクトリ構造の作成**: `skills/manual-to-ppt/` に必要なフォルダを作成
2. **既存スクリプトの移動**: `05_mail/scripts/` から3つのPythonスクリプトを移動・改名
3. **SKILL.md の作成**: スキルドキュメントを作成（使用方法、サンプル）
4. **main.py の作成**: 簡易実行モードと対話形式モードを実装
5. **設定ファイルの作成**: `config_template.json` と `requirements.txt` を作成
6. **ドキュメント整備**: 使用例、トラブルシューティング、FAQを追加
7. **動作確認**: 両モードでテスト実行し、正常に動作することを確認

### スキルの特徴

- **簡単実行**: Excelファイルパスを指定するだけで自動変換
- **対話形式**: ステップバイステップでカスタマイズ可能
- **CellGenTechデザイン**: ブランドに統一されたプロフェッショナルなデザイン
- **再利用可能**: 他のExcelマニュアルにも適用可能な汎用スキル
- **拡張性**: カラースキームやレイアウトのカスタマイズに対応

この計画により、Excelマニュアル→PowerPoint変換機能が、誰でも簡単に使える再利用可能なスキルとして整備されます。
