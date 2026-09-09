# -*- coding: utf-8 -*-
import importlib.util
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('gate',BASE/'p3_production_gate.py'); gate=importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)

def test_controlled_only_is_blocked():
    r=gate.evaluate({'status':'accepted_controlled_only','integration_bridge_installed':False,'production_deployed':False,'production_preregistration_allowed':False,'remaining':['independent_provenance','exchange_calendar','real_registration_transaction','production_call_site'],'controlled_test_method_count':28})
    assert r['status']=='blocked'; assert 'production_call_site' in r['missing']; assert r['production_action_taken'] is False

def test_bridge_receipt_keeps_missing_real_prerequisites_blocked():
    bridge = {'flags': {'integration_bridge_installed': True, 'production_call_site': True,
                        'independent_provenance': False, 'exchange_calendar': True,
                        'real_registration_transaction': False, 'production_deployed': False}}
    r = gate.evaluate({'status': 'accepted_controlled_only', 'production_deployed': True,
                       'production_preregistration_allowed': True, 'remaining': [],
                       'controlled_test_method_count': 28}, bridge)
    assert r['status'] == 'blocked'
    assert 'real_registration_transaction' in r['missing']
    assert r['production_action_taken'] is False
