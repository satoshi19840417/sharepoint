#!/usr/bin/env python3
"""
rerun_override.py - scoped rerun override controller
"""

from __future__ import annotations

import argparse
import getpass
import json
import re
import socket
import sys
from pathlib import Path
from typing import Any, Dict

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.send_ledger import OVERRIDE_KIND_RECIPIENT, OVERRIDE_KIND_REQUEST_KEY, SendLedger

EXIT_OK = 0
EXIT_INVALID_INPUT = 4


def _normalize_email(value: str) -> str:
    raw = str(value or "").strip().lower()
    match = re.search(
        r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})",
        raw,
    )
    return match.group(1) if match else raw


def _load_config(config_path: str) -> Dict[str, Any]:
    path = Path(config_path)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[1] / path
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _build_ledger(config: Dict[str, Any]) -> SendLedger:
    base_dir = Path(__file__).resolve().parents[1]
    ledger_path_cfg = str(config.get("ledger_sqlite_path", "./logs/send_ledger.sqlite3"))
    ledger_path = base_dir / ledger_path_cfg if not Path(ledger_path_cfg).is_absolute() else Path(ledger_path_cfg)
    return SendLedger(
        str(ledger_path),
        retention_days=int(config.get("log_retention_days", 90)),
        busy_timeout_ms=int(config.get("dedupe_busy_timeout_ms", 15000)),
        backoff_attempts=int(config.get("dedupe_retry_attempts", 5)),
        credential_target_name=str(config.get("credential_target_name", "")) or None,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage scoped rerun overrides")
    parser.add_argument("--config", default="config.json", help="path to config.json")
    parser.add_argument("--allow-key", default="", help="allow specific request_key")
    parser.add_argument("--allow-recipient", default="", help="allow specific recipient email")
    parser.add_argument("--ttl-min", type=int, default=0, help="override ttl minutes (1..30)")
    parser.add_argument("--reason", default="", help="override reason")
    parser.add_argument("--status", action="store_true", help="show active overrides")
    parser.add_argument("--clear", action="store_true", help="clear all overrides")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = _load_config(args.config)
    except Exception as exc:
        print(f"設定ファイル読込エラー: {exc}")
        return EXIT_INVALID_INPUT

    op_flags = [
        bool(args.allow_key),
        bool(args.allow_recipient),
        bool(args.status),
        bool(args.clear),
    ]
    if sum(1 for f in op_flags if f) != 1:
        print("操作は1つだけ指定してください: --allow-key / --allow-recipient / --status / --clear")
        return EXIT_INVALID_INPUT

    ledger = _build_ledger(config)
    operator = getpass.getuser()
    host = socket.gethostname()

    if args.status:
        rows = ledger.get_override_status()
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return EXIT_OK

    if args.clear:
        deleted = ledger.clear_overrides()
        print(f"cleared={deleted}")
        return EXIT_OK

    ttl_min = int(args.ttl_min)
    reason = str(args.reason or "").strip()
    if not (1 <= ttl_min <= 30):
        print("--ttl-min は 1..30 で指定してください。")
        return EXIT_INVALID_INPUT
    if not reason:
        print("--reason は必須です。")
        return EXIT_INVALID_INPUT

    if args.allow_key:
        request_key = str(args.allow_key).strip()
        if not request_key:
            print("--allow-key が空です。")
            return EXIT_INVALID_INPUT
        row_id = ledger.add_override(
            kind=OVERRIDE_KIND_REQUEST_KEY,
            target_hash=request_key,
            ttl_min=ttl_min,
            reason=reason,
            operator=operator,
            host=host,
            command_summary_redacted=f"--allow-key {request_key} --ttl-min {ttl_min} --reason <redacted>",
        )
        print(f"added_override_id={row_id} kind=request_key")
        return EXIT_OK

    normalized_email = _normalize_email(args.allow_recipient)
    if not normalized_email or "@" not in normalized_email:
        print("--allow-recipient のメール形式が不正です。")
        return EXIT_INVALID_INPUT
    recipient_hash = ledger.hash_recipient(normalized_email)
    row_id = ledger.add_override(
        kind=OVERRIDE_KIND_RECIPIENT,
        target_hash=recipient_hash,
        ttl_min=ttl_min,
        reason=reason,
        operator=operator,
        host=host,
        command_summary_redacted=f"--allow-recipient <redacted_email> --ttl-min {ttl_min} --reason <redacted>",
    )
    print(f"added_override_id={row_id} kind=recipient")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
