# -*- coding: utf-8 -*-
"""资金流行业.py {d} —— 资金温度最小可用版·行业级净买/流通市值（MA-20261029-01④）

补全全系统缺失的『资金流到哪个行业』维度：
  行业级净买强度 = 该行业当日榜净买额合计 / 该行业(可核)流通市值合计，单位 bp
数据源（全部本地，零外部）：
  代码→行业/流通市值:  {d}/zt_pool.csv + zb_pool.csv + strong_pool.csv（活跃池，已含所属行业）
  当日榜净买额:        {d}/lhb.csv（当日榜行，禁累加多榜）
  席位侧净额/机构/北向: _学习/_席位动向/{d}.csv（含 clean：剔区间累计榜+投资者类别汇总行+去重）
覆盖边界：行业映射只覆盖涨停/炸板/新高活跃池 → 仅对这些票可行业化，覆盖率写进 json。
"""
from __future__ import annotations
import argparse, csv, collections, json
from pathlib import Path

INTERVAL_KW = ("连续", "累计", "严重异常")
AGG_ROWS = {"自然人", "中小投资者", "其他自然人", "机构"}


def _f(x):
    try:
        v = float(x)
        return v if v == v else None
    except Exception:
        return None


def load_map(root: Path, d: str):
    """代码 -> {行业, 流通市值}；三个活跃池按 涨停>炸板>新高 优先级合并"""
    m = {}
    for fn in ("strong_pool.csv", "zb_pool.csv", "zt_pool.csv"):
        p = root / d / fn
        if not p.is_file():
            continue
        for r in csv.DictReader(p.open(encoding="utf-8-sig")):
            code = str(r.get("代码") or "").strip()
            ind = str(r.get("所属行业") or "").strip()
            circ = _f(r.get("流通市值"))
            if not code or not ind:
                continue
            cur = m.setdefault(code, {})
            cur.setdefault("行业", ind)
            if circ and not cur.get("流通市值"):
                cur["流通市值"] = circ
    return m


def load_net1(root: Path, d: str):
    """当日榜股票级净买（多行当日榜取首行，禁累加）"""
    p = root / d / "lhb.csv"
    out = {}
    if not p.is_file():
        return out
    for r in csv.DictReader(p.open(encoding="utf-8-sig")):
        code = str(r.get("代码") or "").strip()
        if not code or code in out:
            continue
        if any(k in str(r.get("上榜原因") or "") for k in INTERVAL_KW):
            continue
        net = _f(r.get("龙虎榜净买额"))
        if net is not None:
            out[code] = net
    return out


def load_seats(root: Path, d: str):
    """席位侧: code -> {净额, 机构净额, 北向净额, 席位数}"""
    p = root / "_学习" / "_席位动向" / f"{d}.csv"
    out = collections.defaultdict(lambda: {"净额": 0.0, "机构净额": 0.0, "北向净额": 0.0, "席位数": 0})
    if not p.is_file():
        return out
    best = {}
    with p.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.reader(f):
            if not r or len(r) < 9:
                continue
            code, seat, typ = str(r[1]).strip(), str(r[3]).strip(), str(r[8]).strip()
            if not code or not seat or seat in AGG_ROWS:
                continue
            if any(k in typ for k in INTERVAL_KW):
                continue
            buy = _f(r[4]) or 0.0
            k = (code, seat)
            if k not in best or buy > (best[k][0] or 0.0):
                best[k] = (buy, _f(r[7]) or 0.0, seat)
    for (code, seat), (_b, net, sname) in best.items():
        v = out[code]
        v["净额"] += net
        v["席位数"] += 1
        if "机构专用" in sname:
            v["机构净额"] += net
        if "股通" in sname:
            v["北向净额"] += net
    return out


