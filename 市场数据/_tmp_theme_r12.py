import json
B = r"D:/股票数据/市场数据/_学习/"
def L(p):
    for enc in ('utf-8','utf-8-sig','gbk','gb18030'):
        try: return json.load(open(p,encoding=enc))
        except Exception as e: last=e
    raise last
d=L(B+"涨停对链条_20261030.json")
for t in d["题材线"]:
    print(f"--- {t['大方向']} 家数{t['家数']} 高{t['最高连板']} 早封{t.get('早封占比')} 开板{t.get('开板占比')} 承载={t.get('承载环节')}")
    print("    画像:", t.get("强度画像"))
    for h in t.get("环节", []):
        names=",".join(f"{x['名称']}({x['连板']}板/封单比{x['封单比']}/开{x['开板次数']})" for x in h.get("个股",[]))
        print(f"      环节[{h['环节']}] 家{h['家数']} 早封{h.get('早封占比')} 快判={h.get('快判')} :: {names}")
