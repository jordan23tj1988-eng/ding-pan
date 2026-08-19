# -*- coding: utf-8 -*-
"""清理 8 个 jsonl 历史重复(保序去重, 保留第一条)。先备份到 _tmp/jsonl_bak_20260816/。"""
import os, json, shutil
L = r"D:\股票数据\市场数据\_学习"
BAK = r"D:\股票数据\市场数据\_tmp\jsonl_bak_20260816"
os.makedirs(BAK, exist_ok=True)

files = {
    "_荐票逐票结算.jsonl": ("荐票日", "代码"),
    "_涨停质量反思.jsonl": ("荐票日",),
    "_质量荐票结算.jsonl": ("荐票日",),
    "_题材荐票结算.jsonl": ("荐票日",),
    "_题材荐票反思.jsonl": ("荐票日",),
    "_逻辑荐票结算.jsonl": ("荐票日",),
    "_逻辑荐票反思.jsonl": ("荐票日",),
    "_席位荐票反思.jsonl": ("荐票日",),
}

total_removed = 0
for fn, keys in files.items():
    p = os.path.join(L, fn)
    if not os.path.isfile(p):
        print(f"{fn}: 不存在, 跳过")
        continue
    shutil.copy2(p, os.path.join(BAK, fn))  # 备份
    lines = []; seen = set(); removed = 0; bad = 0
    for line in open(p, encoding="utf-8"):
        raw = line.rstrip("\n").rstrip("\r")
        if not raw.strip():
            continue
        try:
            r = json.loads(raw)
        except Exception:
            lines.append(raw); bad += 1; continue  # 坏行保留
        k = tuple(r.get(x) for x in keys)
        if k in seen:
            removed += 1; continue
        seen.add(k); lines.append(raw)
    open(p, "w", encoding="utf-8", newline="").write("\n".join(lines) + ("\n" if lines else ""))
    total_removed += removed
    print(f"{fn}: 删重复{removed}行(坏行{bad}), 保留{len(lines)}行")

print(f"\n=== 共清理 {total_removed} 行历史重复 ===")
