# -*- coding: utf-8 -*-
"""卡位纯度每日复算（MA-20261022-04 ①）
用法: python 卡位纯度复算.py 20261023
输入: 20261023/zt_pool.csv, _学习/题材归位_20261023.json, 产业链模板.json
输出: _学习/卡位纯度_20261023.json
口径:
  1) 东财F10 主营构成(按产品/按行业, 最新报告期) 逐项收入占比 + 毛利率
  2) 节点映射: 关键词→产业链模板『人形机器人』节点; 模板外但同链条的相邻节点单列 adjacent
  3) 卡位纯度 = 主营构成中机器人链节点(模板节点+相邻节点)收入占比合计
  4) 真卡位 = 纯度>=50%; 严格模板节点 = 命中的节点属于模板7节点之一
所有百分比保留2位小数, 原始金额保留元。不编造: 取不到数据 → purity=null, 标 卡位不明。
"""
import csv
import json
import os
import sys
import time
from urllib.request import Request, urlopen

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATE = sys.argv[1] if len(sys.argv) > 1 else "20261023"
UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://emweb.securities.eastmoney.com/"}

# 模板节点 → 关键词（严格模板节点）
# 排除词优先: 命中即判非链(防止 光伏电池片→电池、汽车轴承→机器人轴承 这类误配)
VETO = ["光伏", "电池片", "钢帘线", "轮胎", "胎圈", "家电", "包装", "印刷", "广告", "针织",
        "LED", "文体旅", "汽车零部件", "汽车悬架", "减震器", "温控", "电动工具", "煤炭", "煤矿",
        "IC分销", "智慧车管", "智慧车检", "照明", "铝型材", "冲压", "铁芯", "给药装置",
        "离合器", "压力传感", "缝纫", "横机", "外饰", "塑料", "数字孪生", "数字展示", "体验空间"]

# 模板节点 → 关键词（严格模板节点, 机器人专用语)
TEMPLATE_NODES = {
    "谐波减速器": ["谐波减速", "RV减速", "精密减速器"],
    "行星滚柱丝杠": ["丝杠"],
    "无框力矩/空心杯电机": ["无框", "空心杯", "控制电机", "步进电机", "伺服电机"],
    "灵巧手传动": ["微型传动", "精密传动", "灵巧手"],
    "六维力传感器": ["六维力", "力传感器", "力矩传感器"],
    "本体/集成": ["人形机器人", "四足机器人", "机器人组件", "机器人本体", "工业机器人",
              "机器人整机", "机器人系统", "机器人及智能", "机器人业务"],
    "具身大模型": [],
}
# 相邻节点（同链条但不是模板7节点, 单独计数, 不计入严格模板口径）
ADJ_NODES = {
    "微特电机/电机组件": ["微特电机", "电机及组件"],
    "伺服驱动/运动控制": ["伺服", "运动控制", "驱动系统", "自动化核心部件"],
    "机器视觉": ["机器视觉"],
    "触觉/柔性传感": ["触觉", "电子皮肤"],
    "机器人轴承(须明示机器人)": ["机器人轴承"],
}


def code2secu(code):
    code = str(code).zfill(6)
    if code.startswith(("6", "9")):
        return "SH" + code
    if code.startswith(("0", "3")):
        return "SZ" + code
    return "BJ" + code


def fetch_f10(code, retries=3):
    url = ("https://emweb.securities.eastmoney.com/PC_HSF10/BusinessAnalysis/PageAjax?code="
           + code2secu(code))
    for i in range(retries):
        try:
            req = Request(url, headers=UA)
            with urlopen(req, timeout=25) as r:
                raw = r.read()
            if raw[:2] == bytes([0x1F, 0x8B]):  # 服务端偶发 gzip 未声明
                import gzip
                raw = gzip.decompress(raw)
            j = json.loads(raw.decode("utf-8"))
            return j
        except Exception as e:  # noqa: BLE001
            if i == retries - 1:
                return {"_error": str(e)}
            time.sleep(1.2 * (i + 1))
    return {"_error": "unreachable"}


def classify(item_name):
    """返回 (节点名, 是否模板节点)"""
    for v in VETO:
        if v in item_name:
            return None, False
    for node, kws in TEMPLATE_NODES.items():
        for kw in kws:
            if kw and kw in item_name:
                return node, True
    for node, kws in ADJ_NODES.items():
        for kw in kws:
            if kw and kw in item_name:
                return node, False
    return None, False


