# テスト実行レポート

- Run ID: `20260212_174625`
- Stage: `stage2`
- Mail Scope: `self`
- Generated: `2026-02-12T17:46:45.102946`
- Artifact Dir: `C:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\test_artifacts\20260212_174625`

## サマリ

| Status | Count |
|---|---:|
| PASS | 4 |
| FAIL | 0 |
| BLOCKED | 88 |
| PASS_WITH_GAP | 0 |

## ケース結果 (TC-01 .. TC-92)

| TC | Status | Expected | Actual | Notes | Evidence |
|---|---|---|---|---|---|
| TC-01 | BLOCKED | CP932 CSV loads successfully without garble warning. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-02 | BLOCKED | UTF-8 BOM CSV loads successfully. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-03 | BLOCKED | Shift_JIS/CP932 CSV fallback load works. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-04 | BLOCKED | Unreadable mixed binary input should trigger decode warning/error handling. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-05 | BLOCKED | Garbled-character warning should be detected. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-06 | BLOCKED | Alias headers should map to standard columns. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-07 | BLOCKED | Header trim/case-insensitive alias normalization should work. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-08 | BLOCKED | Contact name priority #1 (担当者名) should be used. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-09 | BLOCKED | Contact name priority #2 (氏名) should be used. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-10 | BLOCKED | Contact name priority #3 (姓+名) should be used. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-11 | BLOCKED | Contact name priority #4 (姓のみ) should be used. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-12 | BLOCKED | Contact name fallback should be ご担当者様. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-13 | BLOCKED | Middle name should be inserted in 姓 ミドル 名 order. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-14 | BLOCKED | Invalid email format should be rejected. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-15 | BLOCKED | Missing required value should be row-level error. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-16 | BLOCKED | Duplicate addresses should be de-duplicated with warning. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-17 | BLOCKED | Blank rows should be skipped silently. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-18 | BLOCKED | Non-existent file should return file-not-found error. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-19 | BLOCKED | Product search should return proposal data for target item. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-20 | BLOCKED | All search outcomes should have source URL/site attribution. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-21 | BLOCKED | Selected product URL should pass validity check. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-22 | BLOCKED | Invalid URL should trigger warning path and alternative prompt. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-23 | BLOCKED | Flow should not proceed to mail generation before user approval. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-24 | BLOCKED | Rejection should route to re-search/manual correction. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-25 | BLOCKED | Blacklist match should reject even if whitelist matches. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-26 | BLOCKED | Empty whitelist should allow domain. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-27 | BLOCKED | Whitelist match should allow. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-28 | BLOCKED | Whitelist non-match should reject. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-29 | BLOCKED | Subdomain should match parent domain rule. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-30 | BLOCKED | Normal product query should pass PII check. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-31 | BLOCKED | Email in query should be blocked. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-32 | BLOCKED | Hyphenated phone should be blocked. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-33 | BLOCKED | Spaced phone should be blocked. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-34 | BLOCKED | Company-name match should be warning-only. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-35 | BLOCKED | Combined PII should block with warning context. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-36 | BLOCKED | HTTPS 2xx should be valid. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-37 | BLOCKED | 3xx redirect should be accepted. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-38 | BLOCKED | HEAD=405 should fallback to GET and succeed when GET=200. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-39 | BLOCKED | Redirect depth over max(5) should be blocked. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-40 | BLOCKED | HTTP scheme should emit warning. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-41 | BLOCKED | Unsupported scheme should be rejected. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-42 | BLOCKED | localhost should be blocked. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-43 | BLOCKED | Private IP should be blocked. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-44 | BLOCKED | Domain resolving to private IP should be blocked. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-45 | BLOCKED | HTTP 404 should be treated as invalid. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-46 | BLOCKED | Timeout should retry up to configured count. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-47 | BLOCKED | DNS resolution failure should end as connection error after retries. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-48 | BLOCKED | DOCX template should load successfully. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-49 | BLOCKED | Variable bracket character behavior should match implementation. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-50 | BLOCKED | TXT template should load successfully. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-51 | BLOCKED | Default template should be available. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-52 | BLOCKED | Template variables should be replaced in both formats. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-53 | BLOCKED | create_email_body should inject product/company fields. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-54 | BLOCKED | Strict mode should fail when undefined variable exists. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-55 | BLOCKED | Missing template file should produce file-not-found error. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-56 | PASS | Outlook connection check should succeed. | Outlook接続OK |  | - |
| TC-57 | BLOCKED | dry_run send should succeed with DRYRUN message-id. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-58 | PASS | Self-addressed test send should succeed. | message_id=<OSCPR01MB146947AB50279C765BC4A7DA2C860A@OSCPR01MB14694.jpnprd01.prod.outlook.com> |  | - |
| TC-59 | PASS | send_test_mail should prefix subject with [テスト]. | subject=[テスト] 件名確認 |  | - |
| TC-60 | BLOCKED | Send interval control should enforce >= configured delay. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-61 | BLOCKED | >=5 recipients should trigger final confirmation behavior. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-62 | BLOCKED | Below threshold should not trigger warning behavior. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-63 | PASS | Successful send should obtain non-fallback Message-ID. | message_id=<OSCPR01MB146940DA1681A01C6E4C27689C860A@OSCPR01MB14694.jpnprd01.prod.outlook.com> |  | - |
| TC-64 | BLOCKED | Fallback Message-ID format should follow FALLBACK:{UUID}:{ts}:{hash}. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-65 | BLOCKED | Retryable send errors should retry up to max count. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-66 | BLOCKED | generate_key should create a key. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-67 | BLOCKED | get_key should retrieve generated key. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-68 | BLOCKED | encrypt should produce enc:v1: format. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-69 | BLOCKED | decrypt should return original plaintext. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-70 | BLOCKED | Operation without key should raise key-not-found error. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-71 | BLOCKED | Encrypted column format validator should detect mismatch. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-72 | BLOCKED | Overwrite without force should raise EncryptionError. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-73 | BLOCKED | Audit log file should be generated. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-74 | BLOCKED | Emails in audit details should be encrypted. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-75 | BLOCKED | Screen output should mask email addresses. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-76 | BLOCKED | Sent list CSV should be generated with encrypted mail column. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-77 | BLOCKED | Unsent list CSV should include failed rows and error details. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-78 | BLOCKED | Error logs should mask as ***@domain format. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-79 | BLOCKED | CSV missing required 会社名 column should error. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-80 | BLOCKED | Empty CSV should error. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-81 | BLOCKED | Encrypted-column mismatch should stop with detection error. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-82 | BLOCKED | Unsupported template extension (.pdf) should error. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-83 | BLOCKED | Outlook unavailable should return connection error and stop processing. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-84 | BLOCKED | Sending over max_recipients should fail before send. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-85 | BLOCKED | Partial failures should generate unsent list while keeping successes. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-86 | BLOCKED | Unsent-list rerun with *_enc should work. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-87 | BLOCKED | After key loss, decryption should fail and require new key setup. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-88 | BLOCKED | Decrypting with wrong key should raise DecryptionError. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-89 | BLOCKED | SSRF protection should block private IP URL. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-90 | BLOCKED | Second send to same address in same execution should be skipped. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-91 | BLOCKED | Re-execution within 24h with same payload should request confirmation. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
| TC-92 | BLOCKED | Message-ID should be recorded in send ledger artifacts. | Stage 'stage2' excludes this test case. | Not executed due to stage filter. | - |
