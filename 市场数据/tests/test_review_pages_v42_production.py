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
        # 2026-09-23 用户拍板: 概览页回归黄金组件体系, 段序/形态由 module_golden_index.py 冻结,
        # 每次复盘不得漂移(此前连跑两天即从113KB/78卡涨到240KB/279卡)。合同变更见 _变更总账.md。
        SIDS = ("recommendations", "turning", "routes", "verdict")
        assert html.count('<h2>') == len(SIDS)
        for sid in SIDS:
            assert '<!--GOLDEN-INDEX:%s-->' % sid in html, sid
        # 2026-09-23 用户指正(图1): 概览页内导航(page-map JS 运行时注入)与
        # 机器数据核对层折叠一并退出结果层; 黄金版本来就没有这两样。
        assert "map.className='page-map'" not in html, '概览页内导航已撤(2026-09-23)'
        assert '机器数据核对层' not in html, '机器数据核对层退出概览结果层(2026-09-23)'
        assert 'class="reading-spine"' not in html, '概览阅读条已撤(2026-09-23)'
        assert 'class="citem"' not in html, '概览结果层不再铺判断卡'
        # 证据不删(用户口径: 页面不展示, 体系内部保留): claim 原文进页尾无痕原文库,
        # 隐藏证据锚点仍在; 来源审计折叠本身退出概览结果层(图4/图5)。
        assert 'claim-anchor-bank' in html, 'claim 原文必须留痕(无痕原文库)'
        assert 'id="evidence-' in html, '隐藏证据锚点必须保留'
        assert 'id="audit-fold"' not in html, '来源审计折叠退出概览结果层(2026-09-23)'
        assert '结论' in html
        # 用户指正: 概览走马灯此前是空条; obs 卡此前不显示票名与身位(被 v4.4 去噪规则吃掉)。
        if 'class="obs"' in html:
            assert 'class="obs-nm"' in html, '概览 obs 卡必须带票名(黄金版形态)'
        assert '.obs-head .obs-nm,.obs-watch>.obs-lab{display:none}' not in html, \
            '概览页不得再隐藏票名/身位'
        assert 'class="ticker"' in html


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
