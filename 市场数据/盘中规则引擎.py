# -*- coding: utf-8 -*-
"""盘中规则引擎.py — 阶段②A 机械层(2026-07-19 #029, 设计=升级设计稿v1.9 §3.1机械层/§3.2预案单/§3.3.1成交真实性五条)

铁律: 只执行 盘中/{d}/playbook.json 里晚间已声明的结构化规则,无权发明任何动作;零网络调用,只读本地jsonl。
职责:
 1) 竞价确认(9:25后首个tick, latest=竞价/开盘价, chg=gap): trigger.open_range min_gap/max_gap 判区间;
    一字/涨停封板禁追 → confirm/abort 事件。9:15-9:25竞价段(含诱单期)tick一律只留档不决策(v1.3)。
 2) 盘中触发: buys.intraday.abort_if(结构化支持: "跌破开盘价-X%" / "炸板", "|"分隔可组合)
    与 sells.intraday(stop_pct=止损线 / take_zt="炸板即卖")。自由文本条件 → 流水记 unparsed_skip 留检查点会话人判。
    ★stop_pct基准(v1.9.1裁定): sells必须显式声明 ref_px(参考/成本价),按 latest/ref_px-1 判;
      缺ref_px一律 unparsed_skip 留检查点会话人判(零编造,不退化chg口径)——晚间预案必须把成本价写进sells。
 3) 成交真实性五条(§3.3.1逐条):
    ① 执行价=触发后下一tick价(禁用触发tick自身价);
    ② 流动性帽单笔≤下一tick区间成交量20% — watch.jsonl暂无成交量字段 → 帽子暂按整手取整+流水标注
       liquidity_unknown(字段后补);
    ③ 跌停封死卖单顺延: latest≈round(昨收×比例,2)判定(主板0.9/创业板科创0.8/北交所0.7),盘中开板按开板tick成交,
       收盘仍封→顺延次日开盘(模拟盘引擎接管);涨停封板买侧禁追对称(比例1.1/1.2/1.3);
    ④ 停牌/无行情=无后续tick → 不成交,流末如实记 abort/defer;
    ⑤ 成本双边0.15%(结算侧计,流水注明)+盘中单滑点0.10%(px_exec字段落地)。
    昨收=由tick latest/(1+chg/100)反推(同一快照自洽),非编造。
 4) 输出: 盘中/{d}/执行流水.jsonl 逐笔追加 {"ts","code","name","action","px","rule","route","note"[,px_exec,qty]}
    action∈ confirm|fill_buy|fill_sell|abort|defer|skip;
    盘中/{d}/alerts.jsonl: 持仓炸板 pos_zt_break / 止损线临近 stop_near / 数据断更>3分钟 data_gap·data_stale。
 5) 幂等断点: 启动重读自身流水(route|code|action|rule 去重+状态恢复),已处理事件不重复;
    每tick try/except 绝不崩溃;在线模式15:06自杀。
继承旧口径(_模拟盘设计.md 二/十二): 一字拒单/整手100股取整/成本双边0.15%/禁ST退NC。
用法: python 盘中规则引擎.py {YYYYMMDD} [--replay]
  --replay = 离线回放(读全量 auction_traj.jsonl+watch.jsonl 逐tick推演,不等实时)
  默认在线 = 每25秒增量读两jsonl尾部(字节offset,只消费完整行)
"""
import os, sys, json, glob, re, time, datetime

try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE

SLIP = 0.0010                      # 盘中单滑点0.10% (3.3.1⑤)
FEE_NOTE = "费双边0.15%由模拟盘结算侧计"
CAPITAL = 1000000                  # 每账虚拟本金100万(整手换算用)
GATE_TS = "09:25:00"               # 决策闸: 之前的tick只留档不决策
STALE_SEC = 180                    # 断更报警阈值(秒)
TOL = 0.005                        # 涨跌停价判定容差(元)

def band(code):
    """跌停/涨停比例: 主板0.9/1.1 创业板科创0.8/1.2 北交所0.7/1.3"""
    c = str(code).zfill(6)
    if c.startswith(("30", "68")): return 0.8, 1.2
    if c[0] in "48" or c.startswith("92"): return 0.7, 1.3
    return 0.9, 1.1

def sec(ts):
    try:
        h, m, s = str(ts).split(":"); return int(h)*3600 + int(m)*60 + int(s)
    except Exception:
        return None

