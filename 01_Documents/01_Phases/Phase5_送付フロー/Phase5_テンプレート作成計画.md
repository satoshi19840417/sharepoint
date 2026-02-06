# Phase 5 テンプレート作成計画

**作成日**: 2026年1月30日  
**最終更新**: 2026年1月30日 17:19  
**対象タスク**: 発注書Wordテンプレート / 請書Excelテンプレート作成

---

## 現状分析

### 現在使用中のファイル

**ファイル**: `CGT発注書_サンプル.xlsx`（`01_Documents/03_DataSamples/`）

| シート名 | 用途 | テンプレート化 |
|----------|------|----------------|
| 発注依頼票 | 社内申請用（入力シート） | × 対象外 |
| 発注書 | 業者送付用（PDF化）| ✅ **Wordテンプレート** |
| 発注請書 | 業者返送用（編集可能）| ✅ **Excelテンプレート** |

---

## 差し込みフィールド定義（Content Control方式）

> [!IMPORTANT]
> Power Automate「Populate a Microsoft Word template」はContent Control必須。`<<フィールド名>>`形式は使用不可。

### Wordテンプレート Content Control一覧

| Control名 | SP内部名 | データ元 | 型 |
|-----------|----------|----------|-----|
| Title | Title | SharePointリスト | 文字列 |
| ItemName | ItemName | SharePointリスト | 文字列 |
| Manufacturer | Manufacturer | SharePointリスト | 文字列 |
| Quantity | Quantity | SharePointリスト | 数値 |
| EstimatedAmount | EstimatedAmount | SharePointリスト | 通貨 |
| DeliveryAddress | DeliveryAddress | SharePointリスト | 文字列 |
| QuoteNumber | QuoteNumber | SharePointリスト | 文字列 |
| VendorName | VendorName | 業者マスタ結合 | 文字列 |
| OrderDate | （自動生成） | フロー実行日 | 日付 |

### Excelテンプレート プレースホルダー一覧

| セル位置 | プレースホルダー名 | データ元 | 備考 |
|---------|-------------------|----------|------|
| B3 | VendorName | 業者マスタ結合 | 宛先 |
| G5 | OrderDate | フロー実行日 | 発注日 |
| B10 | ItemName | SharePointリスト | 品目 |
| C10 | Manufacturer | SharePointリスト | メーカー |
| D10 | Quantity | SharePointリスト | 数量 |
| E10 | **（計算式保持）** | =EstimatedAmount/Quantity | 単価（算出） |
| F10 | EstimatedAmount | SharePointリスト | 金額（見積額） |
| F31 | **（計算式保持）** | =SUM(...) | 小計 |
| F32 | **（計算式保持）** | =F31*0.1 | 消費税 |
| F33 | **（計算式保持）** | =F31+F32 | 合計 |

---

## 業者マスタ結合手順

### SharePointリストに必要な列（追加済み前提）

| 列名 | 内部名 | 型 | 用途 |
|------|--------|-----|------|
| 業者ID | VendorID | テキスト | 業者マスタとの結合キー |

### フロー内結合ロジック

```
1. トリガー: SharePointリストの SendStatus = 送付中
2. 業者マスタCSV読込: SharePoint「/Shared 01_Documents/マスタ/業者連絡先.csv」
3. フィルタ: CSV.VendorID = SPリスト.VendorID
4. マッチ時: VendorName, VendorEmail を変数に格納
5. 不一致時: SendStatus=エラー、ErrorLog追記、処理中断
6. 差し込み実行: Word/Excelテンプレートに変数を埋め込み
```

---

## Excelテンプレート セル区分・保護設計

### セル区分

| 区分 | 対象セル | 編集許可 | 備考 |
|------|---------|----------|------|
| 差し込み入力セル | B3, G5, B10, C10, D10, F10 | ロック（自動入力） | フロー差し込み対象 |
| 計算セル | E10, F31, F32, F33 | ロック | 数式保持 |
| 業者入力セル | G10:G20（納期・備考欄）, B35（担当者サイン） | **編集可** | 業者が入力 |

### シート保護設定

| 項目 | 設定値 |
|------|--------|
| 保護パスワード | （なし：編集範囲のみ制御） |
| 編集許可範囲 | G10:G20（納期・備考欄）, B35（担当者サイン欄） |
| 入力規則 | G10:G15: 日付形式、G16:G20: テキスト |
| その他セル | ロック（編集不可） |

---

## Proposed Changes

### テンプレートファイル

#### [NEW] `01_Documents/02_Templates/発注書テンプレート.docx`
- Content Control方式で差し込みフィールド埋め込み
- コントロール名はSP内部名に統一

#### [NEW] `01_Documents/02_Templates/請書テンプレート.xlsx`
- 計算セル（小計・税・合計）は数式保持
- 業者入力欄（納期・サイン）のみ編集許可
- シート保護設定済み

---

## 実装手順

### Step 1: 発注書Wordテンプレート作成

1. 新規Word文書作成
2. 現在のExcel「発注書」レイアウトを再現
3. **Content Control挿入**（開発タブ→プレーンテキストコンテンツコントロール）
4. コントロールのプロパティで「タイトル」をSP内部名に設定
5. SharePointにアップロード

### Step 2: 請書Excelテンプレート作成

1. 現在の「発注請書」シートをコピー
2. **差し込みセル**: 数式参照→プレースホルダー文字列に変更
3. **計算セル**: 数式をそのまま保持
4. **業者入力セル**: G10:G20（納期・備考欄）, B35（サイン）を入力可に設定
5. シート保護を適用（業者入力セル以外をロック）
6. SharePointにアップロード

---

## Verification Plan

### E2Eテスト手順

| # | テスト項目 | 手順 | 合格基準 |
|---|-----------|------|----------|
| 1 | Word差し込み | テストデータでフロー実行 | 全コントロールに正しい値が挿入される |
| 2 | PDF変換 | Word→PDF変換 | レイアウト崩れなし、文字化けなし |
| 3 | Excel差し込み | テストデータでフロー実行 | プレースホルダーが正しく置換される |
| 4 | 計算式確認 | 差し込み後のExcelを開く | 小計・税・合計が正しく計算される |
| 5 | 保護確認 | 業者視点でExcel編集 | 納期・サイン欄のみ編集可、他はロック |
| 6 | 業者マスタ不一致 | 存在しないVendorIDでテスト | SendStatus=エラー、ErrorLog記録 |

### 受入基準

- [ ] 生成PDF: 現在のサンプル帳票とレイアウト一致
- [ ] 生成Excel: 業者入力欄のみ編集可能
- [ ] 業者マスタ不一致時: エラー処理が正常動作
- [ ] 受領環境互換性: Excel 2016以降で表示崩れなし

---

## 次のアクション

計画承認後、テンプレート作成を開始します。
