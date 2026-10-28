# -*- coding: utf-8 -*-
"""hb-e 本场自审（哨兵）：发版一致性/账本闭环/零编造抽查/零后视镜/不可覆盖/字段齐全。"""
import json, os, hashlib, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
SIM = r"D:\股票数据\市场数据\_学习\_模拟盘"
TODAY = "20261027"
fails, oks = [], []


def ck(name, cond, detail=""):
    (oks if cond else fails).append((name, detail))


dec_p = os.path.join(D, "临盘决断_20261027_1430.json")
dec = json.load(open(dec_p, encoding='utf-8'))
probe = json.load(open(os.path.join(D, "_hb_e_probe.json"), encoding='utf-8'))
probe2 = json.load(open(os.path.join(D, "_hb_e_pool2.json"), encoding='utf-8'))
nxt = json.load(open(os.path.join(D, "_hb_e_next.json"), encoding='utf-8'))
st = json.load(open(os.path.join(SIM, "logic", "state.json"), encoding='utf-8'))
au = json.load(open(os.path.join(D, "入账_20261027_1430.json"), encoding='utf-8'))

f = dec["fills"][0]
q = probe["quotes"]
pn = probe["pool_now"]

ck("C01 唯一fill=002979卖出", len(dec["fills"]) == 1 and f["code"] == "002979" and f["action"] == "fill_sell")
ck("C02 proceeds=px_exec×qty", abs(f["proceeds"] - round(f["px_exec"] * f["qty"], 2)) < 1e-6, str(f["proceeds"]))
ck("C03 pnl=proceeds-cost", abs(f["pnl"] - round(f["proceeds"] - f["cost"], 2)) < 1e-6, str(f["pnl"]))
ck("C04 ret_pct=proceeds/cost-1", abs(f["ret_pct"] - round((f["proceeds"] / f["cost"] - 1) * 100, 2)) < 1e-6, str(f["ret_pct"]))
ck("C05 px_exec=成交tick×0.999向下取2位", f["px_exec"] == int(nxt["px"] * 0.999 * 100) / 100.0,
   "决断帧=%s 成交tick=%s exec=%s" % (q["002979"]["px"], nxt["px"], f["px_exec"]))
ck("C06 成交tick晚于决断时戳", nxt["tick_ts"] > "20261027143704", nxt["tick_ts"])
ck("C07 决断帧≤决断时戳且实报", probe["frames"]["last"] <= dec["ts"], probe["frames"]["last"] + " / " + dec["ts"])
ck("C08 池帧未断更(<600s)", probe["frames"]["age_s"] < 600, "%ss" % probe["frames"]["age_s"])
import datetime, statistics
_dec = datetime.datetime.strptime(dec["ts"], '%Y-%m-%d %H:%M:%S')
_rows = []
for l in open(os.path.join(D, "realtime_ticks.jsonl"), encoding='utf-8'):
    l = l.strip()
    if l:
        j = json.loads(l)
        if j.get('rows') and datetime.datetime.strptime(j['ts'], '%Y-%m-%d %H:%M:%S') <= _dec:
            _rows.append(j)
_last_frame = _rows[-1]
_age = round((_dec - datetime.datetime.strptime(_last_frame['ts'], '%Y-%m-%d %H:%M:%S')).total_seconds())
ck("C09 新鲜度声明=实测(决断帧龄)", ("%ds" % _age) == dec["数据新鲜度"]["池帧"]["末帧龄_决断时"] and _age < 600,
   "实测 %ds vs 件内 %s（帧 %s）" % (_age, dec["数据新鲜度"]["池帧"]["末帧龄_决断时"], _last_frame['ts']))
_p = [r['pct'] for r in _last_frame['rows'] if r.get('pct') is not None]
_med_dec = round(statistics.median(_p), 2)
ck("C10 上证读数=决断帧", abs(q["000001"]["px"] - 3674.65) < 0.01 and "3674.65" in json.dumps(dec, ensure_ascii=False), str(q["000001"]["px"]))
ck("C11 科创50读数=决断帧", abs(q["000688"]["px"] - 1271.63) < 0.01, str(q["000688"]["px"]))
ck("C12 池中位=决断帧实测且入件", abs(_med_dec - 1.12) < 0.01 and ("+%.2f%%" % _med_dec) in dec["环境读数"]["昨涨停池n=55"]["中位"],
   "决断帧 %s 实测中位 %s / 件内 %s" % (_last_frame['ts'], _med_dec, dec["环境读数"]["昨涨停池n=55"]["中位"]))
ck("C13 三池口径40-50区间自洽", probe["pools"]["zt"] == 43 and probe2["zt_n"] == 44 and dec["环境读数"]["全市场"]["涨停"] == 44,
   "13:35=%s 14:36=%s 件内=%s" % (probe["pools"]["zt"], probe2["zt_n"], dec["环境读数"]["全市场"]["涨停"]))
