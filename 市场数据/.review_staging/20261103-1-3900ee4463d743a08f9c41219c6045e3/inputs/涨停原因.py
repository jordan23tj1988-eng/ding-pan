# -*- coding: utf-8 -*-
"""涨停原因取数：THS 主源不足时自动补查东财公告线索。

硬边界：公告接口只保留 notice_date <= 目标日的证据；公告标题只是催化线索，
不自动宣称“就是涨停原因”、不自动把行业兜底升级为 A 档。补源原文另存
`_学习/公告催化补充_{d}.json`，供题材路逐票复核。
"""
import csv, datetime, json, os, sys, time, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
L = os.path.join(BASE, "_学习")
THS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://data.10jqka.com.cn/datacenterph/limitup/limtupInfo.html",
}
EM_HEADERS = {"User-Agent": "Mozilla/5.0", "Referer": "https://data.eastmoney.com/"}
RISK_WORDS = ("异常波动", "风险提示", "监管工作函", "监管警示", "问询函", "停牌核查")
CATALYST_WORDS = (
    "重组", "收购", "资产", "合同", "中标", "预中标", "订单", "注册证书", "新兽药",
    "药品", "回购", "增持", "无偿划转", "投资建设", "项目", "业绩预增", "利润预增",
    "摘帽", "复牌", "预重整", "债转股",
)


def _get_json(url, headers, retries=3):
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            return json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8"))
        except Exception as exc:  # 失败要留痕，不能静默当成无公告
            last = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise last


def fetch_ths(d):
    out = {}
    for page in (1, 2):
        url = (
            f"https://data.10jqka.com.cn/dataapi/limit_up/limit_up_pool?page={page}&limit=200"
            "&field=199112,10,9001,330323,330324,330325,9002,330329,133971,133970"
            f"&filter=HS,GEM2STAR&order_field=330324&order_type=0&date={d}"
        )
        j = _get_json(url, THS_HEADERS)
        if j.get("status_code") != 0:
            raise RuntimeError(str(j.get("status_msg")))
        info = (j.get("data") or {}).get("info") or []
        for x in info:
            code = str(x.get("code", "")).zfill(6)
            ts = x.get("first_limit_up_time")
            first_limit = datetime.datetime.fromtimestamp(int(ts)).strftime("%H:%M") if ts else None
            out[code] = {
                "名称": x.get("name"), "原因": x.get("reason_type"),
                "连板口径": x.get("high_days"), "首封": first_limit,
                "渠道": "同花顺涨停池", "证据级别": "THS编辑聚合",
            }
        if len(info) < 200:
            break
    return out


def expected_stocks(d):
    path = os.path.join(BASE, d, "zt_pool.csv")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return {str(row.get("代码", "")).zfill(6): row.get("名称") for row in csv.DictReader(fh) if row.get("代码")}


def fetch_eastmoney_asof(d, stocks):
    """取东财公告标题作为线索；只落盘目标日前公告，不保存未来公告内容。"""
    asof = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    supplement = {"日期": d, "as_of": d, "来源": "东财公告接口(官方公告标题)",
                  "口径": "仅保留notice_date<=as_of；标题为线索，未确认因果",
                  "状态": "pass", "条目": [], "错误": []}
    for code, name in stocks.items():
        url = ("https://np-anotice-stock.eastmoney.com/api/security/ann?sr=-1"
               "&page_size=50&page_index=1&ann_type=A&client_source=web&stock_list=" + code)
        item = {"代码": code, "名称": name, "公告": [], "状态": "pass", "查询接口": url}
        try:
            payload = _get_json(url, EM_HEADERS)
            for ann in ((payload.get("data") or {}).get("list") or []):
                notice_date = (ann.get("notice_date") or "")[:10]
                if notice_date and notice_date <= asof:
                    item["公告"].append({
                        "art_code": ann.get("art_code"), "notice_date": notice_date,
                        "display_time": (ann.get("display_time") or "")[:19],
                        "title": ann.get("title_ch") or ann.get("title"),
                        "columns": [c.get("column_name") for c in (ann.get("columns") or [])],
                    })
        except Exception as exc:
            item["状态"] = "partial"
            item["错误"] = f"{type(exc).__name__}: {exc}"
            supplement["错误"].append({"代码": code, "错误": item["错误"]})
        supplement["条目"].append(item)
        time.sleep(0.08)
    supplement["指标"] = {
        "股票数": len(stocks),
        "有截至日公告股票数": sum(bool(x["公告"]) for x in supplement["条目"]),
        "公告数": sum(len(x["公告"]) for x in supplement["条目"]),
        "错误数": len(supplement["错误"]),
    }
    if supplement["错误"]:
        supplement["状态"] = "partial"
    with open(os.path.join(L, f"公告催化补充_{d}.json"), "w", encoding="utf-8") as fh:
        json.dump(supplement, fh, ensure_ascii=False, indent=2)
    return supplement


