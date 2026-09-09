# -*- coding: utf-8 -*-
"""竞价验证.py —— 早上(9:26后)核对'昨日候选'今天竞价/开盘兑现没
读最近一份 _学习/候选_{d}.json,逐票拉实时 高开幅度/现价/是否涨停,判兑现。
输出 _学习/竞价验证_{today}.json + 打印。用法: python 竞价验证.py"""
import os, sys, glob, json, time, datetime, socket
socket.setdefaulttimeout(5)
try:
    import akshare as ak
except ImportError:
    os.system(sys.executable + " -m pip install akshare --break-system-packages -q"); import akshare as ak

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE
LDIR = os.path.join(BASE, "_学习")

def bid(code):
    for _ in range(2):
        try:
            df = ak.stock_bid_ask_em(symbol=code)
            m = dict(zip(df["item"], df["value"]))
            price = float(m.get("最新", 0) or 0)
            openp = float(m.get("今开", 0) or 0)
            prevc = float(m.get("昨收", 0) or 0)
            up = float(m.get("涨停", 0) or 0)
            hi = round((openp / prevc - 1) * 100, 2) if prevc else None
            sealed = (up > 0 and price >= up - 0.01)
            return hi, price, sealed
        except Exception:
            time.sleep(1)
    return None, None, None

def main():
    snaps = sorted(glob.glob(os.path.join(LDIR, "候选_*.json")))
    if not snaps:
        print("无候选快照"); return
    snap = json.load(open(snaps[-1], encoding="utf-8"))
    cand_day = snap["日期"]
    today = datetime.date.today().strftime("%Y%m%d")
    print(f"验证 {cand_day} 的候选 在 {today} 竞价/开盘表现")
    seen = {}
    res = []
    t0 = time.time()
    for c in snap["候选"]:
        code = str(c.get("代码", "")).zfill(6)
        if not code or code in seen or time.time() - t0 > 30:
            continue
        seen[code] = 1
        hi, price, sealed = bid(code)
        res.append(dict(代码=code, 名称=c["名称"], 组合次日封板率=c["组合次日封板率"],
                        高开幅度=hi, 是否封板=sealed))
    hit = [r for r in res if r["是否封板"]]
    strong = [r for r in res if r["高开幅度"] and r["高开幅度"] >= 4]
    out = {"候选日": cand_day, "验证日": today, "候选数": len(res),
           "封板数": len(hit), "高开≥4%数": len(strong), "明细": res}
    json.dump(out, open(os.path.join(LDIR, "竞价验证_%s.json" % today), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"候选{len(res)}只: 封板{len(hit)} 高开≥4%{len(strong)}")
    for r in res:
        print("  %s(%s) 高开%s%% 封板%s [组合%d%%]" % (r["名称"], r["代码"], r["高开幅度"], "✓" if r["是否封板"] else "✗", r["组合次日封板率"]*100))
    print("已存 竞价验证_%s.json" % today)

if __name__ == "__main__":
    main()
