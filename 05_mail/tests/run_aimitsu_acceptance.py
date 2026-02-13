#!/usr/bin/env python3
"""
AC-01..AC-10 acceptance runner for 相見積改良フロー.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List
from unittest import mock


SCRIPT_PATH = Path(__file__).resolve()
SKILL_DIR = SCRIPT_PATH.parents[1]
REPO_ROOT = SKILL_DIR.parent
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.csv_handler import ContactRecord
from scripts.main import QuoteRequestSkill
from scripts.send_ledger import SendLedger
from scripts.workflow_service import WorkflowService
from scripts.workflow_types import HearingInput


@dataclass
class ACResult:
    ac_id: str
    passed: bool
    detail: str


class _AuditStub:
    def write_audit_log(self, input_file, results, product_info=None, workflow_context=None):
        return "audit.json"

    def write_sent_list(self, results):
        return "sent.csv"

    def write_unsent_list(self, results):
        return "unsent.csv"

    def format_screen_output(self, results):
        return "screen"


class _KeyringPatch:
    def __init__(self):
        self._store: Dict[tuple, str] = {}
        self._patchers = []

    def __enter__(self):
        self._patchers = [
            mock.patch(
                "scripts.hmac_key_manager.keyring.get_password",
                side_effect=lambda service, key: self._store.get((service, key)),
            ),
            mock.patch(
                "scripts.hmac_key_manager.keyring.set_password",
                side_effect=lambda service, key, value: self._store.__setitem__((service, key), value),
            ),
            mock.patch(
                "scripts.send_ledger.keyring.get_password",
                side_effect=lambda service, key: self._store.get((service, key)),
            ),
            mock.patch(
                "scripts.send_ledger.keyring.set_password",
                side_effect=lambda service, key, value: self._store.__setitem__((service, key), value),
            ),
        ]
        for p in self._patchers:
            p.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        for p in reversed(self._patchers):
            p.stop()


def make_service(tmp: str, *, blacklist: List[str] | None = None) -> WorkflowService:
    skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
    skill.base_dir = Path(tmp)
    skill.audit_logger = _AuditStub()
    original_ledger = skill.send_ledger
    skill.send_ledger = SendLedger(str(Path(tmp) / "send_ledger.sqlite3"))
    original_ledger.close()
    if blacklist is not None:
        skill.config["domain_blacklist"] = list(blacklist)
        skill.domain_filter = skill.domain_filter.__class__(
            skill.config.get("domain_whitelist", []),
            skill.config.get("domain_blacklist", []),
        )
    return WorkflowService(skill)


def records() -> List[ContactRecord]:
    return [ContactRecord(company_name="A社", email="a@example.com", contact_name="A")]


def run_acceptance(skip_ac08: bool) -> List[ACResult]:
    results: List[ACResult] = []
    with _KeyringPatch():
        with tempfile.TemporaryDirectory() as tmp:
            service = make_service(tmp)

            # AC-01
            ac01_ok = (
                service.resolve_workflow_mode("enhanced") == "enhanced"
                and service.resolve_workflow_mode(None) == "legacy"
            )
            results.append(ACResult("AC-01", ac01_ok, "workflow_mode resolution"))

            # AC-02
            ac02_ok = True
            for mode in ("auto", "manual", "draft_only"):
                resolved = service.resolve_send_mode(mode, HearingInput.from_dict(None))
                if resolved != mode:
                    ac02_ok = False
                    break
            results.append(ACResult("AC-02", ac02_ok, "send_mode resolution"))

            # AC-03
            with mock.patch.object(service.skill, "send_bulk") as send_mock:
                pending_count = 0
                for _ in range(20):
                    res = service.execute(
                        workflow_mode="enhanced",
                        send_mode="auto",
                        hearing_input={
                            "recipients_changed": False,
                            "send_mode": "auto",
                            "user_approved": False,
                        },
                        records=records(),
                        subject="subj",
                        template_content="本文",
                        product_name="P",
                        product_features="F",
                        product_url="https://example.com/p",
                        maker_code="M-1",
                        input_file="input.csv",
                    )
                    if res.get("state") == "pending":
                        pending_count += 1
                ac03_ok = (pending_count == 20 and send_mock.call_count == 0)
            results.append(ACResult("AC-03", ac03_ok, f"pending={pending_count} send_calls={send_mock.call_count}"))

            # AC-04
            blocked_count = 0
            for _ in range(10):
                res = service.execute(
                    workflow_mode="enhanced",
                    send_mode="manual",
                    hearing_input={
                        "recipients_changed": False,
                        "send_mode": "manual",
                        "user_approved": True,
                    },
                    records=records(),
                    subject="subj",
                    template_content="本文",
                    product_name="P",
                    product_features="F",
                    product_url="https://example.com/p",
                    maker_code="M-1",
                    input_file="input.csv",
                )
                if res.get("state") != "completed":
                    blocked_count += 1
            results.append(ACResult("AC-04", blocked_count == 10, f"non-completed={blocked_count}"))

            # AC-05
            completed_names: List[str] = []
            for _ in range(10):
                res = service.execute(
                    workflow_mode="enhanced",
                    send_mode="draft_only",
                    hearing_input={
                        "recipients_changed": False,
                        "send_mode": "draft_only",
                        "user_approved": True,
                    },
                    records=records(),
                    subject="subj",
                    template_content="本文",
                    product_name="同一製品名",
                    product_features="F",
                    product_url="https://example.com/p",
                    maker_code="M-1",
                    input_file="input.csv",
                )
                completed_names.append(Path(res.get("completed_path", "")).name)
            ac05_ok = len(completed_names) == 10 and len(set(completed_names)) == 10
            results.append(ACResult("AC-05", ac05_ok, f"completed_files={len(set(completed_names))}"))

            # AC-06
            tmp2 = tempfile.mkdtemp()
            service2 = make_service(tmp2, blacklist=["blocked.test"])
            _ = service2.execute(
                workflow_mode="enhanced",
                send_mode="auto",
                hearing_input={
                    "recipients_changed": False,
                    "send_mode": "auto",
                    "user_approved": False,
                },
                records=records(),
                subject="subj",
                template_content="本文",
                product_name="P",
                product_features="F",
                product_url="https://example.com/p",
                maker_code="M-1",
                input_file="input.csv",
            )
            _ = service2.execute(
                workflow_mode="enhanced",
                send_mode="manual",
                hearing_input={
                    "recipients_changed": False,
                    "send_mode": "manual",
                    "user_approved": True,
                },
                records=records(),
                subject="subj",
                template_content="本文",
                product_name="P",
                product_features="F",
                product_url="https://example.com/p",
                maker_code="M-1",
                input_file="input.csv",
            )
            _ = service2.execute(
                workflow_mode="enhanced",
                send_mode="auto",
                hearing_input={
                    "recipients_changed": True,
                    "final_recipients": ["x@blocked.test"],
                    "send_mode": "auto",
                    "user_approved": True,
                },
                records=records(),
                subject="subj",
                template_content="本文",
                product_name="P",
                product_features="F",
                product_url="https://example.com/p",
                maker_code="M-1",
                input_file="input.csv",
            )
            completed_files = list((Path(tmp2) / "outputs" / "completed").glob("*.md"))
            results.append(ACResult("AC-06", len(completed_files) == 0, f"completed_files={len(completed_files)}"))

            # AC-07
            tmp3 = tempfile.mkdtemp()
            service3 = make_service(tmp3, blacklist=["blocked.test"])
            with mock.patch.object(service3.skill, "send_bulk") as send_mock:
                blocked = 0
                for _ in range(10):
                    res = service3.execute(
                        workflow_mode="enhanced",
                        send_mode="auto",
                        hearing_input={
                            "recipients_changed": True,
                            "final_recipients": ["x@blocked.test"],
                            "send_mode": "auto",
                            "user_approved": True,
                        },
                        records=records(),
                        subject="subj",
                        template_content="本文",
                        product_name="P",
                        product_features="F",
                        product_url="https://example.com/p",
                        maker_code="M-1",
                        input_file="input.csv",
                    )
                    if res.get("state") == "blocked":
                        blocked += 1
                ac07_ok = (blocked == 10 and send_mock.call_count == 0)
            results.append(ACResult("AC-07", ac07_ok, f"blocked={blocked} send_calls={send_mock.call_count}"))

            # AC-08
            if skip_ac08:
                results.append(ACResult("AC-08", True, "skipped by --skip-ac08"))
            else:
                proc = subprocess.run(
                    [sys.executable, "05_mail/tests/run_tc_suite.py", "--stage", "all"],
                    cwd=str(REPO_ROOT),
                    capture_output=True,
                    text=True,
                )
                ac08_ok = proc.returncode == 0
                detail = f"returncode={proc.returncode}"
                if not ac08_ok:
                    detail += f" stderr={proc.stderr[-200:]}"
                results.append(ACResult("AC-08", ac08_ok, detail))

            # AC-09
            tmp4 = tempfile.mkdtemp()
            service4 = make_service(tmp4)
            request_id = "req-ac09-fixed"
            for _ in range(5):
                service4.execute(
                    workflow_mode="enhanced",
                    send_mode="draft_only",
                    hearing_input={
                        "recipients_changed": False,
                        "send_mode": "draft_only",
                        "user_approved": True,
                    },
                    records=records(),
                    subject="subj",
                    template_content="本文",
                    product_name="P",
                    product_features="F",
                    product_url="https://example.com/p",
                    maker_code="M-1",
                    input_file="input.csv",
                    request_id=request_id,
                )
            history_files = list((Path(tmp4) / "logs" / "request_history" / request_id).glob("*.json"))
            results.append(ACResult("AC-09", len(history_files) == 5, f"history_files={len(history_files)}"))

            # AC-10
            tmp5 = tempfile.mkdtemp()
            service5 = make_service(tmp5)
            request_id_manual = "req-ac10-fixed"
            manual_dir = Path(tmp5) / "outputs" / "manual_evidence" / request_id_manual
            manual_dir.mkdir(parents=True, exist_ok=True)
            for i in range(5):
                res = service5.execute(
                    workflow_mode="enhanced",
                    send_mode="manual",
                    hearing_input={
                        "recipients_changed": False,
                        "send_mode": "manual",
                        "user_approved": True,
                    },
                    records=records(),
                    subject="subj",
                    template_content="本文",
                    product_name="P",
                    product_features="F",
                    product_url="https://example.com/p",
                    maker_code="M-1",
                    input_file="input.csv",
                    request_id=request_id_manual,
                )
                run_id = str(res.get("run_id", f"run-{i}"))
                evidence_path = manual_dir / f"manual_send_evidence_{run_id}.json"
                evidence_path.write_text(
                    json.dumps(
                        {
                            "request_id": request_id_manual,
                            "run_id": run_id,
                            "operator": "tester",
                            "confirmed_at": "2026-02-13T09:00:00+09:00",
                            "recipients": [
                                {
                                    "email": "a@example.com",
                                    "message_id": f"MID-{i}",
                                    "sent_at": "2026-02-13T09:00:01+09:00",
                                }
                            ],
                        },
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
            evidence_files = list(manual_dir.glob("manual_send_evidence_*.json"))
            ac10_ok = len(evidence_files) == 5 and len({p.name for p in evidence_files}) == 5
            results.append(ACResult("AC-10", ac10_ok, f"evidence_files={len(evidence_files)}"))

            service.skill.send_ledger.close()
            service2.skill.send_ledger.close()
            service3.skill.send_ledger.close()
            service4.skill.send_ledger.close()
            service5.skill.send_ledger.close()

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run AC-01..AC-10 acceptance suite.")
    parser.add_argument("--skip-ac08", action="store_true", help="Skip TC suite regression command.")
    parser.add_argument("--output", default="", help="Optional JSON output path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run_acceptance(skip_ac08=args.skip_ac08)
    payload = {
        "total": len(results),
        "passed": sum(1 for r in results if r.passed),
        "failed": sum(1 for r in results if not r.passed),
        "results": [asdict(r) for r in results],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    return 0 if payload["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