def main():
    zt = list(csv.DictReader(open(os.path.join(BASE, DATE, "zt_pool.csv"), encoding="utf-8-sig")))
    by_code = {r["代码"].zfill(6): r for r in zt}
    gw = json.load(open(os.path.join(BASE, "_学习", "题材归位_%s.json" % DATE), encoding="utf-8"))
    mapping = gw["映射"]
    robot = [c for c, v in mapping.items()
             if str(v.get("大方向") or "").startswith("机器人")]

    tpl = json.load(open(os.path.join(BASE, "产业链模板.json"), encoding="utf-8"))
    robot_tpl = tpl.get("人形机器人", {}).get("环节", {})
    tpl_codes = {}
    for node, arr in robot_tpl.items():
        for c, n in arr:
            tpl_codes[c.zfill(6)] = {"节点": node, "名称": n}

    out = {
        "日期": DATE,
        "脚本": "_ops/卡位纯度复算.py",
        "口径": ("东财F10主营构成(按产品,最新报告期)；卡位纯度=主营构成中落在人形机器人链节点(模板7节点+相邻节点)"
                 "的收入占比合计；真卡位=纯度>=50%；严格模板节点=命中节点属模板7节点之一；取不到数据→purity=null标卡位不明。"),
        "报告期分布": {},
        "机器人涨停": [],
        "模板内标的": [],
        "汇总": {},
    }

    def do_one(code, name, is_zt=True):
        j = fetch_f10(code)
        rec = {"代码": code, "名称": name, "在模板": code in tpl_codes,
               "模板节点": tpl_codes.get(code, {}).get("节点"),
               "source_status": "ok", "purity": None, "strict_template": None,
               "items": [], "报告期": None}
        if "_error" in j:
            rec["source_status"] = "error:" + j["_error"][:80]
            rec["纯度说明"] = "卡位不明(取数失败)"
            return rec
        z = j.get("zygcfx") or []
        if not z:
            rec["source_status"] = "empty"
            rec["纯度说明"] = "卡位不明(F10无主营构成)"
            return rec
        # 最新报告期
        dates = sorted({x.get("REPORT_DATE", "")[:10] for x in z}, reverse=True)
        rp = dates[0]
        rows = [x for x in z if x.get("REPORT_DATE", "")[:10] == rp
                and str(x.get("MAINOP_TYPE")) == "2"]  # 按产品
        if not rows:
            rows = [x for x in z if x.get("REPORT_DATE", "")[:10] == rp]
        rec["报告期"] = rp
        total = 0.0
        in_chain = 0.0
        strict = 0.0
        nodes = []
        for x in rows:
            nm = (x.get("ITEM_NAME") or "").strip()
            ratio = float(x.get("MBI_RATIO") or 0) * 100
            gm = x.get("GROSS_RPOFIT_RATIO")
            inc = x.get("MAIN_BUSINESS_INCOME")
            node, is_tpl = classify(nm)
            total += ratio
            if node:
                in_chain += ratio
                if is_tpl:
                    strict += ratio
                nodes.append(node + ("" if is_tpl else "(相邻)"))
            rec["items"].append({
                "分项": nm, "占比pct": round(ratio, 2),
                "毛利率pct": (round(float(gm) * 100, 2) if gm is not None else None),
                "收入元": (round(float(inc), 2) if inc is not None else None),
                "节点": node, "模板节点": bool(node and is_tpl),
            })
        rec["purity"] = round(in_chain, 2)
        rec["strict_template"] = round(strict, 2)
        rec["链上节点"] = sorted(set(nodes))
        rec["真卡位"] = bool(rec["purity"] is not None and rec["purity"] >= 50)
        rec["主占比项"] = rec["items"][0]["分项"] if rec["items"] else None
        rec["主占比pct"] = rec["items"][0]["占比pct"] if rec["items"] else None
        rec["主占比毛利pct"] = rec["items"][0]["毛利率pct"] if rec["items"] else None
        if not nodes:
            rec["纯度说明"] = "主营无机器人链节点收入=贴标"
        return rec

    seen = set()
    for code in robot:
        v = mapping[code]
        zr = by_code.get(code, {})
        rec = do_one(code, v.get("名称"))
        rec.update({
            "环节标签": v.get("环节"), "所属行业": v.get("所属行业"),
            "连板口径": v.get("连板口径"), "首封": v.get("首封"),
            "最新价": float(zr.get("最新价") or 0),
            "连板数": zr.get("连板数"),
            "封板资金亿": round(float(zr.get("封板资金") or 0) / 1e8, 3),
            "流通市值亿": round(float(zr.get("流通市值") or 0) / 1e8, 2),
            "封单比pct": (round(float(zr.get("封板资金") or 0) / float(zr.get("流通市值") or 1) * 100, 3)),
            "成交额亿": round(float(zr.get("成交额") or 0) / 1e8, 2),
            "换手pct": round(float(zr.get("换手率") or 0), 2),
            "炸板": zr.get("炸板次数"),
        })
        out["机器人涨停"].append(rec)
        seen.add(code)

    # 模板内标的（非今日涨停）也复算, 供历史 union 对照
    for code, meta in tpl_codes.items():
        if code in seen:
            continue
        rec = do_one(code, meta["名称"], is_zt=False)
        out["模板内标的"].append(rec)
        time.sleep(0.15)

    rows = out["机器人涨停"]
    ok = [r for r in rows if r["purity"] is not None]
    true_pos = [r for r in ok if r["真卡位"]]
    strict_pos = [r for r in ok if r["strict_template"] and r["strict_template"] >= 50]
    out["汇总"] = {
        "机器人涨停只数": len(rows),
        "取数成功": len(ok),
        "真卡位只数(纯度>=50%)": len(true_pos),
        "真卡位占比pct": round(len(true_pos) / len(rows) * 100, 2),
        "严格模板节点只数(>=50%)": len(strict_pos),
        "严格模板节点占比pct": round(len(strict_pos) / len(rows) * 100, 2),
        "贴标只数(链上节点=0)": len([r for r in ok if r["purity"] == 0]),
        "纯度中位pct": round(sorted(r["purity"] for r in ok)[len(ok) // 2], 2) if ok else None,
        "真卡位名单": [[r["代码"], r["名称"], r["purity"]] for r in true_pos],
    }
    out["报告期分布"] = {}
    for r in rows + out["模板内标的"]:
        if r["报告期"]:
            out["报告期分布"][r["报告期"]] = out["报告期分布"].get(r["报告期"], 0) + 1

    p = os.path.join(BASE, "_学习", "卡位纯度_%s.json" % DATE)
    json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("WROTE", p, os.path.getsize(p), "bytes")
    print(json.dumps(out["汇总"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
