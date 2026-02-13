"""
統合実行スクリプト - ExcelマニュアルをPowerPointに変換

このスクリプトは、以下の処理を実行します：
1. Excelマニュアルを解析（parse_manual.py）
2. PowerPointスライドを生成（generate_ppt.py）
"""

import os
import sys
from pathlib import Path
import re

# Windows環境でのUnicodeエンコーディング設定
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# スクリプトのディレクトリをパスに追加
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from parse_manual import ExcelManualParser
from generate_ppt import PowerPointGenerator


def extract_step_info(text_content):
    """
    テキストからステップ情報を抽出

    Args:
        text_content: テキストコンテンツのリスト

    Returns:
        ステップ情報の辞書リスト
    """
    steps = []
    for item in text_content:
        if item['type'] == 'text':
            text = item['value']
            # "1.いいえで閉じる" のような形式を解析
            match = re.match(r'^(\d+)\.(.+)$', text)
            if match:
                step_num = int(match.group(1))
                step_text = match.group(2).strip()
                steps.append({
                    'number': step_num,
                    'text': step_text,
                    'row': item['row']
                })
    return steps


def match_images_to_steps(steps, images):
    """
    ステップに画像をマッチング

    Args:
        steps: ステップ情報のリスト
        images: 画像情報のリスト

    Returns:
        ステップと画像をマッチングした辞書
    """
    matched = {}

    for step in steps:
        step_num = step['number']
        step_row = step['row']

        # このステップに対応する画像を検索
        # ステップのすぐ下にある画像を探す
        step_images = []
        for img in images:
            img_row = img['row']
            # ステップの行以降で、次のステップの前にある画像を対象
            if img_row >= step_row:
                # 次のステップの行を取得
                next_step_row = None
                for next_step in steps:
                    if next_step['number'] > step_num:
                        next_step_row = next_step['row']
                        break

                # 次のステップがある場合、その前まで
                if next_step_row is None or img_row < next_step_row:
                    step_images.append(img)

        matched[step_num] = {
            'step': step,
            'images': step_images
        }

    return matched


def convert_excel_to_ppt(excel_path, output_path, temp_dir="temp/images", logo_path=None):
    """
    ExcelマニュアルをPowerPointに変換

    Args:
        excel_path: 入力Excelファイルのパス
        output_path: 出力PowerPointファイルのパス
        temp_dir: 一時画像保存ディレクトリ
        logo_path: ロゴ画像のパス（オプション）

    Returns:
        成功した場合True、失敗した場合False
    """
    print("=" * 60)
    print("ExcelマニュアルをPowerPointに変換")
    print("=" * 60)
    print(f"入力: {excel_path}")
    print(f"出力: {output_path}")
    print(f"一時ディレクトリ: {temp_dir}\n")

    # ステップ1: Excelマニュアルを解析
    print("\n[1/3] Excelマニュアルを解析中...")
    print("-" * 60)
    parser = ExcelManualParser(str(excel_path), str(temp_dir))
    content = parser.parse()

    if not content:
        print("✗ Excelマニュアルの解析に失敗しました")
        return False

    # テキストと画像を分離
    text_content = [item for item in content if item['type'] == 'text']
    image_content = [item for item in content if item['type'] == 'image']

    # ステップ2: ステップ情報を抽出してマッチング
    print("\n[2/3] ステップ情報を整理中...")
    print("-" * 60)
    steps = extract_step_info(text_content)
    print(f"✓ 抽出したステップ数: {len(steps)}")

    matched_data = match_images_to_steps(steps, image_content)
    print(f"✓ ステップと画像のマッチング完了")

    # マッチング結果を表示
    for step_num, data in sorted(matched_data.items()):
        step_info = data['step']
        images = data['images']
        print(f"  STEP {step_num}: {step_info['text']}")
        print(f"    画像数: {len(images)}")

    # ステップ3: PowerPointを生成
    print("\n[3/3] PowerPointスライドを生成中...")
    print("-" * 60)
    generator = PowerPointGenerator(str(output_path), logo_path=logo_path)

    # タイトルスライド
    generator.add_title_slide(
        title="相見積操作マニュアル",
        subtitle="見積依頼の作成と送信"
    )

    # 各ステップのスライド
    for step_num, data in sorted(matched_data.items()):
        step_info = data['step']
        images = data['images']

        # メイン画像（最初の画像）
        main_image_path = images[0]['path'] if images else None

        # 追加画像（2枚目以降）
        additional_images = images[1:] if len(images) > 1 else None

        generator.add_content_slide(
            step_number=step_num,
            step_text=step_info['text'],
            image_path=main_image_path,
            additional_images=additional_images
        )

    # 保存
    print("\n" + "=" * 60)
    print("PowerPointファイルを保存中...")
    print("=" * 60)
    if generator.save():
        print(f"\n✓ 変換が正常に完了しました")
        print(f"  出力ファイル: {output_path}")
        return True
    else:
        print(f"\n✗ 変換に失敗しました")
        return False


def main():
    """メイン処理"""
    # ファイルパス設定
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    excel_path = project_dir / "相見積操作マニュアル.xlsx"
    output_path = project_dir / "相見積操作マニュアル.pptx"
    temp_dir = project_dir / "temp" / "images"
    logo_path = project_dir / "CellGenTech_Logo_20221203_Blue_Horizontal.png"

    # Excelファイルの存在確認
    if not excel_path.exists():
        print(f"✗ エラー: Excelファイルが見つかりません: {excel_path}")
        return 1

    # ロゴファイルの存在確認（警告のみ）
    if not logo_path.exists():
        print(f"! 警告: ロゴファイルが見つかりません: {logo_path}")
        print(f"  ロゴなしでPowerPointを生成します")
        logo_path = None

    # 変換実行
    success = convert_excel_to_ppt(
        excel_path=excel_path,
        output_path=output_path,
        temp_dir=temp_dir,
        logo_path=str(logo_path) if logo_path else None
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
