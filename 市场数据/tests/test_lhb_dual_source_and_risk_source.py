# -*- coding: utf-8 -*-
"""龙虎榜双源校验 + 风险日历事件源接线 —— 离线契约测试(不联网)

覆盖: ①源1 只取"当日榜"行不累加区间榜(20260818 修正) ②源2 剔区间累计榜 + (代码,席位)去重取买入最大
      ③强矛盾判定与清单 ④无数据时 fail-closed ⑤风险日历只认事件源 status=pass, partial 不当"无风险"
"""
import importlib.util, json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def _load(name, fn):
    spec = importlib.util.spec_from_file_location(name, HERE / fn)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _mkroot(tmp_path, d):
    (tmp_path / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "_学习" / "_席位动向").mkdir(parents=True, exist_ok=True)
    (tmp_path / "_学习" / "_交易日历.json").write_text(json.dumps([d]), encoding="utf-8")


LHB_HEAD = "序号,代码,名称,上榜日,解读,收盘价,涨跌幅,龙虎榜净买额,龙虎榜买入额,龙虎榜卖出额,上榜原因\n"
SEAT_HEAD = "日,代码,名称,席位,买入金额,买占比,卖出金额,净额,类型\n"


def _lhb_rows():
    return (
        "1,600354,敦煌种业,2026-09-10,,25.0,10.0,-67791006.75,316529769.66,384320776.41,"
        "有价格涨跌幅限制的日换手率达到20%的前五只证券\n"
        "2,600354,敦煌种业,2026-09-10,,25.0,10.0,-139643753.2,728752819.44,868396572.64,"
        "非S证券连续三个交易日内收盘价格涨幅偏离值累计达到20%的证券\n"
        "3,600354,敦煌种业,2026-09-10,,25.0,10.0,-67791006.75,316529769.66,384320776.41,"
        "有价格涨跌幅限制的日价格振幅达到15%的前五只证券\n"
        "4,600110,诺德股份,2026-09-10,,10.0,10.0,50000000.0,100000000.0,50000000.0,"
        "有价格涨跌幅限制的日收盘价格涨幅偏离值达到7%的前五只证券\n"
    )


def _seat_rows():
    return (
        "20260910,600354,敦煌种业,国泰海通证券股份有限公司总部,119790727.33,0.1,0.0,119790727.33,"
        "有价格涨跌幅限制的日换手率达到20%的前五只证券\n"
        "20260910,600354,敦煌种业,国泰海通证券股份有限公司总部,268062838.73,0.2,0.0,268062838.73,"
        "非S证券连续三个交易日内收盘价格涨幅偏离值累计达到20%的证券\n"
        "20260910,600354,敦煌种业,高盛(中国)证券有限责任公司上海浦东新区世纪大道证券营业部,"
        "66086841.25,0.05,0.0,66086841.25,有价格涨跌幅限制的日换手率达到20%的前五只证券\n"
    )


def test_双源校验_源1只取当日榜且源2剔区间榜去重(tmp_path):
    d = "20260910"
    _mkroot(tmp_path, d)
    (tmp_path / d / "lhb.csv").write_text(LHB_HEAD + _lhb_rows(), encoding="utf-8")
    (tmp_path / "_学习" / "_席位动向" / f"{d}.csv").write_text(SEAT_HEAD + _seat_rows(), encoding="utf-8")

    r = _load("lhbdual", "龙虎榜双源校验.py").build(tmp_path, d)
    assert r["date"] == d and r["status"] == "pass"
    rows = {x["代码"]: x for x in r["全量"]}

    # 源1: 当日榜行 -67791006.75 → -0.6779 亿; 若错误累加区间榜会得 -2.07 亿
    assert abs(rows["600354"]["源1净买亿"] + 0.6779) < 0.001
    # 源2: 区间累计榜已剔 → 国泰 119790727.33 + 高盛 66086841.25 = 1.8588 亿
    assert abs(rows["600354"]["源2买侧净额亿"] - 1.8588) < 0.001
    # 方向相反且 |源2|>1亿 → 强矛盾, 进清单
    assert rows["600354"]["判定"] == "强矛盾"
    assert "600354" in [x["代码"] for x in r["强矛盾清单"]]
    # 只有 600110 未上榜 → 无可比
    assert r["metrics"]["源1代码数"] == 2 and r["metrics"]["可比数"] == 1
    assert r["metrics"]["仅源1"] == 1


def test_双源校验_缺源即fail_closed(tmp_path):
    d = "20260911"
    _mkroot(tmp_path, d)
    m = _load("lhbdual2", "龙虎榜双源校验.py")
    assert m.build(tmp_path, d)["status"] == "unavailable"          # 两源全缺
    (tmp_path / d / "lhb.csv").write_text(LHB_HEAD + _lhb_rows(), encoding="utf-8")
    assert m.build(tmp_path, d)["status"] == "partial"              # 只有源1


def test_风险日历_事件源非pass一律partial(tmp_path):
    d = "20260911"
    _mkroot(tmp_path, d)
    cal = _load("riskcal", "风险日历.py")
    # 事件源文件缺失 → 不得当"无风险"
    r = cal.build(tmp_path, d)
    assert r["status"] == "partial" and any("事件源" in e for e in r["errors"])
    # 事件源存在但自身 partial → 仍 partial, 且把原因带出来
    (tmp_path / "_学习" / f"风险事件_{d}.json").write_text(
        json.dumps({"date": d, "status": "partial", "errors": ["分红源超时"]}, ensure_ascii=False),
        encoding="utf-8")
    r = cal.build(tmp_path, d)
    assert r["status"] == "partial" and any("分红源超时" in e for e in r["errors"])
    # 事件源 pass → 日历 pass, 未接入维度必须写进 note(不得沉默)
    (tmp_path / "_学习" / f"风险事件_{d}.json").write_text(
        json.dumps({"date": d, "status": "pass", "sources": ["东财-限售解禁"],
                    "metrics": {"事件条数": 3, "覆盖维度": ["限售解禁"], "未接入维度": ["股东大会"]}},
                   ensure_ascii=False), encoding="utf-8")
    r = cal.build(tmp_path, d)
    assert r["status"] == "pass" and r["metrics"]["事件条数"] == 3
    assert "股东大会" in r["note"] and "东财-限售解禁" in r["sources"]


def test_风险日历_非交易日unavailable(tmp_path):
    _mkroot(tmp_path, "20260911")
    cal = _load("riskcal2", "风险日历.py")
    assert cal.build(tmp_path, "20260912")["status"] == "unavailable"
