from pathlib import Path
import pytest
import review_pages as p
ROOT=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize('route',['lhb','theme','logic'])
def test_0831_known_schema_variants_preserve_evidence(route):
    model=p.build_page_model(ROOT,'20260831',route)
    assert model['status'] != 'fail', model.get('errors')
    assert model['content_coverage']['total'] == model['content_coverage']['covered']
    if route=='theme':
        assert any(c.get('source_pointer')=='/来源' for c in model['claims'])
