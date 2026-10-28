# -*- coding: utf-8 -*-
"""Fail-closed P3 production gate.

Controlled bridge evidence is TEST ONLY. The production bridge may prove that
the call site is installed, but it cannot manufacture provenance or a real
registration transaction.
"""
from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path

REQUIRED = ['independent_provenance', 'exchange_calendar', 'real_registration_transaction', 'production_call_site']


def evaluate(evidence: dict, bridge: dict | None = None) -> dict:
    bridge = bridge or {}
    old_remaining = list(evidence.get('remaining', []))
    bflags = bridge.get('flags', {}) if isinstance(bridge, dict) else {}
    flags = {
        'controlled_acceptance': evidence.get('status') == 'accepted_controlled_only',
        'integration_bridge_installed': bool(bridge and bflags.get('integration_bridge_installed')) or bool(evidence.get('integration_bridge_installed')),
        'production_call_site': bool(bridge and bflags.get('production_call_site')) if bridge else bool(evidence.get('production_call_site', evidence.get('integration_bridge_installed'))),
        'production_deployed': bool(evidence.get('production_deployed')) and bool(bridge.get('flags', {}).get('production_deployed', False) if bridge else evidence.get('production_deployed')),
        'production_preregistration_allowed': bool(evidence.get('production_preregistration_allowed')),
        'independent_provenance': bool(bflags.get('independent_provenance')) if bridge else 'independent_provenance' not in old_remaining,
        'exchange_calendar': bool(bflags.get('exchange_calendar')) if bridge else 'exchange_calendar' not in old_remaining,
        'real_registration_transaction': bool(bflags.get('real_registration_transaction')) if bridge else 'real_registration_transaction' not in old_remaining,
    }
    missing = set(old_remaining)
    for key in REQUIRED:
        if not flags.get(key): missing.add(key)
    if not flags['integration_bridge_installed']: missing.add('integration_bridge_installed')
    ok = flags['controlled_acceptance'] and not missing and flags['production_deployed'] and flags['production_preregistration_allowed']
    return {'status': 'pass' if ok else 'blocked', 'flags': flags, 'missing': sorted(missing),
            'controlled_test_method_count': evidence.get('controlled_test_method_count'),
            'production_action_taken': False,
            'policy': 'controlled证据与生产证据隔离；缺任一真实资格保持blocked'}


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('--evidence', type=Path, required=True); ap.add_argument('--bridge', type=Path); ap.add_argument('--out', type=Path, required=True); a = ap.parse_args(argv)
    ev = json.loads(a.evidence.read_text(encoding='utf-8')); bridge = json.loads(a.bridge.read_text(encoding='utf-8')) if a.bridge else None
    r = evaluate(ev, bridge); r['generated_at'] = datetime.now().isoformat(timespec='seconds'); a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(r, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'); print(json.dumps(r, ensure_ascii=False)); return 0 if r['status'] == 'pass' else 1


if __name__ == '__main__': raise SystemExit(main())
