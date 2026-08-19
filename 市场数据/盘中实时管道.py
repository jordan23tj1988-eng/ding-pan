# -*- coding: utf-8 -*-
"""
盘中实时管道 v1.1 (2026-08-13 重建)
================================================
原版(竞价轨迹+预案+实时采集)于 8/11 前后丢失, 此版按报警档案+消费者 agent 需求重建。
由 intraday_pipeline_launcher.py (cron 09:14) spawn, 常驻到 15:05。

职责:
  1) 09:15-09:25 竞价段: 观察池逐票竞价轨迹 → 盘中/{d}/auction_traj.jsonl
  2) 09:30-15:00 连续段: 观察池实时 tick(每60s) → 盘中/{d}/realtime_ticks.jsonl
  3) 数据源优先级: iFinD THS_RealtimeQuotes 批量(主) → 腾讯 qt.gtimg.cn 批量(降级)
     东财 82.push2 clist 因风控动态封禁(2026-08-13 实测)不在链内。

观察池: 昨日涨停池(数据/每日/{prev}/zt_pool.csv 或 _学习/涨停复盘/{prev}/limitup.json)
        为空时用自选兜底(市场数据/自选/自选池.csv), 再空则只采上证指数+沪深300。
playbook.json: 本管道不产(属晚间复盘 agent 产物), 保持原边界。

用法: python 盘中实时管道.py [--selftest]
      --selftest: 采集一轮即退出(供 cron 体检/人工验证)
退出条件: 15:05 后自然退出; 连续 30 分钟全源失败则报警退出。
"""
import os, sys, json, time, datetime, subprocess
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE = r"D:\股票数据"
MDIR = os.path.join(BASE, "市场数据")
POOL_CANDIDATES = []          # 启动时填充
IFIND = None                  # iFinDPy 句柄(登录后)
SELFTEST = "--selftest" in sys.argv


def log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    line = "[%s] %s" % (ts, msg)
    print(line, flush=True)


def today():
    return datetime.date.today().strftime("%Y%m%d")


def prev_trading_day(d):
    """留档简化版: 周一前=周五; 其余前一自然日(节假日由调用方容错)"""
    dt = datetime.datetime.strptime(d, "%Y%m%d")
    back = dt - datetime.timedelta(days=3 if dt.weekday() == 0 else 1)
    return back.strftime("%Y%m%d")


def load_pool(d):
    """观察池: 昨日涨停池 → 自选 → 指数兜底, 返回 [(code, name), ...]"""
    prev = prev_trading_day(d)
    cand_files = [
        os.path.join(MDIR, prev, "zt_pool.csv"),
        os.path.join(MDIR, "数据", "每日", prev, "zt_pool.csv"),
        os.path.join(MDIR, "每日数据", prev, "zt_pool.csv"),
        os.path.join(BASE, "_学习", "涨停复盘", prev, "zt_pool.csv"),
    ]
    for f in cand_files:
        if os.path.exists(f):
            try:
                import csv
                rows = list(csv.DictReader(open(f, encoding="utf-8-sig", errors="replace")))
                codes = []
                for r in rows:
                    code = str(r.get("代码", r.get("股票代码", ""))).strip()
                    name = str(r.get("名称", r.get("股票简称", ""))).strip()
                    if code and len(code) == 6:
                        codes.append((code, name))
                if codes:
                    log("观察池=昨日涨停池 %s (%d只)" % (f, len(codes)))
                    return codes
            except Exception as e:
                log("池读取失败 %s: %s" % (f, e))
    # 自选兜底
    for f in [os.path.join(MDIR, "自选", "自选池.csv"), os.path.join(MDIR, "自选池.csv")]:
        if os.path.exists(f):
            try:
                import csv
                rows = list(csv.DictReader(open(f, encoding="utf-8-sig", errors="replace")))
                codes = [(str(r.get("代码", "")).strip(), str(r.get("名称", "")).strip())
                         for r in rows if str(r.get("代码", "")).strip()]
                if codes:
                    log("观察池=自选 (%d只)" % len(codes))
                    return codes
            except Exception as e:
                log("自选读取失败: %s" % e)
    log("观察池=指数兜底(上证+沪深300+创业板)")
    return [("000001.SH", "上证指数"), ("000300.SH", "沪深300"), ("399006.SZ", "创业板指")]


