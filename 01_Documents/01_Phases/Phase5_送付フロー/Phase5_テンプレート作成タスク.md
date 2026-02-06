# Phase 5 テンプレート作成 タスク管理表

**作成日**: 2026年1月30日  
**計画書**: [implementation_plan.md](./implementation_plan.md)

---

## Step 1: 発注書Wordテンプレート作成

- [x] 新規Word文書作成
- [x] Excel「発注書」シートのレイアウト再現
- [x] Content Control挿入（9フィールド）
  - [x] Title
  - [x] ItemName
  - [x] Manufacturer
  - [x] Quantity
  - [x] EstimatedAmount
  - [x] DeliveryAddress
  - [x] QuoteNumber
  - [x] VendorName
  - [x] OrderDate
- [x] コントロールプロパティでタイトルをSP内部名に設定
- [x] SharePointにアップロード（※ローカルに `発注書テンプレート.docx` 作成完了、アップロードは手動）

---

## Step 0: テンプレート二重化対応（2026/02/04 追記）

- [ ] Backupsから重複のないテンプレートを復元
- [ ] `modify_word_template.py` を冪等化（既存ヘッダー/挨拶文/発注依頼者行がある場合は追加しない）
- [ ] `create_test_samples.py` で再生成し、Wordで重複がないことを確認

---

## Step 2: 請書Excelテンプレート作成

- [x] 「発注請書」シートをコピー
- [x] 差し込みセル変更
  - [x] B3 → VendorName プレースホルダー
  - [x] G5 → OrderDate プレースホルダー
  - [x] B10 → ItemName プレースホルダー
  - [x] C10 → Manufacturer プレースホルダー
  - [x] D10 → Quantity プレースホルダー
  - [x] F10 → EstimatedAmount プレースホルダー
- [x] 計算セル確認（E10, F31, F32, F33の数式保持）
- [x] 業者入力セル設定（G10:G20, B35）
- [x] シート保護適用
  - [x] 編集許可範囲設定
  - [x] 入力規則設定（G10:G15は日付、G16:G20はテキスト）
- [x] SharePointにアップロード（※ローカルに `請書テンプレート.xlsx` 作成完了、アップロードは手動）

---

## Step 3: 検証

- [x] Word差し込みテスト（シミュレーション完了: TestOutput参照）
- [ ] PDF変換テスト
- [x] Excel差し込みテスト（シミュレーション完了: TestOutput参照）
- [x] 計算式確認
- [x] シート保護確認
- [ ] 業者マスタ不一致テスト
- [ ] Excel 2016互換性確認（表示崩れ・機能動作）

---

## 受入基準

- [ ] 生成PDF: サンプル帳票とレイアウト一致
- [ ] 生成Excel: 業者入力欄のみ編集可能
- [ ] 業者マスタ不一致時: エラー処理正常動作
- [ ] 受領環境互換性: Excel 2016以降で表示崩れなし
