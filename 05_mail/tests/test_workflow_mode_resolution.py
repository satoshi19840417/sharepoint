from pathlib import Path
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.main import QuoteRequestSkill
from scripts.workflow_service import WorkflowService
from scripts.workflow_types import HearingInput


class WorkflowModeResolutionTests(unittest.TestCase):
    def test_default_workflow_mode_is_legacy(self):
        skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
        service = WorkflowService(skill)
        self.assertEqual(service.resolve_workflow_mode(None), "legacy")

    def test_cli_workflow_mode_takes_precedence(self):
        skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
        skill.config["workflow_mode_default"] = "legacy"
        service = WorkflowService(skill)
        self.assertEqual(service.resolve_workflow_mode("enhanced"), "enhanced")

    def test_config_workflow_mode_applies_when_cli_missing(self):
        skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
        skill.config["workflow_mode_default"] = "enhanced"
        service = WorkflowService(skill)
        self.assertEqual(service.resolve_workflow_mode(None), "enhanced")

    def test_send_mode_resolution(self):
        skill = QuoteRequestSkill(config_path=str(SKILL_DIR / "config.json"))
        service = WorkflowService(skill)
        hearing = HearingInput.from_dict({"send_mode": "manual"})
        self.assertEqual(service.resolve_send_mode(None, hearing), "manual")
        self.assertEqual(service.resolve_send_mode("draft_only", hearing), "draft_only")


if __name__ == "__main__":
    unittest.main()