def build(root: Path, d: str):
    imap = load_map(root, d)
    net1 = load_net1(root, d)
    seats = load_seats(root, d)
    zt = set()
    zp = root / d / "zt_pool.csv"
    if zp.is_file():
        zt = {str(r.get("代码") or "").strip() for r in csv.DictReader(zp.open(encoding="utf-8-sig"))}

    agg = collections.defaultdict(lambda: {"涨停数": 0, "上榜数": 0, "净买亿": 0.0, "流通市值亿": 0.0,
                                           "席位净额亿": 0.0, "机构净额亿": 0.0, "北向净额亿": 0.0,
                                           "票": []})
    covered, uncovered = 0, []
    for code in sorted(set(net1) | set(seats)):
        info = imap.get(code)
        if not info:
            uncovered.append(code)
            continue
        covered += 1
        ind = info["行业"]
        a = agg[ind]
        a["上榜数"] += 1
        a["涨停数"] += 1 if code in zt else 0
        a["净买亿"] += net1.get(code, 0.0) / 1e8
        a["流通市值亿"] += (info.get("流通市值") or 0) / 1e8
        s = seats.get(code) or {}
        a["席位净额亿"] += (s.get("净额") or 0) / 1e8
        a["机构净额亿"] += (s.get("机构净额") or 0) / 1e8
        a["北向净额亿"] += (s.get("北向净额") or 0) / 1e8
        a["票"].append({"代码": code, "净买亿": round(net1.get(code, 0.0) / 1e8, 4),
                        "涨停": code in zt})

    rows = []
    for ind, a in agg.items():
        strength = (a["净买亿"] / a["流通市值亿"] * 10000) if a["流通市值亿"] > 0 else None
        rows.append({"行业": ind, "涨停数": a["涨停数"], "上榜数": a["上榜数"],
                     "净买亿": round(a["净买亿"], 4), "流通市值亿": round(a["流通市值亿"], 2),
                     "净买强度bp": None if strength is None else round(strength, 2),
                     "席位净额亿": round(a["席位净额亿"], 4),
                     "机构净额亿": round(a["机构净额亿"], 4),
                     "北向净额亿": round(a["北向净额亿"], 4),
                     "票": a["票"]})
    rows.sort(key=lambda r: -(r["净买强度bp"] if r["净买强度bp"] is not None else -1e9))
    total_net = sum(r["净买亿"] for r in rows)
    total_circ = sum(r["流通市值亿"] for r in rows)
    return {
        "schema_version": 1,
        "capability": "industry_fund_strength",
        "date": d,
        "口径": "净买强度bp = 行业当日榜净买额合计 / 行业(可核)流通市值合计 ×10000；净买=当日榜行"
                "（禁累加多榜）；席位净额=东财买五席位净额去重加总（天然偏买，非净买权威）",
        "覆盖": {"龙虎榜/席位票数": len(set(net1) | set(seats)), "可行业化": covered,
                 "覆盖pct": round(covered / max(1, len(set(net1) | set(seats))) * 100, 1),
                 "未覆盖": uncovered},
        "合计": {"净买亿": round(total_net, 4), "可核流通市值亿": round(total_circ, 2),
                 "净买强度bp": round(total_net / total_circ * 10000, 2) if total_circ else None},
        "行业": rows,
        "边界": "行业映射来自 zt_pool/zb_pool/strong_pool 三活跃池，未涨停未炸板未新高的上榜票无行业标签→未覆盖；"
                "故本表读『活跃池内资金去向』，不等于全市场行业资金流；分位化需≥60交易日累积，本版只出当日绝对值。",
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('d')
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    a = p.parse_args(argv)
    r = build(a.root.resolve(), a.d)
    out = a.root / "_学习" / f"_资金流行业_{a.d}.json"
    out.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding='utf-8')
    print("[%s] 覆盖 %s%% (%d/%d) 行业数%d 合计净买%+.2f亿 强度%.2fbp" % (
        a.d, r["覆盖"]["覆盖pct"], r["覆盖"]["可行业化"], r["覆盖"]["龙虎榜/席位票数"],
        len(r["行业"]), r["合计"]["净买亿"], r["合计"]["净买强度bp"]))
    print("  %-10s %3s %3s %9s %10s %8s %9s" % ("行业", "涨停", "上榜", "净买亿", "流通亿", "强度bp", "机构净额"))
    for x in r["行业"][:12]:
        print("  %-10s %3d %3d %+9.3f %10.1f %8s %+9.3f" % (
            x["行业"][:10], x["涨停数"], x["上榜数"], x["净买亿"], x["流通市值亿"],
            "-" if x["净买强度bp"] is None else "%.2f" % x["净买强度bp"], x["机构净额亿"]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
