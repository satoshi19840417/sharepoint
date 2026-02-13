"""Core conversion flow for Excel manual -> PowerPoint."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from manual_to_ppt.generate_ppt import PowerPointGenerator
from manual_to_ppt.parse_manual import ExcelManualParser

STEP_PATTERN = re.compile(r"^(\d+)\.(.+)$")


def extract_step_info(text_content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract steps from parsed text entries."""
    steps: list[dict[str, Any]] = []
    for item in text_content:
        if item.get("type") != "text":
            continue
        text = str(item.get("value", ""))
        match = STEP_PATTERN.match(text)
        if not match:
            continue
        steps.append(
            {
                "number": int(match.group(1)),
                "text": match.group(2).strip(),
                "row": int(item.get("row", 0)),
            }
        )
    return steps


def match_images_to_steps(
    steps: list[dict[str, Any]], images: list[dict[str, Any]]
) -> dict[int, dict[str, Any]]:
    """Associate images with each step based on row positions."""
    matched: dict[int, dict[str, Any]] = {}
    ordered_steps = sorted(steps, key=lambda step: step["row"])
    for index, step in enumerate(ordered_steps):
        current_row = int(step["row"])
        next_row = int(ordered_steps[index + 1]["row"]) if index + 1 < len(ordered_steps) else None
        step_images: list[dict[str, Any]] = []
        for image in images:
            image_row = int(image.get("row", 0))
            if image_row < current_row:
                continue
            if next_row is not None and image_row >= next_row:
                continue
            step_images.append(image)
        matched[int(step["number"])] = {"step": step, "images": step_images}
    return matched


def convert_excel_to_ppt(
    excel_path: str | Path,
    output_path: str | Path,
    temp_dir: str | Path = "temp/images",
    logo_path: str | None = None,
    color_scheme: dict[str, tuple[int, int, int]] | None = None,
) -> dict[str, Any]:
    """Convert an Excel manual to a PowerPoint file."""
    excel_path = Path(excel_path)
    output_path = Path(output_path)
    temp_dir = Path(temp_dir)

    parser = ExcelManualParser(str(excel_path), str(temp_dir))
    content = parser.parse()
    if not content:
        raise RuntimeError("Failed to parse Excel manual.")

    text_content = [item for item in content if item.get("type") == "text"]
    image_content = [item for item in content if item.get("type") == "image"]
    steps = extract_step_info(text_content)
    matched_data = match_images_to_steps(steps, image_content)

    generator = PowerPointGenerator(
        output_path=str(output_path),
        logo_path=logo_path,
        color_scheme=color_scheme,
    )
    generator.add_title_slide(title="相見積操作マニュアル", subtitle="見積依頼の作成と送信")

    for step_num, data in sorted(matched_data.items()):
        step_info = data["step"]
        images = data["images"]
        main_image_path = images[0]["path"] if images else None
        additional_images = images[1:] if len(images) > 1 else None
        generator.add_content_slide(
            step_number=step_num,
            step_text=step_info["text"],
            image_path=main_image_path,
            additional_images=additional_images,
        )

    if not generator.save():
        raise RuntimeError("Failed to generate PowerPoint.")

    slides_count = len(generator.prs.slides)
    return {
        "success": True,
        "steps_count": len(steps),
        "slides_count": slides_count,
        "output_path": str(output_path),
    }

