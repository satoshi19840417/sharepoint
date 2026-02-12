# 見積依頼メール改善計画：製品情報拡張とAIチャット統合

## Context

現在の見積依頼メールシステムは、CSVから連絡先を読み込み、テンプレートベースでメールを一斉送信する機能を持っています。しかし、製品情報として製品名と製品URLしか扱えず、メーカー名やメーカーコードなどの詳細情報をメール本文に含めることができません。

ユーザーは、AIチャットで対話的に製品情報を入力し、AIが自動的に製品ページURLを検索して、以下のような期待するメール内容を生成したいと考えています：

**運用フロー:**
1. ユーザーがClaude Codeチャットで「見積依頼メールを送信して」と依頼
2. AIが製品情報（製品名、メーカー名、メーカーコード、数量）を対話的に質問
3. AIがWebSearch toolで製品ページURLを自動検索し、候補を提示
4. ユーザーがURLを選択
5. AIがPII検出とURL検証を実行
6. すべて確認後、メール送信

**依頼内容（AIチャットでの対話入力）:**
```
製品名：トランスブロット® Turbo™ ミニ PVDF 転写パック
メーカー名：BIO-RAD
メーカーコード：170-4156
数量：1個
```

**期待するメール内容（出力）:**
```
セルジェンテック株式会社
ご担当者様 様
お世話になっております。
下記製品のお見積りをお願いしたく、ご連絡いたしました。
■ 製品情報
製品名: トランスブロット® Turbo™ ミニ PVDF 転写パック
メーカー名: BIO-RAD
メーカーコード：170-4156
数量：1個
製品ページ:https://www.bio-rad.com/ja-jp/sku/1704156-trans-blot-turbo-mini-0-2-um-pvdf-transfer-packs?ID=1704156
ご検討のほど、よろしくお願いいたします。
```

この改善により、製品情報の詳細をメールに含めることができ、AIチャットによる対話的な入力と自動検索により、メール送信の効率が大幅に向上します。

## Implementation Approach

### 1. AIチャット統合アプローチ

**実装境界の明確化:**

すべての対話と検索はAIチャット側で実行され、Pythonスクリプトは製品情報を受け取ってメール生成・送信のみを担当します。

**AIチャット側の責務:**
- ユーザーとの対話による製品情報収集（製品名、メーカー名、メーカーコード、数量）
- PII検出（個人情報が含まれていないか確認）
- WebSearch toolによる製品ページURL検索
- 検索結果の候補提示とユーザー選択
- QuoteRequestSkill.validate_url()によるURL有効性検証
- すべての情報が揃ったら、QuoteRequestSkill.send_bulk()を呼び出し

**Pythonスクリプト側の責務:**
- QuoteRequestSkill.send_bulk()の引数拡張（maker_name, maker_code, quantity追加）
- テンプレート変数の拡張（«メーカー名»/{{メーカー名}}、«メーカーコード»/{{メーカーコード}}、«数量»/{{数量}}追加）
- メール本文生成
- Outlook連携によるメール送信
- 監査ログへの製品情報記録

**データフロー:**
```
AIチャット: ユーザーと対話
    ↓
AIチャット: 製品情報収集（製品名、メーカー名、メーカーコード、数量）
    ↓
AIチャット: PII検出（個人情報チェック）
    ↓
AIチャット: WebSearch実行
    ↓
AIチャット: URL候補提示 → ユーザー選択
    ↓
AIチャット: URL検証
    ↓
AIチャット: QuoteRequestSkill.send_bulk() 呼び出し
    ↓
Python: メール本文生成（新変数使用）
    ↓
Python: メール送信
    ↓
Python: 監査ログ記録
```

### 2. テンプレート拡張

**ファイル:** `05_mail/scripts/template_processor.py`

既存のテンプレート変数に以下を追加します：

