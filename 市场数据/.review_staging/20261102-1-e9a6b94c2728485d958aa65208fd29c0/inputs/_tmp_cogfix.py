# -*- coding: utf-8 -*-
"""规范 认知迭代 条目(标题/内容→claim) + 总审顶层未知键归并，满足 review_learning gate"""
import io, json, os

L = r"D:\股票数据\市场数据\_学习"
D = "20261029"

for r in ["auction", "lhb", "theme", "logic", "limitup"]:
    p = os.path.join(L, "%s判断_%s.json" % (r, D))
    j = json.load(io.open(p, encoding="utf-8"))
    items = j.get("认知迭代")
    changed = 0
    if isinstance(items, list):
        new = []
        for it in items:
            if isinstance(it, str):
                new.append({"d": D, "claim": it})
                changed += 1
            elif isinstance(it, dict):
                if it.get("claim"):
                    new.append(it)
                    continue
                title = str(it.get("标题") or it.get("认知点") or "").strip()
                body = str(it.get("内容") or it.get("正文") or "").strip()
                claim = (title + "：" + body).strip("：") if title and body else (title or body)
                rec = {"d": it.get("d") or D, "claim": claim}
                for k, v in it.items():
                    if k not in ("标题", "内容", "认知点", "正文", "claim", "d"):
                        rec[k] = v
                if title:
                    rec["标题"] = title
                new.append(rec)
                changed += 1
            else:
                new.append(it)
        j["认知迭代"] = new
    json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(r, "认知条目", len(j.get("认知迭代") or []), "改写", changed)

# 总审: 未知顶层键归并
tp = os.path.join(L, "总审_%s.json" % D)
t = json.load(io.open(tp, encoding="utf-8"))
unknown = [k for k in ("A档编造检查", "后视镜检查", "检查") if k in t]
if unknown:
    chk = t.get("检查四项")
    if isinstance(chk, dict):
        for k in unknown:
            chk[k] = t.pop(k)
    elif chk is None:
        t["检查四项"] = {k: t.pop(k) for k in unknown}
    else:
        t["检查四项"] = {"原检查四项": chk, **{k: t.pop(k) for k in unknown}}
if "趋同盲区" in t:
    sd = t.get("综合深挖")
    if isinstance(sd, dict):
        sd["趋同盲区"] = t.pop("趋同盲区")
    elif sd is None:
        t["综合深挖"] = {"趋同盲区": t.pop("趋同盲区")}
    else:
        t["综合深挖"] = {"原综合深挖": sd, "趋同盲区": t.pop("趋同盲区")}
json.dump(t, open(tp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("总审 keys now:", list(t.keys()))
