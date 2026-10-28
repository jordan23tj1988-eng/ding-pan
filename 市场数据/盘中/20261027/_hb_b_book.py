# -*- coding: utf-8 -*-
"""hb-b 10:30 场入账：读临盘决断_20261027_1030.json#fills，机械写三本账（账本.jsonl + state.json），不重算价格。"""
import json, os, shutil, datetime

D = os.path.dirname(os.path.abspath(__file__))
SIM = r"D:\股票数据\市场数据\_学习\_模拟盘"
DEC = os.path.join(D, "临盘决断_20261027_1030.json")
AUDIT = os.path.join(D, "入账_20261027_1030.json")

dec = json.load(open(DEC, encoding="utf-8"))
fills = dec["fills"]
TS = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
assert not os.path.exists(AUDIT), "入账审计件已存在，禁止重复入账"

# 幂等保护：今日已有成交行则中止
for b in ("master", "auction", "limitup"):
    rows = [json.loads(l) for l in open(os.path.join(SIM, b, "账本.jsonl"), encoding="utf-8") if l.strip()]
    n_today = sum(1 for r in rows if str(r.get("ts", "")).startswith("2026-10-27"))
    assert n_today == 0, f"{b} 今日已有 {n_today} 条成交行，中止"

audit = {"date": "20261027", "session": "hb-b", "kind": "入账登记（审计件，非发出版）",
         "write_ts": TS, "来源": "临盘决断_20261027_1030.json#fills（本场唯一发出版，未改动）",
         "入账动作": "master/auction/limitup 三本账各追加 sell 行；state.json 同步扣仓加现金；入账前备份 *.bak_hbb_20261027",
         "账本现状": {}}

for route in sorted({f["route"] for f in fills}):
    sdir = os.path.join(SIM, route)
    lg = os.path.join(sdir, "账本.jsonl")
    sp = os.path.join(sdir, "state.json")
    shutil.copy2(lg, lg + ".bak_hbb_20261027")
    shutil.copy2(sp, sp + ".bak_hbb_20261027")
    state = json.load(open(sp, encoding="utf-8"))
    route_fills = [f for f in fills if f["route"] == route]
    cash_before = state["cash"]
    newrows = []
    for f in route_fills:
        # 定位持仓（code + shares + buy_px 三键）
        idx = None
        for i, p in enumerate(state["positions"]):
            if p["code"] == f["code"] and abs(p["shares"] - f["qty"]) < 1e-6 and abs(p["buy_px"] - f["buy_px"]) < 1e-6:
                idx = i
                break
        assert idx is not None, f"{route} 未找到持仓 {f['code']} {f['qty']} @{f['buy_px']}"
        pos = state["positions"].pop(idx)
        state["cash"] = round(state["cash"] + f["proceeds"], 2)
        row = {
            "ev": "sell", "d": "20261027", "code": f["code"], "name": f["name"],
            "shares": f["qty"], "plan_date": "20261026", "buy_date": pos.get("buy_date"),
            "buy_px": f["buy_px"], "sell_date": "20261027", "sell_px": f["px_exec"],
            "leg": "hb_b_catchup", "defers": 0, "switched": False,
            "pnl": f["pnl"], "ret_pct": f["ret_pct"],
            "reason": f"hb-b 10:30 场：{f['rule_src']}；09:40 场未执行→本场 catch_up 补执行｜证据 临盘决断_20261027_1030.json",
            "pnl_note": "毛差(未扣费用)，成交价=决断后下一帧(10:38:49)留档价×(1-0.10%)向下取2位",
            "fill_at": f["ts"], "fill_cls": f["level"], "src": "临盘决断_20261027_1030.json", "ts": TS,
        }
        newrows.append(row)
    with open(lg, "a", encoding="utf-8") as fh:
        for r in newrows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    json.dump(state, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    audit["账本现状"][route] = {
        "rows_20261027": newrows,
        "cash_before": cash_before, "cash_after": state["cash"],
        "positions_after": [[p["code"], p["name"], p["shares"], p["buy_px"]] for p in state["positions"]],
    }
    print(route, "cash", cash_before, "->", state["cash"], "positions_left", len(state["positions"]),
          [(p["code"], p["shares"], p["buy_px"]) for p in state["positions"]])

json.dump(audit, open(AUDIT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("AUDIT", AUDIT, os.path.getsize(AUDIT))
