from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import review_eval as e

def test_prediction_reference_is_unambiguous_and_legacy_prompt_preserved():
    base={'meta':{'d':'20260904'},'event_id':'test'}
    legacy=e._prompt(base,'h')
    current=e._prompt({**base,'meta':{'d':'20260904','prompt_version':2}},'h')
    assert 'prediction.source_id必须引用输入包已有fact' in current
    assert 'prediction.source_id必须引用输入包已有fact' not in legacy
