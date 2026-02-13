# send_bulk テスト入力テンプレート（IWAKI 2362-025N）

- 作成日: 2026-02-13
- 用途: `QuoteRequestSkill.send_bulk(...)` に渡すテスト入力の雛形
- 注意: このテンプレートは**実行しない**前提です（値確認・準備用）

## 1. 連絡先CSVテンプレート
- ファイル: `05_mail/test_artifacts/manual_research/20260213_iwaki_2362-025N_contacts_template.csv`
- 必須列: `会社名`, `メールアドレス`
- 推奨列: `担当者名`, `部署名`, `電話番号`

## 2. send_bulk 引数テンプレート（Python）
```python
from scripts.main import QuoteRequestSkill
from scripts.csv_handler import CSVHandler

# 入力ファイル（テンプレート）
csv_path = r"05_mail/test_artifacts/manual_research/20260213_iwaki_2362-025N_contacts_template.csv"

# スキル初期化（実行はしない）
skill = QuoteRequestSkill(config_path=r"05_mail/config.json")

# CSVロード（実行する場合のみ使用）
# records = CSVHandler(skill.encryption_manager).load_csv(csv_path).records

# テスト用 send_bulk 入力値（本レポート準拠）
subject = "【見積依頼】遠沈管Mini 25mL（2362-025N）"

template_content = """≪会社名≫
≪担当者名≫ 様

お世話になっております。

下記製品のお見積りをお願いしたく、ご連絡いたしました。

■ 製品情報
製品名: ≪製品名≫
メーカー名: ≪メーカー名≫
メーカーコード: ≪メーカーコード≫
数量: ≪数量≫
特徴: ≪製品特徴≫
製品ページ: ≪製品URL≫

ご検討のほど、よろしくお願いいたします。
"""

send_bulk_kwargs = {
    # "records": records,  # 実行時にCSVロード結果をセット
    "subject": subject,
    "template_content": template_content,
    "product_name": "遠沈管Mini 25mL（バルク包装）",
    "product_features": "容量25mL、PP/HDPE、29×75mm、放射線滅菌済み、DNase/RNase/DNAフリー、ノンパイロジェニック",
    "product_url": "https://iwaki.atgc.co.jp/products/tissue-culture/detail/27",
    "maker_name": "IWAKI（AGCテクノグラス）",
    "maker_code": "2362-025N",  # 旧型番2362-025は使用しない
    "quantity": "未指定",
    "input_file": csv_path,
}

# 実行しない（テンプレートのためコメントアウト）
# result = skill.send_bulk(**send_bulk_kwargs)
# print(result)
```

## 3. チェックポイント
- `maker_code` は必ず `2362-025N` を使用する（`2362-025` は旧型番）。
- `quantity` は本件要件どおり `未指定`。
- 価格情報は本テンプレートに含めない。

## 4. 実行時に変更する箇所（必要な場合のみ）
- `csv_path`
- `subject`
- `template_content`
- `records`（CSVロード結果）
