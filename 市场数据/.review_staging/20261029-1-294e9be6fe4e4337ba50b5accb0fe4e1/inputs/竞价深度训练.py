# -*- coding: utf-8 -*-
"""
竞价深度训练.py —— 解决"9:25前竞价指标 → T日涨停 + T+1溢价"深度训练(历史回测)
核心信号: 高开幅度 = 今开 / 昨收 - 1 (竞价的已实现结果, 历史日线可得, 不依赖逐笔)
标签:
  T日涨停  = 当日收盘涨跌幅 >= 9.5%
  T+1开盘溢价 = 次日今开 / 当日昨收 - 1
  T+1收盘溢价 = 次日收盘涨跌幅
分桶统计高开幅度 → 各桶 T日涨停率 + T+1开盘/收盘溢价均值.

数据源: akshare stock_zh_a_hist (需能联网的真机; 沙箱历史日线被墙).
增量缓存: _竞价深度_缓存.csv, 只补新交易日, 重复跑很便宜.
用法:
  python 竞价深度训练.py            # 全市场回测(首跑较慢, 约数十分钟)
  python 竞价深度训练.py --sample 200 --days 60   # 抽样测试
输出: _竞价深度训练.json
"""
import os, json, sys, time, argparse, csv

BASE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(BASE, "_竞价深度_缓存.csv")

# 高开分桶(下限, 上限, 标签)
BUCKETS = [
    (-9.9, -0.03, "大幅低开 <-3%"),
    (-0.03, 0.0, "微低开 -3~0%"),
    (0.0, 0.03, "平开 0~3%"),
    (0.03, 0.05, "高开 3~5%"),
    (0.05, 0.07, "高开 5~7%"),
    (0.07, 0.09, "高开 7~9%"),
    (0.09, 0.098, "接近涨停开 9~9.8%"),
    (0.098, 9.9, "一字/涨停开 ≥9.8%"),
]

def load_cache():
    if not os.path.isfile(CACHE):
        return {}, set()
    rows = list(csv.DictReader(open(CACHE, encoding="utf-8-sig")))
    d = {}
    for r in rows:
        d.setdefault(r["代码"], []).append(r)
    codes = set(d.keys())
    return d, codes

def save_cache(d):
    with open(CACHE, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["代码", "日期", "今开", "昨收", "收盘", "最高", "最低", "次日今开", "次日收盘", "次日最高"])
        for code, rs in d.items():
            for r in rs:
                w.writerow([code, r["日期"], r["今开"], r["昨收"], r["收盘"], r["最高"], r["最低"],
                            r.get("次日今开", ""), r.get("次日收盘", ""), r.get("次日最高", "")])

def fetch_codes(ak):
    try:
        df = ak.stock_info_a_code_name_em()
        return list(df["代码"].astype(str))
    except Exception:
        # 兜底: 用spot接口拿代码
        df = ak.stock_zh_a_spot_em()
        return list(df["代码"].astype(str))

def hist_of(ak, code, start, end):
    df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start, end_date=end, adjust="")
    if df is None or df.empty:
        return []
    need = ["日期", "开盘", "收盘", "最高", "最低"]
    df = df[need].copy()
    df["日期"] = df["日期"].astype(str)
    return df.to_dict("records")