class Engine:
    def __init__(self, d, replay):
        self.d = d; self.replay = replay
        self.dir = os.path.join(BASE, "盘中", d)
        os.makedirs(self.dir, exist_ok=True)
        self.fp_flow = os.path.join(self.dir, "执行流水.jsonl")
        self.fp_alert = os.path.join(self.dir, "alerts.jsonl")
        self.fp_log = os.path.join(self.dir, "rule_engine.log")
        self.done = set(); self.alerted = set(); self.recs = []
        self.pre = {}; self.zt_seen = {}; self.prev_ts = None
        self.buys = []; self.sells = []; self.interest = {}
        self.offsets = {}
        self.restore()
        self.load_playbook()
        self.apply_history()
        self.log("引擎启动 d=%s mode=%s 回读自身流水%d条(幂等续态)" % (d, "replay" if replay else "online", len(self.recs)))

    # ---------- 基础 ----------
    def log(self, *a):
        line = "%s %s" % (datetime.datetime.now().strftime("%H:%M:%S"), " ".join(str(x) for x in a))
        print(line, flush=True)
        try: open(self.fp_log, "a", encoding="utf-8").write(line + "\n")
        except Exception: pass

    def emit(self, ts, code, name, action, px, rule, route, note, **extra):
        key = "%s|%s|%s|%s" % (route, code, action, rule)
        if key in self.done: return False
        self.done.add(key)
        rec = {"ts": ts, "code": code, "name": name, "action": action, "px": px,
               "rule": rule, "route": route, "note": note}
        rec.update(extra)
        open(self.fp_flow, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
        return True

    def alert(self, ts, typ, code, name, msg, key=None):
        k = key or "%s|%s" % (typ, code)
        if k in self.alerted: return
        self.alerted.add(k)
        rec = {"ts": ts, "type": typ, "code": code, "name": name, "msg": msg, "k": k}
        try: open(self.fp_alert, "a", encoding="utf-8").write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception: pass
        self.log("[ALERT]", typ, code, msg)

    # ---------- 幂等: 回读自身流水 ----------
    def restore(self):
        if not os.path.isfile(self.fp_flow): return
        for ln in open(self.fp_flow, encoding="utf-8"):
            try: r = json.loads(ln)
            except Exception: continue
            self.done.add("%s|%s|%s|%s" % (r.get("route"), r.get("code"), r.get("action"), r.get("rule")))
            self.recs.append(r)
        if os.path.isfile(self.fp_alert):
            for ln in open(self.fp_alert, encoding="utf-8"):
                try:
                    a = json.loads(ln)
                    self.alerted.add(a.get("k") or "%s|%s" % (a.get("type"), a.get("code")))
                except Exception: pass

    def apply_history(self):
        for r in self.recs:
            code, rt = r.get("code"), r.get("route")
            act, rule = r.get("action"), r.get("rule") or ""
            for b in self.buys:
                if b["code"] != code or b["route"] != rt: continue
                if act == "confirm" and (rule.startswith("trigger") or rule.startswith("compat")):
                    b["st"] = "confirmed"; b["open_px"] = r.get("px")
                elif act == "defer" and rule == "zt_no_chase":
                    b["st"] = "deferred"
                elif act == "fill_buy": b["st"] = "filled"
                elif act == "abort": b["st"] = "aborted"
            for s in self.sells:
                if s["code"] != code or s["route"] != rt: continue
                if not (rule.startswith("stop_pct") or rule.startswith("take_zt")): continue
                if act == "confirm": s["st"] = "triggered"; s["trig_rule"] = rule
                elif act == "defer": s["st"] = "deferred_dt"; s["trig_rule"] = rule
                elif act == "fill_sell": s["st"] = "filled"

    # ---------- 预案单 ----------
    def _norm_routes(self, pb):
        if isinstance(pb, list):
            return [(p.get("route") or "r%d" % i, p) for i, p in enumerate(pb) if isinstance(p, dict)]
        if isinstance(pb, dict):
            if isinstance(pb.get("routes"), list):
                return [(p.get("route") or "r%d" % i, p) for i, p in enumerate(pb["routes"]) if isinstance(p, dict)]
            if "buys" in pb or "sells" in pb or "watch" in pb:
                return [(pb.get("route") or "master", pb)]
            return [(k, v) for k, v in pb.items()
                    if isinstance(v, dict) and ("buys" in v or "sells" in v or "watch" in v)]
        return []

    def load_playbook(self):
        fp = os.path.join(self.dir, "playbook.json")
        if not os.path.isfile(fp):
            self.log("[!] playbook.json 缺失 — 无规则可执行,仅做数据断更监测"); return
        try:
            pb = json.load(open(fp, encoding="utf-8"))
        except Exception as e:
            self.log("[X] playbook.json 解析失败:", str(e)[:100]); return
        now = datetime.datetime.now().strftime("%H:%M:%S")
        for rt, plan in self._norm_routes(pb):
            for x in plan.get("buys") or []:
                code = str(x.get("code", "")).zfill(6); nm = x.get("name") or ""
                if re.match(r"^(\*?ST|N|C)", nm) or "退" in nm:
                    self.emit(now, code, nm, "skip", None, "forbid_st_new", rt, "禁ST/退/N/C(铁律),弃单")
                    continue
                trig = x.get("trigger"); mode = mn = mx = rule = None
                if trig is None:
                    mode, rule = "compat", "compat:open"   # v3.0兼容: 无trigger=开盘买(9:25确认→下一tick成交)
                elif isinstance(trig, dict) and trig.get("type") == "open_range":
                    mode = "range"
                    mn = float(trig.get("min_gap", -100)); mx = float(trig.get("max_gap", 100))
                    rule = "trigger:open_range[%g,%g]" % (mn, mx)
                else:
                    self.emit(now, code, nm, "skip", None, "unparsed_skip", rt,
                              "trigger不可机读(%s),留检查点会话人判" % json.dumps(trig, ensure_ascii=False)[:60])
                    continue
                aborts = []
                ab = (x.get("intraday") or {}).get("abort_if")
                if ab:
                    for part in str(ab).split("|"):
                        part = part.strip()
                        if not part: continue
                        m = re.match(r"^跌破开盘价\s*[-−]?\s*(\d+(?:\.\d+)?)\s*[%％]$", part)
                        if m: aborts.append(("below_open", float(m.group(1))))
                        elif part == "炸板": aborts.append(("zb", None))
                        else:
                            self.emit(now, code, nm, "skip", None, "unparsed_skip", rt,
                                      "abort_if条件不可机读(%s),留检查点会话人判" % part)
                cs = (x.get("intraday") or {}).get("chase_stop")
                if cs is not None:
                    self.emit(now, code, nm, "skip", None, "unparsed_skip", rt,
                              "chase_stop暂无执行口径(%s),留检查点会话人判" % cs)
                b = {"route": rt, "code": code, "name": nm, "w": x.get("weight_pct"), "mode": mode,
                     "min": mn, "max": mx, "rule": rule, "aborts": aborts, "st": "pending", "open_px": None}
                self.buys.append(b)
                self.interest.setdefault(code, {"buys": [], "sells": []})["buys"].append(b)
            for x in plan.get("sells") or []:
                code = str(x.get("code", "")).zfill(6); nm = x.get("name") or ""
                idt = x.get("intraday") or {}
                stop = idt.get("stop_pct"); take_raw = idt.get("take_zt"); take = False
                if stop is not None:
                    try: stop = float(stop)
                    except Exception:
                        self.emit(now, code, nm, "skip", None, "unparsed_skip", rt,
                                  "stop_pct非数值(%s),留检查点会话人判" % stop)
                        stop = None
                if take_raw:
                    t = str(take_raw).strip()
                    if t == "炸板即卖": take = True
                    elif t == "锁仓": take = False   # 结构化: 明确持有,引擎无动作
                    else:
                        self.emit(now, code, nm, "skip", None, "unparsed_skip", rt,
                                  "take_zt条件不可机读(%s),留检查点会话人判" % take_raw)
                ref = idt.get("ref_px")
                try: ref = float(ref) if ref is not None else None
                except Exception: ref = None
                if stop is not None and ref is None:   # v1.9.1裁定: 零编造,不退化chg口径
                    self.emit(now, code, nm, "skip", None, "unparsed_skip", rt,
                              "stop_pct=%g缺ref_px,止损需晚间预案带成本价,留检查点会话人判" % stop)
                    stop = None
                if stop is None and not take:
                    continue   # 无盘中卖预案(v1.3教训: 止损默认关闭)=引擎不管,晚间腿归模拟盘引擎
                s = {"route": rt, "code": code, "name": nm, "stop": stop, "ref": ref, "take": take,
                     "st": "watching", "trig_rule": None,
                     "rule_stop": ("stop_pct:%g" % stop) if stop is not None else None,
                     "rule_take": "take_zt:炸板即卖"}
                self.sells.append(s)
                self.interest.setdefault(code, {"buys": [], "sells": []})["sells"].append(s)
            for x in plan.get("watch") or []:
                code = str(x.get("code", "")).zfill(6)
                self.emit(now, code, x.get("name") or "", "skip", None, "watch", rt,
                          "watch观察项(if=%s;then=%s)=拍板层职责,引擎不执行,留检查点会话" % (x.get("if"), x.get("then")))
        self.log("预案载入: buys可执行%d sells有盘中预案%d 关注码%d" % (len(self.buys), len(self.sells), len(self.interest)))

    # ---------- tick处理 ----------
    def _gap_excused(self, t1, t2):
        if t1 <= "09:30:30": return True                       # 竞价收单段(9:25:40-9:30)管道本就静默
        if t1 >= "11:25:00" and t2 <= "13:05:00": return True  # 午休
        return False

    def on_row(self, row):
        ts = row.get("ts"); t = row.get("t") or {}
        if not ts: return
        a, b2 = sec(self.prev_ts) if self.prev_ts else None, sec(ts)
        if self.prev_ts is None:
            self.prev_ts = ts
        elif a is not None and b2 is not None and b2 > a:
            if b2 - a > STALE_SEC and not self._gap_excused(self.prev_ts, ts):
                self.alert(ts, "data_gap", "", "", "数据断更%d秒(%s→%s)" % (b2 - a, self.prev_ts, ts),
                           key="data_gap|" + self.prev_ts)
            self.prev_ts = ts
        for code, v in t.items():
            c = str(code).zfill(6)
            if c not in self.interest: continue
            try:
                px = v[0] if isinstance(v, (list, tuple)) and v else None
                chg = v[1] if isinstance(v, (list, tuple)) and len(v) > 1 else None
                if px is None: continue
                self.on_tick(ts, c, float(px), float(chg) if chg is not None else None)
            except Exception as e:
                self.log("tick EXC", c, str(e)[:100])

    def on_tick(self, ts, code, px, chg):
        if code not in self.pre and chg is not None and chg > -99.9:
            pre = round(px / (1 + chg / 100.0), 2)
            if pre > 0: self.pre[code] = pre
        if ts < GATE_TS:
            return   # 9:15-9:25竞价段(含9:15-9:20诱单期): 只留档不决策(设计稿v1.3)
        pre = self.pre.get(code)
        ztp = dtp = None
        if pre:
            lo, hi = band(code)
            ztp = round(pre * hi, 2); dtp = round(pre * lo, 2)
        sealed_zt = ztp is not None and abs(px - ztp) <= TOL
        sealed_dt = dtp is not None and abs(px - dtp) <= TOL
        if sealed_zt: self.zt_seen[code] = True
        zb_now = bool(self.zt_seen.get(code)) and not sealed_zt   # 曾封涨停,现已开=炸板
        for b in self.interest[code]["buys"]:
            self._buy(ts, code, px, chg, b, sealed_zt, zb_now)
        for s in self.interest[code]["sells"]:
            self._sell(ts, code, px, chg, s, sealed_zt, sealed_dt, zb_now, dtp)

    def _buy(self, ts, code, px, chg, b, sealed_zt, zb_now):
        if b["st"] in ("filled", "aborted"): return
        if b["st"] == "pending":                       # 竞价确认: 9:25后首个tick
            if b["mode"] == "range":
                if chg is None: return                 # gap未采集,等下一tick,不猜
                if not (b["min"] <= chg <= b["max"]):
                    self.emit(ts, code, b["name"], "abort", px, b["rule"], b["route"],
                              "竞价gap %.2f%%越界[%g,%g],弃单" % (chg, b["min"], b["max"]))
                    b["st"] = "aborted"; return
            if sealed_zt:
                self.emit(ts, code, b["name"], "abort", px, "zt_no_chase", b["route"],
                          "9:25一字/涨停封板,禁追(3.3.1买侧对称)")
                b["st"] = "aborted"; return
            self.emit(ts, code, b["name"], "confirm", px, b["rule"], b["route"],
                      "竞价确认 gap=%s%%;开盘价%.2f;成交=下一tick(3.3.1①)"
                      % (("%.2f" % chg) if chg is not None else "未采集", px))
            b["st"] = "confirmed"; b["open_px"] = px
            return                                     # 禁用触发tick自身价成交
        # confirmed / deferred: 先查abort_if,再查封板,再成交
        for kind, xv in b["aborts"]:
            if kind == "below_open" and b.get("open_px") and px <= b["open_px"] * (1 - xv / 100.0) + 1e-9:
                self.emit(ts, code, b["name"], "abort", px, "abort_if:跌破开盘价-%g%%" % xv, b["route"],
                          "现价%.2f<=开盘%.2f×(1-%g%%),放弃买入" % (px, b["open_px"], xv))
                b["st"] = "aborted"; return
            if kind == "zb" and zb_now:
                self.emit(ts, code, b["name"], "abort", px, "abort_if:炸板", b["route"], "标的炸板,放弃买入")
                b["st"] = "aborted"; return
        if sealed_zt:
            if b["st"] != "deferred":
                self.emit(ts, code, b["name"], "defer", px, "zt_no_chase", b["route"],
                          "涨停封板禁追,等开板(开板tick才可成交,3.3.1买侧)")
                b["st"] = "deferred"
            return
        exec_px = round(px * (1 + SLIP), 4)
        qty = None
        try:
            if b.get("w"): qty = int(CAPITAL * float(b["w"]) / 100.0 / exec_px / 100) * 100
        except Exception: qty = None
        self.emit(ts, code, b["name"], "fill_buy", px, b["rule"], b["route"],
                  "下一tick价成交;滑点0.10%%→exec%.4f;%s;liquidity_unknown(无量字段,20%%帽待字段后补);整手%s股(weight%s%%/本金100万)"
                  % (exec_px, FEE_NOTE, qty if qty is not None else "未定", b.get("w")),
                  px_exec=exec_px, qty=qty)
        b["st"] = "filled"

    def _sell(self, ts, code, px, chg, s, sealed_zt, sealed_dt, zb_now, dtp):
        if s["st"] == "filled": return
        if zb_now:
            self.alert(ts, "pos_zt_break", code, s["name"], "持仓炸板: 现价%.2f跌落涨停价" % px)
        if s["st"] == "watching":
            trig = None
            if s["take"] and zb_now:
                trig = (s["rule_take"], "炸板即卖触发(曾封涨停,现%.2f已开板)" % px)
            if trig is None and s["stop"] is not None:
                cur = None
                if s.get("ref"):   # v1.9.1裁定: 唯一基准=ref_px,载入时已保证有(缺则skip)
                    cur = (px / s["ref"] - 1) * 100.0; base = "ref_px%.2f" % s["ref"]
                if cur is not None:
                    if cur <= s["stop"]:
                        trig = (s["rule_stop"], "止损触发: 当前%.2f%%<=线%g%%(基准=%s)" % (cur, s["stop"], base))
                    elif cur <= s["stop"] + 1.0:
                        self.alert(ts, "stop_near", code, s["name"],
                                   "止损线临近: 当前%.2f%% 线%g%%" % (cur, s["stop"]))
            if trig:
                self.emit(ts, code, s["name"], "confirm", px, trig[0], s["route"],
                          trig[1] + ";成交=下一tick(3.3.1①)")
                s["st"] = "triggered"; s["trig_rule"] = trig[0]
            return                                     # 禁用触发tick自身价成交
        # triggered / deferred_dt: 下一tick成交或顺延
        rule = s.get("trig_rule") or s.get("rule_stop") or s["rule_take"]
        if sealed_dt:
            if s["st"] != "deferred_dt":
                self.emit(ts, code, s["name"], "defer", px, rule, s["route"],
                          "跌停封死(≈%.2f),卖单顺延: 盘中开板按开板tick成交;收盘仍封→顺延次日开盘(模拟盘引擎接管)"
                          % (dtp if dtp is not None else px))
                s["st"] = "deferred_dt"
            return
        exec_px = round(px * (1 - SLIP), 4)
        note = "下一tick价成交;滑点0.10%%→exec%.4f;%s;liquidity_unknown(无量字段,20%%帽待字段后补);数量=在持全量(结算侧核定)" % (exec_px, FEE_NOTE)
        if s["st"] == "deferred_dt": note = "跌停开板成交(挂单顺延后);" + note
        self.emit(ts, code, s["name"], "fill_sell", px, rule, s["route"], note, px_exec=exec_px)
        s["st"] = "filled"

    def finalize(self, ts):
        for b in self.buys:
            if b["st"] in ("confirmed", "deferred"):
                self.emit(ts, b["code"], b["name"], "abort", None,
                          b["rule"] if b["st"] == "confirmed" else "zt_no_chase", b["route"],
                          "流末仍未成交(涨停封死/停牌/无下一tick),如实弃单,留晚间复盘")
                b["st"] = "aborted"
        for s in self.sells:
            if s["st"] == "triggered":
                self.emit(ts, s["code"], s["name"], "defer", None, s.get("trig_rule") or "", s["route"],
                          "已触发但无下一tick可成交(停牌/断流),留晚间结算处理")

    def summary(self):
        cnt = {}
        if os.path.isfile(self.fp_flow):
            for ln in open(self.fp_flow, encoding="utf-8"):
                try:
                    a = json.loads(ln)["action"]; cnt[a] = cnt.get(a, 0) + 1
                except Exception: pass
        self.log("[√] 流水汇总:", json.dumps(cnt, ensure_ascii=False))

    # ---------- 运行模式 ----------
    def run_replay(self):
        rows = []
        for fn in ("auction_traj.jsonl", "watch.jsonl"):
            fp = os.path.join(self.dir, fn)
            if not os.path.isfile(fp):
                self.log("[!]", fn, "缺失"); continue
            for ln in open(fp, encoding="utf-8"):
                try:
                    r = json.loads(ln)
                    if isinstance(r, dict) and "ts" in r and "t" in r: rows.append(r)
                except Exception: pass
        rows.sort(key=lambda r: str(r["ts"]))
        self.log("回放: %d行tick" % len(rows))
        for r in rows:
            try: self.on_row(r)
            except Exception as e: self.log("row EXC", str(e)[:120])
        self.finalize(str(rows[-1]["ts"]) if rows else datetime.datetime.now().strftime("%H:%M:%S"))
        self.summary()

    def read_new(self, fp):
        rows = []
        try: size = os.path.getsize(fp)
        except OSError: return rows
        off = self.offsets.get(fp, 0)
        if size <= off: return rows
        try:
            with open(fp, "rb") as f:
                f.seek(off); data = f.read()
        except OSError:
            return rows
        nl = data.rfind(b"\n")
        if nl < 0: return rows                    # 尾部不完整行,下轮再读
        self.offsets[fp] = off + nl + 1
        for ln in data[:nl + 1].splitlines():
            try:
                r = json.loads(ln.decode("utf-8"))
                if isinstance(r, dict) and "ts" in r and "t" in r: rows.append(r)
            except Exception: pass
        return rows

    def run_online(self):
        if datetime.date.today().weekday() >= 5:
            self.log("周末,不跑"); return
        files = [os.path.join(self.dir, "auction_traj.jsonl"), os.path.join(self.dir, "watch.jsonl")]
        last_seen = time.time(); stale_flag = False
        while True:
            now = datetime.datetime.now().strftime("%H:%M:%S")
            if now >= "15:06:00":
                self.finalize(now); self.summary(); self.log("[√] 15:06 自杀收工"); break
            rows = []
            for fp in files: rows.extend(self.read_new(fp))
            rows.sort(key=lambda r: str(r.get("ts") or ""))
            for r in rows:
                try: self.on_row(r)
                except Exception as e: self.log("row EXC", str(e)[:120])
            if rows:
                last_seen = time.time(); stale_flag = False
            else:
                trading = ("09:15:00" <= now < "11:32:00") or ("13:00:00" <= now < "15:01:00")
                if trading and time.time() - last_seen > STALE_SEC and not stale_flag:
                    self.alert(now, "data_stale", "", "",
                               "管道数据断更%d秒(在线墙钟检测)" % int(time.time() - last_seen),
                               key="data_stale|" + now[:5])
                    stale_flag = True
            time.sleep(25)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    d = args[0] if args else datetime.date.today().strftime("%Y%m%d")
    replay = "--replay" in sys.argv
    eng = Engine(d, replay)
    if replay: eng.run_replay()
    else: eng.run_online()

if __name__ == "__main__":
    main()
