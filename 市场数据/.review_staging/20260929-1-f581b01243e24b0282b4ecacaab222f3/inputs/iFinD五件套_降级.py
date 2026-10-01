# -*- coding: utf-8 -*-
"""
iFinD五件套_降级.py — akshare(东财) 风控/断供时的 iFinD iwencai 降级收集器
================================================
(2026-08-13 新建, 任务5: 主源切换的降级臂)
触发: 市场数据下载.py 探测 akshare 涨停池 8 天全失败时调用本脚本; 也可手动:
  用法: python iFinD五件套_降级.py [YYYYMMDD]

输出: 市场数据/{d}/zt_pool.csv(简化schema) + summary.json + downgrade_flag.json
schema 差异(与 akshare 口径对照):
  - zt_pool.csv 列: 代码,名称,涨跌幅,最新价,连板数,所属行业(缺列填null)
  - iwencai 涨停池含 ST(akshare 也含,统计层剔除逻辑一致)
  - strong_pool/dt_pool/zb_pool: iwencai 口径不稳定 → v1 不产, 在 summary 标注 null
  - downgrade_flag.json: {"降级": true, "源": "ifind_iwencai", ...} 供下游识别
注意: 本脚本只用 iFinD(IPC) + sina 指数(http), 不碰东财域名。
"""
import sys, os, json, time, datetime, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r"D:\股票数据\市场数据"


def log(msg):
    print("[%s] %s" % (datetime.datetime.now().strftime("%H:%M:%S"), msg), flush=True)


def login():
    import iFinDPy
    a = json.load(open(r"D:\股票数据\_ifind_auth.json", encoding="utf-8"))
    rc = iFinDPy.THS_iFinDLogin(a["account"], a["password"])
    log("iFinD login rc=%d" % rc)
    return iFinDPy if rc == 0 else None


def iwencai_zt(IF, date_str):
    """涨停池: 返回 (rows, 涨停列名)"""
    d = datetime.datetime.strptime(date_str, "%Y%m%d")
    q = "%d月%d日涨停股票" % (d.month, d.day)
    r = IF.THS_iwencai(q, "stock")
    if not isinstance(r, dict) or r.get("errorcode") != 0:
        log("iwencai 涨停池失败: %s" % (r.get("errorcode") if isinstance(r, dict) else r))
        return None
    tbl = (r.get("tables") or [{}])[0].get("table")
    if not isinstance(tbl, dict):
        return None
    codes = tbl.get("股票代码", []); names = tbl.get("股票简称", [])
    zt_col = None
    for k in tbl.keys():
        if "涨停" in str(k):
            zt_col = k
            break
    rows = []
    for i, c in enumerate(codes):
        row = {"代码": c, "名称": names[i] if i < len(names) else "",
               "涨停列": (tbl[zt_col][i] if zt_col and isinstance(tbl.get(zt_col), list) and i < len(tbl[zt_col]) else None)}
        rows.append(row)
    log("iwencai 涨停池 %d 只 (%s)" % (len(rows), zt_col))
    return rows


def iwencai_extra(IF, date_str, kw):
    """额外查询(连板/跌停等), 返回 {代码: {...}}"""
    d = datetime.datetime.strptime(date_str, "%Y%m%d")
    q = "%d月%d日%s" % (d.month, d.day, kw)
    try:
        r = IF.THS_iwencai(q, "stock")
        if not isinstance(r, dict) or r.get("errorcode") != 0:
            return None
        tbl = (r.get("tables") or [{}])[0].get("table")
        if not isinstance(tbl, dict):
            return None
        return tbl
    except Exception as e:
        log("iwencai[%s] 异常: %s" % (kw, e))
        return None


