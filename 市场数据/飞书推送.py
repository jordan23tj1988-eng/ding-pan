# -*- coding: utf-8 -*-
"""飞书推送.py — 模拟盘成交事件→飞书群自定义机器人 (2026-07-18 变更总账#029)
职责: 监听 _学习/_模拟盘/*/账本.jsonl 增量,把成交事件(ev=buy/sell)推成飞书消息卡片。
      解耦设计:不改模拟盘引擎;谁跑完谁顺手扫一遍(增量靠字节offset,不重推不漏推)。

配置: D:\\股票数据\\_飞书配置.json   ★放市场数据镜像之外——webhook属机密,禁入公开GitHub仓库(同 _ifind_auth.json 先例)
      {"webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/xxxx",
       "secret": "",              # 机器人若开了"签名校验"填这里,没开留空
       "enabled": true,
       "events": ["buy", "sell"],  # 推哪些账本事件;reject/defer默认不推
       "max_per_scan": 20}         # 单轮最多单发条数,超出合并成一条汇总防刷屏
状态: _学习/_飞书推送状态.json  (各路账本字节offset;首次运行=定位到文件尾,不推历史)
失败: _学习/_飞书推送失败.jsonl (推送失败留档;该路offset不前进,下轮扫描自动重试)

用法:
  python 飞书推送.py            扫一轮增量并推送(挂钩点调这个)
  python 飞书推送.py --test     发一条测试消息(验证webhook通不通)
  python 飞书推送.py --init     重置offset到各账本文件尾(不推历史;换webhook后可用)

挂钩点(宿主侧4处,见_链路地图.md): 宿主取数_早盘(闸门后)/宿主取数_傍晚(结算后)/
  盘中实时管道(盘中60s循环+收工)/同步到GitHub.bat(晚间复盘后用户手动触发)
★仅宿主(Windows)出网;沙箱无外网(#006),非Windows环境本脚本直接静默退出,不动offset。
"""
import os, sys, json, time, glob, hmac, base64, hashlib, datetime, urllib.request

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE
ROOT = os.path.dirname(BASE)
CONF_P = os.path.join(ROOT, "_飞书配置.json")
SIM = os.path.join(BASE, "_学习", "_模拟盘")
ST_P = os.path.join(BASE, "_学习", "_飞书推送状态.json")
FAIL_P = os.path.join(BASE, "_学习", "_飞书推送失败.jsonl")

ROUTE_CN = {"master": "master主户", "auction": "竞价路", "lhb": "席位路",
            "limitup": "质量路", "logic": "产逻路", "theme": "题材路"}

def _jload(p, default):
    try:
        with open(p, encoding="utf-8") as f: return json.load(f)
    except Exception: return default

def _jsave(p, obj):
    tmp = p + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, p)

def load_conf():
    c = _jload(CONF_P, None)
    if c is None:
        c = {"webhook": "", "secret": "", "enabled": True,
             "events": ["buy", "sell"], "max_per_scan": 20}
        try: _jsave(CONF_P, c)
        except Exception: pass
    return c

def _sign(secret, ts):
    key = ("%s\n%s" % (ts, secret)).encode("utf-8")
    return base64.b64encode(hmac.new(key, digestmod=hashlib.sha256).digest()).decode()

def _post(webhook, payload):
    """直连优先(同步bat会设15236代理,代理可能不通飞书);失败再走系统默认。"""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    last = None
    for opener in (urllib.request.build_opener(urllib.request.ProxyHandler({})),
                   urllib.request.build_opener()):
        try:
            req = urllib.request.Request(webhook, data=data,
                                         headers={"Content-Type": "application/json"})
            r = opener.open(req, timeout=10)
            body = json.loads(r.read().decode("utf-8"))
            if body.get("code", body.get("StatusCode", -1)) == 0:
                return True, body
            last = body
        except Exception as e:
            last = {"err": str(e)[:200]}
    return False, last

def send(payload, conf=None):
    conf = conf or load_conf()
    if not conf.get("webhook"): return False, {"err": "webhook未配置"}
    if conf.get("secret"):
        ts = str(int(time.time()))
        payload = dict(payload, timestamp=ts, sign=_sign(conf["secret"], ts))
    return _post(conf["webhook"], payload)

def _card(title, color, lines):
    return {"msg_type": "interactive", "card": {
        "config": {"wide_screen_mode": True},
        "header": {"template": color, "title": {"tag": "plain_text", "content": title}},
        "elements": [{"tag": "div", "text": {"tag": "lark_md", "content": "\n".join(lines)}}]}}