def ths_code(code):
    if code.endswith((".SH", ".SZ", ".BJ")):
        return code
    if code.startswith(("4", "8")):
        return code + ".BJ"
    if code.startswith(("5", "6", "9")):
        return code + ".SH"
    return code + ".SZ"


def ifind_login():
    global IFIND
    try:
        import iFinDPy
        auth = json.load(open(os.path.join(BASE, "_ifind_auth.json"), encoding="utf-8"))
        rc = iFinDPy.THS_iFinDLogin(auth["account"], auth["password"])
        IFIND = iFinDPy if rc == 0 else None
        log("iFinD login rc=%s" % rc)
        return rc == 0
    except Exception as e:
        log("iFinD login 异常: %s" % e)
        IFIND = None
        return False


def fetch_ifind(codes):
    """iFinD 批量实时: 返回 {thscode: {latest, pct, amount, volume, bid1, ask1}}"""
    if IFIND is None:
        return None
    try:
        code_str = ",".join(ths_code(c) for c, _ in codes)
        r = IFIND.THS_RealtimeQuotes(code_str,
            "latest;changeRatio;amount;volume;bid1;ask1;open;high;low;preClose")
        if not isinstance(r, dict) or r.get("errorcode") != 0:
            log("iFinD 实时 errorcode=%s" % (r.get("errorcode") if isinstance(r, dict) else "?"))
            return None
        out = {}
        for t in r.get("tables") or []:
            code = t.get("thscode")          # 外层标量
            nt = t.get("table")              # 嵌套 OrderedDict, 每字段=list
            if not code or not isinstance(nt, dict):
                continue
            row = {}
            for k in ("latest", "changeRatio", "amount", "volume",
                      "bid1", "ask1", "open", "high", "low", "preClose"):
                v = nt.get(k)
                if isinstance(v, list) and v:
                    row[k] = v[-1]
                else:
                    row[k] = None
            row["pct"] = row.get("changeRatio")   # 与腾讯 fetch 键名统一
            out[code] = row
        return out or None
    except Exception as e:
        log("iFinD 实时异常: %s" % e)
        return None


def fetch_tencent(codes):
    """腾讯批量: q=sh600519,sz000001,... 返回 {code6: {...}}"""
    try:
        q = ",".join(("sh" + c if ths_code(c).endswith("SH") else "sz" + c) for c, _ in codes)
        url = "http://qt.gtimg.cn/q=" + q
        r = subprocess.run(["curl", "--noproxy", "*", "-s", "-m", "10", url],
                           capture_output=True, text=True, timeout=30)
        if r.returncode != 0 or "v_pv_none_match" in r.stdout and len(codes) == 1:
            log("腾讯实时失败")
            return None
        out = {}
        for line in r.stdout.strip().split(";"):
            if "=" not in line:
                continue
            head, body = line.split("=", 1)
            code = head.split("_")[-1][2:]
            f = body.strip('"\n').split("~")
            if len(f) < 40:
                continue
            out[code] = {"latest": float(f[3]) if f[3] else None,
                         "pct": float(f[32]) if f[32] else None,
                         "amount": float(f[37]) if f[37] else None,
                         "volume": float(f[36]) if f[36] else None,
                         "bid1": float(f[9]) if f[9] else None,
                         "ask1": float(f[19]) if f[19] else None,
                         "open": float(f[5]) if f[5] else None,
                         "high": float(f[33]) if f[33] else None,
                         "low": float(f[34]) if f[34] else None,
                         "preClose": float(f[4]) if f[4] else None}
        return out or None
    except Exception as e:
        log("腾讯实时异常: %s" % e)
        return None


def fetch_batch(codes):
    """源优先级: iFinD → 腾讯"""
    d = fetch_ifind(codes)
    if d:
        return ("iFinD", d)
    d = fetch_tencent(codes)
    if d:
        return ("腾讯", d)
    return (None, None)


