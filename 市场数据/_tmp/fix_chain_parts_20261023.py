# -*- coding: utf-8 -*-
"""20261023 链路补件：
1) 交易计划_master_20261023.json（总审筛选清单 -> master 正式计划，权重=建议权重%，buy_gate 取自原路计划）
2) theme 题材生命周期判断：'口径与盲区' 归位（合并进 说明 文本，字段删除）
3) cycle判断_20261023.json 归档（生产走 judgment.bodies.cycle 路径，与昨日同构）
"""
import json, os, shutil

os.chdir(r"D:\股票数据\市场数据")
D = "20261023"
L = "_学习"

# ---------- 1) master 交易计划 ----------
tot = json.load(open(os.path.join(L, f"总审_{D}.json"), encoding="utf-8"))
rows = tot["筛选清单"]["明细"]
keep = [r for r in rows if str(r["留/剔"]).startswith("留")]

plans = {}
for route in ["auction", "lhb", "theme", "logic", "limitup"]:
    p = os.path.join(L, f"交易计划_{route}_{D}.json")
    plans[route] = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {"buys": [], "sells": []}

buys = []
for i, r in enumerate(keep, 1):
    code, name = r["票"].split(" ", 1) if " " in r["票"] else (r["票"], "")
    src_route = r["路"]
    src_buy = next((b for b in plans[src_route].get("buys", []) if str(b.get("代码")) == code), {})
    gate = src_buy.get("buy_gate") or {"min_gap_pct": -3, "max_gap_pct": 3}
    reason = (
        f"【总审筛选清单第{i}顺位·{r['留/剔']}·原提 {r['来自路']} {r['原权重%']}%→建议 {r['建议权重%']}%】"
        f"{r.get('原因', '')} 来源：_学习/总审_{D}.json#筛选清单/明细、_学习/交易计划_{src_route}_{D}.json#buys。"
    )
    buys.append({
        "代码": code,
        "名称": name,
        "权重%": r["建议权重%"],
        "buy_gate": gate,
        "理由": reason,
    })

sells = []
for route, pl in plans.items():
    for s in pl.get("sells", []):
        sells.append(dict(s, 来源路=route))

total = round(sum(b["权重%"] for b in buys), 4)
mp = {
    "日期": D,
    "路": "master",
    "buys": buys,
    "sells": sells,
    "notes": (
        f"总审 B中性·置信58；筛选 {tot['筛选清单']['并集数']}→{len(buys)} 只、合计 {total}%（留用率 {round(len(buys)/tot['筛选清单']['并集数']*100,2)}%）。"
        "剔除：002474（auction 自我豁免被驳回）、301502（theme/logic 双侧负桶）、688836（价格口径 P0：153.20 vs 双源 624.00，200 股=124,800 元=nav 12.30% 越档 4 倍）。"
        "线级约束：同一大方向（题材归位口径）合计权重上限 7%，超限即按线级优先级砍尾；线内涨停<8 只则线内票全弃。"
        "引擎消费字段为『权重%』；本计划不构成操作指令。"
    ),
    "source": f"_学习/总审_{D}.json#筛选清单；各路 交易计划_{ '{route}' }_{D}.json#buys（buy_gate 原样继承）",
}
op = os.path.join(L, f"交易计划_master_{D}.json")
json.dump(mp, open(op, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("master 计划:", op, os.path.getsize(op), "bytes | buys", len(buys), "合计", total, "| sells", len(sells))
for b in buys:
    print("  ", b["代码"], b["名称"], b["权重%"], b["buy_gate"])

# ---------- 2) theme 生命周期判断字段归位 ----------
lp = os.path.join(L, f"题材生命周期判断_{D}.json")
life = json.load(open(lp, encoding="utf-8"))
if "口径与盲区" in life:
    shutil.copy2(lp, lp + ".bak_keyalign")
    kb = life.pop("口径与盲区")
    if isinstance(kb, dict):
        txt = "；".join(f"{k}：{v}" for k, v in kb.items())
    else:
        txt = str(kb)
    old = life.get("说明")
    life["说明"] = (f"{old}｜【口径与盲区】{txt}" if old else f"【口径与盲区】{txt}")
    order = ["日期", "路", "来源", "逐线判断", "高低切", "说明", "底座", "概率说明", "独立盲区声明"]
    life = {k: life[k] for k in order if k in life} | {k: v for k, v in life.items() if k not in order}
    json.dump(life, open(lp, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    print("生命周期判断归位 OK，现顶层:", list(life), "| 说明长度", len(life["说明"]))
else:
    print("生命周期判断无需改，顶层:", list(life))

# ---------- 3) cycle判断 归档 ----------
cp = os.path.join(L, f"cycle判断_{D}.json")
arc = os.path.join(L, "_归档")
if os.path.exists(cp):
    os.makedirs(arc, exist_ok=True)
    shutil.move(cp, os.path.join(arc, f"cycle判断_{D}_结构化归档.json"))
    print("cycle判断 已归档 ->", os.path.join(arc, f"cycle判断_{D}_结构化归档.json"), "（生产走 judgment.bodies.cycle）")
else:
    print("cycle判断 不存在，跳过")
