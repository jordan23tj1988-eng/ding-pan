# -*- coding: utf-8 -*-
"""limitup body 梯队表跨格拼接修复（零语义、视觉零影响）
根因: 梯队表 <tr><td>2 板</td>…<td>…000678 襄阳轴承</td></tr><tr><td>3 板</td>…
      剥标签后成「…襄阳轴承 3 板」，limitup数据核对.py:433 的 ([汉]{2,8})\s*(\d+)\s*板
      把「襄阳轴承 3 板」读成该票 3 板（池中真值 2 板）→ FAIL。
修法: 板数列加零宽空格前缀 \u200b。\u200b 不是 \s，正则的 \s* 到此断链，名字无法跨格抓数字；
      显示上零宽字符不可见，表格列数与文案一字不改。
"""
import os, re, shutil

os.chdir(r"D:\股票数据\市场数据")
p = "_学习/limitup_body_20261023.html"
raw = open(p, encoding="utf-8").read()
shutil.copy2(p, p + ".bak_ladder")

pat = re.compile(r"<td>(\d) 板</td>")
n = len(pat.findall(raw))
new = pat.sub(lambda m: "<td>\u200b%s 板</td>" % m.group(1), raw)
open(p, "w", encoding="utf-8", newline="\n").write(new)
print("加零宽断隔 %d 处" % n)

# 复验: 剥离标签后不应再出现「襄阳轴承 <任意空白> 3 板」这类跨格
plain = re.sub(r"<[^>]+>", " ", new)
bad = [m.group(0) for m in re.finditer(r"([\u4e00-\u9fa5]{2,8})\s*(\d+)\s*板", plain)
       if "襄阳" in m.group(1)]
print("复验 襄阳 跨格命中:", bad)
print("div", new.count("<div"), new.count("</div>"), "| td", new.count("<td>"), "| 裸null", new.count(">null<"))
