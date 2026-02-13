import datetime as dt
from pathlib import Path
import sys
import tempfile
import unittest


SKILL_DIR = Path(__file__).resolve().parents[1]
if str(SKILL_DIR) not in sys.path:
    sys.path.insert(0, str(SKILL_DIR))

from scripts.draft_repository import DraftRepository


class DraftNamingAndStorageTests(unittest.TestCase):
    def test_filename_rule_and_sanitization(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = DraftRepository(Path(tmp))
            run_started_at = dt.datetime(2026, 2, 13, 0, 30, tzinfo=dt.timezone.utc)
            filename = repo.build_draft_filename(
                run_started_at=run_started_at,
                product_name='A/B:C*D?"E<F>G|H........',
                request_id="request-1",
                run_id="run-1",
            )
            self.assertTrue(filename.startswith("260213_"))
            self.assertTrue(filename.endswith(".md"))
            self.assertNotIn("/", filename)
            self.assertNotIn(":", filename)
            self.assertNotIn("|", filename)

    def test_duplicate_filenames_get_version_suffix(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = DraftRepository(Path(tmp))
            run_started_at = dt.datetime.now(dt.timezone.utc)
            p1 = repo.save_draft(
                content="# A",
                run_started_at=run_started_at,
                product_name="同名製品",
                request_id="request-dup",
                run_id="run-dup",
            )
            p2 = repo.save_draft(
                content="# B",
                run_started_at=run_started_at,
                product_name="同名製品",
                request_id="request-dup",
                run_id="run-dup",
            )
            self.assertTrue(p1.exists())
            self.assertTrue(p2.exists())
            self.assertNotEqual(p1.name, p2.name)
            self.assertIn("_v2.md", p2.name)

    def test_move_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = DraftRepository(Path(tmp))
            run_started_at = dt.datetime.now(dt.timezone.utc)
            p = repo.save_draft(
                content="# A",
                run_started_at=run_started_at,
                product_name="製品A",
                request_id="request-1",
                run_id="run-1",
            )
            completed = repo.move_to_completed(p)
            self.assertTrue(completed.exists())
            self.assertIn(str(Path("outputs") / "completed"), str(completed))


if __name__ == "__main__":
    unittest.main()

