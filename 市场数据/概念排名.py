# -*- coding: utf-8 -*-
"""
概念排名.py —— 生成"概念板块当日涨幅排名"
==========================================
概念板块清单取自根目录 concept_rank.csv(名称,code), 遍历拉当日涨幅, 按涨幅排序输出。
数据源(直连, 绕过代理; v3 2026-07-17晚: 实测clist路径也被按路径封(直连/代理均000),新增 ulist.np 批量模式为首选——ulist是push2域唯一实测可达路径(200);v2 clist与push2his保留作回退,仅限当日):
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

def fetch_ifind_concepts(d):
    """★v5首选(2026-07-18,变更总账#011): iFind同花顺概念指数全清单(~389个,885xxx.TI)。
    路线: iwencai清单(指数代码/指数简称) -> 当日用THS_RQ实时(盘后=收盘),历史日用THS_HQ(d,d)。
    覆盖<50个视为失败返回None(走v4 THS涨停榜等回退)。涨幅口径=同花顺概念指数当日涨跌幅%。"""
    try:
        import ifind_source as ifs
        if not ifs.login(verbose=False):
            return None
        THS = ifs._mod()
        lst = ifs._to_df(THS.THS_iwencai("概念指数", "zhishu"))
        if lst is None or "指数代码" not in lst.columns:
            return None
        codes = [str(x) for x in lst["指数代码"].dropna() if str(x).endswith(".TI")]
        names = dict(zip(lst["指数代码"].astype(str), lst["指数简称"].astype(str)))
        if not codes:
            return None
        ds = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
        today = datetime.date.today().strftime("%Y%m%d")
        vals = {}
        for i in range(0, len(codes), 100):
            grp = ",".join(codes[i:i + 100])
            try:
                if d == today:
                    df = ifs._to_df(THS.THS_RQ(grp, "changeRatio"))
                else:
                    df = ifs._to_df(THS.THS_HQ(grp, "changeRatio", "", ds, ds))
            except Exception:
                df = None
            if df is not None and "changeRatio" in df.columns:
                for _, r in df.iterrows():
                    try:
                        vals[str(r["thscode"])] = round(float(r["changeRatio"]), 2)
                    except Exception:
                        pass
            time.sleep(0.3)
        if len(vals) < 50:
            return None
        return [{"名称": names.get(c, c), "代码": c.replace(".TI", ""), "涨幅": v}
                for c, v in vals.items()]
    except Exception:
        return None

def fetch_ths_blocktop(d):
    """★v4首选(2026-07-17,变更总账#009): 同花顺涨停板块榜 dataapi/limit_up/block_top。
    本机实测: EM push2 全路径直连/代理均不可达, 而 THS data.10jqka dataapi 免cookie可达(涨停池回填同源)。
    口径说明: 返回"当日有涨停的板块"热度榜(板块涨幅change/涨停数/连板数/板块高度), 非全概念清单;
    EM 各回退路保留, 用于全清单口径(网络恢复时)。返回 [dict] 或 None。"""
    import urllib.request
    H2 = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
          "Referer": "https://data.10jqka.com.cn/datacenterph/limitup/limtupInfo.html"}
    url = ("https://data.10jqka.com.cn/dataapi/limit_up/block_top"
           "?filter=HS,GEM2STAR&date=" + d)
    try:
        j = json.loads(urllib.request.urlopen(
            urllib.request.Request(url, headers=H2), timeout=15).read().decode())
        if j.get("status_code") != 0:
            return None
        rows = []
        for b in (j.get("data") or []):
            try:
                rows.append({"名称": b.get("name"), "代码": str(b.get("code", "")),
                             "涨幅": round(float(b["change"]), 2) if b.get("change") is not None else None,
                             "涨停数": b.get("limit_up_num"),
                             "连板数": b.get("continuous_plate_num"),
                             "高度": b.get("high"),
                             "蝉联天数": b.get("days")})
            except Exception:
                continue
        return rows or None
    except Exception:
        return None

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

def pull_all_ulist(concepts):
    """★v3首选: push2 ulist.np 按secids批量拉概念板块当日涨跌幅(f3)。
    2026-07-17实测: push2域仅 /api/qt/ulist.np 路径可达(200), clist与push2his均被按路径封(000)。
    50只/批, 全部概念约7批。仅当日收盘后有效。返回 {code: chg} 或 None。"""
    sess = _sess(); res = {}
    codes = [c for _, c in concepts if c]
    try:
        for i in range(0, len(codes), 50):
            batch = codes[i:i + 50]
            secids = ",".join("90.BK%s" % c for c in batch)
            for _ in range(2):
                try:
                    r = sess.get("https://push2.eastmoney.com/api/qt/ulist.np/get",
                                 params={'ut': 'bd1d9ddb04089700cf9c27f6f7426281', 'fltt': 2, 'invt': 2,
                                         'fields': 'f3,f12,f14', 'secids': secids}, timeout=8)
                    diff = (r.json().get('data') or {}).get('diff') or []
                    if isinstance(diff, dict):
                        diff = list(diff.values())
                    for it in diff:
                        c = str(it.get('f12', ''))
                        if c.startswith('BK'):
                            c = c[2:]
                        try:
                            res[c] = float(it['f3'])
                        except Exception:
                            pass
                    break
                except Exception:
                    time.sleep(1.2)
            time.sleep(1.5)   # ★批间节流:2026-07-17 连发7批触EM WAF临时封IP,冷却后恢复;宁慢勿封
        return res or None
    except Exception:
        return res or None

def pull_all_clist():
    """push2 clist 实时列表一把拉全概念板块当日涨幅(m:90+t:3);仅当日收盘后有效。返回 {code: chg} 或 None。
    (2026-07-17 新机实测: push2his 整域直连000不可达, 而 push2 直连200——clist成为宿主环境首选回退。)"""
    sess = _sess(); res = {}
    try:
        for pn in range(1, 20):
            r = sess.get("https://push2.eastmoney.com/api/qt/clist/get",
                         params={'pn': pn, 'pz': 100, 'po': 1, 'np': 1, 'fltt': 2, 'invt': 2,
                                 'fid': 'f3', 'fs': 'm:90+t:3', 'fields': 'f3,f12,f14',
                                 'ut': 'bd1d9ddb04089700cf9c27f6f7426281'}, timeout=8)
            d = r.json()
            diff = (d.get('data') or {}).get('diff') or []
            if isinstance(diff, dict):
                diff = list(diff.values())
            if not diff:
                break
            for it in diff:
                c = str(it.get('f12', ''))
                if c.startswith('BK'):
                    c = c[2:]
                try:
                    res[c] = float(it['f3'])
                except Exception:
                    pass
            if len(diff) < 100:
                break
        return res or None
    except Exception:
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
    mode = None; clist_map = None; ths_rows = None
    ifd_rows = fetch_ifind_concepts(d)   # ★v5首选: iFind概念指数全清单(2026-07-18 #011)
    ths_rows = fetch_ths_blocktop(d)     # v4首选降二: THS涨停板块榜(涨停数/高度等仍从这并入)
    if ifd_rows:
        mode = "ifind"
        if ths_rows:   # 按名称并入涨停数/连板数/高度/蝉联天数(THS榜~20个,其余留空)
            m = {r["名称"]: r for r in ths_rows if r.get("名称")}
            for r in ifd_rows:
                t = m.get(r["名称"])
                if t:
                    r.update({k: t.get(k) for k in ("涨停数", "连板数", "高度", "蝉联天数")})
    elif ths_rows:
        mode = "ths"
    if mode is None and d == datetime.date.today().strftime("%Y%m%d"):
        clist_map = pull_all_ulist(concepts)   # ★v3首选:ulist批量(唯一实测可达)
        if clist_map:
            mode = "clist"
    if mode is None and _probe_direct(date_str):
        mode = "direct"
    if mode is None and d == datetime.date.today().strftime("%Y%m%d"):
        clist_map = pull_all_clist()
        if clist_map:
            mode = "clist"
    if mode is None:
        try:
            import akshare as ak
            df = ak.stock_board_concept_hist_em(symbol="BK308614", period='daily',
                                                start_date=date_str, end_date=date_str, adjust='')
            if df is not None and len(df) > 0:
                mode = "akshare"
        except Exception:
            pass

    out = []
    if mode == "ifind":
        out = ifd_rows
        n_merge = sum(1 for x in out if x.get("涨停数") not in (None, ""))
        print(f"概念排名 {d}: iFind概念指数全清单 {len(out)} 个(并入THS涨停榜字段 {n_merge} 个), "
              f"-> {os.path.join(D, 'concept_rank.csv')}")
    elif mode == "ths":
        out = ths_rows
        print(f"概念排名 {d}: THS涨停板块榜 {len(out)} 个板块(含板块涨幅/涨停数/连板数/高度), "
              f"-> {os.path.join(D, 'concept_rank.csv')}")
    elif mode is None:
        for name, code in concepts:
            out.append({"名称": name, "代码": code, "涨幅": None})
        print(f"概念排名 {d}: 数据源暂不可达(push2被墙/限流), 仅保留概念清单(涨幅为空); "
              f"网络恢复或本地好网络环境运行即可补齐涨幅。")
    else:
        sess = _sess()
        for name, code in concepts:
            if mode == "direct":
                chg = pull_change_direct(sess, code, date_str)
            elif mode == "clist":
                chg = clist_map.get(code) if clist_map else None
            else:
                chg = pull_change_akshare(code, date_str)
            out.append({"名称": name, "代码": code, "涨幅": round(chg, 2) if chg is not None else None})
        ok = sum(1 for x in out if x["涨幅"] is not None)
        print(f"概念排名 {d}: 成功 {ok}/{len(concepts)} ({mode}), -> {os.path.join(D, 'concept_rank.csv')}")

    out.sort(key=lambda x: x["涨幅"] if x["涨幅"] is not None else -999, reverse=True)
    with open(os.path.join(D, "concept_rank.csv"), "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["名称", "代码", "涨幅", "涨停数", "连板数", "高度", "蝉联天数"], restval="")
        w.writeheader()
        w.writerows(out)

if __name__ == "__main__":
    main()
