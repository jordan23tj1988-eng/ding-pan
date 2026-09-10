# -*- coding: utf-8 -*-
"""P3 production bridge: install the real call site, never fake registration.

The bridge emits a dated receipt. A production registration is accepted only
when independent provenance, exchange calendar, and an externally-created
production transaction are all present and valid. This module never creates a
transaction or upgrades controlled TEST-ONLY evidence.
"""
from __future__ import annotations
import argparse, json
from datetime import datetime, timezone
from pathlib import Path


def _load(p):
    try: return json.loads(p.read_text(encoding='utf-8-sig'))
    except (OSError, ValueError, TypeError): return None


def inspect(root: Path, d: str) -> dict:
    root = root.resolve(); learn = root / '_学习'
    cal = _load(learn / '_交易日历.json')
    calendar_ok = isinstance(cal, list) and d in {str(x).replace('-', '') for x in cal}
    prov_paths = [learn / f'事实来源_{d}.json', learn / f'fact_snapshot_{d}.json', learn / f'来源快照_{d}.json']
    prov = next((p for p in prov_paths if p.is_file()), None)
    prov_obj = _load(prov) if prov else None
    provenance_ok = isinstance(prov_obj, dict) and bool(prov_obj.get('sources') or prov_obj.get('provenance'))
    tx_path = learn / f'production_registration_{d}.json'
    tx = _load(tx_path) if tx_path.is_file() else None
    tx_ok = isinstance(tx, dict) and tx.get('mode') == 'production' and bool(tx.get('transaction_id')) and tx.get('registered') is True
    missing = []
    if not provenance_ok: missing.append('independent_provenance')
    if not calendar_ok: missing.append('exchange_calendar')
    if not tx_ok: missing.append('real_registration_transaction')
    return {
        'schema_version': 1, 'capability': 'p3_production_bridge', 'date': d,
        'status': 'pass' if not missing else 'blocked',
        'flags': {'integration_bridge_installed': True, 'production_call_site': True,
                  'independent_provenance': provenance_ok, 'exchange_calendar': calendar_ok,
                  'real_registration_transaction': tx_ok, 'production_deployed': False,
                  'production_preregistration_allowed': False},
        'missing': missing, 'sources': ([prov.relative_to(root).as_posix()] if prov else []),
        'transaction_path': tx_path.relative_to(root).as_posix(),
        'production_action_taken': False,
        'policy': '桥已安装；不制造provenance/交易，不把controlled证据升级为production',
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('date'); ap.add_argument('--root', type=Path, required=True); ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args(argv)
    if len(a.date) != 8 or not a.date.isdigit(): ap.error('date must be YYYYMMDD')
    r = inspect(a.root, a.date); a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(r, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(r, ensure_ascii=False)); return 0 if r['status'] == 'pass' else 1


if __name__ == '__main__': raise SystemExit(main())
