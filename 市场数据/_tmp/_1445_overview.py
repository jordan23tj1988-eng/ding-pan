# -*- coding: utf-8 -*-
"""14:45尾盘场·数据总览(只读汇总,不写任何文件)"""
import json, io, os, glob, datetime

BASE = r"D:\股票数据\市场数据"

def rd(p):
    return io.open(p, encoding="utf-8").read()

now = datetime.datetime.now()
print("NOW:", now.strftime("%Y-%m-%d %H:%M:%S"))

# ── 活跃 warboard: 最新含 warboard.json 的日期目录 ──
dirs = sorted(glob.glob(os.path.join(BASE, "盘中", "20*")))
wb_dir = None
for _d in reversed(dirs):
    if os.path.isfile(os.path.join(_d, "warboard.json")):
        wb_dir = _d
        break
print("\nWB_DIR:", wb_dir)
wb_path = os.path.join(wb_dir, "warboard.json")
st = os.stat(wb_path)
print("WB mtime:", datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"))

w = json.loads(rd(wb_path))
print("WB date:", w.get("date"))
print("WB last_ts:", w.get("last_ts"))
print("WB keys:", list(w.keys()))
print("pulse:", json.dumps(w.get("pulse", {}), ensure_ascii=False)[:500])
resp = w.get("responses") or []
print("\nresponses count:", len(resp))
for r in resp[-6:]:
    print("  seq=%s trig=%s ts=%s" % (r.get("seq"), r.get("trigger"), r.get("ts")))
    print("    note:", (r.get("note") or "").replace("\n", " | ")[:400])

print("\ncards count:", len(w.get("cards") or []))
for c in w.get("cards") or []:
    st_ = c.get("status")
    if st_ in ("已成交", "持有中", "已卖出", "卖出顺延"):
        print("  [持仓/成交] %s %s %s px=%s chg=%s sell=%s abort=%s fill=%s" % (
            c.get("code"), c.get("name"), st_, c.get("px"), c.get("chg_pct"),
            c.get("sell"), c.get("abort"), json.dumps(c.get("fill"), ensure_ascii=False)))

# ── 账本 ──
LED = os.path.join(BASE, "_学习", "_模拟盘", "盘中作战")
print("\nLEDGER DIR:", LED)
if os.path.exists(os.path.join(LED, "state.json")):
    s = json.loads(rd(os.path.join(LED, "state.json")))
    print("state:", json.dumps(s, ensure_ascii=False))
if os.path.exists(os.path.join(LED, "账本.jsonl")):
    lines = [json.loads(x) for x in rd(os.path.join(LED, "账本.jsonl")).splitlines() if x.strip()]
    print("账本 lines:", len(lines))
    for t in lines[-12:]:
        print("  ", json.dumps(t, ensure_ascii=False))

# ── 今日临盘决断 ──
td = now.strftime("%Y%m%d")
tdir = os.path.join(BASE, "盘中", td)
print("\n今日临盘决断目录:", tdir)
for f in sorted(glob.glob(os.path.join(tdir, "临盘决断_*.json"))):
    d = json.loads(rd(f))
    print(" ", os.path.basename(f), "→", json.dumps(d, ensure_ascii=False)[:300])

# ── 今日报警 ──
pa = os.path.join(tdir, "pipeline_alarm.jsonl")
if os.path.exists(pa):
    print("\npipeline_alarm:", rd(pa).strip())
al = os.path.join(BASE, "盘中", "报警_%s.jsonl" % td)
if os.path.exists(al):
    print("\n报警今日文件存在:", al)
    for x in rd(al).splitlines()[-5:]:
        print("  ", x[:200])

# ── 其他新鲜度线索: 分时形态库 / 盘中管道输出 ──
for p in [os.path.join(BASE, "盘中", "launcher.log")]:
    if os.path.exists(p):
        st2 = os.stat(p)
        print("\nlauncher.log mtime:", datetime.datetime.fromtimestamp(st2.st_mtime).strftime("%Y-%m-%d %H:%M:%S"))
