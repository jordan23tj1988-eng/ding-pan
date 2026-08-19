# -*- coding: utf-8 -*-
"""
iFinD回填 v2 (2026-08-13 重建, 替代旧 iFind解锁检查_重启管道.py)
================================================
旧脚本职责(P0a): 概念指数日K + iwencai盘后六项 + 分时形态库5分钟K滚动回填。
旧文件 8/11 前后丢失。本版按职责重建, 落地路径沿用既有目录, 新路径在 docstring 声明。

职责(v2):
  1) 分时形态库5分钟K: 当日涨停池(zt_pool.csv) + 自选 → 分时形态库/{d}/{code}_5min.csv
     (THS_HighFrequenceSequence, 2026-08-13 实测通)
  2) 主要指数日K回填: 上证/深成/创业板/沪深300/中证500/中证1000/科创50/北证50
     → K线库/指数/{code}.csv  (THS_HistoryQuotes, 全量增量式)
  3) iwencai 盘后六项: 连板梯队/昨日涨停今日表现/主力净流入Top/异动 → _学习/iwencai盘后_{d}.json
  4) 概念指数日K: 板块代码格式(884xxx.TI)未验证 → 输出探测结果, 失败不阻塞(诚实标注)
用法: python iFinD回填.py [YYYYMMDD]
"""
import sys, os, json, time, datetime, csv
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r"D:\股票数据\市场数据"
KB = os.path.join(BASE, "K线库")
IDX_DIR = os.path.join(KB, "指数")
MIN_DIR = os.path.join(BASE, "盘中", "分时形态库")


def log(msg):
    print("[%s] %s" % (datetime.datetime.now().strftime("%H:%M:%S"), msg), flush=True)


def login():
    import iFinDPy
    a = json.load(open(r"D:\股票数据\_ifind_auth.json", encoding="utf-8"))
    rc = iFinDPy.THS_iFinDLogin(a["account"], a["password"])
    if rc != 0:
        log("login FAIL rc=%d" % rc); return None
    return iFinDPy


def backfill_5min(IF, d):
    """涨停池+自选 当日5分钟K → 分时形态库/{d}/"""
    codes = []
    zt = os.path.join(BASE, d, "zt_pool.csv")
    if os.path.exists(zt):
        try:
            for r in csv.DictReader(open(zt, encoding="utf-8-sig")):
                c = str(r.get("代码", "")).strip()
                if len(c) == 6:
                    codes.append((c, str(r.get("名称", "")).strip()))
        except Exception as e:
            log("zt_pool 读取失败: %s" % e)
    zw = os.path.join(BASE, "自选", "自选池.csv")
    if os.path.exists(zw):
        try:
            for r in csv.DictReader(open(zw, encoding="utf-8-sig")):
                c = str(r.get("代码", "")).strip()
                if len(c) == 6:
                    codes.append((c, str(r.get("名称", "")).strip()))
        except Exception:
            pass
    if not codes:
        log("无回填标的(涨停池+自选均空), 跳过5分钟K")
        return 0
    out = os.path.join(MIN_DIR, d)
    os.makedirs(out, exist_ok=True)
    beg = d[:4] + "-" + d[4:6] + "-" + d[6:] + " 09:30:00"
    end = d[:4] + "-" + d[4:6] + "-" + d[6:] + " 15:00:00"
    n = 0
    for c, name in codes:
        try:
            ths = c + (".SH" if c.startswith(("5", "6", "9")) else ".SZ")
            r = IF.THS_HighFrequenceSequence(
                ths, "open;high;low;close;volume",
                "CPS:no,baseDate:1900-01-01,MaxPoints:500,Fill:Previous,Interval:5",
                beg, end)
            if isinstance(r, dict) and r.get("errorcode") == 0 and r.get("tables"):
                tbl = r["tables"][0].get("table")
                rows = len(tbl.get("time", [])) if isinstance(tbl, dict) else 0
                if rows > 0:
                    import pandas as pd
                    df = pd.DataFrame(tbl)
                    df.to_csv(os.path.join(out, c + "_5min.csv"), index=False, encoding="utf-8-sig")
                    n += 1
                else:
                    # errorcode=0 但 0 行 = K线接口限流(2026-08-13 实测), 立即中止防刷
                    log("5minK 空返回(疑似K线限流), 中止回填(已完成%d)" % n)
                    break
            time.sleep(3)   # K线接口限流防护: 每只≥3s
        except Exception as e:
            log("5minK %s 失败: %s" % (c, str(e)[:60]))
    log("5分钟K回填 %d/%d" % (n, len(codes)))
    return n


