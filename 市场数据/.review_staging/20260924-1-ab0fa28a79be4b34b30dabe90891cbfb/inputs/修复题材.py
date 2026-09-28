# -*- coding: utf-8 -*-
"""修复盘中作战 warboard 的题材(theme)缺失 —— 2026-08-14
根因: 0813 席位荐票 3 只(太极实业/瑞康医药/通宇通讯)非涨停, 不在 zt_pool.csv,
      warboard_build.py 只从 zt_pool 取行业 → theme 空 → 题材列"—"+dim题材"无概念数据"。
修复: 用 eastmoney 所属行业(f127, 与 zt_pool 同源)回填 theme, 并用 conc_pct 重算 dim。
用法: env -u PYTHONPATH python 修复题材.py
"""
import json, io, os, sys, importlib

BASE = r"D:\股票数据\市场数据"
sys.path.insert(0, r"D:\盯盘台作战台_806")
sys.path.insert(0, BASE)

eng = importlib.import_module("盘中回应引擎")

wb_path = os.path.join(BASE, "盘中", "20260813", "warboard.json")
wb = json.load(io.open(wb_path, encoding="utf-8"))

# eastmoney 所属行业(与 zt_pool 同源: akshare stock_zt_pool_em → push2 f127), 直连 curl 实测
THEME_FIX = {
    "600667": "工程咨询服务Ⅱ",  # 十一科技工程总包占大头, 东财行业=工程咨询服务Ⅱ(非半导体)
    "002589": "医药商业",      # 东财行业=医药商业(与 zt_pool 药易购同命名)
    "002792": "通信设备",      # 东财行业=通信设备(与 zt_pool 星网锐捷同命名)
}

# 10:00 conc_pct(最后一个 response 的快照, 与其余23卡同口径)
rs = wb.get("responses") or []
conc_pct = (rs[-1].get("conc_pct") or {}) if rs else {}
if not conc_pct:
    print("[FAIL] 无 conc_pct(response 空), 无法重算 dim"); sys.exit(1)

# 腾讯报价(重拉; 午间休市=11:30冻结)
key = eng.ths_key()
codes = [eng.mkt(c["code"]) for c in wb["cards"]]
q = eng.fetch_tencent(codes)

changed = []
for c in wb["cards"]:
    if c["code"] in THEME_FIX:
        old = c["theme"]
        c["theme"] = THEME_FIX[c["code"]]
        v = q.get(eng.mkt(c["code"]))
        if v:
            c["px"] = v["px"]
            c["chg_pct"] = v["chg"]
        c["dim"] = eng.dim_eval(c, v, conc_pct)
        c["auction"]["note"] = "成交条件: " + " ".join(
            "%s:%s" % (k, val) for k, val in c["dim"].items() if k != "综合")
        # 重算概念涨幅_cs(影响已触发内部排序)
        th = (c["theme"] or "").split("/")[0]
        hit = eng._conc_hit(th, conc_pct)
        c["_cs"] = hit[1] if hit else 0
        changed.append((c["code"], c["name"], old, c["theme"]))

json.dump(wb, io.open(wb_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("[OK] theme 回填:", [(x[0], x[1], "%r→%s" % (x[2], x[3])) for x in changed])
for c in wb["cards"]:
    if c["code"] in THEME_FIX:
        print("  %s %s | theme=%s | 题材=%s | 个股=%s | 综合=%s | _cs=%s" % (
            c["code"], c["name"], c["theme"], c["dim"].get("题材"),
            c["dim"].get("个股"), c["dim"].get("综合"), round(c.get("_cs") or 0, 2)))
