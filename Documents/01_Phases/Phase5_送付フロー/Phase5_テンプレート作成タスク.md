# Phase 5 テンプレート作成 タスク管理表

**作成日**: 2026年1月30日  
**計画書**: [implementation_plan.md](./implementation_plan.md)

---

## Step 1: 発注書Wordテンプレート作成

- [ ] 新規Word文書作成
- [ ] Excel「発注書」シートのレイアウト再現
- [ ] Content Control挿入（9フィールド）
  - [ ] Title
  - [ ] ItemName
  - [ ] Manufacturer
  - [ ] Quantity
  - [ ] EstimatedAmount
  - [ ] DeliveryAddress
  - [ ] QuoteNumber
  - [ ] VendorName
  - [ ] OrderDate
- [ ] コントロールプロパティでタイトルをSP内部名に設定
- [ ] SharePointにアップロード

---

## Step 2: 請書Excelテンプレート作成

- [ ] 「発注請書」シートをコピー
- [ ] 差し込みセル変更
  - [ ] B3 → VendorName プレースホルダー
  - [ ] G5 → OrderDate プレースホルダー
  - [ ] B10 → ItemName プレースホルダー
  - [ ] C10 → Manufacturer プレースホルダー
  - [ ] D10 → Quantity プレースホルダー
  - [ ] F10 → EstimatedAmount プレースホルダー
- [ ] 計算セル確認（E10, F31, F32, F33の数式保持）
- [ ] 業者入力セル設定（G10:G20, B35）
- [ ] シート保護適用
  - [ ] 編集許可範囲設定
  - [ ] 入力規則設定（G10:G15は日付、G16:G20はテキスト）
- [ ] SharePointにアップロード

---

## Step 3: 検証

- [ ] Word差し込みテスト
- [ ] PDF変換テスト
- [ ] Excel差し込みテスト
- [ ] 計算式確認
- [ ] シート保護確認
- [ ] 業者マスタ不一致テスト
- [ ] Excel 2016互換性確認（表示崩れ・機能動作）

---

## 受入基準

- [ ] 生成PDF: サンプル帳票とレイアウト一致
- [ ] 生成Excel: 業者入力欄のみ編集可能
- [ ] 業者マスタ不一致時: エラー処理正常動作
- [ ] 受領環境互換性: Excel 2016以降で表示崩れなし