| 新変数 | 説明 | 例 |
|--------|------|-----|
| `«メーカー名»` または `{{メーカー名}}` | メーカー名 | BIO-RAD |
| `«メーカーコード»` または `{{メーカーコード}}` | メーカーコード | 170-4156 |
| `«数量»` または `{{数量}}` | 数量 | 1個 |

**注意:** テンプレート変数は «...» (Word形式) と {{...}} (汎用形式) の両方をサポートします。

**変更箇所:**
- `create_email_body()` メソッドに新しい引数を追加（`maker_name`, `maker_code`, `quantity`）
- デフォルトテンプレートを更新して新変数を含める

### 3. QuoteRequestSkill拡張

**ファイル:** `05_mail/scripts/main.py`

既存のQuoteRequestSkillクラスを以下のように拡張します：

**変更点:**
1. **render_email()メソッド**: 新しい引数（`maker_name`, `maker_code`, `quantity`）を追加（デフォルト値=""で後方互換性維持）
2. **send_bulk()メソッド**: 新しい引数を追加（デフォルト値=""で後方互換性維持）し、本文生成時にrender_email()に渡す

**使用例（AIチャットから呼び出し）:**
```python
# AIチャットが収集した製品情報をsend_bulk()に渡す
skill.send_bulk(
    records=contacts,
    subject="見積依頼",
    template_content=template,
    product_name="トランスブロット® Turbo™ ミニ PVDF 転写パック",
    product_features="",  # オプション
    product_url="https://www.bio-rad.com/ja-jp/sku/1704156-...",
    maker_name="BIO-RAD",         # 新規追加
    maker_code="170-4156",        # 新規追加
    quantity="1個",               # 新規追加
    input_file="contacts.csv",
)
```

**後方互換性:**
新しい引数はすべてデフォルト値=""を持つため、既存のコード（maker_name等を指定しない呼び出し）も引き続き動作します。

### 4. AIチャット側の処理フロー（参考）

**注意:** このセクションはPythonスクリプト側の実装ではなく、AIチャットが実行する処理の説明です。

**製品情報収集:**
```
AI: 製品名を教えてください。
ユーザー: トランスブロット® Turbo™ ミニ PVDF 転写パック
AI: メーカー名を教えてください。
ユーザー: BIO-RAD
AI: メーカーコードを教えてください。
ユーザー: 170-4156
AI: 数量を教えてください。
ユーザー: 1個
```

**PII検出:**
AIは入力内容に個人情報（メールアドレス、電話番号、個人名等）が含まれていないか確認します。

**Web検索:**
```
検索クエリ: "BIO-RAD 170-4156 トランスブロット® Turbo™ ミニ PVDF 転写パック"
↓
WebSearch tool実行
↓
候補URL（上位3件）:
1. https://www.bio-rad.com/ja-jp/sku/1704156-...
2. https://www.example.com/product/...
3. https://www.another-site.com/...
↓
AI: 以下の候補が見つかりました。どれを使用しますか？
ユーザー: 1番目
```

**URL検証:**
AIは `QuoteRequestSkill.validate_url()` メソッドを使用して、選択されたURLが有効か（HTTPS、アクセス可能、リダイレクト対応等）を確認します。

### 5. 監査ログ拡張

**ファイル:** `05_mail/scripts/audit_logger.py`

製品情報を監査ログに記録するため、`write_audit_log()` メソッドを拡張します。

**追加情報:**
```json
{
  "execution_id": "...",
  "product_info": {
    "product_name": "...",
    "maker_name": "...",
    "maker_code": "...",
    "quantity": "...",
    "product_url": "..."
  },
  ...
}
```

### 6. エラーハンドリング

以下のエラーケースに対応します：

1. **製品情報検証エラー**: 必須フィールドが空の場合
2. **Web検索エラー**: 検索APIが利用できない、検索結果が0件
3. **URL検証エラー**: URLが無効、アクセスできない
4. **ユーザー入力エラー**: 不正な入力形式

