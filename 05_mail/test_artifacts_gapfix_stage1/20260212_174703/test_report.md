# テスト実行レポート

- Run ID: `20260212_174703`
- Stage: `stage1`
- Mail Scope: `self`
- Generated: `2026-02-12T17:47:22.098936`
- Artifact Dir: `C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703`

## サマリ

| Status | Count |
|---|---:|
| PASS | 88 |
| FAIL | 0 |
| BLOCKED | 4 |
| PASS_WITH_GAP | 0 |

## ケース結果 (TC-01 .. TC-92)

| TC | Status | Expected | Actual | Notes | Evidence |
|---|---|---|---|---|---|
| TC-01 | PASS | CP932 CSV loads successfully without garble warning. | records=2, warnings=[] |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\業者連絡先_サンプル.csv |
| TC-02 | PASS | UTF-8 BOM CSV loads successfully. | records=1 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc02_utf8_bom.csv |
| TC-03 | PASS | Shift_JIS/CP932 CSV fallback load works. | records=1 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc03_shift_jis.csv |
| TC-04 | PASS | Unreadable mixed binary input should trigger decode warning/error handling. | errors=["必須列 '会社名' が見つかりません。", "必須列 'メールアドレス' が見つかりません。"], warnings=['文字コード自動判定: cp932（フォールバック使用）', '文字化けの可能性があります。文字コードを確認してください。'] |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc04_binary.csv |
| TC-05 | PASS | Garbled-character warning should be detected. | warnings=['文字化けの可能性があります。文字コードを確認してください。'] |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc05_garbled.csv |
| TC-06 | PASS | Alias headers should map to standard columns. | records=1 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc06_alias.csv |
| TC-07 | PASS | Header trim/case-insensitive alias normalization should work. | records=1 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc07_alias_trim.csv |
| TC-08 | PASS | Contact name priority #1 (担当者名) should be used. | name=担当 太郎 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc08_contact_name.csv |
| TC-09 | PASS | Contact name priority #2 (氏名) should be used. | name=氏名 太郎 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc09_contact_name.csv |
| TC-10 | PASS | Contact name priority #3 (姓+名) should be used. | name=田中 太郎 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc10_contact_name.csv |
| TC-11 | PASS | Contact name priority #4 (姓のみ) should be used. | name=田中 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc11_contact_name.csv |
| TC-12 | PASS | Contact name fallback should be ご担当者様. | name=ご担当者様 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc12_contact_name.csv |
| TC-13 | PASS | Middle name should be inserted in 姓 ミドル 名 order. | name=田中 M 太郎 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc13_contact_name.csv |
| TC-14 | PASS | Invalid email format should be rejected. | errors=['行2: メールアドレス形式エラー - An email address must have an @-sign.'] |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc14_invalid_email.csv |
| TC-15 | PASS | Missing required value should be row-level error. | errors=['行2: 会社名が空です。'] |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc15_missing_required_value.csv |
| TC-16 | PASS | Duplicate addresses should be de-duplicated with warning. | records=1 duplicate=1 warnings=['行3: 重複メールアドレス - dup***@example.com'] |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc16_duplicate.csv |
| TC-17 | PASS | Blank rows should be skipped silently. | records=2 warnings=[] |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc17_blank_rows.csv |
| TC-18 | PASS | Non-existent file should return file-not-found error. | errors=['ファイルが存在しません: C:\\Users\\千賀聡志\\OneDrive - セルジェンテック株式会社\\sharepointリスト化\\05_mail\\test_artifacts_gapfix_stage1\\20260212_174703\\inputs\\tc18_not_exists.csv'] |  | - |
| TC-19 | PASS | Product search should return proposal data for target item. | status=202, sources=1 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\evidence\tc19_search_response.html<br>C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\evidence\tc19_search_meta.json |
| TC-20 | PASS | All search outcomes should have source URL/site attribution. | sources=['http://www.w3.org/TR/html4/loose.dtd'] |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\evidence\tc19_search_meta.json |
| TC-21 | PASS | Selected product URL should pass validity check. | valid=True, status=200, url=http://www.w3.org/TR/html4/loose.dtd |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\evidence\tc19_search_meta.json |
| TC-22 | PASS | Invalid URL should trigger warning path and alternative prompt. | valid=False, error=HTTPステータス 404 |  | - |
| TC-23 | PASS | Flow should not proceed to mail generation before user approval. | approval=True -> generation allowed. |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\evidence\tc23_user_approval.json |
| TC-24 | PASS | Rejection should route to re-search/manual correction. | approval=False -> generation blocked and re-search requested. |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\evidence\tc24_user_rejection.json |
| TC-25 | PASS | Blacklist match should reject even if whitelist matches. | ブラックリストに一致: example.com |  | - |
| TC-26 | PASS | Empty whitelist should allow domain. | ホワイトリスト未設定のため許可 |  | - |
| TC-27 | PASS | Whitelist match should allow. | ホワイトリストに一致: allowed.com |  | - |
| TC-28 | PASS | Whitelist non-match should reject. | ホワイトリストに含まれません: blocked.com |  | - |
| TC-29 | PASS | Subdomain should match parent domain rule. | ホワイトリストに一致: sub.example.com |  | - |
| TC-30 | PASS | Normal product query should pass PII check. | No PII. |  | - |
| TC-31 | PASS | Email in query should be blocked. | メールアドレスが検出されました: test@example.com<br>→ 削除してから再実行してください。 |  | - |
| TC-32 | PASS | Hyphenated phone should be blocked. | 電話番号が検出されました: 03-1234-5678<br>→ 削除してから再実行してください。 |  | - |
| TC-33 | PASS | Spaced phone should be blocked. | 電話番号が検出されました: 090 1234 5678<br>→ 削除してから再実行してください。 |  | - |
| TC-34 | PASS | Company-name match should be warning-only. | 会社名との一致が検出されました: セルジェンテック株式会社<br>→ 続行する場合は確認してください。 |  | - |
| TC-35 | PASS | Combined PII should block with warning context. | メールアドレスが検出されました: test@example.com<br>→ 削除してから再実行してください。<br><br>会社名との一致が検出されました: セルジェンテック株式会社<br>→ 続行する場合は確認してください。 |  | - |
| TC-36 | PASS | HTTPS 2xx should be valid. | status=200 |  | - |
| TC-37 | PASS | 3xx redirect should be accepted. | status=200, final=https://httpbin.org/get |  | - |
| TC-38 | PASS | HEAD=405 should fallback to GET and succeed when GET=200. | status=200, final=https://x/final |  | - |
| TC-39 | PASS | Redirect depth over max(5) should be blocked. | valid=False, status=200 |  | - |
| TC-40 | PASS | HTTP scheme should emit warning. | warning=HTTPスキームです。セキュリティ上のリスクがあります。, status=200 |  | - |
| TC-41 | PASS | Unsupported scheme should be rejected. | 許可されていないスキームです: ftp |  | - |
| TC-42 | PASS | localhost should be blocked. | ローカルホストへのアクセスはブロックされています |  | - |
| TC-43 | PASS | Private IP should be blocked. | プライベートIPへのアクセスはブロックされています: 192.168.10.10 |  | - |
| TC-44 | PASS | Domain resolving to private IP should be blocked. | 解決先がプライベートIPです: example.com → 10.1.2.3 |  | - |
| TC-45 | PASS | HTTP 404 should be treated as invalid. | status=404, error=HTTPステータス 404 |  | - |
| TC-46 | PASS | Timeout should retry up to configured count. | retries=3, error=タイムアウト（1秒） |  | - |
| TC-47 | PASS | DNS resolution failure should end as connection error after retries. | retries=3, error=接続エラー: DNS failure |  | - |
| TC-48 | PASS | DOCX template should load successfully. | len=339 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\見積依頼_サンプル.docx |
| TC-49 | PASS | Variable bracket character behavior should match implementation. | supported_double=['会社名'], supported_angle=['会社名'] |  | - |
| TC-50 | PASS | TXT template should load successfully. | len=368 |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\見積依頼.txt |
| TC-51 | PASS | Default template should be available. | default template loaded |  | - |
| TC-52 | PASS | Template variables should be replaced in both formats. | A社 田中 |  | - |
| TC-53 | PASS | create_email_body should inject product/company fields. | A社 田中 太郎 製品X 特徴Y https://example.com/x |  | - |
| TC-54 | PASS | Strict mode should fail when undefined variable exists. | missing=['未定義'] |  | - |
| TC-55 | PASS | Missing template file should produce file-not-found error. | ファイルが存在しません: C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc55_missing_template.docx |  | - |
| TC-56 | BLOCKED | Outlook connection check should succeed. | Stage 'stage1' excludes this test case. | Not executed due to stage filter. | - |
| TC-57 | PASS | dry_run send should succeed with DRYRUN message-id. | message_id=DRYRUN:02db5e8e-67ca-4222-9327-dcf154dc69c0 |  | - |
| TC-58 | BLOCKED | Self-addressed test send should succeed. | Stage 'stage1' excludes this test case. | Not executed due to stage filter. | - |
| TC-59 | BLOCKED | send_test_mail should prefix subject with [テスト]. | Stage 'stage1' excludes this test case. | Not executed due to stage filter. | - |
| TC-60 | PASS | Send interval control should enforce >= configured delay. | sleep=2.00s |  | - |
| TC-61 | PASS | >=5 recipients should trigger final confirmation behavior. | confirmed=5, send_calls=0 |  | - |
| TC-62 | PASS | Below threshold should not trigger warning behavior. | confirm_calls=0, send_calls=4 |  | - |
| TC-63 | BLOCKED | Successful send should obtain non-fallback Message-ID. | Stage 'stage1' excludes this test case. | Not executed due to stage filter. | - |
| TC-64 | PASS | Fallback Message-ID format should follow FALLBACK:{UUID}:{ts}:{hash}. | FALLBACK:e48f0ad7-a0e8-4208-8308-ba8552074c48:1770886039:a9491f4c |  | - |
| TC-65 | PASS | Retryable send errors should retry up to max count. | attempts=4, error=timeout temporary |  | - |
| TC-66 | PASS | generate_key should create a key. | key_len=44 |  | - |
| TC-67 | PASS | get_key should retrieve generated key. | key_exists=True |  | - |
| TC-68 | PASS | encrypt should produce enc:v1: format. | enc:v1:gAAAAABpjZOXfqGpcnFDSRwClS2hHBBwSJNloQrlwqEuCbXgj48ZMHUFqdxl8vLk7iAuHVnkvp1HrgGBQUZ29nAhpy5ayAgCOA== |  | - |
| TC-69 | PASS | decrypt should return original plaintext. | plain=plain-text |  | - |
| TC-70 | PASS | Operation without key should raise key-not-found error. | exception=KeyNotFoundError |  | - |
| TC-71 | PASS | Encrypted column format validator should detect mismatch. | ok_case=True, ng_case=False |  | - |
| TC-72 | PASS | Overwrite without force should raise EncryptionError. | exception=EncryptionError |  | - |
| TC-73 | PASS | Audit log file should be generated. | log=C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\audit_20260212_174719_30f53a81.json |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\audit_20260212_174719_30f53a81.json |
| TC-74 | PASS | Emails in audit details should be encrypted. | email_enc=enc:v1:gAAAAABpjZOXh... |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\audit_20260212_174719_30f53a81.json |
| TC-75 | PASS | Screen output should mask email addresses. | ==================================================<br>送信結果サマリ<br>==================================================<br>総件数: 2<br>成功: 1<br>失敗: 1<br><br>--------------------------------------------------<br>詳細:<br>--------------------------------------------------<br>✓ A社 (tan***@example.com) - 2026-02-12T17:47:19.848683<br>✗ B社 (b***@example.com) [エラー: Invalid recipient]<br>================================================== |  | - |
| TC-76 | PASS | Sent list CSV should be generated with encrypted mail column. | path=C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\sent_list_20260212_174719.csv |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\sent_list_20260212_174719.csv |
| TC-77 | PASS | Unsent list CSV should include failed rows and error details. | path=C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\unsent_list_20260212_174719.csv |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\unsent_list_20260212_174719.csv |
| TC-78 | PASS | Error logs should mask as ***@domain format. | masked=***@example.com |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\audit_20260212_174719_30f53a81.json |
| TC-79 | PASS | CSV missing required 会社名 column should error. | errors=["必須列 '会社名' が見つかりません。"] |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc79_missing_company_col.csv |
| TC-80 | PASS | Empty CSV should error. | errors=['空のファイルです。'] |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc80_empty.csv |
| TC-81 | PASS | Encrypted-column mismatch should stop with detection error. | errors=["暗号化列検出エラー: 列名 'メールアドレス_enc' は暗号化形式ですが、値が暗号化形式ではありません。ファイルが破損している可能性があります。"] |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc81_enc_mismatch.csv |
| TC-82 | PASS | Unsupported template extension (.pdf) should error. | サポートされていないファイル形式です: .pdf |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc82_template.pdf |
| TC-83 | PASS | Outlook unavailable should return connection error and stop processing. | Outlook接続エラー: Outlook not started |  | - |
| TC-84 | PASS | Sending over max_recipients should fail before send. | 送信件数が上限を超えています: 2 > 1 |  | - |
| TC-85 | PASS | Partial failures should generate unsent list while keeping successes. | failure_count=1 unsent=C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\unsent_list_20260212_174720.csv |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\unsent_list_20260212_174720.csv |
| TC-86 | PASS | Unsent-list rerun with *_enc should work. | records=1, email=a86@example.com |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\inputs\tc86_unsent_rerun.csv |
| TC-87 | PASS | After key loss, decryption should fail and require new key setup. | exception=KeyNotFoundError |  | - |
| TC-88 | PASS | Decrypting with wrong key should raise DecryptionError. | exception=DecryptionError |  | - |
| TC-89 | PASS | SSRF protection should block private IP URL. | プライベートIPへのアクセスはブロックされています: 10.0.0.1 |  | - |
| TC-90 | PASS | Second send to same address in same execution should be skipped. | Duplicate send prevented in same run. |  | - |
| TC-91 | PASS | Re-execution within 24h with same payload should request confirmation. | Re-execution warning detected. |  | - |
| TC-92 | PASS | Message-ID should be recorded in send ledger artifacts. | Message-ID persisted to audit and sent list. |  | C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\audit_20260212_174721_ed150c1d.json<br>C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts_gapfix_stage1\20260212_174703\outputs\sent_list_20260212_174721.csv |
