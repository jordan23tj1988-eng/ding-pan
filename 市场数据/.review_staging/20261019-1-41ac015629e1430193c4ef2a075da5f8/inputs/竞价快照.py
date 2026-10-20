# -*- coding: utf-8 -*-
"""
竞价快照.py —— 早盘9:26跑,抓盯盘清单的集合竞价定强度(米氏第一式原料)
================================================================
盯盘清单 = 昨日 analysis.json 的核心标的 + 昨日连板≥2 + 主线题材票(自动构建)。
抓每票: 竞价价(=今开)、高开幅度、竞价成交额/量、是否一字。按竞价额+高开排"定强度榜"。
落地: 市场数据\YYYYMMDD\竞价快照.csv + 竞价强度榜(打印)。
⚠️ 需 9:25-9:30 之间跑;实时接口偶发不稳,带重试;全失败则退回盘后用"首封时间"近似(见复盘任务)。
用法: python 竞价快照.py
"""
import sys, os, json, glob, time, datetime
try:
    import akshare as ak
except ImportError:
    os.system(sys.executable + " -m pip install akshare --break-system-packages -q"); import akshare as ak
import pandas as pd

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE

def prev_dir(today):
    for dd in range(1, 8):
        d = (today - datetime.timedelta(days=dd)).strftime("%Y%m%d")
        if os.path.isfile(os.path.join(BASE, d, "zt_pool.csv")):
            return d
    return None

def build_watchlist(pd_dir):
    """从昨日数据构建盯盘清单(代码集合)。"""
    wl = {}
    zt = pd.read_csv(os.path.join(BASE, pd_dir, "zt_pool.csv"), dtype={"代码": str})
    zt["代码"] = zt["代码"].str.zfill(6)
    for _, r in zt[zt["连板数"] >= 1].iterrows():
        wl[r["代码"]] = r["名称"]  # 昨日全部涨停(含连板)进清单
    ana = os.path.join(BASE, pd_dir, "analysis.json")
    if os.path.isfile(ana):
        a = json.load(open(ana, encoding="utf-8"))
        for c in a.get("核心标的", []):
            wl[str(c["代码"]).zfill(6)] = c["名称"]
    return wl

def bid_of(code):
    """逐票竞价:返回(竞价价,高开幅度,竞价额)。带重试。"""
    for i in range(3):
        try:
            df = ak.stock_bid_ask_em(symbol=code)   # 实时5档+竞价
            m = dict(zip(df["item"], df["value"])) if "item" in df.columns else {}
            price = float(m.get("最新", m.get("今开", 0)) or 0)
            prevc = float(m.get("昨收", 0) or 0)
            amt = float(m.get("金额", 0) or 0)
            hi = round((price / prevc - 1) * 100, 2) if prevc else None
            return price, hi, amt
        except Exception:
            time.sleep(1)
    return None, None, None

def main():
    today = datetime.date.today()
    d = today.strftime("%Y%m%d")
    pdir = prev_dir(today)
    if not pdir:
        print("无昨日数据,无法建清单"); return
    wl = build_watchlist(pdir)
    print(f"盯盘清单 {len(wl)} 只(来自 {pdir})")
    rows = []
    for code, name in wl.items():
        price, hi, amt = bid_of(code)
        if price:
            rows.append(dict(代码=code, 名称=name, 竞价价=price, 高开幅度=hi, 竞价成交额=amt))
    if not rows:
        print("竞价接口全失败(网络);今日竞价用盘后'首封时间≤092500'近似替代"); return
    df = pd.DataFrame(rows).sort_values("竞价成交额", ascending=False)
    outdir = os.path.join(BASE, d); os.makedirs(outdir, exist_ok=True)
    df.to_csv(os.path.join(outdir, "竞价快照.csv"), index=False, encoding="utf-8-sig")
    print("\n=== 竞价定强度榜(按竞价额) Top15 ===")
    print(df.head(15).to_string(index=False))
    strong = df[(df["高开幅度"] >= 3)].head(10)
    print("\n=== 高开≥3%(竞价示强) ===")
    print(strong[["代码", "名称", "高开幅度", "竞价成交额"]].to_string(index=False))
    print(f"\n完成 → {os.path.join(outdir,'竞价快照.csv')}")

if __name__ == "__main__":
    main()
