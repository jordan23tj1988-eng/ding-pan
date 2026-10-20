# -*- coding: utf-8 -*-
import sys, io, json, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r"D:/股票数据/市场数据"; L = B + "/_学习"
zc = json.load(open(L + "/涨停对链条_20261020.json", encoding='utf-8'))
want = {"机器人", "低空经济", "医药", "PCB", "消费电子", "AI算力", "数字安全", "物理AI", "端侧AI", "重组", "传媒短剧"}
for t in zc["题材线"]:
    if t["大方向"] not in want: continue
    print(f"## {t['大方向']} 家数{t['家数']} 最高{t['最高连板']}板 最早{t['最早封板']} 开板占比{t['开板占比']}")
    for st in t["环节"]:
        print(f"   环节[{st['环节']}] 家数{st['家数']} 早封{st['早封占比']} 开板{st['开板占比']} {st['快判']}")
        for s in st["个股"]:
            print(f"      {s['代码']} {s['名称']} {s['连板']}板 首封{s['首封']} 开{s['开板次数']} 封单比{s['封单比']} 催化={s.get('催化')}")

# yesterday logic judgment: 600267 / 海正
try:
    y = json.load(open(L + "/logic判断_20261019.json", encoding='utf-8'))
    s = json.dumps(y, ensure_ascii=False)
    print("\n== 昨日logic判断含海正/600267: ", "海正" in s, s.count("600267"))
    for m in re.finditer("海正", s):
        print("   ...", s[max(0,m.start()-260):m.start()+200])
        break
    print("\n昨日 判断:", json.dumps(y.get("判断", {}), ensure_ascii=False)[:1200])
    print("\n昨日 荐票:", json.dumps(y.get("荐票", {}), ensure_ascii=False)[:1200])
except Exception as e:
    print("y FAIL", e)