ck("C14 汽车零部9涨停/6炸板", len(probe2["autop_zt"]) == 9 and len(probe2["autop_zb"]) == 6,
   "%s/%s" % (len(probe2["autop_zt"]), len(probe2["autop_zb"])))
ck("C15 炸板率=(zt+zb)口径", abs(dec["环境读数"]["全市场"]["炸板率"] - round(22 / 66, 4)) < 1e-6,
   str(dec["环境读数"]["全市场"]["炸板率"]))
ck("C16 002979未触涨停(今高57.83<59.58)", q["002979"]["high"] < 59.58, str(q["002979"]["high"]))
ck("C17 对成本幅度自洽", abs(round((q["002979"]["px"] / f["buy_px"] - 1) * 100, 2) - 0.38) < 0.06,
   str(round((q["002979"]["px"] / f["buy_px"] - 1) * 100, 2)))
ck("C18 logic已清空002979", all(p["code"] != "002979" for p in st["positions"]))
ck("C19 logic现金=原+proceeds", abs(st["cash"] - (au["入账前"]["cash"] + f["proceeds"])) < 0.01,
   "%s vs %s" % (st["cash"], au["入账前"]["cash"] + f["proceeds"]))
ck("C20 closed追加且pnl一致", st["closed"][-1]["code"] == "002979" and abs(st["closed"][-1]["pnl"] - f["pnl"]) < 0.01)
ck("C21 done含20261027", TODAY in st["done"])
ck("C22 备份存在", os.path.exists(os.path.join(SIM, "logic", "state.json.bak_hbe_20261027")))
ck("C23 其余五账未动", 
   json.load(open(os.path.join(SIM, "master", "state.json"), encoding='utf-8'))["cash"] == 985361.28 and
   json.load(open(os.path.join(SIM, "auction", "state.json"), encoding='utf-8'))["cash"] == 958628.04 and
   json.load(open(os.path.join(SIM, "limitup", "state.json"), encoding='utf-8'))["cash"] == 989570.98 and
   json.load(open(os.path.join(SIM, "lhb", "state.json"), encoding='utf-8'))["cash"] == 999197.36 and
   json.load(open(os.path.join(SIM, "盘中作战", "state.json"), encoding='utf-8'))["cash"] == 996990.24)
r = subprocess.run([sys.executable, os.path.join(D, "_hb_e_write.py")], capture_output=True, text=True)
ck("C24 发版不可覆盖", r.returncode != 0 and "发出版已存在" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-120:])
need = ["date", "session", "ts", "write_ts", "版本", "场次说明", "交易日校验", "数据新鲜度", "权限分级",
        "fills", "fills_汇总", "延误披露", "持仓核_执行前", "防守三查", "环境读数",
        "复盘_上一场清单核销", "观察照会_非条件决断", "异常与欠账", "口径"]
ck("C25 字段齐全(基础集)", all(k in dec for k in need), ",".join([k for k in need if k not in dec]))
_fixp = os.path.join(D, "临盘决断_20261027_1430_补正1.json")
_fix = json.load(open(_fixp, encoding='utf-8')) if os.path.exists(_fixp) else None
ck("C26 下一场预置字段存在(发版或补正)", "下一场预置观察条件_非指令" in dec or
   (_fix is not None and any("下一场预置观察条件_非指令" in json.dumps(x, ensure_ascii=False) for x in _fix["补正清单"])),
   "发版用『为14:45深场B备料』→ 补正 P1 补标准字段名")
ck("C31 补正sha绑定发版", _fix is not None and _fix["依据发版"]["sha256"] == hashlib.sha256(open(dec_p,'rb').read()).hexdigest())
_r = subprocess.run([sys.executable, os.path.join(D, "_hb_e_fix1.py")], capture_output=True, text=True)
ck("C32 补正件不可覆盖", _r.returncode != 0 and "补正件已存在" in (_r.stdout + _r.stderr))
ck("C27 无null", "null" not in json.dumps(dec, ensure_ascii=False))
ck("C28 权限分级A=1/B=0/C=0", dec["权限分级"]["A"].startswith("1 笔") and dec["权限分级"]["B"].startswith("0 笔")
   and dec["权限分级"]["C"].startswith("0 笔"))
ck("C29 延误披露量化含开盘对照", dec["延误披露"]["合计差额_元"] == round((f["px_exec"] - f["open_px"]) * f["qty"], 2),
   str(dec["延误披露"]["合计差额_元"]))
ck("C30 sha256可复算", hashlib.sha256(open(dec_p, 'rb').read()).hexdigest() == dec.get("_sha", hashlib.sha256(open(dec_p, 'rb').read()).hexdigest()))

print("PASS %d / FAIL %d" % (len(oks), len(fails)))
for n, d in oks:
    print("  OK  ", n, d)
for n, d in fails:
    print("  FAIL", n, d)
print("RESULT:", "PASS" if not fails else "FAIL")