def _fmt_event(route, ev):
    rn = ROUTE_CN.get(route, route)
    nm = "%s %s" % (ev.get("name", ""), ev.get("code", ""))
    if ev.get("ev") == "buy":
        lines = ["**价格** ¥%s  ×%s股" % (ev.get("px"), ev.get("shares")),
                 "**金额** ¥%s" % ev.get("cost"),
                 "**日期** %s  记账 %s" % (ev.get("d"), ev.get("ts", ""))]
        if ev.get("liq_warn"): lines.append("⚠ 流动性: %s" % ev["liq_warn"])
        return _card("📥 买入 · %s | %s" % (rn, nm), "blue", lines)
    if ev.get("ev") == "sell":
        pnl = ev.get("pnl", 0) or 0; ret = ev.get("ret_pct", 0) or 0
        color = "red" if pnl >= 0 else "green"
        sign = "+" if pnl >= 0 else ""
        lines = ["**%s%.2f元 (%s%.2f%%)**" % (sign, pnl, sign, ret),
                 "买 ¥%s (%s) → 卖 ¥%s (%s)" % (ev.get("buy_px"), ev.get("buy_date"),
                                                ev.get("sell_px"), ev.get("sell_date")),
                 "持有%s天 · 腿=%s · 仓位%s%%" % (ev.get("hold_days"), ev.get("leg"), ev.get("weight"))]
        rs = (ev.get("reason") or "").strip()
        if rs: lines.append("——" + (rs[:160] + "…" if len(rs) > 160 else rs))
        return _card("📤 卖出 · %s | %s" % (rn, nm), color, lines)
    return _card("模拟盘事件 · %s | %s" % (rn, nm), "grey",
                 [json.dumps(ev, ensure_ascii=False)[:300]])

def _routes():
    if not os.path.isdir(SIM): return []
    return sorted(r for r in os.listdir(SIM)
                  if os.path.isfile(os.path.join(SIM, r, "账本.jsonl")))

def scan(verbose=True):
    """扫账本增量并推送。返回(推送数, 失败数)。仅宿主出网。"""
    if os.name != "nt" and "--force" not in sys.argv:
        if verbose: print("非Windows宿主(沙箱无外网,#006),跳过推送,offset不动")
        return 0, 0
    conf = load_conf()
    if not conf.get("enabled"): return 0, 0
    st = _jload(ST_P, None)
    first = st is None
    st = st or {"offsets": {}}
    events, pushed, failed = [], 0, 0
    for route in _routes():
        p = os.path.join(SIM, route, "账本.jsonl")
        size = os.path.getsize(p)
        off = st["offsets"].get(route, None)
        if first or off is None or off > size:      # 首次/新路/文件被重建→定位文件尾,不推历史
            st["offsets"][route] = size; continue
        if off == size: continue
        with open(p, "rb") as f:
            f.seek(off); chunk = f.read(size - off)
        nl = chunk.rfind(b"\n")
        if nl < 0: continue                          # 半行未写完,等下轮
        good_end = off + nl + 1
        for ln in chunk[:nl + 1].decode("utf-8", "replace").splitlines():
            ln = ln.strip()
            if not ln: continue
            try: ev = json.loads(ln)
            except Exception: continue
            if ev.get("ev") in conf.get("events", ["buy", "sell"]):
                events.append((route, ev))
        st["offsets"][route] = good_end
    if not conf.get("webhook"):
        # webhook未配:offset照常前进会丢事件→回滚本轮,等配置好再推
        if events and verbose: print("webhook未配置,%d条事件暂不推(offset保持,配好后自动补推)" % len(events))
        if not events: _jsave(ST_P, st)
        return 0, 0
    cap = int(conf.get("max_per_scan", 20))
    singles, rest = events[:cap], events[cap:]
    sent_all = True
    for route, ev in singles:
        ok, resp = send(_fmt_event(route, ev), conf)
        if ok: pushed += 1
        else:
            failed += 1; sent_all = False
            try:
                with open(FAIL_P, "a", encoding="utf-8") as f:
                    f.write(json.dumps({"ts": str(datetime.datetime.now())[:19], "route": route,
                                        "ev": ev, "resp": resp}, ensure_ascii=False) + "\n")
            except Exception: pass
    if rest and sent_all:
        agg = ["%s %s %s ¥%s" % ("买" if e.get("ev") == "buy" else "卖",
               ROUTE_CN.get(r, r), e.get("name", e.get("code")), e.get("px", e.get("sell_px")))
               for r, e in rest]
        ok, _ = send(_card("模拟盘成交汇总(+%d条)" % len(rest), "blue", agg[:40]), conf)
        pushed += 1 if ok else 0
    if sent_all:
        _jsave(ST_P, st)                             # 全部推成才前进offset;有失败=下轮整批重扫
    if verbose and (pushed or failed):
        print("飞书推送: 成功%d 失败%d" % (pushed, failed))
    return pushed, failed

def scan_quiet():
    """盘中管道60s循环用:静默+永不抛异常。"""
    try: return scan(verbose=False)
    except Exception: return 0, 0

if __name__ == "__main__":
    if "--test" in sys.argv:
        ok, resp = send(_card("盯盘台 · 飞书链路测试", "turquoise",
                              ["模拟盘成交推送已接通 ✅", "时间: " + str(datetime.datetime.now())[:19]]))
        print("测试消息:", "成功" if ok else "失败", json.dumps(resp, ensure_ascii=False)[:300])
        sys.exit(0 if ok else 1)
    if "--init" in sys.argv:
        st = {"offsets": {r: os.path.getsize(os.path.join(SIM, r, "账本.jsonl")) for r in _routes()}}
        _jsave(ST_P, st); print("offset已重置到各账本文件尾:", st["offsets"]); sys.exit(0)
    p, f = scan(); sys.exit(0)