すべてのエラーは適切なメッセージを表示し、ユーザーに再入力を促します。

## Critical Files

### 新規作成ファイル

**なし** - AIチャット統合アプローチでは、新規Pythonモジュールの作成は不要です。

### 変更が必要な既存ファイル

| ファイル | 変更内容 | 影響範囲 | 推定変更行数 |
|---------|---------|---------|-------------|
| `05_mail/scripts/template_processor.py` | `create_email_body()` に新引数追加（maker_name, maker_code, quantity、デフォルト値=""）、変数マッピング追加 | 小 | 約10行 |
| `05_mail/scripts/main.py` | `render_email()`, `send_bulk()` に新引数追加（デフォルト値=""）、render_email呼び出し箇所の引数追加 | 小-中 | 約20行 |
| `05_mail/scripts/audit_logger.py` | `write_audit_log()` の product_info 引数追加（Optional、デフォルトNone）、ログエントリへの製品情報記録 | 小 | 約10行 |
| `05_mail/tests/test_send_bulk_dedupe.py` | `_AuditStub.write_audit_log()` のシグネチャ修正（product_info引数追加） | 小 | 約1行 |
| `05_mail/tests/test_rerun_detection.py` | `_AuditStub.write_audit_log()` のシグネチャ修正（product_info引数追加） | 小 | 約1行 |

### テストファイルの影響

**修正が必要なテストファイル:**
- `test_send_bulk_dedupe.py` と `test_rerun_detection.py` の `_AuditStub.write_audit_log()` メソッドに product_info 引数を追加（デフォルト値=None）

**その他のテストファイル:**
既存の他のテストは、新引数がデフォルト値を持つため、修正不要です。

**新機能のテストケース（任意）:**
| ファイル | 変更内容 | 必須／任意 |
|---------|---------|----------|
| `05_mail/tests/run_tc_suite.py` | 製品情報を含むテストケースを追加 | 任意 |
| 新規テストファイル | テンプレート新変数のレンダリングテスト | 任意 |

### 設定ファイル

**変更不要** - Web検索やPII検出はAIチャット側で実行されるため、config.jsonへの設定追加は不要です。

## Implementation Details

### 1. template_processor.py の変更

**ファイル:** `c:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\scripts\template_processor.py`

**変更箇所1:** `create_email_body()` メソッドのシグネチャ

```python
def create_email_body(
    self,
    template_content: str,
    company_name: str,
    contact_name: str,
    product_name: str,
    product_features: str,
    product_url: str,
    maker_name: str = "",           # 追加
    maker_code: str = "",           # 追加
    quantity: str = "",             # 追加
    **extra_variables
) -> TemplateResult:
```

**変更箇所2:** 変数マッピング

```python
variables = {
    "会社名": company_name,
    "担当者名": contact_name,
    "製品名": product_name,
    "製品特徴": product_features,
    "製品URL": product_url,
    "メーカー名": maker_name,       # 追加
    "メーカーコード": maker_code,   # 追加
    "数量": quantity,               # 追加
    # ... 既存のエイリアス ...
}
```

### 2. main.py の変更

**ファイル:** `c:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\scripts\main.py`

**変更箇所1:** `render_email()` メソッドのシグネチャ

```python
def render_email(
    self,
    template_content: str,
    record: ContactRecord,
    product_name: str,
    product_features: str,
    product_url: str,
    maker_name: str = "",       # 追加
    maker_code: str = "",       # 追加
    quantity: str = ""          # 追加
) -> str:
    """メール本文をレンダリングする。"""
    result = self.template_processor.create_email_body(
        template_content=template_content,
        company_name=record.company_name,
        contact_name=record.contact_name,
        product_name=product_name,
        product_features=product_features,
        product_url=product_url,
        maker_name=maker_name,          # 追加
        maker_code=maker_code,          # 追加
        quantity=quantity,              # 追加
    )
    return result.content
```

