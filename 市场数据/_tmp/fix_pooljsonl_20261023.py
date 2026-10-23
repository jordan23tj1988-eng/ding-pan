# -*- coding: utf-8 -*-
"""修 _竞价池结算.jsonl 中 20261022 的占位坏行（次日封板 0/13 / 胜率 0/0 / 均收 null）
→ 用 竞价池结算_20261022.json#汇总 的真实 T+1 结算值替换（保留 .bak）。
原因：该行在 T+1 数据未到时提前落盘，C9 previous_pool_check 读到 null 直接 fail。
"""
import json, os, shutil

os.chdir(r"D:\股票数据\市场数据")
L = "_学习"
jp = os.path.join(L, "_竞价池结算.jsonl")
settle = json.load(open(os.path.join(L, "竞价池结算_20261022.json"), encoding="utf-8"))
s = settle["汇总"]
new_row = {
    "池日": "20261022",
    "池家数": s.get("池家数"),
    "次日封板": s.get("次日封板"),
    "执行胜率": s.get("执行胜率"),
    "执行均收": s.get("执行均收"),
    "全场涨停均收": s.get("全场涨停均收"),
    "增益pp": s.get("增益pp"),
}
print("新行:", json.dumps(new_row, ensure_ascii=False))

lines = [x for x in open(jp, encoding="utf-8").read().splitlines() if x.strip()]
shutil.copy2(jp, jp + ".bak_20261023")
out, done = [], False
for line in lines:
    row = json.loads(line)
    if row.get("池日") == "20261022":
        if not done:
            out.append(json.dumps(new_row, ensure_ascii=False))
            done = True
        else:
            print("丢弃重复池日行:", line[:120])
        continue
    out.append(line)
if not done:
    out.append(json.dumps(new_row, ensure_ascii=False))
open(jp, "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print("jsonl 行数", len(out), "| 20261022 已替换:", done)

tail = [json.loads(x) for x in out[-2:]]
print("尾两行:", json.dumps(tail, ensure_ascii=False))
