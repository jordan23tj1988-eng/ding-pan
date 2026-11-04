# -*- coding: utf-8 -*-
import json
from pathlib import Path

raw = Path(r"D:\股票数据\市场数据\盘中\20261104\playbook.json").read_bytes()
d = json.loads(raw.decode("utf-8"))
assert d["date"] == "20261104"
assert sum(b["weight_pct"] for b in d["buys"]) <= 1.5
assert all(b["trigger"]["open_range"]["opening"] and b["trigger"]["open_range"]["min_gap"] < b["trigger"]["open_range"]["max_gap"] for b in d["buys"])
assert all(w.get("confirm") and w.get("falsify") for w in d["watch"])
assert len(d["route_plans"]) == 5 and all(len(r) == 5 for r in d["route_plans"])
assert d["sells"] == []
assert d["cash_pct"] == 98.5
assert all(b["intraday"]["stop_pct"] is None for b in d["buys"])
auction_tickets = {"605577", "002088", "601123", "002827", "601599"}
assert not (set(w["代码"] for w in d["watch"]) .intersection(auction_tickets))
print("ALL ASSERTIONS PASS")
print("buys", [(b["代码"], b["名名"], b["weight_pct"]) for b in d["buys"]])
print("watch", [(w["代码"], w["名称"], w["source"].split("（")[0]) for w in d["watch"]])
print("cash", d["cash_pct"], "sells", len(d["sells"]), "route_plans", [(r["route"], r["buys_count"], r["sells_count"]) for r in d["route_plans"]])
print("notes paras", d["notes"].count("\n") + 1, "chars", len(d["notes"]))
print("stop_note?", "【止损口径·默认关闭】" in d["notes"], "| 688809不可执行?", "不可执行" in json.dumps(d["buys"][1], ensure_ascii=False))