def write_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def run_auction_phase(codes, outdir, d):
    """09:15-09:25 竞价轨迹, 每20s一轮"""
    log("竞价段启动 %d只" % len(codes))
    while True:
        now = datetime.datetime.now()
        hm = now.strftime("%H:%M")
        if hm >= "09:26":
            break
        if hm < "09:15":
            time.sleep(10)
            continue
        src, data = fetch_batch(codes)
        if data:
            row = {"ts": now.strftime("%Y-%m-%d %H:%M:%S"), "phase": "auction",
                   "src": src, "n": len(data)}
            for c, name in codes:
                tc = ths_code(c)
                v = data.get(tc) or data.get(c)
                if v:
                    row.setdefault("rows", []).append(
                        {"code": c, "name": name, "latest": v["latest"], "pct": v["pct"],
                         "amount": v["amount"], "bid1": v["bid1"], "ask1": v["ask1"]})
            write_jsonl(os.path.join(outdir, "auction_traj.jsonl"), row)
            log("竞价tick %s 源=%s" % (hm, src))
        time.sleep(20)
    log("竞价段结束")


def run_continuous_phase(codes, outdir, d):
    log("连续段启动")
    fail_streak = 0
    while True:
        now = datetime.datetime.now()
        hm = now.strftime("%H:%M")
        if hm >= "15:05":
            log("收盘退出")
            break
        if hm < "09:31" and not SELFTEST:
            time.sleep(10)
            continue
        src, data = fetch_batch(codes)
        if data:
            fail_streak = 0
            row = {"ts": now.strftime("%Y-%m-%d %H:%M:%S"), "phase": "continuous",
                   "src": src, "n": len(data)}
            for c, name in codes:
                tc = ths_code(c)
                v = data.get(tc) or data.get(c)
                if v:
                    row.setdefault("rows", []).append(
                        {"code": c, "name": name, "latest": v["latest"], "pct": v["pct"],
                         "amount": v["amount"], "volume": v["volume"],
                         "open": v["open"], "high": v["high"], "low": v["low"],
                         "preClose": v["preClose"]})
            write_jsonl(os.path.join(outdir, "realtime_ticks.jsonl"), row)
            log("tick %s 源=%s" % (hm, src))
        else:
            fail_streak += 1
            log("取数失败 streak=%d" % fail_streak)
            if fail_streak >= 30 and not SELFTEST:
                log("连续30分钟全源失败, 报警退出")
                with open(os.path.join(outdir, "pipeline_alarm.jsonl"), "a", encoding="utf-8") as f:
                    f.write(json.dumps({"ts": now.strftime("%Y-%m-%d %H:%M:%S"),
                                        "level": "ALARM", "type": "all_source_dead",
                                        "detail": "盘中管道30分钟无数据源"}, ensure_ascii=False) + "\n")
                break
        if SELFTEST:
            log("selftest 完成")
            break
        time.sleep(60)


def main():
    d = today()
    outdir = os.path.join(MDIR, "盘中", d)
    os.makedirs(outdir, exist_ok=True)
    codes = load_pool(d)
    if not ifind_login():
        log("iFinD 不可用, 仅腾讯降级(竞价轨迹可用但无 Level1 盘口)")
    now = datetime.datetime.now()
    if now.strftime("%H:%M") <= "09:26" or SELFTEST:
        run_auction_phase(codes, outdir, d) if now.strftime("%H:%M") >= "09:15" else None
        if SELFTEST:
            # selftest: 直接采一轮连续段验证
            src, data = fetch_batch(codes)
            if data:
                row = {"ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                       "phase": "selftest", "src": src, "n": len(data)}
                write_jsonl(os.path.join(outdir, "realtime_ticks.jsonl"), row)
                log("selftest OK: %d只" % len(data))
            else:
                log("selftest FAIL: 双源均无数据")
                sys.exit(1)
            sys.exit(0)
    run_continuous_phase(codes, outdir, d)


if __name__ == "__main__":
    main()