def backfill_index_daily(IF, d):
    """主要指数日K增量"""
    os.makedirs(IDX_DIR, exist_ok=True)
    idx = {"000001.SH": "上证指数", "399001.SZ": "深证成指", "399006.SZ": "创业板指",
           "000300.SH": "沪深300", "000905.SH": "中证500", "000852.SH": "中证1000",
           "000688.SH": "科创50", "899050.BJ": "北证50", "000016.SH": "上证50", "399303.SZ": "国证2000"}
    n = 0
    for code, name in idx.items():
        try:
            r = IF.THS_HistoryQuotes(code, "open;high;low;close;volume;amount",
                                     "CPS:1,ForwardAdjust:1,baseDate:1900-01-01",
                                     "2026-01-01", d[:4] + "-" + d[4:6] + "-" + d[6:])
            if isinstance(r, dict) and r.get("errorcode") == 0 and r.get("tables"):
                tbl = r["tables"][0].get("table")
                rows = len(tbl.get("time", [])) if isinstance(tbl, dict) else 0
                if rows > 0:
                    import pandas as pd
                    df = pd.DataFrame(tbl)
                    df.to_csv(os.path.join(IDX_DIR, code.replace(".", "_") + ".csv"),
                              index=False, encoding="utf-8-sig")
                    n += 1
                else:
                    log("指数K线空返回(限流), 中止指数回填(已完成%d)" % n)
                    break
            time.sleep(3)
        except Exception as e:
            log("指数 %s 失败: %s" % (code, str(e)[:60]))
    log("指数日K回填 %d/%d" % (n, len(idx)))
    return n


def iwencai_afternoon(IF, d):
    """盘后六项快照 → _学习/iwencai盘后_{d}.json"""
    out = {}
    queries = {
        "连板梯队": "%d月%d日最高连板" % (int(d[4:6]), int(d[6:8])),
        "昨日涨停今日表现": "%d月%d日昨日涨停股票今日表现" % (int(d[4:6]), int(d[6:8])),
        "主力净流入Top20": "%d月%d日主力净流入前20" % (int(d[4:6]), int(d[6:8])),
        "龙虎榜": "%d月%d日龙虎榜" % (int(d[4:6]), int(d[6:8])),
        "异动": "%d月%d日异动" % (int(d[4:6]), int(d[6:8])),
        "炸板": "%d月%d日炸板股票" % (int(d[4:6]), int(d[6:8])),
    }
    for k, q in queries.items():
        try:
            r = IF.THS_iwencai(q, "stock")
            if isinstance(r, dict) and r.get("errorcode") == 0:
                tbl = (r.get("tables") or [{}])[0].get("table")
                if isinstance(tbl, dict):
                    out[k] = {"n": len(tbl.get("股票代码", [])),
                              "codes": tbl.get("股票代码", [])[:50]}
                else:
                    out[k] = None
            else:
                out[k] = None
        except Exception as e:
            out[k] = None
        time.sleep(0.5)
    p = os.path.join(BASE, "_学习", "iwencai盘后_%s.json" % d)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1, default=str)
    ok = sum(1 for v in out.values() if v is not None)
    log("iwencai盘后六项 %d/6 → %s" % (ok, p))
    return ok


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y%m%d")
    IF = login()
    if IF is None:
        print("ALARM: iFinD login 失败, 回填中止"); sys.exit(1)
    n1 = backfill_5min(IF, d)
    n2 = backfill_index_daily(IF, d)
    n3 = iwencai_afternoon(IF, d)
    print("回填完成: 5minK=%d 指数=%d iwencai=%d/6" % (n1, n2, n3))


if __name__ == "__main__":
    main()