**変更箇所2:** `send_bulk()` メソッドのシグネチャ

```python
def send_bulk(
    self,
    records: List[ContactRecord],
    subject: str,
    template_content: str,
    product_name: str,
    product_features: str,
    product_url: str,
    maker_name: str = "",                   # 追加
    maker_code: str = "",                   # 追加
    quantity: str = "",                     # 追加
    input_file: str = "",
    confirm_rerun_callback: Optional[Callable[[ContactRecord, Dict[str, Any]], bool]] = None,
) -> Dict[str, Any]:
```

**変更箇所3:** `send_bulk()` 内のメール本文生成呼び出し

```python
body = self.render_email(
    template_content=template_content,
    record=record,
    product_name=product_name,
    product_features=product_features,
    product_url=product_url,
    maker_name=maker_name,          # 追加
    maker_code=maker_code,          # 追加
    quantity=quantity,              # 追加
)
```

**変更箇所4:** 監査ログ出力の呼び出し

```python
# 製品情報を監査ログに記録（いずれかの製品情報があれば記録）
product_info = None
if product_name or maker_name or maker_code or quantity or product_url:
    product_info = {
        "product_name": product_name,
        "maker_name": maker_name,
        "maker_code": maker_code,
        "quantity": quantity,
        "product_url": product_url,
    }

audit_log_path = self.audit_logger.write_audit_log(
    input_file,
    results,
    product_info=product_info  # 追加
)
```

### 3. audit_logger.py の変更

**ファイル:** `c:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\scripts\audit_logger.py`

**変更箇所1:** `write_audit_log()` メソッドのシグネチャ

```python
def write_audit_log(
    self,
    input_file: str,
    results: List[Dict[str, Any]],
    product_info: Optional[Dict[str, str]] = None  # 追加
) -> str:
```

**変更箇所2:** ログエントリへの製品情報追加

```python
entry_dict = asdict(entry)
if product_info:
    entry_dict["product_info"] = product_info  # 追加

# ファイル書き込み
with open(log_file, 'w', encoding='utf-8') as f:
    json.dump(entry_dict, f, ensure_ascii=False, indent=2)
```

### 4. テストスタブの変更

**ファイル:** `c:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\tests\test_send_bulk_dedupe.py`

**ファイル:** `c:\Users\千賀聡志\OneDrive - セルジェンテック株式会社\sharepointリスト化\05_mail\tests\test_rerun_detection.py`

**変更箇所:** `_AuditStub.write_audit_log()` メソッドのシグネチャ

```python
class _AuditStub:
    def __init__(self) -> None:
        self.execution_id = "test-run"

    def write_audit_log(self, input_file, results, product_info=None):  # 引数追加
        return "audit.json"

    def write_sent_list(self, results):
        return "sent.csv"

    def write_unsent_list(self, results):
        return "unsent.csv"
```

## Verification Plan

### 単体テスト（任意）

新しい変数を使用したテンプレートレンダリングのテストを追加できます：

```python
def test_template_with_new_variables():
    processor = TemplateProcessor()
    template = """
製品名: «製品名»
メーカー名: «メーカー名»
メーカーコード: «メーカーコード»
数量: «数量»
"""
    result = processor.create_email_body(
        template_content=template,
        company_name="Test Corp",
        contact_name="Test User",
        product_name="Product A",
        product_features="",
        product_url="https://example.com",
        maker_name="Maker B",
        maker_code="ABC123",
        quantity="10個"
    )

    assert "Product A" in result.content
    assert "Maker B" in result.content
    assert "ABC123" in result.content
    assert "10個" in result.content
```

### 既存テストへの影響確認

**修正が必要なテスト:**
1. **`test_send_bulk_dedupe.py`** - `_AuditStub.write_audit_log()` に product_info 引数追加（約1行）
2. **`test_rerun_detection.py`** - `_AuditStub.write_audit_log()` に product_info 引数追加（約1行）

