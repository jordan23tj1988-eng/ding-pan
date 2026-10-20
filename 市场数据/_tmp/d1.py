import json, io, os, glob
B = r"D:/股票数据/市场数据"
def L(p):
    for enc in ("utf-8-sig","utf-8","gbk","gb18030"):
        try:
            with io.open(p, encoding=enc) as f: return json.load(f)
        except UnicodeDecodeError: continue
        except Exception as e: print("ERR", p, enc, e); return None
    print("FAIL", p); return None

files = [
 "_学习/题材归位_20261020.json",
 "_学习/涨停对链条_20261020.json",
 "_学习/_题材四维.json",
 "_学习/主流题材6有_20261020.json",
 "_学习/_市场温度表.json",
 "_学习/风险日历_20261020.json",
 "_学习/风险事件_20261020.json",
 "_学习/子agent增强/战绩画像_theme_20261020.json",
 "_学习/_认知库_theme.json",
 "_学习/总审_20261019.json",
 "_学习/能力预加载_20261020.json",
 "_学习/_模拟盘/theme/状态.json",
 "_学习/题材荐票_20261019.json",
 "_学习/题材龙头判断_20261019.json",
 "_学习/题材生命周期判断_20261019.json",
]
for f in files:
    p = os.path.join(B, f)
    print("="*70)
    print("FILE:", f, "exists=", os.path.exists(p))
    if not os.path.exists(p):
        # glob variants
        d = os.path.dirname(p)
        print("  siblings:", [os.path.basename(x) for x in glob.glob(os.path.join(d, "*"))][:40])
        continue
    j = L(p)
    if j is None: continue
    s = json.dumps(j, ensure_ascii=False, indent=1)
    print("LEN", len(s))
    print(s[:6000])
