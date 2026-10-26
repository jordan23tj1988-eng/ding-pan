# -*- coding: utf-8 -*-
"""warboard 自动重建(晚间复盘后): 五路判断标的 -> 盘中/{d}/warboard.json -> 重渲 intraday.html
机制固化 2026-08-13(用户拍板方案3): 替代人工建票; 挂 cron 21:00 watchdog 兜底。
数据源: _学习/{路}判断_{d}.json(荐票.标的, 五路统一) + 总审_{d}.json + 推演_{d}.json
        + fact_{d}.json(脉搏) + {d}/zt_pool.csv(行业) + THS概念快照(收盘概念榜)
        + _学习/_模拟盘/盘中作战/state.json(账本现值)
铁律: 零编造——任何取不到的数据置 null/空, 不补造; 剔除名单只认总审结论文本中的"剔除+代码"。
用法: python warboard_build.py [YYYYMMDD]   (默认今天)
"""
import sys, os, io, json, csv, re, datetime, urllib.request

BASE = r"D:\股票数据\市场数据"
LX = os.path.join(BASE, "_学习")
LEDGER_DIR = os.path.join(LX, "_模拟盘", "盘中作战")

def rd(p):
    return io.open(os.path.join(BASE, p), encoding="utf-8").read()

def rj(p):
    return json.loads(rd(p))

def ths_get(path):
    """THS 网关(与盘中回应引擎同源)"""
    env = {}
    for ln in io.open(os.path.expandvars(r"%APPDATA%\hithink-finance\credentials.env"), encoding="utf-8"):
        ln = ln.strip()
        if "=" in ln and not ln.startswith("#"):
            k, v = ln.split("=", 1)
            env[k.strip()] = v.strip()
    key = env.get("HITHINK_FINANCE_API_KEY") or env.get("X_API_KEY") or env.get("THS_API_KEY") or ""
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    req = urllib.request.Request("https://fuyao.aicubes.cn" + path, headers={"X-api-key": key})
    for _ in range(3):
        try:
            d = json.loads(opener.open(req, timeout=15).read())
            if d.get("code") == 0 and d.get("data"):
                return d["data"]
        except Exception:
            pass
    return None

def concept_top():
    """收盘概念涨跌榜(THS概念快照实测); 失败返回 None(不编造)"""
    cch = os.path.join(BASE, "盘中", "ths_concepts_cache.json")
    raw = json.loads(rd(cch)) if os.path.isfile(cch) else []
    codes = [c.get("thscode") for c in raw if isinstance(c, dict) and c.get("thscode")]
    if not codes:
        return None
    # 名称映射: 目录接口(thscode→name), snapshot 只有 thscode+涨跌幅
    nmap = {}
    cat = ths_get("/api/a-share-index/catalog/ths-index-list?tag=cn_concept")
    for it in ((cat or {}).get("item") or []):
        if it.get("thscode") and it.get("name"):
            nmap[it["thscode"]] = it["name"]
    rows = []
    for i in range(0, len(codes), 30):
        chunk = codes[i:i + 30]
        data = ths_get("/api/a-share-index/prices/snapshot?thscodes=" + ",".join(chunk))
        if not data:
            continue
        items = data.get("item") or data.get("list") or (data if isinstance(data, list) else [])
        for it in items:
            nm = nmap.get(it.get("thscode")) or it.get("name") or it.get("ths_name")
            chg = it.get("price_change_ratio_pct")
            if chg is None:
                chg = it.get("chg_pct") or it.get("change_percent") or it.get("pct_change")
            if nm is None or chg is None:
                continue
            try:
                rows.append((nm, float(chg)))
            except (TypeError, ValueError):
                continue
    rows.sort(key=lambda x: -x[1])
    return [[n, round(c, 2)] for n, c in (rows[:4] + rows[-2:])] or None

