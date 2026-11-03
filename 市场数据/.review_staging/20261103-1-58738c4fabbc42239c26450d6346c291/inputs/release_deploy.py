# -*- coding: utf-8 -*-
"""Deploy only the CURRENT accepted immutable release to the live HTML site.

The release builder deliberately does not mutate the live site. This explicit,
fail-closed step closes that boundary without copying source data or internal
models/audits. It is idempotent and writes a receipt only after hash verification.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import uuid

from review_publish import contained, read_json, verify_release, valid_date

HTML_ROOTS = ("", "archive", "history_sources")
CORE_PAGES = {"index.html", "cycle.html", "auction.html", "lhb.html", "theme.html", "logic.html", "limitup.html", "history.html", "intraday.html"}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def html_files(site: Path):
    return sorted(p for p in site.rglob("*.html") if p.is_file())


def deploy_release(root: Path, d: str, *, site: Path | None = None) -> dict:
    root = Path(root).resolve(strict=True)
    valid_date(d)
    accepted = verify_release(root, d)
    if accepted.get("status") != "pass":
        return {"status": "fail", "d": d, "errors": ["release not accepted", *accepted.get("errors", [])]}
    build_id = accepted["build_id"]
    source = contained(root, f"releases/{build_id}/site")
    destination = Path(site).resolve() if site is not None else root / "复盘" / "盯盘台"
    destination.parent.mkdir(parents=True, exist_ok=True)
    files = html_files(source)
    if not files:
        return {"status": "fail", "d": d, "errors": ["accepted release has no HTML"]}
    expected = {p.relative_to(source).as_posix(): sha(p) for p in files}
    stage = destination.parent / (".deploy-" + uuid.uuid4().hex)
    try:
        for rel, digest in expected.items():
            target = stage / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / rel, target)
            if sha(target) != digest:
                raise ValueError("staged hash mismatch: " + rel)
        for rel, digest in expected.items():
            target = destination / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            os.replace(stage / rel, target)
            if sha(target) != digest:
                raise ValueError("live hash mismatch: " + rel)
        receipt = {"schema_version": 1, "status": "pass", "errors": [], "d": d,
                   "build_id": build_id, "revision": accepted["revision"],
                   "manifest_sha256": accepted["manifest_sha256"], "site": str(destination),
                   "files": expected, "deployed_at": dt.datetime.now(dt.timezone.utc).isoformat()}
        out = root / ".review_deploy"
        out.mkdir(exist_ok=True)
        tmp = out / (d + ".json.tmp")
        tmp.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, out / (d + ".json"))
        return receipt
    except Exception as exc:
        return {"status": "fail", "d": d, "errors": [str(exc)]}
    finally:
        if stage.exists():
            shutil.rmtree(stage, ignore_errors=True)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("d")
    p.add_argument("--root", required=True)
    p.add_argument("--site")
    args = p.parse_args(argv)
    result = deploy_release(Path(args.root), args.d, site=Path(args.site) if args.site else None)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
