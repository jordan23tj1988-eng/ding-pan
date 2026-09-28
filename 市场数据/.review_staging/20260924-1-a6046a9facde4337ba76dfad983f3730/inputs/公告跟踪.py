# -*- coding: utf-8 -*-
"""公告跟踪.py —— 给候选/龙头股拉近1-2日公告新闻,自动标 利空/利好/监管
数据: akshare stock_news_em(个股新闻公告)。输出 _学习/公告_{d}.json。
代码来源: 当日 analysis.json核心标的 + 候选_{d}.json(去重,限~24只)。
用法: python 公告跟踪.py [YYYYMMDD]"""
import os, sys, glob, json, time, datetime, socket, re
socket.setdefaulttimeout(5)
try:
    import akshare as ak
except ImportError:
    os.system(sys.executable + " -m pip install akshare --break-system-packages -q"); import akshare as ak

BASE = r"D:\股票数据\市场数据"
if not os.path.isdir(BASE):
    g = glob.glob("/sessions/*/mnt/股票数据/市场数据"); BASE = g[0] if g else BASE

BAD = ["监管", "异常波动", "异动", "问询", "关注函", "暂停交易", "减持", "解禁", "质押", "预亏", "预减", "亏损", "立案", "处罚", "退市", "风险提示", "停牌", "核查", "被查", "诉讼", "冻结"]
GOOD = ["中标", "签约", "签订", "收购", "重组", "增持", "回购", "预增", "预盈", "扭亏", "大额订单", "涨价", "获批", "中标", "合作", "定增过会", "业绩大增"]

NEG = ["暂未", "未能", "尚未", "终止", "取消", "放弃", "无法", "不予", "不及预期", "低于预期", "拟终止"]
def classify(titles):
    txt = " ".join(titles)
    bad = [k for k in BAD if k in txt]
    good = [k for k in GOOD if k in txt]
    neg = any(n in txt for n in NEG)
    if bad: return "利空", bad
    if good and neg: return "存疑", good + ["(含否定词)"]   # 如"暂未签订"
    if good: return "利好", good
    if neg: return "存疑", ["否定/澄清"]
    return "中性", []

def latest(guess):
    for dd in range(0, 8):
        d = (guess - datetime.timedelta(days=dd)).strftime("%Y%m%d")
        if os.path.isfile(os.path.join(BASE, d, "analysis.json")):
            return d
    return None

def main():
    guess = datetime.date.today()
    if len(sys.argv) > 1:
        guess = datetime.datetime.strptime(sys.argv[1], "%Y%m%d").date()
    d = latest(guess)
    if not d:
        print("无analysis.json"); return
    codes = {}
    try:
        aj = json.load(open(os.path.join(BASE, d, "analysis.json"), encoding="utf-8"))
        for c in aj.get("核心标的", []):
            codes[str(c["代码"]).zfill(6)] = str(c["名称"])
    except Exception:
        pass
    cp = os.path.join(BASE, "_学习", "候选_%s.json" % d)
    if os.path.isfile(cp):
        for c in json.load(open(cp, encoding="utf-8")).get("候选", []):
            if c.get("代码"):
                codes[str(c["代码"]).zfill(6)] = c["名称"]
    codes = dict(list(codes.items())[:24])
    print(f"{d} 跟踪 {len(codes)} 只公告")
    recent = [d, (datetime.datetime.strptime(d, "%Y%m%d") - datetime.timedelta(days=1)).strftime("%Y%m%d")]
    out = {}
    t0 = time.time()
    for code, name in codes.items():
        if time.time() - t0 > 35:
            break
        try:
            df = ak.stock_news_em(symbol=code)
        except Exception:
            continue
        if df is None or len(df) == 0:
            continue
        SKIP = ["龙虎榜数据", "资金流向", "融资融券", "分时", "股价异动榜", "涨停揭秘", "盘口异动", "主力"]
        titles = []
        for _, r in df.head(15).iterrows():
            tm = str(r.get("发布时间", ""))[:10].replace("-", "")
            ti = str(r.get("新闻标题", ""))
            if tm in recent and not any(s in ti for s in SKIP):
                titles.append(ti)
        if not titles:
            continue
        tag, kws = classify(titles)
        if tag != "中性":
            out[code] = dict(名称=name, 标签=tag, 关键词=kws, 标题=titles[:3])
    json.dump(out, open(os.path.join(BASE, "_学习", "公告_%s.json" % d), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("有公告异动的:")
    for code, v in out.items():
        print("  %s(%s) [%s:%s] %s" % (v["名称"], code, v["标签"], "/".join(v["关键词"]), v["标题"][0][:36]))
    print("已存 公告_%s.json" % d)

if __name__ == "__main__":
    main()
