# -*- coding: utf-8 -*-
"""四结算脚本 append -> append_dedup 去重门禁补丁(整读整写)。"""
import os
BASE = r"D:\股票数据\市场数据"

def patch_file(fn, reps):
    p = os.path.join(BASE, fn)
    s = open(p, encoding="utf-8").read()
    orig = s
    for old, new, tag in reps:
        n = s.count(old)
        assert n == 1, f"{fn} [{tag}] 匹配数={n} (应=1)"
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8").write(s)
    print(f"OK {fn}: {len(orig)} -> {len(s)} chars")

IMP = '\nsys.path.insert(0, BASE)\nfrom _jsonl_append import append_dedup'
BASE_LINE = 'BASE=os.path.dirname(os.path.abspath(__file__)); L=os.path.join(BASE,"_学习")'

# ---------- 质量荐票结算.py ----------
patch_file("质量荐票结算.py", [
    (BASE_LINE, BASE_LINE + IMP, "import"),
    (r'''        open(os.path.join(L,"_荐票逐票结算.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(
            荐票日=dprev,代码=c,名称=t.get("名称"),质量分=t.get("质量分"),预测执1胜率=t.get("预测执1胜率"),
            预测执1均涨=t.get("预测执1均涨"),主导因子=t.get("主导因子") or t.get("匹配桶"),
            T1高开=ope,执行收益=exe,判定=verdict,次日封板=feng),ensure_ascii=False)+"\n")''',
     r'''        append_dedup(os.path.join(L,"_荐票逐票结算.jsonl"), dict(
            荐票日=dprev,代码=c,名称=t.get("名称"),质量分=t.get("质量分"),预测执1胜率=t.get("预测执1胜率"),
            预测执1均涨=t.get("预测执1均涨"),主导因子=t.get("主导因子") or t.get("匹配桶"),
            T1高开=ope,执行收益=exe,判定=verdict,次日封板=feng), ("荐票日","代码"))''', "逐票"),
    (r'''    open(os.path.join(L,"_涨停质量反思.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(
        荐票日=dprev,结算日=dnext,执行胜率=f"{win}/{n}",Top5均收=top_avg,全场均收=mkt_avg,选股增益pp=edge,
        套票因子=dict(lose),赚票因子=dict(winf),打脸明细=miss,反思=refl),ensure_ascii=False)+"\n")''',
     r'''    append_dedup(os.path.join(L,"_涨停质量反思.jsonl"), dict(
        荐票日=dprev,结算日=dnext,执行胜率=f"{win}/{n}",Top5均收=top_avg,全场均收=mkt_avg,选股增益pp=edge,
        套票因子=dict(lose),赚票因子=dict(winf),打脸明细=miss,反思=refl), "荐票日")''', "质量反思"),
    (r'''    open(os.path.join(L,"_质量荐票结算.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(荐票日=dprev,**out["汇总"]),ensure_ascii=False)+"\n")''',
     r'''    append_dedup(os.path.join(L,"_质量荐票结算.jsonl"), dict(荐票日=dprev,**out["汇总"]), "荐票日")''', "质量汇总"),
])

# ---------- 题材荐票结算.py ----------
patch_file("题材荐票结算.py", [
    (BASE_LINE, BASE_LINE + IMP, "import"),
    (r'''    open(os.path.join(L,"_题材荐票结算.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(荐票日=dprev,**out["汇总"]),ensure_ascii=False)+"\n")''',
     r'''    append_dedup(os.path.join(L,"_题材荐票结算.jsonl"), dict(荐票日=dprev,**out["汇总"]), "荐票日")''', "题材汇总"),
    (r'''    open(os.path.join(L,"_题材荐票反思.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(荐票日=dprev,结算日=dnext,反思=refl,明细=[dict(代码=r["代码"],名称=r["名称"],身位=r.get("身位"),执行收益=r["执行收益"],判定=r["判定"]) for r in res]),ensure_ascii=False)+"\n")''',
     r'''    append_dedup(os.path.join(L,"_题材荐票反思.jsonl"), dict(荐票日=dprev,结算日=dnext,反思=refl,明细=[dict(代码=r["代码"],名称=r["名称"],身位=r.get("身位"),执行收益=r["执行收益"],判定=r["判定"]) for r in res]), "荐票日")''', "题材反思"),
])

# ---------- 逻辑荐票结算.py ----------
patch_file("逻辑荐票结算.py", [
    ('sys.path.insert(0, BASE)\nfrom logic_pool import load_logic_picks',
     'sys.path.insert(0, BASE)\nfrom logic_pool import load_logic_picks\nfrom _jsonl_append import append_dedup', "import"),
    (r'''    open(os.path.join(L,"_逻辑荐票结算.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(荐票日=dprev,**out["汇总"]),ensure_ascii=False)+"\n")''',
     r'''    append_dedup(os.path.join(L,"_逻辑荐票结算.jsonl"), dict(荐票日=dprev,**out["汇总"]), "荐票日")''', "逻辑汇总"),
    (r'''    open(os.path.join(L,"_逻辑荐票反思.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(荐票日=dprev,结算日=dnext,反思=refl,明细=[dict(代码=r["代码"],名称=r["名称"],类型=r.get("类型"),执行收益=r["执行收益"],判定=r["判定"]) for r in res]),ensure_ascii=False)+"\n")''',
     r'''    append_dedup(os.path.join(L,"_逻辑荐票反思.jsonl"), dict(荐票日=dprev,结算日=dnext,反思=refl,明细=[dict(代码=r["代码"],名称=r["名称"],类型=r.get("类型"),执行收益=r["执行收益"],判定=r["判定"]) for r in res]), "荐票日")''', "逻辑反思"),
])

# ---------- 席位荐票结算.py ----------
patch_file("席位荐票结算.py", [
    (BASE_LINE, BASE_LINE + IMP, "import"),
    (r'''    open(os.path.join(L,"_席位荐票反思.jsonl"),"a",encoding="utf-8").write(json.dumps(dict(
        荐票日=dprev,执行胜率=f"{win}/{n}",均收=avg,立功=hero,打脸=flop,反思=refl),ensure_ascii=False)+"\n")''',
     r'''    append_dedup(os.path.join(L,"_席位荐票反思.jsonl"), dict(
        荐票日=dprev,执行胜率=f"{win}/{n}",均收=avg,立功=hero,打脸=flop,反思=refl), "荐票日")''', "席位反思"),
])

print("全部补丁完成")
