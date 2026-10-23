# -*- coding: utf-8 -*-
"""宿主汇总 能力使用回执_20261023.json + 修 theme判断顶层字段名（数据源→来源、昨日自我对账→昨日结算）"""
import json, os, sys, hashlib, shutil, datetime

os.chdir(r"D:\股票数据\市场数据")
D = "20261023"
L = "_学习"

# ---------- 1) theme 判断顶层字段名对齐 ROUTE_AUDIT_KEYS ----------
tp = os.path.join(L, f"theme判断_{D}.json")
t = json.load(open(tp, encoding="utf-8"))
ren = {"数据源": "来源", "昨日自我对账": "昨日结算"}
changed = []
if any(k in t for k in ren):
    shutil.copy2(tp, tp + ".bak_keyalign")
    for old, new in ren.items():
        if old in t:
            if new in t:
                # 已有同名键：合并不覆盖
                print("WARN 目标键已存在，两者并存处理:", new)
                t[new] = [t[new], t.pop(old)]
            else:
                t[new] = t.pop(old)
            changed.append((old, new))
    order = ["日期", "路", "判断", "荐票", "认知迭代", "深挖", "来源", "昨日结算"]
    t = {k: t[k] for k in order if k in t} | {k: v for k, v in t.items() if k not in order}
    json.dump(t, open(tp, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("theme 字段改名:", changed, "| 现顶层:", list(t))

# ---------- 2) 能力使用回执 ----------
pre_path = os.path.join(L, f"能力预加载_{D}.json")
pre = json.load(open(pre_path, encoding="utf-8"))
sha = hashlib.sha256(open(pre_path, "rb").read()).hexdigest()
pre_routes = pre.get("routes", {})

RECEIPTS = {
    "auction": f"能力回执_auction_{D}.json",
    "lhb": f"能力回执_lhb_{D}.json",
    "theme": f"能力回执_theme_{D}.json",
    "logic": f"能力回执_logic_{D}.json",
    "limitup": f"能力回执_limitup_{D}.json",
}

routes = {}
problems = []
for route in ["auction", "lhb", "theme", "logic", "limitup", "cycle", "master"]:
    st = pre_routes.get(route, {})
    eligible = st.get("eligible_count", 0)
    rp = os.path.join(L, RECEIPTS.get(route, f"能力回执_{route}_{D}.json"))
    data = json.load(open(rp, encoding="utf-8")) if os.path.exists(rp) else None

    if data is None:
        # 无回执文件：只有当预加载确实无可消费能力时才允许按 no_eligible 写，否则报错
        if eligible == 0:
            routes[route] = {
                "status": "no_eligible_capabilities",
                "considered_ids": [],
                "applied": [],
                "rejected": [],
                "note": f"来源=_学习/能力预加载_{D}.json#routes.{route}：eligible_count=0、status={st.get('status')}，本路本日无可消费已验证能力；本路未写独立回执文件，按预加载状态登记，判断由当日原始数据直算。",
            }
        else:
            problems.append(f"{route}: 预加载 eligible_count={eligible} 但无回执文件")
        continue

    # 统一 applied 条目：必须有 id/effect/source_locator
    raw_app = data.get("applied") or data.get("回执") or []
    applied, rejected = [], data.get("rejected") or []
    for a in raw_app:
        dec = a.get("decision") or a.get("决定") or "applied"
        item = {
            "id": a.get("id"),
            "effect": a.get("effect"),
            "source_locator": a.get("source_locator"),
        }
        if dec == "rejected":
            rejected.append({"id": a.get("id"), "reason": a.get("reason") or a.get("理由")})
        else:
            if not (item["id"] and item["effect"] and item["source_locator"]):
                problems.append(f"{route}: applied {item['id']} 缺 effect/source_locator")
            applied.append(item)

    status = "applied" if applied else ("no_eligible_capabilities" if eligible == 0 else "rejected_all")
    routes[route] = {
        "status": status,
        "considered_ids": [x.get("id") for x in raw_app if x.get("id")],
        "applied": applied,
        "rejected": rejected,
        "note": data.get("备注") or data.get("note") or None,
    }

if problems:
    print("PROBLEMS:", problems)
    sys.exit(3)

out = {
    "schema_version": 1,
    "as_of": D,
    "written_at": f"{D} 复盘(宿主汇总，源=五路能力回执+能力预加载；cycle/master 按预加载状态登记)",
    "preload": {"path": f"_学习/能力预加载_{D}.json", "sha256": sha},
    "routes": routes,
}
op = os.path.join(L, f"能力使用回执_{D}.json")
json.dump(out, open(op, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("写入", op, os.path.getsize(op), "bytes")
for k, v in routes.items():
    print(" ", k, v["status"], "applied", len(v["applied"]))
