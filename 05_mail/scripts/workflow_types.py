"""
workflow_types.py - 相見積ワークフロー向け型定義
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

WorkflowMode = Literal["enhanced", "legacy"]
SendMode = Literal["auto", "manual", "draft_only"]
WorkflowState = Literal["completed", "pending", "blocked", "failed"]


@dataclass
class HearingInput:
    recipients_changed: bool = False
    final_recipients: List[str] = field(default_factory=list)
    send_mode: Optional[SendMode] = None
    other_requests: str = ""
    user_approved: bool = False

    @classmethod
    def from_dict(cls, raw: Optional[Dict[str, Any]]) -> "HearingInput":
        data = raw or {}
        return cls(
            recipients_changed=bool(data.get("recipients_changed", False)),
            final_recipients=[str(v) for v in (data.get("final_recipients") or [])],
            send_mode=data.get("send_mode"),
            other_requests=str(data.get("other_requests", "")),
            user_approved=bool(data.get("user_approved", False)),
        )


@dataclass
class WorkflowResult:
    request_id: str
    run_id: str
    workflow_mode: WorkflowMode
    send_mode: SendMode
    state: WorkflowState
    draft_path: str
    completed_path: str = ""
    error_path: str = ""
    history_path: str = ""
    blocked_reasons: List[str] = field(default_factory=list)
    audit_log_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "run_id": self.run_id,
            "workflow_mode": self.workflow_mode,
            "send_mode": self.send_mode,
            "state": self.state,
            "draft_path": self.draft_path,
            "completed_path": self.completed_path,
            "error_path": self.error_path,
            "history_path": self.history_path,
            "blocked_reasons": list(self.blocked_reasons),
            "audit_log_path": self.audit_log_path,
        }

