# -*- coding: utf-8 -*-
"""
概念排名.py —— 生成"概念板块当日涨幅排名"
==========================================
概念板块清单取自根目录 concept_rank.csv(名称,code), 遍历拉当日涨幅, 按涨幅排序输出。
数据源(直连, 绕过被墙的 push2 列表接口与代理):
  首选: push2his kline  https://91.push2his.eastmoney.com/api/qt/stock/kline/get
        secid 尝试 90.BK{code} 与 90.{code}
  回退: akshare stock_board_concept_hist_em(symbol='BK{code}')  (用户本地好网络时)
输出: YYYYMMDD/concept_rank.csv (名称, 代码, 涨幅)
说明: 涨停数列当前环境缺"股票→概念"映射, 暂留空(字段保留, 后续接入成分股接口补齐)。
用法: python 概念排名.py [YYYYMMDD]
"""
import sys, os, json, glob, csv, datetime, time
import requests as _requests

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据")
    BASE = g[0] if g else BASE

def _sess():
    s = _requests.Session()
    s.trust_env = False   # 不走代理, 直连 push2his
    return s

def pull_change_direct(sess, code, date_str):
    """直连 push2his 拉概念板块当日涨幅, 返回 float 或 None。"""
    for secid in (f"90.BK{code}", f"90.{code}"):
        p = {'secid': secid, 'fields1': 'f1,f2,f3', 'fields2': 'f51,f53',
             'klt': '101', 'fqt': '0', 'beg': date_str, 'end': date_str,
             'ut': 'fa5fd1943c7b386f172d6893dbfba10b', 'rt': '1'}
        for _ in range(2):
            try:
                r = sess.get("https://91.push2his.eastmoney.com/api/qt/stock/kline/get",
                             params=p, timeout=8)
                d = r.json()
                if d.get('data') and d['data'].get('klines'):
                    last = d['data']['klines'][-1].split(',')
                    return float(last[1]) if len(last) > 1 else None
                return None
            except Exception:
                time.sleep(1.2)
    return None

def pull_change_akshare(code, date_str):
    """akshare 回退(用户本地能直连 push2 时可用)。"""
    try:
        import akshare as ak
        df = ak.stock_board_concept_hist_em(symbol=f"BK{code}", period='daily',
                                            start_date=date_str, end_date=date_str, adjust='')
        if df is not None and len(df) > 0 and '涨跌幅' in df.columns:
            return float(df.iloc[-1]['涨跌幅'])
    except Exception:
        pass
    return None

def _probe_direct(date_str):
    """探测 push2his 是否可达, 返回 bool。避免对不可达主机海量重试被沙箱强杀。"""
    sess = _sess()
    try:
        r = sess.get("https://91.push2his.eastmoney.com/api/qt/stock/kline/get",
                     params={'secid': '90.BK308614', 'fields1': 'f1', 'fields2': 'f51,f53',
                             'klt': '101', 'fqt': '0', 'beg': date_str, 'end': date_str,
                             'ut': 'fa5fd1943c7b386f172d6893dbfba10b', 'rt': '1'}, timeout=8)
        d = r.json()
        return bool(d.get('data') and d['data'].get('klines'))
    except Exception:
        return False

def main():
    guess = datetime.date.today()
    if len(sys.argv) > 1:
        guess = datetime.datetime.strptime(sys.argv[1], "%Y%m%d").date()
    d = guess.strftime("%Y%m%d")
    date_str = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    D = os.path.join(BASE, d)
    os.makedirs(D, exist_ok=True)

    base_csv = os.path.join(BASE, "concept_rank.csv")
    if not os.path.isfile(base_csv):
        print("缺概念底表 concept_rank.csv(名称,code), 无法生成排名"); return
    concepts = []
    with open(base_csv, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            concepts.append((row.get("名称", row.get("name", "")).strip(),
                             str(row.get("代码", row.get("code", "")).strip())))

    # 先探测数据源, 不可达则仅落清单, 不批量重试(防沙箱强杀)
    mode = None
    if _probe_direct(date_str):
        mode = "direct"
    else:
        try:
            import akshare as ak
            df = ak.stock_board_concept_hist_em(symbol="BK308614", period='daily',
                                                start_date=date_str, end_date=date_str, adjust='')
            if df is not None and len(df) > 0:
                mode = "akshare"
        except Exception:
            pass

    out = []
    if mode is None:
        for name, code in concepts:
            out.append({"名称": name, "代码": code, "涨幅": None})
        print(f"概念排名 {d}: 数据源暂不可达(push2被墙/限流), 仅保留概念清单(涨幅为空); "
              f"网络恢复或本地好网络环境运行即可补齐涨幅。")
    else:
        sess = _sess()
        for name, code in concepts:
            chg = pull_change_direct(sess, code, date_str) if mode == "direct" else pull_change_akshare(code, date_str)
            out.append({"名称": name, "代码": code, "涨幅": round(chg, 2) if chg is not None else None})
        ok = sum(1 for x in out if x["涨幅"] is not None)
        print(f"概念排名 {d}: 成功 {ok}/{len(concepts)} ({mode}), -> {os.path.join(D, 'concept_rank.csv')}")

    out.sort(key=lambda x: x["涨幅"] if x["涨幅"] is not None else -999, reverse=True)
    with open(os.path.join(D, "concept_rank.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["名称", "代码", "涨幅"])
        w.writeheader()
        w.writerows(out)

if __name__ == "__main__":
    main()