def sina_turnover():
    """两市成交额(亿): 新浪指数源, 独立于东财"""
    try:
        import requests
        sess = requests.Session(); sess.trust_env = False
        r = sess.get("http://hq.sinajs.cn/list=s_sh000001,s_sz399106",
                     headers={"Referer": "https://finance.sina.com.cn", "User-Agent": "Mozilla/5.0"},
                     timeout=10)
        r.encoding = "gbk"
        parts = [p.split(",") for p in r.text.strip().split(";") if "=" in p]
        total = 0.0
        for p in parts:
            # 字段: var hq_str...="名称,当前,涨跌,幅度,成交量(手),成交额(万)"
            if len(p) >= 6 and p[5].strip():
                try:
                    total += float(p[5].strip().strip('"')) / 1e4  # 万 → 亿
                except Exception:
                    pass
        return round(total, 0) if total > 0 else None
    except Exception as e:
        log("sina 成交额失败: %s" % e)
        return None


def main():
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y%m%d")
    OUT = os.path.join(BASE, date_str)
    os.makedirs(OUT, exist_ok=True)
    IF = login()
    if IF is None:
        print("[FAIL] iFinD login 失败, 降级收集器不可用")
        sys.exit(1)

    # 1. 涨停池
    rows = iwencai_zt(IF, date_str)
    if not rows:
        print("[FAIL] iwencai 涨停池空")
        sys.exit(1)
    import csv
    zt_path = os.path.join(OUT, "zt_pool.csv")
    with open(zt_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["序号", "代码", "名称", "涨跌幅", "最新价", "成交额", "流通市值", "总市值",
                    "换手率", "封板资金", "首次封板时间", "最后封板时间", "炸板次数",
                    "涨停统计", "连板数", "所属行业"])
        for i, r_ in enumerate(rows, 1):
            w.writerow([i, r_["代码"], r_["名称"], None, None, None, None, None,
                        None, None, None, None, None, None, None, None])
    log("zt_pool.csv 已写(简化schema, %d只)" % len(rows))

    # 2. 连板数增强(尝试 iwencai "N连板")
    lb_map = {}
    for n in (2, 3, 4, 5, 6, 7):
        t = iwencai_extra(IF, date_str, "%d连板股票" % n)
        if t and t.get("股票代码"):
            for c in t["股票代码"]:
                lb_map[str(c)] = n
    if lb_map:
        # 回写连板数列
        import csv as _csv
        rows_out = list(_csv.DictReader(open(zt_path, encoding="utf-8-sig")))
        for r_ in rows_out:
            if r_["代码"] in lb_map:
                r_["连板数"] = lb_map[r_["代码"]]
        with open(zt_path, "w", encoding="utf-8-sig", newline="") as f:
            w = _csv.DictWriter(f, fieldnames=rows_out[0].keys())
            w.writeheader(); w.writerows(rows_out)
        log("连板数增强: %d 只" % len(lb_map))

    # 3. 跌停池尝试
    dt_rows = iwencai_extra(IF, date_str, "跌停股票")
    n_dt = len(dt_rows.get("股票代码", [])) if dt_rows else None

    # 4. summary(降级口径)
    summary = {
        "日期": date_str,
        "两市成交额_亿": sina_turnover(),
        "涨停家数": len(rows),
        "跌停家数": n_dt,
        "炸板家数": None,
        "炸板率": None,
        "最高连板": max(lb_map.values()) if lb_map else None,
        "连板梯队": None,
        "涨停行业扎堆Top12": None,
        "连板≥2行业Top8": None,
        "统计口径": "iFinD iwencai 降级版(akshare断供); 含ST未剔除",
        "剔除涨停家数": None,
        "龙虎榜条数": None,
        "抓取时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    with open(os.path.join(OUT, "downgrade_flag.json"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"降级": True, "源": "ifind_iwencai",
                            "时间": summary["抓取时间"],
                            "说明": "akshare/东财不可用时的 iFinD 问财降级产出; schema 为简化版"},
                           ensure_ascii=False, indent=2))
    print("[降级完成] %s 涨停%d 跌停%s 最高%s板 量能%s亿" % (
        date_str, len(rows), n_dt, summary["最高连板"], summary["两市成交额_亿"]))


if __name__ == "__main__":
    main()
