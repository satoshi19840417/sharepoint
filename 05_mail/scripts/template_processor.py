"""
template_processor.py - テンプレート処理モジュール

要件定義書 v11 §6.5 に基づくテンプレート処理機能を提供する。
- Word(.docx)形式: «変数名» 形式の差し込み
- テキスト(.txt)形式: {{変数名}} 形式の差し込み
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# python-docxは実行時にインポート（オプショナル依存）
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


@dataclass
class TemplateResult:
    """テンプレート処理結果"""
    success: bool
    content: str = ""
    error: str = ""
    missing_variables: List[str] = None

    def __post_init__(self):
        if self.missing_variables is None:
            self.missing_variables = []


class TemplateProcessor:
    """テンプレート処理クラス"""

    # Word形式の差し込み変数パターン（«変数名»）
    WORD_VARIABLE_PATTERN = re.compile(r'«([^»]+)»')

    # 汎用形式の差し込み変数パターン（{{変数名}}）
    GENERIC_VARIABLE_PATTERN = re.compile(r'\{\{([^}]+)\}\}')

    def __init__(self):
        pass

    def load_template(self, filepath: str) -> TemplateResult:
        """
        テンプレートファイルを読み込む。

        Args:
            filepath: テンプレートファイルパス

        Returns:
            TemplateResult（contentにテンプレート内容）
        """
        path = Path(filepath)

        if not path.exists():
            return TemplateResult(
                success=False,
                error=f"ファイルが存在しません: {filepath}"
            )

        suffix = path.suffix.lower()

        if suffix == ".docx":
            return self._load_docx(path)
        elif suffix == ".txt":
            return self._load_text(path)
        else:
            return TemplateResult(
                success=False,
                error=f"サポートされていないファイル形式です: {suffix}"
            )

    def _load_docx(self, path: Path) -> TemplateResult:
        """Wordファイルを読み込む"""
        if not DOCX_AVAILABLE:
            return TemplateResult(
                success=False,
                error="python-docxがインストールされていません。"
            )

        try:
            doc = Document(str(path))
            paragraphs = [p.text for p in doc.paragraphs]
            content = "\n".join(paragraphs)
            return TemplateResult(success=True, content=content)
        except Exception as e:
            return TemplateResult(
                success=False,
                error=f"Wordファイル読み込みエラー: {e}"
            )

    def _load_text(self, path: Path) -> TemplateResult:
        """テキストファイルを読み込む"""
        try:
            # UTF-8で試行、失敗したらCP932
            try:
                content = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                content = path.read_text(encoding='cp932')
            return TemplateResult(success=True, content=content)
        except Exception as e:
            return TemplateResult(
                success=False,
                error=f"テキストファイル読み込みエラー: {e}"
            )

    def extract_variables(self, template_content: str) -> List[str]:
        """
        テンプレートから変数名を抽出する。

        Args:
            template_content: テンプレート内容

        Returns:
            変数名のリスト
        """
        variables = set()

        # Word形式
        for match in self.WORD_VARIABLE_PATTERN.finditer(template_content):
            variables.add(match.group(1).strip())

        # 汎用形式
        for match in self.GENERIC_VARIABLE_PATTERN.finditer(template_content):
            variables.add(match.group(1).strip())

        return list(variables)

    def render(self, template_content: str, variables: Dict[str, str],
               strict: bool = False) -> TemplateResult:
        """
        テンプレートに変数を適用する。

        Args:
            template_content: テンプレート内容
            variables: 変数辞書 {変数名: 値}
            strict: Trueの場合、未定義変数があればエラー

        Returns:
            TemplateResult
        """
        content = template_content
        missing = []

        # 必要な変数を抽出
        required_vars = self.extract_variables(template_content)

        # 欠損チェック
        for var in required_vars:
            if var not in variables:
                missing.append(var)

        if strict and missing:
            return TemplateResult(
                success=False,
                error=f"未定義の変数があります: {', '.join(missing)}",
                missing_variables=missing
            )

        # 変数置換（Word形式）
        for var_name, value in variables.items():
            content = content.replace(f"«{var_name}»", value)

        # 変数置換（汎用形式）
        for var_name, value in variables.items():
            content = content.replace(f"{{{{{var_name}}}}}", value)

        return TemplateResult(
            success=True,
            content=content,
            missing_variables=missing
        )

    def create_email_body(
        self,
        template_content: str,
        company_name: str,
        contact_name: str,
        product_name: str,
        product_features: str,
        product_url: str,
        **extra_variables
    ) -> TemplateResult:
        """
        メール本文を生成する（ヘルパーメソッド）。

        Args:
            template_content: テンプレート内容
            company_name: 会社名
            contact_name: 担当者名
            product_name: 製品名
            product_features: 製品特徴
            product_url: 製品URL
            **extra_variables: 追加の変数

        Returns:
            TemplateResult
        """
        variables = {
            "会社名": company_name,
            "担当者名": contact_name,
            "製品名": product_name,
            "製品特徴": product_features,
            "製品URL": product_url,
            # 一般的なエイリアス
            "姓": contact_name.split()[0] if " " in contact_name else contact_name,
        }
        variables.update(extra_variables)

        return self.render(template_content, variables, strict=False)


def get_default_template() -> str:
    """デフォルトのメールテンプレートを返す"""
    return """«会社名»
«担当者名» 様

お世話になっております。

下記製品のお見積りをお願いしたく、ご連絡いたしました。

■ 製品情報
製品名: «製品名»
特徴: «製品特徴»
製品ページ: «製品URL»

ご検討のほど、よろしくお願いいたします。
"""
