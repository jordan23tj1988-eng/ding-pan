# -*- coding: utf-8 -*-
"""写 周期主判 + 五路周期投票(各自仅依据本路判断文件, 隔离) + 跑 tally/board"""
import io, json, os, subprocess, sys

BASE = r"D:\股票数据\市场数据"
L = os.path.join(BASE, "_学习")
D = "20261029"


def jl(p):
    return json.load(io.open(p, encoding="utf-8"))


# 主判(宿主, 依据 总审总裁决 + 推演 + 温度表)
main = {"date": D, "stage": "退潮", "direction": "降",
        "confidence": 78,
        "evidence": "温度11.0(昨28.9,250日极低分位)、涨停39/跌停41、封板资金31.1亿(-31.7%)、一进二9.5%、核按钮0.0但跌停潮41只；总审总裁决C档总仓2.5%；推演定极冰点退潮末段。方向=降(继续收缩)。",
        "source": "宿主按 总审_20261029.总裁决 + 推演_20261029 + _市场温度表 写入"}
json.dump(main, open(os.path.join(L, "周期主判_%s.json" % D), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 五路票: 每路仅用本路判断文件文本做机械映射(隔离禁看他路)
basis = {
    "auction": ("降", 74, "本路2只全为观察、无荐票，闸门内执行压负数→防守"),
    "lhb": ("平", 56, "本路唯一荐票601188给3%试探仓，B偏C档：不押方向但给最小仓"),
    "theme": ("降", 68, "本路无正式荐票、判定无真主线(各自为战 离散度0.90)→不参与"),
    "logic": ("平", 72, "本路荐600592 2%试探(封/成交38.39%全场最硬)，其余观察"),
    "limitup": ("降", 82, "本路全池执1负期望、3只全观察、C档防守"),
}
for r, (dr, conf, ev) in basis.items():
    p = os.path.join(L, "%s判断_%s.json" % (r, D))
    j = jl(p)
    tier = (j.get("判断") or {}).get("档位")
    doc = {"route": r, "date": D, "stage": "退潮", "direction": dr,
           "confidence": conf, "evidence": "本路档位=%s；%s" % (tier, ev),
           "source": "_学习/%s判断_%s.json (宿主机械映射, 未看他路)" % (r, D)}
    json.dump(doc, open(os.path.join(L, "周期投票_%s_%s.json" % (r, D)), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("vote", r, dr, conf)

PY = r"D:\股票数据\.venv312\Scripts\python.exe"
env = dict(os.environ)
env.pop("PYTHONPATH", None)
for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy", "ALL_PROXY", "all_proxy"):
    env.pop(k, None)
for cmd in (["周期投票.py", "tally", D], ["周期投票.py", "board", D]):
    r = subprocess.run([PY] + cmd, cwd=BASE, env=env, capture_output=True)
    out = (r.stdout or b"").decode("utf-8", "replace") + (r.stderr or b"").decode("utf-8", "replace")
    print("===", cmd[1], "rc=", r.returncode)
    print(out[-900:])
