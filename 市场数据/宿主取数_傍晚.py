# -*- coding: utf-8 -*-
"""宿主取数_傍晚.py — 傍晚取数tier在Windows宿主预跑(2026-07-17起,新机沙箱无外网,变更总账#005)
用法: python 宿主取数_傍晚.py [YYYYMMDD]  默认今天;周末自动退出。
产物: 各脚本正常产物 + _学习/宿主取数日志_{d}.json (沙箱18:00链路开工先核验此日志)
顺序铁律: 取数在前(市场数据下载/质量训练--fetch补bars) -> 昨日五路结算在后(依赖当日bars)。
"""
import os, sys, json, time, datetime, subprocess
# ★国内行情站绕开系统代理直连(2026-07-17实测:代理封push2系,直连200;requests/urllib继承no_proxy)
_np = ".eastmoney.com,.sinajs.cn,.sina.com.cn,.gtimg.cn,.10jqka.com.cn,.hexin.cn"
os.environ["NO_PROXY"] = os.environ["no_proxy"] = _np

BASE = r"D:\股票数据\市场数据"
# ★Windows宿主兼容:各脚本checkpoint写死"/tmp/..."(Linux沙箱习惯),在Windows上解析为 <当前盘>:\tmp —— 预建之(2026-07-17)
try:
    os.makedirs(os.path.splitdrive(BASE)[0] + os.sep + "tmp", exist_ok=True)
except Exception:
    pass
d = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y%m%d")
if datetime.datetime.strptime(d, "%Y%m%d").weekday() >= 5:
    print("周末,不跑"); sys.exit(0)

def prev_trade_day(d):
    ds = sorted(x for x in os.listdir(BASE) if x.isdigit() and len(x) == 8 and x < d)
    return ds[-1] if ds else None

dprev = prev_trade_day(d)
steps = [
    ("市场数据下载.py", [d], True),
    ("公告跟踪.py", [d], False),
    ("涨停原因.py", [d], False),
    ("市场温度.py", [], False),
    ("涨停质量训练.py", ["--prep", "--fetch"], False),
    ("席位动向库.py", ["fetch", d], False),
    ("概念排名.py", [], False),
    ("分析引擎.py", [], False),
    ("情绪先行指标.py", [d], False),
    ("中报预增雷达.py", [d], False),
]
if dprev:
    steps += [
        ("竞价池结算.py", [dprev], False),
        ("质量荐票结算.py", [dprev], False),
        ("席位荐票结算.py", [dprev], False),
        ("题材荐票结算.py", [dprev], False),
        ("逻辑荐票结算.py", [dprev], False),
    ]
steps += [("飞书推送.py", [], False)]  # 模拟盘成交事件→飞书(补推昨晚结算增量;#029)
log = {"d": d, "dprev": dprev, "start": str(datetime.datetime.now()), "steps": []}
crit_fail = False
for name, args, critical in steps:
    p = os.path.join(BASE, name)
    if not os.path.exists(p):
        log["steps"].append({"script": name, "rc": -404}); print("缺脚本", name); continue
    t0 = time.time(); print("==>", name, " ".join(args), flush=True)
    try:
        rc = subprocess.run([sys.executable, p] + args, cwd=BASE, timeout=(7200 if "雷达" in name else 2400)).returncode
    except Exception as e:
        rc = -99; print("  EXC", e)
    log["steps"].append({"script": name, "args": args, "rc": rc, "sec": round(time.time() - t0, 1)})
    if rc != 0 and critical: crit_fail = True
log["end"] = str(datetime.datetime.now())
os.makedirs(os.path.join(BASE, "_学习"), exist_ok=True)
with open(os.path.join(BASE, "_学习", "宿主取数日志_%s.json" % d), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=2)
bad = [s["script"] for s in log["steps"] if s.get("rc") != 0]
print(("[X] 关键步骤失败: " if crit_fail else "[√] 宿主傍晚取数完成. 失败步骤: ") + (",".join(bad) if bad else "无"))
sys.exit(1 if crit_fail else 0)