def _announcement_clues(item, d):
    target = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    recent_floor = (datetime.date.fromisoformat(target) - datetime.timedelta(days=10)).isoformat()
    anns = [a for a in item.get("公告", []) if recent_floor <= a["notice_date"] <= target]
    positive = [a for a in anns if any(w in (a.get("title") or "") for w in CATALYST_WORDS)
                and not any(w in (a.get("title") or "") for w in RISK_WORDS)]
    same_day = [a for a in positive if a["notice_date"] == target]
    return anns, positive, same_day


def build_fallback_mapping(d, stocks, supplement, existing):
    mapping = dict(existing)
    for item in supplement["条目"]:
        code = item["代码"]
        if code in mapping:
            continue
        anns, positive, same_day = _announcement_clues(item, d)
        titles = [a["title"] for a in positive[:5]]
        same_day_titles = [a["title"] for a in same_day[:5]]
        mapping[code] = {
            "名称": item["名称"],
            "原因": ("公告线索（未确认因果）｜" + same_day_titles[0]) if same_day_titles else None,
            "原因线索": titles,
            "同日公告线索": same_day_titles,
            "公告证据数": len(anns),
            "渠道": "东财公告接口",
            "证据级别": "官方公告标题线索",
            "原因状态": "有近期公告线索但未确认因果" if titles else (
                "仅风险/异动或无近期催化线索" if anns else "截至日未发现公告线索"),
            "as_of": d,
        }
    return mapping


def main(d):
    expected = expected_stocks(d)
    try:
        primary = fetch_ths(d)
        ths_error = None
    except Exception as exc:
        primary = {}
        ths_error = f"{type(exc).__name__}: {exc}"
    # 内容不足即补源：有涨停真源时以其覆盖数为分母，阈值为80%；无zt_pool时空结果触发。
    threshold = max(1, int(len(expected) * 0.8)) if expected else 1
    need_fallback = len(primary) < threshold
    missing = {c: n for c, n in expected.items() if c not in primary}
    supplement = None
    if need_fallback:
        supplement = fetch_eastmoney_asof(d, missing or expected)
        mapping = build_fallback_mapping(d, expected, supplement, primary)
    else:
        mapping = primary
    status = "pass" if not ths_error and not need_fallback else "partial"
    out = {
        "日期": d, "as_of": d, "来源": "同花顺涨停原因(B档) + 内容不足自动补东财公告线索",
        "状态": status, "主源条数": len(primary), "条数": len(mapping),
        "预期涨停数": len(expected) or None, "自动补源": need_fallback,
        "补源渠道": "东财公告接口" if need_fallback else None,
        "补源口径": "官方公告标题线索；不确认因果、不自动升级A档" if need_fallback else None,
        "主源错误": ths_error, "映射": mapping,
    }
    with open(os.path.join(L, f"涨停原因_{d}.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f"{d} 涨停原因{len(mapping)}条已存 | 主源={len(primary)} | 自动补源={need_fallback} | 状态={status}")
    if supplement:
        print("补源指标", supplement["指标"])
    for code, value in list(mapping.items())[:5]:
        print(" ", code, value.get("名称"), "|", value.get("原因"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y%m%d")))
