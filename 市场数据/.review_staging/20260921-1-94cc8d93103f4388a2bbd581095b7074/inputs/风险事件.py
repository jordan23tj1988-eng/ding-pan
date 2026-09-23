# -*- coding: utf-8 -*-
"""风险事件.py {d} —— 风险日历的真实事件源(东财 datacenter 直连)。

覆盖维度(逐项实测可过滤):
  ① 限售解禁   RPT_LIFT_STAGE    filter=(FREE_DATE='YYYY-MM-DD')
  ② 分红除权   RPT_SHAREBONUS_DET filter=(EX_DIVIDEND_DATE='YYYY-MM-DD')
未接入维度(实测过滤不可用/无端点): 财报披露日历、股东大会、业绩预告 —— 如实列进 未接入维度, 不声称无此类风险。

直连三坑(与 席位动向库.py 同款): ①必须清代理(ProxyHandler({})) ②必须带 Referer data.eastmoney.com
③filter 值必须双引号包裹。产出 _学习/风险事件_{d}.json, 供 风险日历.py 消费。
"""
from __future__ import annotations
import argparse, json, ssl, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path
from capability_common import valid_date, write_json

EM = "https://datacenter-web.eastmoney.com/api/data/v1/get"
_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def _dash(d: str) -> str:
    return f"{d[:4]}-{d[4:6]}-{d[6:]}"


def _get(report: str, flt: str, page_size: int = 200):
    """返回 (rows, error)。rows=None 表示取数失败。"""
    url = (f"{EM}?reportName={report}&columns=ALL&pageSize={page_size}&pageNumber=1"
           f"&filter={urllib.parse.quote(flt)}")
    try:
        op = urllib.request.build_opener(
            urllib.request.ProxyHandler({}),
            urllib.request.HTTPSHandler(context=_CTX))
        req = urllib.request.Request(url, headers={
            "Referer": "https://data.eastmoney.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with op.open(req, timeout=25) as r:
            j = json.loads(r.read().decode("utf-8", "replace"))
    except Exception as e:                      # 网络/HTTP 异常
        return None, f"{type(e).__name__}: {str(e)[:120]}"
    if not j.get("success"):
        return None, f"EM success=False msg={str(j.get('message'))[:80]}"
    return (j.get("result") or {}).get("data") or [], None


def fetch_lift(d: str):
    """限售解禁。LIFT_MARKET_CAP 单位=万元(实测 68.875万股×19.89元=1369.92), CURRENT_FREE_SHARES 单位=万股。"""
    rows, err = _get("RPT_LIFT_STAGE", f"(FREE_DATE='{_dash(d)}')")
    if rows is None:
        return None, err
    out = []
    for x in rows:
        ratio = x.get("FREE_RATIO")
        out.append({
            "类型": "限售解禁",
            "代码": str(x.get("SECURITY_CODE") or ""),
            "名称": x.get("SECURITY_NAME_ABBR"),
            "解禁日": str(x.get("FREE_DATE") or "")[:10],
            "解禁类型": x.get("FREE_SHARES_TYPE"),
            "解禁股数万股": x.get("CURRENT_FREE_SHARES"),
            "解禁市值万元": x.get("LIFT_MARKET_CAP"),
            "占流通股_pct": round(ratio * 100, 4) if isinstance(ratio, (int, float)) else None,
        })
    return out, None


def fetch_bonus(d: str):
    """分红除权。方案原字段单位未逐项实测, 保留东财原字段名供引用前核对。"""
    rows, err = _get("RPT_SHAREBONUS_DET", f"(EX_DIVIDEND_DATE='{_dash(d)}')")
    if rows is None:
        return None, err
    out = []
    for x in rows:
        out.append({
            "类型": "分红除权",
            "代码": str(x.get("SECURITY_CODE") or ""),
            "名称": x.get("SECURITY_NAME_ABBR"),
            "股权登记日": str(x.get("EQUITY_RECORD_DATE") or "")[:10],
            "除权除息日": str(x.get("EX_DIVIDEND_DATE") or "")[:10],
            "方案原字段": {k: x.get(k) for k in ("BONUS_IT_RATIO", "BONUS_RATIO", "IT_RATIO",
                                                 "PRETAX_BONUS_RMB", "ASSIGN_PROGRESS")},
        })
    return out, None


SOURCES = [("限售解禁", fetch_lift, "东财 RPT_LIFT_STAGE"),
           ("分红除权", fetch_bonus, "东财 RPT_SHAREBONUS_DET")]
NOT_INTEGRATED = ["财报披露日历", "股东大会", "业绩预告"]


def build(root: Path, d: str):
    valid_date(d)
    events, ok_src, bad_src, errors, counts = [], [], [], [], {}
    for label, fn, endpoint in SOURCES:
        rows, err = fn(d)
        if rows is None:
            bad_src.append(label)
            errors.append(f"{label} 取数失败: {err}")
            continue
        ok_src.append(f"{endpoint}")
        counts[label] = len(rows)
        events.extend(rows)
    if not ok_src and bad_src:
        status = "unavailable"
    elif bad_src:
        status = "partial"
    else:
        status = "pass"
    return {
        "schema_version": 1, "capability": "risk_events", "date": d, "status": status,
        "sources": ok_src,
        "metrics": {"事件条数": len(events), **{f"{k}条数": v for k, v in counts.items()},
                    "覆盖维度": [x[0] for x in SOURCES if x[0] not in bad_src],
                    "未接入维度": NOT_INTEGRATED},
        "errors": errors,
        "note": ("覆盖维度=" + "+".join(x[0] for x in SOURCES if x[0] not in bad_src)
                 + "；未接入维度=" + "/".join(NOT_INTEGRATED)
                 + " —— 未接入≠无风险，引用时不得据此声称无此类风险"),
        "生成时间": datetime.now().isoformat(timespec="seconds"),
        "事件": events,
    }


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('d')
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--out', type=Path)
    a = p.parse_args(argv)
    r = build(a.root.resolve(), a.d)
    out = a.out or (a.root / "_学习" / f"风险事件_{a.d}.json")
    write_json(out, r)
    print("[%s] %s 事件=%d 覆盖=%s 未接入=%s" % (
        r["status"], out.name, r["metrics"]["事件条数"],
        "+".join(r["metrics"]["覆盖维度"]), "/".join(r["metrics"]["未接入维度"])))
    for e in r["errors"]:
        print("  ERR", e)
    return 0 if r["status"] == "pass" else 1


if __name__ == '__main__':
    raise SystemExit(main())