def bucket_of(g):
    for lo, hi, lab in BUCKETS:
        if lo <= g < hi:
            return lab
    return BUCKETS[-1][2]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0, help="只取前N只(测试)")
    ap.add_argument("--days", type=int, default=60, help="回测交易日窗口")
    ap.add_argument("--start", type=str, default="", help="起始日 YYYYMMDD, 默认今天-days交易日")
    args = ap.parse_args()

    import datetime
    today = datetime.datetime.now()
    end = today.strftime("%Y%m%d")
    if not args.start:
        # 粗略往前推 days*1.5 天(含休市)
        sd = today - datetime.timedelta(days=int(args.days * 1.6) + 10)
        start = sd.strftime("%Y%m%d")
    else:
        start = args.start

    print("载入 akshare ...")
    import akshare as ak
    cache, cached_codes = load_cache()
    codes = fetch_codes(ak)
    if args.sample:
        codes = codes[:args.sample]
    print("待处理 %d 只, 缓存 %d 只" % (len(codes), len(cached_codes)))

    stats = {b[2]: {"n": 0, "zt": 0, "o1_sum": 0.0, "c1_sum": 0.0} for b in BUCKETS}
    total = 0
    for i, code in enumerate(codes):
        try:
            # 该代码缓存里最大日期
            cmax = max((r["日期"] for r in cache.get(code, [])), default="")
            fstart = (cmax[:8] if cmax else start)
            # 至少补一天
            recs = hist_of(ak, code, fstart, end)
            if not recs:
                continue
            # 计算 昨收(上一行收盘) 与 次日字段
            for j, r in enumerate(recs):
                if j == 0:
                    r["昨收"] = ""  # 无前收
                else:
                    r["昨收"] = recs[j-1]["收盘"]
                if j + 1 < len(recs):
                    nx = recs[j+1]
                    r["次日今开"] = nx["开盘"]
                    r["次日收盘"] = nx["收盘"]
                    r["次日最高"] = nx["最高"]
                else:
                    r["次日今开"] = r["次日收盘"] = r["次日最高"] = ""
            # 写回缓存(只用有昨收的行)
            cache.setdefault(code, [])
            # 去重日期
            have = {r["日期"] for r in cache[code]}
            for r in recs:
                if r["日期"] not in have and r.get("昨收") not in ("", None):
                    cache[code].append({
                        "代码": code, "日期": r["日期"], "今开": r["开盘"], "昨收": r["昨收"],
                        "收盘": r["收盘"], "最高": r["最高"], "最低": r["最低"],
                        "次日今开": r.get("次日今开", ""), "次日收盘": r.get("次日收盘", ""), "次日最高": r.get("次日最高", ""),
                    })
                    have.add(r["日期"])
            # 统计(仅用当日有 昨收 且 有次日 的行)
            for r in recs:
                if r.get("昨收") in ("", None):
                    continue
                昨收 = float(r["昨收"]); 今开 = float(r["开盘"]); 收盘 = float(r["收盘"])
                g = 今开 / 昨收 - 1
                zt = (收盘 / 昨收 - 1) >= 0.095  # T日涨停
                if not r.get("次日今开"):
                    continue  # 无次日, 跳过溢价统计但仍可计涨停? 涨停需要T日, 有; 但分桶需一致
                o1 = float(r["次日今开"]) / 昨收 - 1
                c1 = float(r["次日收盘"]) / 昨收 - 1
                lab = bucket_of(g)
                s = stats[lab]
                s["n"] += 1; total += 1
                if zt: s["zt"] += 1
                s["o1_sum"] += o1; s["c1_sum"] += c1
            if (i + 1) % 50 == 0:
                print("  %d/%d 已处理" % (i+1, len(codes)))
            time.sleep(0.02)
        except Exception as e:
            if (i + 1) % 50 == 0:
                print("  %d 处异常:%s" % (i+1, repr(e)[:60]))
            continue

    save_cache(cache)
    # 汇总
    out = {
        "窗口": "%s~%s" % (start, end),
        "样本数": total,
        "基准涨停率": round(stats_sum(stats, "zt") / total, 4) if total else 0,
        "基准T+1开盘溢价": round(stats_sum(stats, "o1_sum") / total, 4) if total else 0,
        "基准T+1收盘溢价": round(stats_sum(stats, "c1_sum") / total, 4) if total else 0,
        "分桶": [],
        "生成时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "说明": "高开幅度=今开/昨收-1; T日涨停=收盘涨跌幅≥9.5%; T+1溢价=次日开/收相对当日昨收。沙箱无历史日线故需真机跑。",
    }
    for b in BUCKETS:
        s = stats[b[2]]
        n = s["n"]
        out["分桶"].append({
            "桶": b[2], "样本": n,
            "T日涨停率": round(s["zt"]/n, 4) if n else 0,
            "T+1开盘溢价": round(s["o1_sum"]/n, 4) if n else 0,
            "T+1收盘溢价": round(s["c1_sum"]/n, 4) if n else 0,
        })
    json.dump(out, open(os.path.join(BASE, "_竞价深度训练.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("竞价深度训练完成: 样本%d, 分桶%d, 已存 _竞价深度训练.json" % (total, len(out["分桶"])))

def stats_sum(stats, key):
    return sum(s[key] for s in stats.values())

if __name__ == "__main__":
    main()
