"""Candidate replacement for sync_watchdog.py; no installation or production defaults.

Old review_done/repo_synced/pending_dates/do_sync/main names are thin wrappers.
Configure REVIEW_ROOT and REVIEW_REPO for no-argument task compatibility, or pass
--root and --repo. Only accepted immutable site artifacts are mirrored. The old
whole-source robocopy /MIR behavior is deliberately not invoked.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from review_publish import (atomic_json, contained, digest, exclusive, fail,
                            read_json, tree_hashes, valid_date, verify_release)


def configured(root=None, repo=None):
    root = root if root is not None else os.environ.get("REVIEW_ROOT")
    repo = repo if repo is not None else os.environ.get("REVIEW_REPO")
    if not root or not repo:
        raise ValueError("explicit root/repo or REVIEW_ROOT/REVIEW_REPO required")
    root, repo = Path(root).resolve(strict=True), Path(repo).resolve(strict=True)
    if root == repo or root.is_relative_to(repo) or repo.is_relative_to(root):
        raise ValueError("source and git repo must be disjoint")
    return root, repo


def git(repo, *args, allowed=(0,), binary=False):
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True,
                            timeout=120, text=not binary,
                            **({} if binary else {"encoding": "utf-8", "errors": "replace"}))
    if result.returncode not in allowed:
        message = result.stderr.decode("utf-8", "replace") if binary else result.stderr
        raise RuntimeError(f"git {args[0]} failed ({result.returncode}): {message.strip()}")
    return result


def robocopy(src, dst, *extra):
    """Compatibility helper; return codes 0..7 are success, >=8 fail."""
    if not Path(src).is_dir():
        raise FileNotFoundError(src)
    result = subprocess.run(["robocopy", str(src), str(dst), *extra, "/R:2", "/W:3"],
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if not 0 <= result.returncode <= 7:
        raise RuntimeError(f"robocopy failed ({result.returncode}): {result.stderr}")
    return result.returncode


def review_done(d: str, *, root=None) -> bool:
    root = root if root is not None else os.environ.get("REVIEW_ROOT")
    return root is not None and verify_release(Path(root), d)["status"] == "pass"


def remote_tip(repo, remote, branch):
    if not isinstance(remote, str) or not re_safe(remote) or not re_safe(branch):
        raise ValueError("invalid remote/branch")
    result = git(repo, "ls-remote", "--exit-code", remote, "refs/heads/" + branch)
    lines = [line.split() for line in result.stdout.splitlines() if line.strip()]
    expected = "refs/heads/" + branch
    if len(lines) != 1 or len(lines[0]) != 2 or lines[0][1] != expected:
        raise ValueError("remote ref confirmation ambiguous")
    return lines[0][0]


def re_safe(value):
    import re
    return isinstance(value, str) and bool(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_./-]*", value)) and ".." not in value


def artifact_hashes(root, manifest):
    directory = contained(root, f"releases/{manifest['build_id']}")
    prefix = f"releases/{manifest['build_id']}"
    out = {f"{prefix}/manifest.json": digest(directory / "manifest.json"),
           "CURRENT.json": digest(contained(root, "CURRENT.json"))}
    for name, sha in manifest["page_hashes"].items():
        contained(directory / "site", name)
        out[f"{prefix}/site/{name}"] = sha
    return out


def verify_commit(repo, commit, artifacts):
    for name, sha in artifacts.items():
        if digest(contained(repo, name)) != sha:
            raise ValueError(f"mirror hash mismatch: {name}")
        content = git(repo, "show", f"{commit}:{name}", binary=True).stdout
        if hashlib.sha256(content).hexdigest() != sha:
            raise ValueError(f"confirmed commit artifact mismatch: {name}")


def repo_synced(d: str, *, root=None, repo=None, remote="origin", branch="master") -> bool:
    try:
        root, repo = configured(root, repo)
        valid_date(d)
        m = verify_release(root, d)
        if m["status"] != "pass":
            return False
        state = read_json(contained(root, f".review_sync/{d}.json"))
        if state.get("schema_version") != 1 or state.get("status") != "pass" or state.get("d") != d:
            return False
        if any(state.get(k) != m.get(k) for k in ("build_id", "revision", "manifest_sha256")):
            return False
        if state.get("repo") != str(repo) or state.get("remote") != remote or state.get("branch") != branch:
            return False
        if state.get("remote_url") != git(repo, "remote", "get-url", remote).stdout.strip():
            return False
        commit = remote_tip(repo, remote, branch)  # live confirmation, never archive.exists
        if state.get("remote_commit") != commit:
            return False
        artifacts = artifact_hashes(root, m)
        if state.get("artifact_hashes") != artifacts:
            return False
        verify_commit(repo, commit, artifacts)
        return True
    except Exception:
        return False


def copy_release(root, repo, git_dir, manifest):
    """Build private mirror first. Existing immutable versions are verified only."""
    build_id = manifest["build_id"]
    source = contained(root, f"releases/{build_id}")
    target = contained(repo, f"releases/{build_id}")
    expected = {"manifest.json": digest(source / "manifest.json")}
    expected.update({f"site/{name}": sha for name, sha in manifest["page_hashes"].items()})
    if target.exists():
        if tree_hashes(target) != expected:
            raise ValueError("immutable mirror release differs; will not overwrite")
    else:
        temp = contained(git_dir, "review-stage-" + uuid.uuid4().hex)
        temp.mkdir()
        try:
            for name in expected:
                dst = contained(temp, name)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(contained(source, name), dst)
            if tree_hashes(temp) != expected:
                raise ValueError("copy hash mismatch")
            target.parent.mkdir(exist_ok=True)
            os.rename(temp, target)
        finally:
            if temp.exists():
                # temp is an explicitly checked private directory under this repo's git dir.
                contained(git_dir, temp)
                shutil.rmtree(temp)
    pointer = read_json(contained(root, "CURRENT.json"))
    atomic_json(contained(repo, "CURRENT.json"), pointer)


def sync_release(root: Path, repo: Path, d: str, *, remote="origin", branch="master") -> dict:
    try:
        valid_date(d)
        root, repo = configured(root, repo)
        if not re_safe(remote) or not re_safe(branch):
            raise ValueError("invalid remote/branch")
        git_dir = Path(git(repo, "rev-parse", "--absolute-git-dir").stdout.strip()).resolve(strict=True)
        # No writes outside the explicitly selected repo (linked worktrees require parent integration).
        if not git_dir.is_relative_to(repo):
            raise ValueError("external git directory is unsupported")
        with exclusive(root), exclusive(git_dir, "review_sync.lock"):
            manifest = verify_release(root, d)
            if manifest["status"] != "pass":
                return fail(d, ["review not accepted", *manifest["errors"]])
            if git(repo, "branch", "--show-current").stdout.strip() != branch:
                raise ValueError("checked-out branch mismatch")
            # Allow only this build's retry residue; never commit unrelated edits.
            changed = git(repo, "status", "--porcelain", "-z", "--untracked-files=all").stdout.split("\0")
            own = "releases/" + manifest["build_id"] + "/"
            for row in changed:
                if row and not (row[3:] == "CURRENT.json" or row[3:].startswith(own)):
                    raise ValueError("unrelated working-tree changes: " + row)
            git(repo, "pull", "--ff-only", remote, branch)
            copy_release(root, repo, git_dir, manifest)
            artifacts = artifact_hashes(root, manifest)
            # Preserve the validated Windows bytes; never silently normalize an artifact.
            # Scoped config does not alter the repository/global configuration.
            git(repo, "-c", "core.autocrlf=false", "add", "--", "CURRENT.json", f"releases/{manifest['build_id']}")
            git(repo, "-c", "core.autocrlf=false", "add", "--renormalize", "--", "CURRENT.json", f"releases/{manifest['build_id']}")
            changed_index = git(repo, "diff", "--cached", "--quiet", allowed=(0, 1)).returncode == 1
            if changed_index:
                git(repo, "commit", "-m", f"review {d} revision {manifest['revision']} build {manifest['build_id']}")
            commit = git(repo, "rev-parse", "HEAD").stdout.strip()
            verify_commit(repo, commit, artifacts)
            # Always push, including the clean-tree retry after a rejected earlier push.
            git(repo, "push", remote, "HEAD:refs/heads/" + branch)
            confirmed = remote_tip(repo, remote, branch)
            if confirmed != commit:
                raise ValueError("remote commit does not equal pushed commit")
            verify_commit(repo, confirmed, artifacts)
            # Source and pointer are protected by the same lock used by publishing.
            again = verify_release(root, d)
            if again.get("manifest_sha256") != manifest["manifest_sha256"]:
                raise ValueError("source release changed during sync")
            state = {"schema_version": 1, "status": "pass", "errors": [], "d": d,
                     "build_id": manifest["build_id"], "revision": manifest["revision"],
                     "manifest_sha256": manifest["manifest_sha256"], "artifact_hashes": artifacts,
                     "remote_commit": confirmed, "remote": remote, "branch": branch,
                     "remote_url": git(repo, "remote", "get-url", remote).stdout.strip(),
                     "repo": str(repo), "confirmed_at": dt.datetime.now(dt.timezone.utc).isoformat()}
            state_dir = contained(root, ".review_sync")
            state_dir.mkdir(exist_ok=True)
            atomic_json(contained(root, f".review_sync/{d}.json"), state)
            return state
    except Exception as exc:
        return fail(d, [exc])


def pending_dates(*, root=None, repo=None):
    root, repo = configured(root, repo)
    try:
        d = read_json(contained(root, "CURRENT.json"))["d"]
        return [d] if review_done(d, root=root) and not repo_synced(d, root=root, repo=repo) else []
    except (OSError, ValueError, KeyError):
        return []


def do_sync(dates, *, root=None, repo=None):
    root, repo = configured(root, repo)
    return all(sync_release(root, repo, d)["status"] == "pass" for d in dates)


def run_once(root, repo, *, d=None, notify=None):
    """Retry current revision, emitting a local receipt only after remote verification.

    notify is an optional parent-owned delivery callback, never an implicit network
    sender. Failed callbacks remain retryable; delivery should deduplicate build_id.
    """
    try:
        root, repo = configured(root, repo)
        d = d or read_json(contained(root, "CURRENT.json"))["d"]
        result = sync_release(root, repo, d)
        if result["status"] != "pass":
            return result
        if not repo_synced(d, root=root, repo=repo):
            return fail(d, ["remote confirmation changed before notification"])
        with exclusive(root, ".review_notify.lock"):
            receipt = contained(root, f".review_sync/notified-{result['build_id']}.json")
            if not receipt.exists():
                event = {key: result[key] for key in
                         ("d", "build_id", "revision", "manifest_sha256", "remote_commit")}
                # A durable local outbox is the CLI handoff; parent wires real delivery.
                outbox = contained(root, f".review_sync/event-{result['build_id']}.json")
                if not outbox.exists():
                    atomic_json(outbox, event)
                if notify is not None:
                    notify(event)
                    atomic_json(receipt, event)
        return result
    except Exception as exc:
        return fail(d, [exc])


def run_loop(root, repo, *, interval=60, iterations=None, clock=None, sleeper=None, notify=None):
    import time
    if interval <= 0 or (iterations is not None and iterations < 1):
        raise ValueError("interval and iterations must be positive")
    clock, sleeper = clock or dt.datetime.now, sleeper or time.sleep
    results, count = [], 0
    while iterations is None or count < iterations:
        if clock().weekday() < 5:
            result = run_once(root, repo, notify=notify)
            if iterations is not None:
                results.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
        count += 1
        if iterations is None or count < iterations:
            sleeper(interval)
    return results


def main(check=False):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path)
    parser.add_argument("--repo", type=Path)
    parser.add_argument("--date")
    parser.add_argument("--check", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--once", action="store_true")
    mode.add_argument("--loop", action="store_true")
    mode.add_argument("--background", action="store_true")
    parser.add_argument("--interval", type=float, default=60)
    args = parser.parse_args()
    try:
        root, repo = configured(args.root, args.repo)
        if check or args.check:
            dates = [args.date] if args.date else pending_dates(root=root, repo=repo)
            rows = [{"d": d, "review_done": review_done(d, root=root), "repo_synced": repo_synced(d, root=root, repo=repo)} for d in dates]
            print(json.dumps(rows, ensure_ascii=False))
            return 0
        if args.background:
            import sys
            import os
            flags = (subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS) if os.name == "nt" else 0
            child = subprocess.Popen([sys.executable, "-B", str(Path(__file__).resolve()),
                "--root", str(root), "--repo", str(repo), "--loop", "--interval", str(args.interval)],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=flags, start_new_session=os.name != "nt")
            print(json.dumps({"status": "started", "pid": child.pid}))
            return 0
        if args.loop:
            run_loop(root, repo, interval=args.interval)
            return 0
        result = run_once(root, repo, d=args.date)
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["status"] == "pass" else 1
    except Exception as exc:
        print(json.dumps(fail(args.date, [exc]), ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