**修正不要なテスト:**
3. **`test_mail_sender_message_id.py`** - Message-ID取得テスト（変更不要）
4. **`test_audit_logger_masking.py`** - 監査ログマスキングテスト（変更不要）
5. **`test_url_validator.py`** - URL検証テスト（変更不要）

**検証方法:**
```bash
cd 05_mail
pytest tests/
```

### 手動テスト（AIチャット統合）

**1. AIチャットでの対話的入力テスト**

```
ユーザー: 見積依頼メールを送信して

AI: 製品情報を教えてください。

ユーザー:
製品名：トランスブロット® Turbo™ ミニ PVDF 転写パック
メーカー名：BIO-RAD
メーカーコード：170-4156
数量：1個

AI: （PII検出実行）個人情報は含まれていません。
AI: （WebSearch実行）製品ページを検索しています...
AI: 以下の候補が見つかりました：
    1. https://www.bio-rad.com/ja-jp/sku/1704156-...
    2. https://www.example.com/...
    どちらを使用しますか？

ユーザー: 1番目

AI: （URL検証実行）URLは有効です。
AI: （メール送信実行）
AI: メール送信が完了しました。送信件数: X件
```

**2. メール本文の確認**

送信されたメール（または下書き）を確認し、以下が正しく含まれているか確認：
- 製品名
- メーカー名
- メーカーコード
- 数量
- 製品URL

**3. 監査ログの確認**

`05_mail/logs/audit_YYYYMMDD_HHMMSS_*.json` を確認し、product_info フィールドに製品情報が記録されているか確認：

```json
{
  "execution_id": "...",
  "product_info": {
    "product_name": "トランスブロット® Turbo™ ミニ PVDF 転写パック",
    "maker_name": "BIO-RAD",
    "maker_code": "170-4156",
    "quantity": "1個",
    "product_url": "https://www.bio-rad.com/ja-jp/sku/1704156-..."
  },
  ...
}
```

**4. エラーケースのテスト**

- PII検出：製品情報に個人情報（メールアドレス等）を含めた場合、AIがブロックするか確認
- URL検証失敗：無効なURLを選択した場合、AIが警告して再入力を促すか確認
- Web検索失敗：検索結果が0件の場合、AIが手動URL入力を促すか確認

## Implementation Milestones

### Phase 1: テンプレート拡張（30分）
1. `template_processor.py` の `create_email_body()` メソッドに新引数追加（maker_name, maker_code, quantity、デフォルト値=""）
2. 変数マッピングに新変数追加（「メーカー名」、「メーカーコード」、「数量」）
3. 簡単な単体テストで動作確認（任意）

### Phase 2: main.py 拡張（30分）
1. `render_email()` メソッドに新引数追加（デフォルト値=""）
2. `send_bulk()` メソッドに新引数追加（デフォルト値=""）
3. `render_email()` 呼び出し箇所で新引数を渡す
4. 監査ログ出力呼び出しで product_info を渡す（付与条件を適切に設定）

### Phase 3: 監査ログ拡張とテスト修正（20分）
1. `audit_logger.py` の `write_audit_log()` メソッドに product_info 引数追加（Optional、デフォルトNone）
2. ログエントリに product_info を追加
3. `test_send_bulk_dedupe.py` と `test_rerun_detection.py` の `_AuditStub.write_audit_log()` に product_info 引数追加
4. 既存テストが引き続きパスすることを確認（pytest tests/）

### Phase 4: AIチャット統合テスト（30分）
1. AIチャットで対話的に製品情報を入力
2. WebSearchでURL検索
3. メール送信実行
4. メール本文と監査ログの確認

**合計推定時間: 約2時間**

## Risks and Mitigations

### Risk 1: 既存テストへの影響
**リスク:** `write_audit_log()` の引数追加により、テストスタブが未対応でテストが失敗する可能性

