"""
draft_repository.py - Markdown草案の命名・保存・移動
"""

from __future__ import annotations

import datetime as dt
import hashlib
import re
from pathlib import Path
from zoneinfo import ZoneInfo

INVALID_WINDOWS_CHARS = re.compile(r'[\\/:*?"<>|]')


class DraftRepository:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.drafts_dir = self.base_dir / "outputs" / "drafts"
        self.completed_dir = self.base_dir / "outputs" / "completed"
        self.error_dir = self.base_dir / "outputs" / "error"
        for d in (self.drafts_dir, self.completed_dir, self.error_dir):
            d.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def build_short_hash(value: str, length: int = 12) -> str:
        return hashlib.sha256(value.encode("utf-8")).hexdigest()[:length]

    @staticmethod
    def sanitize_product_name(product_name: str) -> str:
        raw = str(product_name or "")
        text = INVALID_WINDOWS_CHARS.sub("_", raw)
        text = text.rstrip(" .")
        text = text.strip()
        if not text:
            text = "unknown_product"
        if len(text) > 40:
            text = text[:40]
        return text

    @staticmethod
    def yymmdd_jst(run_started_at: dt.datetime) -> str:
        jst = run_started_at.astimezone(ZoneInfo("Asia/Tokyo"))
        return jst.strftime("%y%m%d")

    def build_draft_filename(
        self,
        *,
        run_started_at: dt.datetime,
        product_name: str,
        request_id: str,
        run_id: str,
    ) -> str:
        date_part = self.yymmdd_jst(run_started_at)
        product_safe = self.sanitize_product_name(product_name)
        request_id12 = self.build_short_hash(request_id)
        run_id12 = self.build_short_hash(run_id)
        return f"{date_part}_{product_safe}_{request_id12}_{run_id12}.md"

    def _resolve_unique_path(self, directory: Path, filename: str) -> Path:
        target = directory / filename
        if not target.exists():
            return target
        stem = target.stem
        suffix = target.suffix
        version = 2
        while True:
            candidate = directory / f"{stem}_v{version}{suffix}"
            if not candidate.exists():
                return candidate
            version += 1

    def save_draft(
        self,
        *,
        content: str,
        run_started_at: dt.datetime,
        product_name: str,
        request_id: str,
        run_id: str,
    ) -> Path:
        filename = self.build_draft_filename(
            run_started_at=run_started_at,
            product_name=product_name,
            request_id=request_id,
            run_id=run_id,
        )
        path = self._resolve_unique_path(self.drafts_dir, filename)
        path.write_text(content, encoding="utf-8")
        return path

    def move_to_completed(self, draft_path: Path) -> Path:
        destination = self._resolve_unique_path(self.completed_dir, Path(draft_path).name)
        return Path(draft_path).replace(destination)

    def move_to_error(self, draft_path: Path) -> Path:
        destination = self._resolve_unique_path(self.error_dir, Path(draft_path).name)
        return Path(draft_path).replace(destination)

