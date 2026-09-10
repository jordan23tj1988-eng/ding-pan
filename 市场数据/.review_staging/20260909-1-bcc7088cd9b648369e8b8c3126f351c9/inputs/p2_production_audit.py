# -*- coding: utf-8 -*-
"""P2 production call site.

Runs the real review_learning consumer with explicit INPUT_ROOT and an
independent RUN_ROOT. It never writes historical inputs. A failed audit is
recorded and returned to the caller; it is not converted to success.
"""
from __future__ import annotations
import argparse, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path


def run(root: Path, d: str, out: Path) -> dict:
    started = datetime.now(timezone.utc).isoformat()
    root = Path(root).resolve(); out = Path(out).resolve()
    audit_dir = out / d
    cmd = [sys.executable, '-B', str(root / 'review_learning.py'), 'audit', d,
           '--root', str(root), '--out', str(audit_dir)]
    p = None; stdout = ''; stderr = ''; status = 'fail'; validation_errors = []
    if len(d) != 8 or not d.isdigit():
        validation_errors.append('date must be YYYYMMDD')
    else:
        try:
            datetime.strptime(d, '%Y%m%d')
        except ValueError:
            validation_errors.append('date is not a calendar date')
    if not root.is_dir():
        validation_errors.append('input root is not a directory: ' + str(root))
    if not (root / 'review_learning.py').is_file():
        validation_errors.append('review_learning.py is missing under input root')
    if out == root or root in out.parents:
        validation_errors.append('run output must be outside input root')
    if not validation_errors:
        try:
            audit_dir.mkdir(parents=True, exist_ok=True)
            p = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True,
                               encoding='utf-8', errors='replace', timeout=900,
                               env={k: v for k, v in __import__('os').environ.items()
                                    if k != 'PYTHONPATH'})
            stdout, stderr = p.stdout[-4000:], p.stderr[-4000:]
            status = 'pass' if p.returncode == 0 else 'fail'
        except (OSError, subprocess.TimeoutExpired) as exc:
            stderr = str(exc); status = 'fail'
    if validation_errors:
        stderr = '; '.join(validation_errors)
    receipt = {'schema_version': 1, 'capability': 'p2_production_audit',
               'date': d, 'status': status, 'started_at': started,
               'finished_at': datetime.now(timezone.utc).isoformat(),
               'command': [str(x) for x in cmd], 'run_root': str(audit_dir),
               'returncode': None if p is None else p.returncode,
               'stdout_tail': stdout, 'stderr_tail': stderr,
               'historical_inputs_modified': False,
               'policy': '独立run输出；失败原样保留，不覆盖历史发布物'}
    try:
        audit_dir.mkdir(parents=True, exist_ok=True)
        (audit_dir / 'production_receipt.json').write_text(
            json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except OSError as exc:
        receipt['receipt_write_error'] = str(exc)
    return receipt


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('date'); ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(argv)
    if len(a.date) != 8 or not a.date.isdigit(): ap.error('date must be YYYYMMDD')
    r = run(a.root, a.date, a.out)
    print(json.dumps(r, ensure_ascii=False))
    return 0 if r['status'] == 'pass' else 1


if __name__ == '__main__':
    raise SystemExit(main())
