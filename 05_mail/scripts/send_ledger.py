"""
send_ledger.py - 送信履歴（再実行検知）管理モジュール

24時間以内の再実行検知に使う台帳をJSON Linesで保持する。
"""

import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class SendLedger:
    """送信台帳の読み書きを行うクラス。"""

    def __init__(self, ledger_path: str, retention_days: int = 30):
        self.ledger_path = Path(ledger_path)
        self.retention_days = retention_days
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _utcnow() -> datetime.datetime:
        return datetime.datetime.now(datetime.timezone.utc)

    @staticmethod
    def _to_utc(ts: datetime.datetime) -> datetime.datetime:
        if ts.tzinfo is None:
            return ts.replace(tzinfo=datetime.timezone.utc)
        return ts.astimezone(datetime.timezone.utc)

    @staticmethod
    def _parse_iso_timestamp(value: str) -> Optional[datetime.datetime]:
        if not value:
            return None
        try:
            return SendLedger._to_utc(datetime.datetime.fromisoformat(value))
        except ValueError:
            return None

    def load_recent_entries(self, now: Optional[datetime.datetime] = None) -> List[Dict[str, Any]]:
        """保持期間内の有効な履歴のみを読み込む。"""
        current = self._to_utc(now) if now is not None else self._utcnow()
        cutoff = current - datetime.timedelta(days=self.retention_days)

        if not self.ledger_path.exists():
            return []

        entries: List[Dict[str, Any]] = []
        with open(self.ledger_path, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    entry = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                ts = self._parse_iso_timestamp(str(entry.get("timestamp", "")))
                if ts is None or ts < cutoff:
                    continue

                entry["_timestamp_utc"] = ts.isoformat()
                entries.append(entry)

        return entries

    def find_recent(
        self,
        dedupe_key: str,
        window_hours: int = 24,
        run_id: Optional[str] = None,
        now: Optional[datetime.datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """指定キーのうち、window_hours以内に送信履歴がある場合は最新1件を返す。"""
        current = self._to_utc(now) if now is not None else self._utcnow()
        window_start = current - datetime.timedelta(hours=window_hours)

        entries = self.load_recent_entries(now=current)
        for entry in reversed(entries):
            if str(entry.get("dedupe_key", "")) != dedupe_key:
                continue
            if run_id and str(entry.get("run_id", "")) != run_id:
                continue
            ts = self._parse_iso_timestamp(str(entry.get("timestamp", "")))
            if ts is None:
                continue
            if ts >= window_start:
                return entry
        return None

    def append_entry(
        self,
        dedupe_key: str,
        recipient: str,
        message_id: str,
        run_id: str,
        sent_at: Optional[datetime.datetime] = None,
    ) -> Dict[str, Any]:
        """台帳に1件追記する。"""
        timestamp = self._to_utc(sent_at) if sent_at is not None else self._utcnow()
        entry = {
            "timestamp": timestamp.isoformat(),
            "dedupe_key": dedupe_key,
            "recipient": recipient,
            "message_id": message_id,
            "run_id": run_id,
        }
        with open(self.ledger_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry
