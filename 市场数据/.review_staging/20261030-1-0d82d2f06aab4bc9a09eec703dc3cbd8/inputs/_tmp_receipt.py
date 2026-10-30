# -*- coding: utf-8 -*-
"""构建 _学习/能力使用回执_20261029.json (七域) —— 严格按 能力进化接线._validate_receipt 规则"""
import json, io, os, hashlib

BASE = r"D:\股票数据\市场数据"
D = "20261029"
L = os.path.join(BASE, "_学习")
ROUTES = ["auction", "lhb", "theme", "logic", "limitup", "cycle", "master"]
PRELOAD = os.path.join(L, "能力预加载_%s.json" % D)


def sha(p):
    return hashlib.sha256(io.open(p, "rb").read()).hexdigest()


pre = json.load(io.open(PRELOAD, encoding="utf-8"))
routes = pre.get("routes") or {}
eligible = {r: [str(x.get("id")) for x in ((routes.get(r) or {}).get("records") or [])] for r in ROUTES}

out_routes = {}
for r in ROUTES:
    ids = eligible[r]
    frag_p = os.path.join(L, "_能力回执片段_%s_%s.json" % (r, D))
    frag = None
    if os.path.isfile(frag_p):
        try:
            frag = json.load(io.open(frag_p, encoding="utf-8"))
        except Exception:
            frag = None
    applied, rejected = [], []
    if frag:
        for x in (frag.get("采用") or []):
            cid = str(x.get("capability_id") or x.get("id") or "")
            if cid in ids:
                applied.append({"id": cid,
                                "effect": str(x.get("效果") or x.get("effect") or "")[:400] or "已用于本路判断证据链",
                                "source_locator": "_学习/%s判断_%s.json#判断.证据" % (r, D)})
        for x in (frag.get("拒绝") or []):
            cid = str(x.get("capability_id") or x.get("id") or "")
            if cid in ids:
                rejected.append({"id": cid, "reason": str(x.get("理由") or x.get("reason") or "")[:300] or "本路未采用"})
    used = set([a["id"] for a in applied] + [b["id"] for b in rejected])
    for cid in ids:
        if cid not in used:
            rejected.append({"id": cid,
                             "reason": "本路判断未引用该能力(无 effect 证据, 不写 applied 以防编造)"})
    if not ids:
        status = "no_eligible_capabilities"
    else:
        status = "applied" if applied else "rejected_all"
    out_routes[r] = {"status": status,
                     "considered_ids": ids,
                     "applied": applied,
                     "rejected": rejected}

doc = {"schema_version": 1, "as_of": D, "decision_cutoff": D,
       "preload": {"path": PRELOAD, "sha256": sha(PRELOAD)},
       "routes": out_routes,
       "source": "宿主按七域实际使用情况汇总(五路取 _能力回执片段_{route}, cycle/master 见 rejected 理由; 零编造: 无 effect 不写 applied)"}
outp = os.path.join(L, "能力使用回执_%s.json" % D)
json.dump(doc, open(outp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({r: {"status": out_routes[r]["status"], "eligible": len(eligible[r]),
                      "applied": len(out_routes[r]["applied"]), "rejected": len(out_routes[r]["rejected"])}
                  for r in ROUTES}, ensure_ascii=False, indent=1))
print("WROTE", outp)
