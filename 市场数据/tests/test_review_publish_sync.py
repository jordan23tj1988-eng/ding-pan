"""Real LOCAL bare git remotes only; source pages are copied real judgments."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from tests.test_review_publish import CODE, TASK, PROD, D, BUILDER
sys.path.insert(0, str(CODE))
import review_publish as pub
import sync_watchdog_candidate as sync


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="p0-git-", dir=TASK / "evidence")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "source"
        self.root.mkdir()
        (self.root / "_学习").mkdir()
        self.jpath = self.root / "_学习" / f"judgment_{D}.json"
        shutil.copy2(PROD / "_学习" / f"judgment_{D}.json", self.jpath)
        (self.root / "review_pages.py").write_text(BUILDER, encoding="utf-8")
        self.remote = self.base / "remote.git"
        self.repo = self.base / "repo"
        self.cmd(self.base, "init", "--bare", str(self.remote))
        self.cmd(self.base, "init", "-b", "master", str(self.repo))
        self.cmd(self.repo, "config", "user.name", "P0 isolated test")
        self.cmd(self.repo, "config", "user.email", "p0-test@example.invalid")
        self.cmd(self.repo, "config", "commit.gpgsign", "false")
        (self.repo / "README.md").write_text("Isolated local remote test only\n")
        self.cmd(self.repo, "add", "README.md")
        self.cmd(self.repo, "commit", "-m", "local test fixture")
        self.cmd(self.repo, "remote", "add", "origin", str(self.remote))
        self.cmd(self.repo, "push", "-u", "origin", "master")
        self.release()

    def cmd(self, cwd, *args):
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout.strip()

    def release(self):
        with patch.object(pub, "run_checks", return_value=[
            {"name": n, "status": "pass", "errors": [], "test_injection": True}
            for n in pub.REQUIRED_CHECKS]), patch.object(pub, "validate_references", return_value=[]):
            m = pub.build_release(self.root, D, publish=True)
        self.assertEqual(m["status"], "pass", m)
        return m

    def test_remote_rejection_not_success_retry_then_same_day_revision(self):
        hook = self.remote / "hooks" / "pre-receive"
        hook.write_text('#!/bin/sh\necho "CONTROLLED TEST: reject push" >&2\nexit 1\n'.replace('\\n','\n'), encoding="utf-8")
        failed = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(failed["status"], "fail", failed)
        self.assertIn("push", " ".join(failed["errors"]))
        self.assertFalse(sync.repo_synced(D, root=self.root, repo=self.repo))
        self.assertFalse((self.root / ".review_sync" / f"{D}.json").exists())
        hook.unlink()
        recovered = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(recovered["status"], "pass", recovered)
        self.assertTrue(sync.repo_synced(D, root=self.root, repo=self.repo))
        old_commit = recovered["remote_commit"]
        # NOOP commit still verifies the real remote.
        noop = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(noop["status"], "pass", noop)
        self.assertEqual(noop["remote_commit"], old_commit)
        self.jpath.write_bytes(self.jpath.read_bytes() + b"\n")
        newer = self.release()
        self.assertFalse(sync.repo_synced(D, root=self.root, repo=self.repo))
        updated = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(updated["status"], "pass", updated)
        self.assertEqual(updated["build_id"], newer["build_id"])
        self.assertNotEqual(updated["remote_commit"], old_commit)
        self.assertTrue(sync.repo_synced(D, root=self.root, repo=self.repo))

    def test_archive_existence_and_forged_record_do_not_suffice(self):
        (self.repo / "archive").mkdir()
        (self.repo / "archive" / f"{D}.html").write_text("CONTROLLED TEST obsolete flag")
        self.assertTrue(sync.review_done(D, root=self.root))
        self.assertFalse(sync.repo_synced(D, root=self.root, repo=self.repo))
        pointer = json.loads((self.root / "CURRENT.json").read_text())
        target = self.root / pointer["release"] / "site" / "cycle.html"
        target.write_text("CONTROLLED TAMPER")
        self.assertFalse(sync.review_done(D, root=self.root))
        result = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(result["status"], "fail")

    def test_copy_failure_propagates(self):
        with patch.object(sync.shutil, "copy2", side_effect=OSError("CONTROLLED COPY FAILURE")):
            result = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(result["status"], "fail", result)
        self.assertIn("CONTROLLED COPY FAILURE", " ".join(result["errors"]))
        self.assertFalse(sync.repo_synced(D, root=self.root, repo=self.repo))

    def test_pull_failure_propagates(self):
        self.cmd(self.repo, "remote", "set-url", "origin", str(self.base / "absent.git"))
        result = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(result["status"], "fail", result)
        self.assertFalse(sync.repo_synced(D, root=self.root, repo=self.repo))

    def test_commit_failure_propagates(self):
        hook = self.repo / ".git" / "hooks" / "pre-commit"
        hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        result = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(result["status"], "fail", result)
        self.assertIn("commit", " ".join(result["errors"]))
        self.assertFalse(sync.repo_synced(D, root=self.root, repo=self.repo))
        hook.unlink()
        self.assertEqual(sync.sync_release(self.root, self.repo, D)["status"], "pass")

    def test_remote_change_invalidates_record(self):
        result = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(result["status"], "pass", result)
        self.cmd(self.remote, "update-ref", "refs/heads/master", self.cmd(self.repo, "rev-parse", "HEAD~1"))
        self.assertFalse(sync.repo_synced(D, root=self.root, repo=self.repo))

    def test_robocopy_return_codes(self):
        for code in range(9):
            r = subprocess.CompletedProcess([], code, "", "CONTROLLED ROBOCOPY STATUS")
            with patch.object(sync.subprocess, "run", return_value=r):
                if code < 8:
                    self.assertEqual(sync.robocopy(self.root, self.repo), code)
                else:
                    with self.assertRaises(RuntimeError):
                        sync.robocopy(self.root, self.repo)

    def test_add_failure_is_propagated(self):
        original = sync.git
        def injected(repo, *args, **kw):
            if "add" in args:
                raise RuntimeError("CONTROLLED git add failure")
            return original(repo, *args, **kw)
        with patch.object(sync, "git", side_effect=injected):
            result = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(result["status"], "fail", result)
        self.assertIn("git add failure", " ".join(result["errors"]))
        self.assertFalse(sync.repo_synced(D, root=self.root, repo=self.repo))

    def test_unconfirmed_push_is_not_recorded(self):
        original = sync.git
        def injected(repo, *args, **kw):
            if args[0] == "ls-remote":
                raise RuntimeError("CONTROLLED remote confirmation unavailable")
            return original(repo, *args, **kw)
        with patch.object(sync, "git", side_effect=injected):
            result = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(result["status"], "fail", result)
        self.assertFalse((self.root / ".review_sync" / f"{D}.json").exists())
        # The remote did receive the commit; retry performs genuine confirmation.
        retry = sync.sync_release(self.root, self.repo, D)
        self.assertEqual(retry["status"], "pass", retry)

if __name__ == "__main__":
    unittest.main(verbosity=2)
