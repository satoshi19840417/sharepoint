"""
run_aimitsu_workflow.py - 相見積改良フロー CLI
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _import_runtime():
    if __package__:
        from .main import QuoteRequestSkill  # type: ignore
        from .workflow_service import WorkflowService  # type: ignore
        return QuoteRequestSkill, WorkflowService

    this_file = Path(__file__).resolve()
    scripts_dir = this_file.parent
    skill_dir = scripts_dir.parent
    repo_root = skill_dir.parent
    for p in (repo_root, skill_dir):
        if str(p) not in sys.path:
            sys.path.insert(0, str(p))
    from scripts.main import QuoteRequestSkill  # type: ignore
    from scripts.workflow_service import WorkflowService  # type: ignore

    return QuoteRequestSkill, WorkflowService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run aimitsu enhanced/legacy workflow.")
    parser.add_argument("--config-path", default="", help="config.json path")
    parser.add_argument("--contacts-csv", required=True, help="Contact CSV path")
    parser.add_argument("--template", default="", help="Template path (.docx/.txt)")
    parser.add_argument("--subject", default="見積依頼", help="Mail subject")
    parser.add_argument("--product-name", required=True, help="Product name")
    parser.add_argument("--product-features", default="", help="Product features")
    parser.add_argument("--product-url", required=True, help="Product URL")
    parser.add_argument("--maker-name", default="", help="Maker name")
    parser.add_argument("--maker-code", default="UNKNOWN", help="Maker code")
    parser.add_argument("--quantity", default="", help="Quantity")
    parser.add_argument("--workflow-mode", choices=["enhanced", "legacy"], default="")
    parser.add_argument("--send-mode", choices=["auto", "manual", "draft_only"], default="")
    parser.add_argument("--hearing-input", default="", help="hearing_input JSON file path")
    parser.add_argument("--request-id", default="", help="Reuse request_id for rerun")
    parser.add_argument("--rerun-of-run-id", default="", help="Optional rerun_of_run_id")
    parser.add_argument("--user-approved", action="store_true", help="Set user_approved=true")
    return parser.parse_args()


def main() -> int:
    QuoteRequestSkill, WorkflowService = _import_runtime()
    args = parse_args()
    skill = QuoteRequestSkill(config_path=args.config_path or None)

    contacts_result = skill.load_contacts(args.contacts_csv)
    if not contacts_result.get("success"):
        print(
            json.dumps(
                {
                    "error": "contacts load failed",
                    "errors": contacts_result.get("errors", []),
                    "warnings": contacts_result.get("warnings", []),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 4

    template_result = skill.load_template(args.template if args.template else None)
    if not template_result.get("success"):
        print(
            json.dumps(
                {"error": "template load failed", "detail": template_result.get("error", "")},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 4

    workflow_service = WorkflowService(skill)
    hearing_input = workflow_service.load_hearing_input(args.hearing_input)
    result = workflow_service.execute(
        workflow_mode=args.workflow_mode or None,
        send_mode=args.send_mode or None,
        hearing_input=hearing_input,
        records=contacts_result.get("records", []),
        subject=args.subject,
        template_content=template_result.get("content", ""),
        product_name=args.product_name,
        product_features=args.product_features,
        product_url=args.product_url,
        maker_name=args.maker_name,
        maker_code=args.maker_code,
        quantity=args.quantity,
        input_file=args.contacts_csv,
        request_id=args.request_id,
        rerun_of_run_id=args.rerun_of_run_id,
        user_approved=bool(args.user_approved),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    state = str(result.get("state", "failed"))
    if state == "completed":
        return 0
    if state in {"pending", "blocked"}:
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

