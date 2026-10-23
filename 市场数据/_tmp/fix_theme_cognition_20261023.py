# -*- coding: utf-8 -*-
"""theme判断_20261023.json 认知迭代条目对齐标准 schema（日期/标题/正文/可证伪条件/依据）
原文全保留：旧判据/今日事实/修正 三段拼进正文，不删字。
"""
import json, os, shutil

os.chdir(r"D:\股票数据\市场数据")
p = "_学习/theme判断_20261023.json"
o = json.load(open(p, encoding="utf-8"))
items = o["认知迭代"]
out = []
for i, it in enumerate(items):
    if "正文" in it and "标题" in it:
        out.append(it)
        continue
    title = f"{it.get('类型', '修正')}｜{str(it.get('旧判据', ''))[:48]}"
    body = (
        f"旧判据：{it.get('旧判据', '')}\n"
        f"今日事实：{it.get('今日事实', '')}\n"
        f"修正：{it.get('修正', '')}"
    )
    rec = {
        "日期": "2026-10-23",
        "标题": title,
        "正文": body,
        "可证伪条件": it.get("可证伪") or it.get("可证伪条件") or "",
        "依据": it.get("今日事实", ""),
    }
    out.append(rec)

shutil.copy2(p, p + ".bak_cogitem")
o["认知迭代"] = out
json.dump(o, open(p, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
print("theme 认知条目改标准:", len(out), "条")
for r in out:
    print(" -", r["标题"][:60], "| 正文", len(r["正文"]), "| 可证伪", len(r["可证伪条件"]))
