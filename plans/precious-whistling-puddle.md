# Phase 5 送付フロー準備 - 実装計画

## Context

Phase 5（送付フロー準備）は承認済みの発注をPDF/Excelで業者に自動送付するフローの準備段階。テンプレート作成は完了済みだが、SharePoint列追加・業者マスタ準備・ドキュメント更新が未実施のまま残っている。これらを一括で進め、Power Automateフロー構築の前提を整える。

---

## 成果物一覧

| # | 成果物 | パス |
|---|--------|------|
| 1 | SharePoint列追加スクリプト | `02_Scripts/AddPhase5Columns.ps1` |
| 2 | 業者マスタCSVテンプレート | `01_Documents/02_Templates/vendor_master_template.csv` |
| 3 | ドキュメント更新（4ファイル） | 下記参照 |

---

## 1. PowerShellスクリプト作成: `02_Scripts/AddPhase5Columns.ps1`

### 概要
既存リスト `発注依頼_Requests_Test` に Phase 5 必要列を追加する。`CreateInventoryList.ps1` のパターンを踏襲。

### 追加する列

| InternalName | DisplayName | 型 | 必須 | 備考 |
|---|---|---|---|---|
| `OrderID` | 発注ID | Text | Yes | グルーピングキー (例: PO-20260204-001) |
| `DeliveryAddress` | 納品先 | Text | No | OrderIDグループ内で一致必須 |
| `VendorID` | 業者ID | Text | No | OrderIDグループ内で一致必須 |
| `QuoteNumber` | 見積書番号 | Text | No | 空白可 |
| `SortOrder` | 表示順 | Number | No | 明細の並び順 |
| `SendStatus` | 送付ステータス | Choice | No | 未送付/送付中/送付済/エラー |
| `ErrorLog` | エラーログ | Note | No | エラーメッセージ記録用（複数行） |

### スクリプト構造
```
1. PnP.PowerShell モジュール確認・インストール（既存パターン踏襲）
2. 接続（Interactive → DeviceLogin フォールバック）
3. リスト存在確認（存在しなければ中断）
4. ヘルパー関数定義（Add-TextField / Add-NumberField）
5. 各列を追加（-ErrorAction SilentlyContinue で冪等性確保）
   - SendStatus は Get-PnPField で既存チェック → 無ければ Choice で作成
6. 全列の存在確認レポート
7. （オプション）テンプレートファイルのアップロード
```

### 参照ファイル
- パターン元: [CreateInventoryList.ps1](02_Scripts/CreateInventoryList.ps1)
- 列定義元: [Phase5_送付フロー計画書.md](01_Documents/01_Phases/Phase5_送付フロー/Phase5_送付フロー計画書.md)
- データモデル検証: [verify_flow_error_handling.py](01_Documents/01_Phases/Phase5_送付フロー/verify_flow_error_handling.py)

---

## 2. 業者マスタCSVテンプレート: `01_Documents/02_Templates/vendor_master_template.csv`

### 概要
Power Automateフローが業者情報を参照するためのCSVフォーマットを定義。既存の `業者連絡先_サンプル.csv`（Outlookエクスポート90列超）を簡素化。

### 列定義

| 列名 | 必須 | 用途 |
|------|------|------|
| 業者ID | Yes | VendorIDルックアップキー |
| 業者名 | Yes | テンプレート差し込み (VendorName) |
| メールアドレス | Yes | 送付先メール |
| 担当者名 | No | 連絡先 |
| 電話番号 | No | 連絡先 |
| 住所 | No | 業者住所 |
| 備考 | No | 自由記述 |

### フォーマット
- エンコーディング: UTF-8 with BOM（Excel互換）
- サンプルデータ2行入り

---

## 3. ドキュメント更新

### 3a. `01_Documents/00_Overview/実施済み作業一覧.md`
- 完了済みセクションに「Phase 5 テンプレート作成完了（2026/02/06）」を追記
- 「次回作業 > Phase 5 準備」のチェックリストを実態に合わせて更新:
  - テンプレート関連4タスク → `[x]` に変更
  - SharePoint列追加 → 列名を具体化（7列）
  - 業者マスタCSV → 新タスクとして追加

### 3b. `01_Documents/00_Overview/SharePointリスト化全体計画.md`
- Phase 5 ステータスを `📝 計画確定` → `🔧 実装中（テンプレート完了・列追加待ち）` に更新
- 実装前準備チェックリストを実態に合わせて更新
- バージョン・最終更新日を更新

### 3c. `01_Documents/README.md`
- 「現在のタスク」テーブルを更新:
  - Phase 5 テンプレート作成 → `✅ 完了`
  - Phase 5 列追加・業者マスタ → `🔄 進行中` として追加

### 3d. `01_Documents/01_Phases/Phase5_送付フロー/Phase5_テンプレート作成タスク.md`
- 受入基準の未完了項目に「※GUI操作待ち」注釈を追加（作業漏れではないことを明示）

---

## 実行順序

| Step | 内容 | 依存 |
|------|------|------|
| 1 | `AddPhase5Columns.ps1` 作成 | なし |
| 2 | `vendor_master_template.csv` 作成 | なし |
| 3 | ドキュメント4ファイル更新 | なし |
| 4 | PowerShellスクリプト実行（ユーザー操作） | Step 1 |
| 5 | テンプレートSharePointアップロード（ユーザー操作） | Step 4 |

Step 1-3 は並行実施可能。Step 4-5 はユーザーによるGUI/ターミナル操作。

---

## 検証方法

1. **スクリプト検証**: `AddPhase5Columns.ps1` 実行後、末尾の自動チェックで7列すべて `[OK]` と表示されること
2. **CSV検証**: `vendor_master_template.csv` をExcelで開き、文字化けがないこと
3. **ドキュメント検証**: 各mdファイルのチェックボックスが実態と一致すること
4. **E2E検証**（将来）: SharePoint上で手動アイテム作成 → 新列に値入力 → 保存可能であること
