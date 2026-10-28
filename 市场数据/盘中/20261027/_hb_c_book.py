# -*- coding: utf-8 -*-
"""hb-c 11:00 场入账：读 临盘决断_20261027_1100.json#fills，机械写 limitup/auction 两本账（账本.jsonl + state.json），不重算价格。"""
import json, os, shutil, datetime

D = os.path.dirname(os.path.abspath(__file__))
SIM = r"D:\股票数据\市场数据\_学习\_模拟盘"
DEC = os.path.join(D, "临盘决断_20261027_1100.json")
AUDIT = os.path.join(D, "入账_20261027_1100.json")

dec = json.load(open(DEC, encoding="utf-8"))
fills = dec["fills"]
TS = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
assert not os.path.exists(AUDIT), "入账审计件已存在，禁止重复入账"

# 幂等保护：今日已有成交行必须恰为 hb-b 的 8 条
pre = {}
for b in ("master", "auction", "limitup"):
    rows = [json.loads(l) for l in open(os.path.join(SIM, b, "账本.jsonl"), encoding="utf-8") if l.strip()]
    pre[b] = sum(1 for r in rows if str(r.get("ts", "")).startswith("2026-10-27"))
assert sum(pre.values()) == 8, f"今日成交行数应为 8（hb-b），实际 {pre}"

audit = {"date": "20261027", "session": "hb-c", "kind": "入账登记（审计件，非发出版）",
         "write_ts": TS, "来源": "临盘决断_20261027_1100.json#fills（本场唯一发出版，未改动）",
         "入账动作": "limitup/auction 两本账各追加 sell 行；state.json 同步扣仓加现金；入账前备份 *.bak_hbc_20261027",
         "入账前行数": pre, "账本现状": {}}

for route in sorted({f["route"] for f in fills}):
    sdir = os.path.join(SIM, route)
    lg = os.path.join(sdir, "账本.jsonl")
    sp = os.path.join(sdir, "state.json")
    shutil.copy2(lg, lg + ".bak_hbc_20261027")
    shutil.copy2(sp, sp + ".bak_hbc_20261027")
    state = json.load(open(sp, encoding="utf-8"))
    route_fills = [f for f in fills if f["route"] == route]
    cash_before = state["cash"]
    newrows = []
    for f in route_fills:
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
            "shares": f["qty"], "plan_date": pos.get("plan_date"), "buy_date": pos.get("buy_date"),
            "buy_px": f["buy_px"], "sell_date": "20261027", "sell_px": f["px_exec"],
            "leg": "hb_c_defense", "defers": 0, "switched": False,
            "pnl": f["pnl"], "ret_pct": f["ret_pct"],
            "reason": f"hb-c 11:00 场 B级预案外防守：{f['trigger_evidence']}｜证据 临盘决断_20261027_1100.json",
            "pnl_note": "毛差(未扣费用)，成交价=决断后下一帧(11:06:10)留档价×(1-0.10%)向下取2位",
            "fill_at": f["ts"], "fill_cls": f["level"], "src": "临盘决断_20261027_1100.json", "ts": TS,
        }
        newrows.append(row)
    with open(lg, "a", encoding="utf-8") as fh:
        for r in newrows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    state["date"] = "20261027"
    json.dump(state, open(sp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    audit["账本现状"][route] = {
        "rows_20261027": newrows, "cash_before": cash_before, "cash_after": state["cash"],
        "positions_after": [[p["code"], p["name"], p["shares"], p["buy_px"]] for p in state["positions"]],
    }
    print(route, "cash", cash_before, "->", state["cash"], "positions_left", len(state["positions"]),
          [(p["code"], p["shares"]) for p in state["positions"]])

json.dump(audit, open(AUDIT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("AUDIT", AUDIT, os.path.getsize(AUDIT))

# 入账后核验：账本末行 vs 决断件 fills 一致
ok = True
for route in audit["账本现状"]:
    rows = [json.loads(l) for l in open(os.path.join(SIM, route, "账本.jsonl"), encoding="utf-8") if l.strip()]
    last = rows[-len(audit["账本现状"][route]["rows_20261027"]):]
    for r, f in zip(last, audit["账本现状"][route]["rows_20261027"]):
        if abs(r["sell_px"] - f["sell_px"]) > 1e-9 or r["code"] != f["code"]:
            ok = False
print("VERIFY_LEDGER", "PASS" if ok else "FAIL")
