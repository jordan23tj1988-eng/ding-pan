# -*- coding: utf-8 -*-
"""把五路/总审判断文件里超出 review_contract 白名单的顶层字段就地搬家（不丢信息），
搬法：内容并入白名单内的语义最近字段，原键删除。"""
import json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
L = os.path.join(BASE, "_学习")
D = "20261020"

def load(p):
    return json.load(open(p, encoding="utf-8"))

def save(p, o):
    json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 1) 五路：能力回执 -> 验证注记
for r in ("auction", "lhb", "theme", "logic", "limitup"):
    p = os.path.join(L, "%s判断_%s.json" % (r, D))
    o = load(p)
    moved = []
    for k in ("能力回执", "能力承接"):
        if k in o:
            moved.append("%s：%s" % (k, json.dumps(o.pop(k), ensure_ascii=False)))
    if moved:
        note = o.get("验证注记") or ""
        o["验证注记"] = (note + "；" if note else "") + "；".join(moved)
        save(p, o)
        print(r, "moved:", [m[:20] for m in moved])

# 2) 总审：超出白名单的顶层键 数据缺口/角色 -> 回填窗口标注 / 来源
p = os.path.join(L, "总审_%s.json" % D)
o = load(p)
changed = []
if "数据缺口" in o:
    gaps = o.pop("数据缺口")
    o["回填窗口标注"] = (o.get("回填窗口标注") or "") + "；数据缺口：" + json.dumps(gaps, ensure_ascii=False)
    changed.append("数据缺口")
if "角色" in o:
    role = o.pop("角色")
    o["来源"] = (o.get("来源") or "") + "；角色：" + str(role)
    changed.append("角色")
o.setdefault("schema_version", 1)
if changed:
    save(p, o)
print("总审 moved:", changed, "keys:", sorted(o))

# 3) 显示还剩哪些未知键
import review_contract as rc
for r in ("auction", "lhb", "theme", "logic", "limitup"):
    o = load(os.path.join(L, "%s判断_%s.json" % (r, D)))
    print(r, "unknown:", sorted(set(o) - set(rc.ROUTE_AUDIT_KEYS)))
o = load(p)
print("master unknown:", sorted(set(o) - set(rc.TOTAL_AUDIT_KEYS)))