def main():
    d = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().strftime("%Y%m%d")
    wb_path = os.path.join(BASE, "盘中", d, "warboard.json")
    if os.path.isfile(wb_path) and "--force" not in sys.argv:
        print("已存在,跳过:", wb_path, "(加 --force 重跑)")
        return 0

    # ── 0. 输入完整性防护(20260903 #118): 全部输入缺失=日期错位/晚间复盘未跑, 拒绝写空卡 ──
    _inputs = [os.path.join(LX, "%s判断_%s.json" % (_road, d))
               for _road in ("auction", "lhb", "theme", "logic", "limitup")]
    _inputs += [os.path.join(LX, _f) for _f in (
        "judgment_%s.json" % d, "总审_%s.json" % d, "席位荐票_%s.json" % d,
        "涨停质量荐票_%s.json" % d, "涨停对链条_%s.json" % d,
        "竞价评分_%s.json" % d, "题材归位_%s.json" % d)]
    if not any(os.path.isfile(_p) for _p in _inputs):
        print("[warboard_build] %s: 全部 %d 个输入文件均不存在(疑似日期错位或晚间复盘未跑), 拒绝写空卡, rc=2" % (d, len(_inputs)))
        return 2

    # ── 1. 五路标的合并去重 ──
    merged = {}
    for road in ("auction", "lhb", "theme", "logic", "limitup"):
        p = os.path.join(LX, "%s判断_%s.json" % (road, d))
        if not os.path.isfile(p):
            continue
        j = rj(p)
        rec = j.get("荐票") or {}
        for t in (rec.get("标的") or []):
            code = str(t.get("代码") or "").strip()
            if not code:
                continue
            m = merged.setdefault(code, {"code": code, "name": t.get("名称"), "type": t.get("类型", ""),
                                         "sources": [], "why": t.get("理由", ""),
                                         "hist": t.get("历史对照", "")})
            m["sources"].append(road)
            if (t.get("类型") or "") == "荐票":
                m["type"] = "荐票"
            if t.get("名称"):
                m["name"] = t.get("名称")
            if len(t.get("理由") or "") < len(m["why"] or ""):
                m["why"] = t.get("理由") or m["why"]

    # ── 1b. 总路观察点(judgment bodies.index obs卡: 名称+代码+位置标签) ──
    jp = os.path.join(LX, "judgment_%s.json" % d)
    if os.path.isfile(jp):
        try:
            ibody = rj(jp).get("bodies", {}).get("index", "") or ""
        except Exception:
            ibody = ""
        pairs = re.findall(r'obs-nm[^>]*>\s*([^<]+?)\s*<[^>]*class="mut"[^>]*>\s*([0-9]{6})', ibody)
        poss = re.findall(r'obs-pos[^>]*>([^<]+)', ibody)
        for i, (nm, code) in enumerate(pairs):
            code = code.strip()
            nm = re.sub(r"<[^>]+>", "", nm).strip()
            m = merged.setdefault(code, {"code": code, "name": nm, "type": "",
                                         "sources": [], "why": "", "hist": ""})
            m["sources"].append("index")
            if not m["name"] and nm:
                m["name"] = nm
            if not m["why"] and len(poss) == len(pairs):
                m["why"] = poss[i].strip()

    # ── 1c. 发出版荐票(席位/质量 top5, 与判断标的并行入列; 来源chip区分荐票) ──
    for _road, _fname, _chip in (("lhb_rec", "席位荐票_%s.json", "席位荐票"),
                                 ("qlt_rec", "涨停质量荐票_%s.json", "质量荐票")):
        _p = os.path.join(LX, _fname % d)
        if not os.path.isfile(_p):
            print("跳过(缺发出版):", _fname % d)
            continue
        for _t in (rj(_p).get("top5") or []):
            _code = str(_t.get("代码") or "").strip()
            if not _code:
                continue
            _m = merged.setdefault(_code, {"code": _code, "name": _t.get("名称"), "type": "",
                                           "sources": [], "why": "", "hist": ""})
            _m["sources"].append(_road)
            if _t.get("名称"):
                _m["name"] = _t.get("名称")
            if _road == "lhb_rec":
                _w = "综合分%s" % _t.get("综合分") if _t.get("综合分") is not None else ""
                _seats = _t.get("席位") or []
                if _seats and isinstance(_seats, list):
                    _s0 = _seats[0]
                    _w += "·%s%s档净买%s万" % ((_s0.get("名") or "")[:10], _s0.get("档") or "?",
                                              _s0.get("净额万") if _s0.get("净额万") is not None else "?")
            else:
                _parts = []
                if _t.get("质量分") is not None:
                    _parts.append("质量分%s" % _t["质量分"])
                if _t.get("连板") is not None:
                    _parts.append("%s板%s开" % (_t["连板"], _t.get("开板次数") or 0))
                if _t.get("大方向"):
                    _parts.append(str(_t["大方向"]))
                _w = "·".join(_parts)
            if not _m["why"]:
                _m["why"] = _w

    # ── 1d. 涨停复盘主线承载核心(涨停对链条 环节.快判=主线承载核心 → 个股全入) ──
    cpath = os.path.join(LX, "涨停对链条_%s.json" % d)
    if os.path.isfile(cpath):
        try:
            cj = rj(cpath)
            for _t in (cj.get("题材线") or []):
                _dir = _t.get("大方向") or ""
                for _s in (_t.get("环节") or []):
                    if not str(_s.get("快判") or "").startswith("主线承载核心"):
                        continue
                    for _g in (_s.get("个股") or []):
                        _code = str(_g.get("代码") or "").strip()
                        if not _code:
                            continue
                        _m = merged.setdefault(_code, {"code": _code, "name": _g.get("名称"), "type": "",
                                                       "sources": [], "why": "", "hist": ""})
                        _m["sources"].append("mainline")
                        if _g.get("名称"):
                            _m["name"] = _g.get("名称")
                        if not _m["why"]:
                            _m["why"] = "%s·%s·%s板" % (_dir, _s.get("环节"), _g.get("连板") or "?")
        except Exception as e:
            print("1d主线核心解析失败:", e)

    # ── 1e. 涨停路观察票(judgment bodies.limitup 文本'观察N只(简称/…)' → zt_pool名称映射代码) ──
    if os.path.isfile(jp):
        try:
            lbody = rj(jp).get("bodies", {}).get("limitup", "") or ""
        except Exception:
            lbody = ""
        mo = re.search(r"观察(\d)只\(([^)]+)\)", lbody)
        if mo:
            nmap = {}
            _ztp = os.path.join(BASE, d, "zt_pool.csv")
            if os.path.isfile(_ztp):
                for _r in list(csv.reader(io.open(_ztp, encoding="utf-8-sig")))[1:]:
                    if len(_r) > 2 and _r[1]:
                        nmap.setdefault(re.sub(r"\s+", "", _r[2]), _r[1])
            for _short in mo.group(2).split("/"):
                _short = re.sub(r"\s+", "", _short.strip())
                if not _short:
                    continue
                _hit = next(((_c, _n) for _n, _c in nmap.items() if _short in _n or _n in _short), None)
                if not _hit:
                    print("1e观察简称未映射:", _short)
                    continue
                _code, _nm = _hit
                _m = merged.setdefault(_code, {"code": _code, "name": _nm, "type": "",
                                               "sources": [], "why": "", "hist": ""})
                _m["sources"].append("qlt_obs")
                if not _m["name"]:
                    _m["name"] = _nm
                if not _m["why"]:
                    _m["why"] = "涨停路观察(非荐票,带历史对照)"

    # ── 1f. 集合竞价优势票(竞价评分并列最高档, 未入列补入, 来源"竞价优势") ──
    jjp = os.path.join(LX, "竞价评分_%s.json" % d)
    if os.path.isfile(jjp):
        try:
            jj = rj(jjp)
            detail = jj.get("明细") or []
            if detail:
                top_score = max((x.get("竞价分") or 0) for x in detail)
                for x in detail:
                    if (x.get("竞价分") or 0) >= top_score - 0.001:  # 并列最高档
                        _code = str(x.get("代码") or "").strip()
                        if _code and _code not in merged:
                            _m = merged.setdefault(_code, {"code": _code, "name": x.get("名称"), "type": "",
                                                           "sources": [], "why": "", "hist": ""})
                            _m["sources"].append("auc_adv")
                            if not _m["why"]:
                                _m["why"] = "集合竞价优势(评分%s池内最高档·%s%s板)" % (
                                    x.get("竞价分"), x.get("信号"), x.get("连板"))
        except Exception as e:
            print("1f竞价优势补入失败:", e)

    # ── 2. 剔除名单(总审结论文本正则: 名称+代码 ... 剔除) ──
    removed = set()
    zp = os.path.join(LX, "总审_%s.json" % d)
    if os.path.isfile(zp):
        zj = rj(zp).get("总裁决", {})
        concl = zj.get("结论", "") if isinstance(zj, dict) else str(zj)
        for m in re.finditer(r"([\u4e00-\u9fa5]{2,6})?\s*(\d{6})[^。;；]*?(剔除|禁入)", concl):
            removed.add(m.group(2))

    # ── 3. 行业(zt_pool) + 连板数 + 题材名(题材归位大方向, 用户20260816: 题材≠行业) ──
    zt_pool = os.path.join(BASE, d, "zt_pool.csv")
    ind = {}
    board_map = {}
    if os.path.isfile(zt_pool):
        for r in list(csv.reader(io.open(zt_pool, encoding="utf-8-sig")))[1:]:
            if len(r) > 2:
                ind[r[1]] = r[15] if len(r) > 15 else ""
                if len(r) > 14 and str(r[14]).strip().isdigit():
                    board_map[r[1]] = int(r[14])
    theme_map = {}
    gtp = os.path.join(LX, "题材归位_%s.json" % d)
    if os.path.isfile(gtp):
        try:
            gj = rj(gtp)
            for _c, _v in (gj.get("映射") or {}).items():
                if isinstance(_v, dict) and _v.get("大方向"):
                    theme_map[_c] = _v["大方向"]
        except Exception as e:
            print("题材归位读取失败:", e)

    cards = []
    for code, m in merged.items():
        if code in removed:
            print("剔除:", code, m["name"], "(总审结论)")
            continue
        src = [{"auction": "竞价", "lhb": "席位", "theme": "题材", "logic": "逻辑", "limitup": "质量",
                "index": "总", "lhb_rec": "席位荐票", "qlt_rec": "质量荐票",
                "mainline": "主线核心", "qlt_obs": "涨停观察", "auc_adv": "竞价优势"}[s] for s in m["sources"]]
        # 方案3(2026-08-13用户拍板): 荐票标的入盘 status=待触发(荐票身份由 sources chip 表达), 非荐票=观察
        is_rec = (m.get("type") or "") == "荐票"
        # 甜点买入条件(M28: 第3板一字开炸板<3%回封)。仅2板票: T+1冲第3板适用
        sweet = ("T+1第3板甜点:开盘一字→盘中炸板<3%回封成交(M28:26年471次/胜68%/单笔+4.18%);深炸>3%观望;换手板非甜点"
                 if board_map.get(code) == 2 else None)
        cards.append({
            "code": code, "name": m["name"], "status": ("待触发" if is_rec else "观察"), "sources": src,
            "theme": theme_map.get(code) or ind.get(code, ""),
            "board": board_map.get(code),
            "sweet": sweet,
            "why": (m["why"] or "")[:120],
            "trigger": "明晨9:25起多维判定(所有路经验)：竞价闸门(高开≥5%弃/低开≤0或0~5承接)+题材温度+个股强度+纪律，共振才成交",
            "abort": None, "sell": "断板即止", "px": None, "chg_pct": None, "auction": None,
            "timeline": [["%s-%s-%s晚" % (d[:4], d[4:6], d[6:]),
                          ("五路荐票入列(荐票·待触发)" if is_rec else "五路建票入列(观察)")]],
            "dim": None,
        })

    # ── 4. judgment(总裁决 hero 结构) ──
    zong = rj(zp).get("总裁决", {}) if os.path.isfile(zp) else {}
    zconcl = (zong.get("依据") or zong.get("结论") or "") if isinstance(zong, dict) else str(zong)
    zstage = (zong.get("档位") or "B防守") if isinstance(zong, dict) else "B防守"
    _band = str(zstage).strip().upper()[:1]
    pos = "≤2成" if (_band in ("C", "D") or "防守" in str(zstage) or "空仓" in zconcl[:80]) else "≥5成"
    jdate = "%s%s晚" % (d[4:6], d[6:])

    # ── 5. checks(推演可证伪前5) ──
    checks = []
    tp = os.path.join(LX, "推演_%s.json" % d)
    if os.path.isfile(tp):
        for x in (rj(tp).get("次日可证伪预测") or [])[:5]:
            c = x.get("判定条件") or {}
            now = x.get("now") or ""
            checks.append({"name": x.get("项", ""), "now": now or None,
                           "expect": "%s %s 锚%s" % (c.get("指标", ""), c.get("方向", ""), c.get(">=", c.get("代码", "?"))),
                           "ok": None, "cond": c})

    # ── 6. pulse(fact 快照: facts.{名称}.value) ──
    pulse = {"zt": None, "dt": None, "zb": None, "zb_rate": None, "top_lb": None, "concept_top": concept_top()}
    fp = os.path.join(LX, "fact_%s.json" % d)
    if os.path.isfile(fp):
        facts = rj(fp).get("facts") or {}
        keymap = {"zt": "涨停数", "dt": "跌停数", "zb": "炸板数", "zb_rate": "炸板率", "top_lb": "最高板"}
        for k, fk in keymap.items():
            fv = facts.get(fk)
            if isinstance(fv, dict):
                pulse[k] = fv.get("value")
            elif fv is not None:
                pulse[k] = fv
        # zb_rate 渲染口径=百分数(str拼接"%"): 比例值×100
        if isinstance(pulse["zb_rate"], (int, float)) and pulse["zb_rate"] <= 1:
            pulse["zb_rate"] = round(pulse["zb_rate"] * 100, 1)
    # 缺项兜底: 市场温度表(真实数据,不编造)
    tt = os.path.join(LX, "_市场温度表.json")
    if os.path.isfile(tt):
        t = rj(tt)
        row = t.get(d) or {}
        for k, fk in (("zt", "涨停数"), ("dt", "跌停数"), ("zb", "炸板数"),
                      ("zb_rate", "炸板率"), ("top_lb", "最高板")):
            if pulse[k] is None:
                pulse[k] = row.get(fk)

    # ── 7. account(账本现值) ──
    stj = os.path.join(LEDGER_DIR, "state.json")
    account = {"起算": "20260813", "nav": 1.0, "week_pct": 0.0, "pos_pct": 0.0,
               "cash_pct": 100.0, "n_pos": 0, "清仓": [], "口径": "盘中作战独立账本"}
    if os.path.isfile(stj):
        st = json.load(open(stj, encoding="utf-8"))
        cash = st.get("cash", 1000000)
        posv = sum((p.get("shares") or 0) * (p.get("px") or 0) for p in (st.get("positions") or []))
        nav = (cash + posv) / float(st.get("本金", 1000000))
        account.update({"起算": st.get("起算", "20260813"), "nav": round(nav, 4),
                        "cash_pct": round(cash / float(st.get("本金", 1000000)) * 100, 1),
                        "n_pos": len(st.get("positions") or [])})

    # ── 7b. Master 指派清单(盘中作战台"指派/待深挖"标记, 带时间戳守铁律②) ──
    assigns = []
    if os.path.isfile(zp):
        _zj = rj(zp)
        for a in (_zj.get("指派清单") or []):
            if not isinstance(a, dict):
                continue
            assigns.append({
                "id": a.get("指派ID", "—"), "to": a.get("指派给", "—"),
                "task": a.get("深挖任务", "—"), "status": a.get("状态", "待承接"),
                "ts": "%s-%s-%s晚" % (d[:4], d[4:6], d[6:]),  # 指派写入时点(复盘场)
            })

    # ── 7c. 连板票列表(用户20260816: 第二页固定放连板票观察, 标记几板, 只观察不荐) ──
    lb_cards = []
    def _fnum(x):
        try:
            return round(float(x), 2)
        except (TypeError, ValueError):
            return None
    if os.path.isfile(zt_pool):
        def _is_bj(c):
            return c[0] in ('4', '8', '9')
        for _r in list(csv.reader(io.open(zt_pool, encoding="utf-8-sig")))[1:]:
            if len(_r) <= 14:
                continue
            _code = str(_r[1]).strip()
            _board = str(_r[14]).strip()
            if not (_code and _board.isdigit() and int(_board) >= 2):
                continue
            if _is_bj(_code):
                continue
            lb_cards.append({"代码": _code, "名称": _r[2].strip(), "连板": int(_board),
                              "题材": theme_map.get(_code, ""), "行业": _r[15] if len(_r) > 15 else "",
                              "现价": _fnum(_r[4]) if len(_r) > 4 else None,
                              "涨跌幅": _fnum(_r[3]) if len(_r) > 3 else None,
                              "在总表": _code in merged})
        lb_cards.sort(key=lambda x: (-x["连板"], x["代码"]))

    war = {
        "date": d,
        "ts": "%s-%s-%s 晚间复盘重建" % (d[:4], d[4:6], d[6:]),
        "rebuild_from": "晚间复盘重建(五路标的+总路观察点+席位/质量荐票+主线承载核心+涨停观察建卡%d只)+明晨竞价判定+盘中回应引擎" % len(cards),
        "aucsum": None,
        "assigns": assigns,
        "judgment": {"date": jdate, "stage": zstage, "pos_band": pos,
                     "line": zconcl[:160] if zconcl else "五路判断已出,总审结论缺失(脚本不编造)",
                     "checks": checks,
                     "response": {"ts": None, "verdict": "验证中", "note": "等待明晨首个竞价场回应(09:25)"}},
        "account": account, "pulse": pulse, "pipeline": None, "cards": cards,
        "连板票": lb_cards,
        "response": None, "checks": checks, "concept_top": pulse["concept_top"],
        "responses": [], "last_ts": None,
    }
    os.makedirs(os.path.dirname(wb_path), exist_ok=True)
    json.dump(war, io.open(wb_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("已写:", wb_path, "| cards:", len(cards), "| checks:", len(checks))

    # ── 8. 重渲 intraday ──
    gen = r"D:\盯盘台作战台_806\生成作战台.py"
    if os.path.isfile(gen):
        import subprocess
        subprocess.run([sys.executable, gen, d], check=False)
    return 0

if __name__ == "__main__":
    sys.exit(main())
