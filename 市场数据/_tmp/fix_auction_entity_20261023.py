# -*- coding: utf-8 -*-
"""auction_body 实体归一化：HTML 实体 &lt;/&gt; → 全角 ＜/＞
根因（照 20261015 先例）：body 里写 &lt;5%，DOM 抽取后 claim 文本为 <5%，
canonical_text 不解码实体 → 'legacy claim absent from source'。
零语义改动：只换符号写法，不动数字与结论。
"""
import os, shutil

os.chdir(r"D:\股票数据\市场数据")
p = "_学习/auction_body_20261023.html"
raw = open(p, encoding="utf-8").read()
n1, n2 = raw.count("&lt;"), raw.count("&gt;")
shutil.copy2(p, p + ".bak_entity")
new = raw.replace("&lt;", "＜").replace("&gt;", "＞")
open(p, "w", encoding="utf-8", newline="\n").write(new)
print(f"{p}: &lt; {n1} 处 / &gt; {n2} 处 -> 全角；剩余实体 {new.count('&lt;')+new.count('&gt;')}")
print("div", new.count("<div"), new.count("</div>"))
