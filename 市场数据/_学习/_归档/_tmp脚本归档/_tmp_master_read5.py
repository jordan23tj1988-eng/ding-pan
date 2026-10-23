import json, io, os, re
B = r"D:\股票数据\市场数据\_学习"
def L(p):
    with io.open(p, encoding='utf-8-sig') as f:
        return json.load(f)

T = L(os.path.join(B, "_市场温度表.json"))
print("温度表 type", type(T).__name__)
if isinstance(T, dict):
    ks = list(T.keys())
    print("顶层键前20", ks[:20])
    # find date-keyed node
    dk = [k for k in ks if re.fullmatch(r"20\d{6}", str(k))]
    print("日期键数", len(dk), dk[-5:] if dk else "")
    if not dk:
        for k in ks:
            v = T[k]
            if isinstance(v, dict):
                sub = [x for x in v.keys() if re.fullmatch(r"20\d{6}", str(x))]
                if sub:
                    print("嵌套日期在键", k, "共", len(sub), sub[-3:])
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                print("列表键", k, "len", len(v), "keys", list(v[0].keys())[:15])
elif isinstance(T, list):
    print("len", len(T), "keys", list(T[0].keys())[:20])
    print("末条", json.dumps(T[-1], ensure_ascii=False)[:600])
