# -*- coding: utf-8 -*-
import importlib.util
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
S = importlib.util.spec_from_file_location('review_learning', ROOT / 'review_learning.py')
M = importlib.util.module_from_spec(S)
S.loader.exec_module(M)
LEARN = ROOT / '_学习'

@pytest.mark.parametrize('d', ['20260710','20260814','20260817','20260824','20260825'])
def test_real_legacy_wrappers_normalize_without_inventing(d):
    raw=json.loads((LEARN/f'自主拓展应答_{d}.json').read_text(encoding='utf-8'))
    items=json.loads((LEARN/f'自主拓展清单_{d}.json').read_text(encoding='utf-8'))['items']
    result=M.normalize_responses(raw,items,d)
    assert set(result)=={x['id'] for x in items}

def test_real_unknown_route_is_rejected():
    d='20260713'
    raw=json.loads((LEARN/f'自主拓展应答_{d}.json').read_text(encoding='utf-8'))
    items=json.loads((LEARN/f'自主拓展清单_{d}.json').read_text(encoding='utf-8'))['items']
    with pytest.raises(ValueError, match='未知项'):
        M.normalize_responses(raw,items,d)
