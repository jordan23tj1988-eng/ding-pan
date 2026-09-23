# -*- coding: utf-8 -*-
"""E3 高危边回归(2026-09-23): 概览黄金骨架 .obs 卡必须仍被晨场脚本解析到。

高危边#E3 原事故: 首页观察点卡片 markup 漂移 -> 竞价快线.parse_watchlist / 竞价上首页.inject_obs
两处 parser 静默匹配 0 只(退出码 0 无报错)。概览页换了渲染器, 必须实测这两个 parser 仍能
在候选页上取到 5 只票、并幂等注入"今晨竞价"块。
"""
import importlib.util, re, sys
from pathlib import Path

MKT = Path("D:/股票数据/市场数据")
CAND = MKT / "_tmp" / "golden_full_site_20260922" / "index.html"
sys.path.insert(0, str(MKT))

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

home = load("jjsy", MKT / "竞价上首页.py")
html = CAND.read_text(encoding="utf-8")

segs = html.split('<div class="obs">')[1:]
print("obs 卡段数:", len(segs))

RX_NM = (r'class="obs-nm">(.*?)</(?:div|span)>\s*<span class="obs-pos')
codes = []
for i, seg in enumerate(segs, 1):
    nm = re.search(RX_NM, seg, re.S) or re.search(r'class="obs-nm">(.*?)</div>', seg, re.S) \
         or re.search(r'class="obs-nm">(.*?)</span></span>', seg, re.S)
    got = re.findall(r'(\d{6})', nm.group(1)) if nm else []
    codes.append(got)
    print("  卡%d 代码=%s" % (i, got))
print("解析到代码数:", sum(len(c) for c in codes), "(期望 == obs 卡段数)")

# 竞价上首页.inject_obs 幂等性 + 注入数
mingxi = [{"代码": c, "名称": "样本", "竞价涨幅": "+1.00%"} for c in ("000001", "600000")]
out1, ch1 = home.inject_obs(html, mingxi, "09-23 09:26")
out2, ch2 = home.inject_obs(out1, mingxi, "09-23 09:26")
print("inject_obs changed1=%s changed2=%s 幂等=%s" % (ch1, ch2, out1 == out2))
print("注入后 obs-jj 块数:", out1.count('<div class="obs-jj">'))

# 竞价快线.parse_watchlist 只读现站 judgment(不经页面), 确认不因本次改动受影响
fast = load("jjkx", MKT / "竞价快线.py")
try:
    wl = fast.parse_watchlist()
    print("parse_watchlist 只数:", len(wl), "前3:", [(x["代码"], x["名称"]) for x in wl[:3]])
except Exception as e:
    print("parse_watchlist 异常:", type(e).__name__, e)
