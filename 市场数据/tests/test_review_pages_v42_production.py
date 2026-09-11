"""v4.2 production-renderer acceptance checks.

This suite intentionally imports the production renderer, not the isolated Codex
candidate under codex_workspace.
"""
import importlib.util
import json
from pathlib import Path
import tempfile

PROD = Path(r"D:/股票数据/市场数据/review_pages.py")
SAMPLE = Path(r"D:/股票数据/codex_workspace/stability-20260906/p1/evidence/samples/20260904")


def load_production():
    spec = importlib.util.spec_from_file_location("production_review_pages_v42", PROD)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_v42_reading_spine_claim_roles_and_proof_links():
    api = load_production()
    with tempfile.TemporaryDirectory(prefix="v42-prod-") as td:
        result = api.build_site(SAMPLE, "20260904", Path(td))
        assert result["status"] in {"ok", "degraded"}
        html = Path(result["pages"]["index"]).read_text(encoding="utf-8")
        assert 'data-template-version="p1.3"' in html
        assert html.count('class="reading-spine"') == 1
        assert 'class="claim-role role-' in html
        assert 'class="claim-proof"' in html
        assert 'href="#evidence-' in html
        for label in ("结论", "来源审计"):
            assert label in html
        # v4.3：静态"阅读顺序 01结论/02指标/03分段证据/04来源审计"改为真实栏目锚点，
        # 原"分段证据"并入各栏目依据组，故此处改为校验锚点齐全（合同变更见 _变更总账.md）
        for sid in ("observations", "routes", "turning", "verdict", "master"):
            assert 'href="#%s"' % sid in html
        assert 'href="#audit-fold"' in html


def test_v42_contract_hash_matches_css_snapshot():
    api = load_production()
    contract = json.loads((PROD.parent / "_契约/页面契约.v1.json").read_text(encoding="utf-8"))
    assert contract["template_version"] == "p1.3"
    assert "v4.2 reading spine / claim proof layer" in contract["visual"]["css"]
    assert "@media(max-width:640px){.reading-spine" in contract["visual"]["css"]
    assert ".navbar{display:block;top:6px;margin:6px 8px 0" in contract["visual"]["css"]
    assert ".navbar .pills{width:100%;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));min-width:0" in contract["visual"]["css"]
    assert ".reading-spine{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))" in contract["visual"]["css"]
    assert api._page_css(contract).count("v4.2 reading spine / claim proof layer") == 1


def test_v42_publish_kpi_provenance_matches_p13_models():
    spec = importlib.util.spec_from_file_location("production_review_publish_v42", PROD.parent / "review_publish.py")
    review_pub = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(review_pub)
    root = PROD.parent
    cycle_sources = review_pub.expected_kpis(root, "20260908", "cycle", "p1.3")[1]
    lhb_sources = review_pub.expected_kpis(root, "20260908", "lhb", "p1.3")[1]
    assert cycle_sources == {"_学习/_市场温度表.json", "_学习/_周期投票台账.jsonl"}
    assert lhb_sources == {"_学习/_资金温度.json", "_学习/席位荐票_20260908.json"}
