# -*- coding: utf-8 -*-
"""2026-11-04 遗留修复（用户拍板「按照你的建议修改」）：

1. index 重复「二 拐点预警」—— 根因是 body 里有 3 个 turning 段（一 明日核心观察点 / 三 明日验证 / 四 总裁决
   中的 turning），渲染器每个 turning body 段都会起一个机器段头（固定「二 拐点预警」）⇒ 页面出现两个同号段。
   修法：把「三 明日验证」整段降为 h3（标题去掉序号）并前移到「二 五路看牌」之前，成为「一 明日核心观察点」
   的姊妹内容（同为明日 oriented），turning 段数回到 1，页面回黄金版四段。正文一字不动，只动标题层级与位置。
2. 「五 深挖」→「五 自主深挖」：能力模块 `_sync_capability_blocks` 靠字面「自主深挖」摘旧模块，
   只写「深挖」会被算成业务段 ⇒ 段数超契约。纯标题措辞替换。
"""
import json
import re
import shutil
from pathlib import Path

L = Path(r"D:\股票数据\市场数据\_学习")
p = L / "judgment_20261103.json"
shutil.copy2(p, L / "judgment_20261103.json.bak_next_20261104")

with open(p, encoding="utf-8") as f:
    J = json.load(f)
B = J["bodies"]

# ---- 1. index：明日验证段降级前移 ----
h = B["index"]
s = h.find("三 明日验证")
assert s > 0, "index 未找到「三 明日验证」"
a = h.rfind("<h2", 0, s)
b = h.find("<h2", s)
block = h[a:b]
assert block.count("<h2") == 1, block.count("<h2")
h3 = re.sub(r"<h2>(三 )?明日验证", "<h3>明日验证", block, count=1).replace("</h2>", "</h3>", 1)
h_new = h[:a] + h[b:]                               # 先从原位摘除
anchor = h_new.find("<h2>二 五路看牌")
assert anchor > 0, "index 未找到「二 五路看牌」"
h_new = h_new[:anchor] + h3 + h_new[anchor:]        # 插到五路看牌之前
B["index"] = h_new
print("index: %d → %d 字符, h2=%d h3=%d" % (len(h), len(h_new), h_new.count("<h2"), h_new.count("<h3")))
for m in re.finditer(r"<h[23][^>]*>(.*?)</h[23]>", h_new, re.S):
    print("   ", m.group(0)[:3], re.sub("<[^>]+>", "", m.group(1)).strip()[:40])

# ---- 2. 全路「N 深挖」→「N 自主深挖」 ----
pat = re.compile(r"(<h2>[一二三四五六七八九] )深挖")
total = 0
for route, body in B.items():
    new, n = pat.subn(r"\1自主深挖", body)
    if n:
        B[route] = new
        total += n
        print("措辞: %-8s 深挖→自主深挖 %d 处" % (route, n))
print("措辞合计", total, "处")

with open(p, "w", encoding="utf-8") as f:
    json.dump(J, f, ensure_ascii=False)
print("已写回 judgment_20261103.json")
