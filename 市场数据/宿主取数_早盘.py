# -*- coding: utf-8 -*-
"""宿主取数_早盘.py — 早盘竞价实时取数在Windows宿主预跑(2026-07-17起,新机沙箱无外网,变更总账#005)
用法: python 宿主取数_早盘.py [YYYYMMDD]  默认今天;周末自动退出。计划任务09:24触发。
步骤: 竞价快线(自等9:26)→全市场快照→模拟盘morning→昨日池初读→今晨闸门→9:31:40后存盘中涨停池
产物: 各脚本正常产物 + {d}/zt_pool_盘中0931.csv + _学习/宿主取数日志_早盘_{d}.json
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
log = {"d": d, "dprev": dprev, "start": str(datetime.datetime.now()), "steps": []}

def run(name, args):
    p = os.path.join(BASE, name); t0 = time.time()
    print("==>", name, " ".join(args), flush=True)
    try:
        rc = subprocess.run([sys.executable, p] + args, cwd=BASE, timeout=1200).returncode
    except Exception as e:
        rc = -99; print("  EXC", e)
    log["steps"].append({"script": name, "args": args, "rc": rc, "sec": round(time.time() - t0, 1)})

run("竞价快线.py", [])
run("竞价全市场快照.py", [])
run("模拟盘引擎.py", ["morning", d])
if dprev:
    run("竞价池初读.py", [dprev])
    run("竞价闸门.py", [dprev])
run("飞书推送.py", [])  # 模拟盘成交事件→飞书(增量扫账本,webhook未配则静默;#029)
# 9:31:40后存盘中涨停池(供沙箱建"竞价选股池·当日"表,首封≤09:31口径)
try:
    while datetime.datetime.now().time() < datetime.time(9, 31, 40):
        time.sleep(5)
    import akshare as ak
    df = ak.stock_zt_pool_em(date=d)
    os.makedirs(os.path.join(BASE, d), exist_ok=True)
    out = os.path.join(BASE, d, "zt_pool_盘中0931.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    log["steps"].append({"script": "zt_pool盘中0931", "rc": 0, "rows": len(df)})
    print("盘中涨停池 ->", out, len(df), "行")
except Exception as e:
    log["steps"].append({"script": "zt_pool盘中0931", "rc": -1, "err": str(e)[:200]})
log["end"] = str(datetime.datetime.now())
os.makedirs(os.path.join(BASE, "_学习"), exist_ok=True)
with open(os.path.join(BASE, "_学习", "宿主取数日志_早盘_%s.json" % d), "w", encoding="utf-8") as f:
    json.dump(log, f, ensure_ascii=False, indent=2)
bad = [s["script"] for s in log["steps"] if s.get("rc") != 0]
print("[√] 宿主早盘取数完成. 失败步骤: " + (",".join(bad) if bad else "无"))