**対策:**
- 新引数はすべてデフォルト値を設定し、後方互換性を維持
- `test_send_bulk_dedupe.py` と `test_rerun_detection.py` の `_AuditStub.write_audit_log()` に product_info 引数を追加（デフォルト値=None）
- その他の既存テストは修正不要

**検証:** 実装後に `pytest tests/` を実行し、すべてのテストがパスすることを確認

### Risk 2: 再実行判定キーの問題
**リスク:** 現在の再実行判定は template_content ベースで、製品情報の差分（例：同じテンプレートだが製品が異なる）を見落とす可能性

**対策:**
- 現行の実装を維持し、このリスクは許容する
- 将来的に改善が必要な場合は、dedupe_key の計算に製品情報（product_name, maker_code等）を含める

**理由:**
- 同じ製品を同じ連絡先に24時間以内に再送することは稀
- 製品が異なる場合はテンプレート内容も変わることが多い（期待する内容.txtの例では製品名が本文に含まれる）

### Risk 3: テンプレート互換性
**リスク:** 既存のテンプレートファイルに新変数（«メーカー名»等）がない場合、変数が展開されずそのまま残る

**対策:**
- `render()` は strict=False で実行されるため、未定義変数はそのまま残る（エラーにはならない）
- ユーザーには新しいテンプレート変数の使用を推奨するが、既存テンプレートも引き続き動作

**検証:** 既存のテンプレートファイルでメール送信テストを実施

### Risk 4: AIチャット側の実装負担
**リスク:** AIチャット側での対話フロー、WebSearch、PII検出、URL検証の統合は、このPython実装とは別に実施が必要

**対策:**
- Python側の実装は最小限に抑え、AIチャット側の負担を明確化
- AIチャット側の実装は、Claude Codeの標準的なツール（WebSearch, Grep, Read等）を使用
- 段階的な実装：まずPython側を実装し、その後AIチャット側の統合を進める

## Summary

この実装により、見積依頼メール送信が大幅に効率化されます：

### Pythonスクリプト側の変更（約45行、2時間）

1. **テンプレート変数の拡張**: «メーカー名»/{{メーカー名}}、«メーカーコード»/{{メーカーコード}}、«数量»/{{数量}} を追加
2. **引数拡張**: `send_bulk()` と `render_email()` に製品情報の引数を追加（デフォルト値=""で後方互換性維持）
3. **監査ログ拡張**: 製品情報を監査ログに記録（適切な付与条件で）
4. **テストスタブ修正**: `_AuditStub.write_audit_log()` に product_info 引数追加（2ファイル）
5. **既存機能の維持**: 重複排除、再実行検知、Message-ID取得などは変更なし

### AIチャット側の統合（別途実施）

1. **対話的な製品情報収集**: ユーザーとの対話で製品名、メーカー名、メーカーコード、数量を収集
2. **PII検出**: 個人情報が含まれていないか確認
3. **WebSearch統合**: 製品ページURLを自動検索し、候補を提示
4. **URL検証**: URLの有効性を確認
5. **メール送信**: すべての情報が揃ったら `send_bulk()` を呼び出し

### 期待される効果

実装後、ユーザーはAIチャットで「見積依頼メールを送信して」と依頼するだけで：
- AIが製品情報を順次質問
- 製品ページURLを自動検索・提示
- メール本文に詳細な製品情報（製品名、メーカー名、メーカーコード、数量、製品URL）を自動挿入
- 期待するメール内容を生成して送信

従来の手作業でのURL検索やコピー＆ペーストが不要となり、メール送信の効率が大幅に向上します。

## 変更サマリ

- **変更ファイル数**: 5ファイル（うちテストスタブ2ファイル）
- **推定変更行数**: 約45行
- **推定実装時間**: 約2時間
- **新規ファイル**: なし
- **設定変更**: なし
