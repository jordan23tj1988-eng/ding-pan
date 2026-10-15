import json, hashlib, os, datetime
R = r"D:\股票数据\市场数据"
os.chdir(R)
D = "20261015"
PRE = "_学习/能力预加载_%s.json" % D
pre = json.load(open(PRE, encoding="utf-8"))
sha = hashlib.sha256(open(PRE, "rb").read()).hexdigest()
routes = {}
for r in ["auction", "lhb", "theme", "logic", "limitup"]:
    p = "_学习/_能力回执片段_%s_%s.json" % (r, D)
    routes[r] = json.load(open(p, encoding="utf-8"))
for r in ["cycle", "master"]:
    elig = [str(x.get("id")) for x in ((pre["routes"].get(r) or {}).get("records") or [])]
    routes[r] = {"status": "no_eligible_capabilities" if not elig else "applied",
                 "considered_ids": elig, "applied": [], "rejected": [],
                 "note": "宿主合并：该域当日 eligible_count=%d" % len(elig)}
out = {"schema_version": 1, "as_of": D,
       "preload": {"path": PRE, "sha256": sha},
       "generated_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
       "note": "宿主合并七域回执片段（五路=子agent产物；cycle/master 宿主按预加载 eligible 判定）。",
       "routes": routes}
p = "_学习/能力使用回执_%s.json" % D
json.dump(out, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("WROTE", p, os.path.getsize(p))
for r, v in routes.items():
    print(" ", r, v["status"], v["considered_ids"], "applied=%d" % len(v.get("applied") or []))
