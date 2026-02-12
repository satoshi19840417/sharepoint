# SharePointリスト化 全体計画（ステータス別整理版）

**最終更新**: 2026年2月10日
**現在のバージョン**: 1.1.0.3

---

## フェーズ一覧

| フェーズ | 内容 | ステータス |
|----------|------|-----------|
| Phase 1 | 採番の安定化 | ✅ 完了 |
| Phase 2 | Title仕様の確定 | ✅ 完了 |
| Phase 3 | Teams通知MVP | ✅ 完了 |
| Phase 4 | 承認（Approvals）＋送付ゲート | ✅ 完了 |
| Phase 5 | 外部送付の拡張 | 🔧 実装中（テンプレート完了・列追加待ち） |

---

## ✅ 完了済み（Phase 1〜4）

### Phase 1〜3: 基盤機能
- 採番安定化、Title仕様確定、Teams通知MVP

### Phase 4: 承認機能
- 基本承認フロー（承認/保留/拒否）
- メール通知、ステータス更新
- フィールド名マッピングコメント追加

---

## 📝 Phase 5: 送付フロー（計画確定）

| 項目 | 決定内容 |
|------|---------|
| 発注書 | Word→PDF自動生成 |
| 請書 | Excel（業者編集可能） |
| 送付担当者 | sengas@cellgentech.com |
| トリガー | SendStatus手動変更 |
| 業者マスタ | `業者連絡先yymmdd.csv` |

**実装前準備**:
- [x] Wordテンプレート作成（完了 2026/02/06）
- [x] Excelテンプレート作成（完了 2026/02/06）
- [x] 列追加スクリプト作成（`02_Scripts/AddPhase5Columns.ps1`）
- [x] 業者マスタCSVテンプレート作成
- [ ] SharePoint列追加スクリプト実行
- [ ] 業者マスタCSVインポート
- [ ] PDF変換テスト / Excel 2016互換性テスト

詳細: `01_Documents/01_Phases/Phase5_送付フロー/Phase5_送付フロー計画書.md`

---

## 環境情報

| 項目 | 値 |
|------|------|
| SharePointサイト | https://cellgentech.sharepoint.com/sites/SP__Prototype |
| リスト名 | 発注依頼_Requests_Test |
| 承認フロー | Requests_Approval_SP |
| 最新パッケージ | 03_Release/automation_1_1_0_2.zip |
