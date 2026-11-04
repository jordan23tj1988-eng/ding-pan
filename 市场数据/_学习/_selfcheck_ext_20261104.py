# -*- coding: utf-8 -*-
import json, os, re, sys
BASE = r"D:/股票数据/市场数据/_学习"
lst = json.load(open(os.path.join(BASE, "自主拓展清单_20261104.json"), encoding="utf-8"))
ans = json.load(open(os.path.join(BASE, "自主拓展应答_20261104.json"), encoding="utf-8"))
ids = [it["id"] for it in lst["items"]]
top = set(ans) - {"应答日期"}
print("清单项数", len(ids), "应答项数", len(top))
missing = [i for i in ids if i not in top]
extra = sorted(top - set(ids))
print("缺项", missing)
print("多项", extra)
ok = True
if missing or extra:
    ok = False
allowed = {"立项", "并入", "不深挖"}
cnt = {"立项": 0, "并入": 0, "不深挖": 0}
topics = []
for i in ids:
    v = ans.get(i, {})
    dec = v.get("决定")
    rid = v.get("专题id", "")
    if dec not in allowed:
        print("✗ 非法决定", i, dec); ok = False; continue
    cnt[dec] += 1
    if dec == "立项":
        if not rid or not re.match(r"^topic-[a-z0-9\-]+-20261104$", rid):
            print("✗ 立项专题id不合规", i, rid); ok = False
        else:
            topics.append((i, rid))
    else:
        if rid not in ("", None):
            print("! 非立项项带专题id", i, rid)
    print(f"  {i:24s} {dec}  理由{len(v.get('理由',''))}字  专题id={rid or '（空）'}")
print("决定分布: 立项%d / 并入%d / 不深挖%d" % (cnt["立项"], cnt["并入"], cnt["不深挖"]))
assert set(ids) - {"应答日期"} == set(ids) & top, "键集不一致"
assert not missing and not extra, "键集不完整"
assert sum(cnt.values()) == len(ids), "项数不符"
print("立项专题:", topics)
print("应答日期键:", ans.get("应答日期"), "| 额外键:", sorted(set(ans) - set(ids) - {"应答日期"}))
print("校验结果:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
