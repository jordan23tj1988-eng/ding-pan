# -*- coding: utf-8 -*-
"""龙虎榜双源校验.py {d} —— 源1=市场数据/{d}/lhb.csv(股票级净买) vs 源2=_学习/_席位动向/{d}.csv(东财买入前五买侧净额)。

产出 _学习/龙虎榜双源校验_{d}.json：一致/分歧/强矛盾/打折清单。分歧票引用须标注"双源分歧"，强矛盾票禁入荐票。
口径(20260818 修正)：股票级净买只取"当日榜"行(上榜原因不含 连续/累计/严重异常)，多行当日榜取同一值；不累加多榜行(累加=重复计+混入区间榜)。
源2 清洗(20260812 配方)：剔区间累计榜(类型含 连续/累计) → 剔(代码,席位)重复取买入金额最大 → 买侧净额按代码加总。
缺口声明：源2 只有买入前五、无卖出前五 → 天然偏买，本脚本不把源2 当净买权威，只做方向/量级交叉。
"""
from __future__ import annotations
import argparse, csv, collections
from pathlib import Path
from capability_common import valid_date, load_json, write_json

INTERVAL_KW = ("连续", "累计", "严重异常")
STRONG_YI = 1.0        # 强矛盾阈值(亿)
DISCOUNT_RATIO = 3.0   # 源2/源1 ≥ 3 判打折


def _f(x):
    try:
        v = float(x)
        return v if v == v else None      # NaN -> None
    except (TypeError, ValueError):
        return None


def read_source1(root: Path, d: str):
    """源1: lhb.csv 股票级净买(元)。返回 {code: {...}}"""
    p = root / d / "lhb.csv"
    if not p.is_file():
        return {}
    out = {}
    with p.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            code = str(r.get("代码") or "").strip()
            if not code:
                continue
            reason = str(r.get("上榜原因") or "")
            net = _f(r.get("龙虎榜净买额"))
            cur = out.setdefault(code, {"名称": str(r.get("名称") or "").strip(),
                                        "当日榜净买元": None, "区间榜有值": False, "行数": 0})
            cur["行数"] += 1
            if any(k in reason for k in INTERVAL_KW):
                if net is not None:
                    cur["区间榜有值"] = True
            elif net is not None and cur["当日榜净买元"] is None:
                cur["当日榜净买元"] = net
    for v in out.values():
        v["口径"] = "当日榜" if v["当日榜净买元"] is not None else "仅区间累计榜"
    return out


def read_source2(root: Path, d: str):
    """源2: 东财席位动向买侧明细(元)。返回 {code: {"名称","买侧净额元","席位数","类型集合"}}"""
    p = root / "_学习" / "_席位动向" / f"{d}.csv"
    if not p.is_file():
        return {}
    best = {}            # (code,seat) -> row, 取买入金额最大
    names = {}
    with p.open(encoding="utf-8-sig", newline="") as f:
        for r in csv.reader(f):
            if not r or len(r) < 9:
                continue
            code, seat, typ = str(r[1]).strip(), str(r[3]).strip(), str(r[8]).strip()
            if not code or not seat:
                continue
            if any(k in typ for k in INTERVAL_KW):      # 剔区间累计榜
                continue
            buy = _f(r[4]) or 0.0
            key = (code, seat)
            if key not in best or buy > (best[key][0] or 0.0):
                best[key] = (buy, _f(r[7]) or 0.0, seat)
            names[code] = str(r[2]).strip()
    agg = collections.defaultdict(lambda: {"买侧净额元": 0.0, "席位数": 0, "席位": []})
    for (code, seat), (_buy, net, sname) in best.items():
        agg[code]["买侧净额元"] += net
        agg[code]["席位数"] += 1
        agg[code]["席位"].append({"席位": sname, "净额元": round(net, 2)})
    for code, v in agg.items():
        v["名称"] = names.get(code, "")
        v["买侧净额元"] = round(v["买侧净额元"], 2)
    return dict(agg)


def build(root: Path, d: str):
    valid_date(d)
    s1, s2 = read_source1(root, d), read_source2(root, d)
    src = []
    if (root / d / "lhb.csv").is_file():
        src.append(f"{d}/lhb.csv")
    if (root / "_学习" / "_席位动向" / f"{d}.csv").is_file():
        src.append(f"_学习/_席位动向/{d}.csv")

    rows, strong, diverge, discount, only1, only2 = [], [], [], [], [], []
    for code in sorted(set(s1) | set(s2)):
        a, b = s1.get(code), s2.get(code)
        n1 = (a or {}).get("当日榜净买元")
        n2 = (b or {}).get("买侧净额元")
        y1 = round(n1 / 1e8, 4) if n1 is not None else None
        y2 = round(n2 / 1e8, 4) if n2 is not None else None
        name = (a or {}).get("名称") or (b or {}).get("名称") or ""
        scope = (a or {}).get("口径", "-")
        if y1 is None or y2 is None:
            kind = "无源1" if y1 is None else "无源2"
            (only2 if y1 is None else only1).append(code)
        elif (y1 > 0) == (y2 > 0) or (y1 == 0 and y2 == 0):
            if abs(y1) > 0 and abs(y2) / abs(y1) >= DISCOUNT_RATIO:
                kind = "打折"
                discount.append(code)
            else:
                kind = "一致"
        else:
            kind = "强矛盾" if (abs(y1) > STRONG_YI or abs(y2) > STRONG_YI) else "分歧"
            (strong if kind == "强矛盾" else diverge).append(code)
        rows.append({"代码": code, "名称": name, "源1净买亿": y1, "源2买侧净额亿": y2,
                     "判定": kind, "源1口径": scope,
                     "席位明细": (b or {}).get("席位", []) if b else []})

    comparable = [r for r in rows if r["源1净买亿"] is not None and r["源2买侧净额亿"] is not None]
    status = "pass" if (s1 and s2) else ("partial" if (s1 or s2) else "unavailable")
    errors = []
    if not s1:
        errors.append(f"{d}/lhb.csv 缺失: 股票级净买不可得")
    if not s2:
        errors.append(f"_学习/_席位动向/{d}.csv 缺失: 买侧明细不可得")
    result = {
        "schema_version": 1, "capability": "lhb_dual_source", "date": d, "status": status,
        "sources": src,
        "metrics": {"源1代码数": len(s1), "源2代码数": len(s2), "可比数": len(comparable),
                    "一致": len(comparable) - len(strong) - len(diverge) - len(discount),
                    "分歧": len(diverge), "强矛盾": len(strong), "打折": len(discount),
                    "仅源1": len(only1), "仅源2": len(only2)},
        "errors": errors,
        "note": "源1=股票级净买(当日榜行,禁累加多榜); 源2=东财买入前五买侧净额(无卖出前五,天然偏买,不作净买权威); "
                "强矛盾(|任一|>1亿且方向相反)=卖压污染嫌疑禁入荐票; 打折(源2/源1≥3倍)=净买打折读",
        "口径": "源1取当日榜行(上榜原因不含 连续/累计/严重异常); 源2剔区间累计榜+(代码,席位)去重取买入金额最大",
        "统计": {"lhb代码数": len(s1), "席位明细代码数": len(s2), "可比": len(comparable),
                 "一致": len(comparable) - len(strong) - len(diverge) - len(discount),
                 "分歧": len(diverge), "强矛盾": len(strong), "打折": len(discount),
                 "仅源1无席位明细": len(only1), "仅源2未上榜": len(only2)},
        "强矛盾清单": [r for r in rows if r["判定"] == "强矛盾"],
        "分歧清单": [r for r in rows if r["判定"] == "分歧"],
        "打折清单": [r for r in rows if r["判定"] == "打折"],
        "全量": rows,
    }
    return result


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument('d')
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--out', type=Path)
    a = p.parse_args(argv)
    r = build(a.root.resolve(), a.d)
    out = a.out or (a.root / "_学习" / f"龙虎榜双源校验_{a.d}.json")
    write_json(out, r)
    print("[%s] %s 可比=%d 一致=%d 分歧=%d 强矛盾=%d 打折=%d" % (
        r["status"], out.name, r["统计"]["可比"], r["统计"]["一致"],
        r["统计"]["分歧"], r["统计"]["强矛盾"], r["统计"]["打折"]))
    for r_ in r["强矛盾清单"]:
        print("  强矛盾 %s %s 源1=%s亿 源2=%s亿" % (r_["代码"], r_["名称"], r_["源1净买亿"], r_["源2买侧净额亿"]))
    return 0 if r["status"] == "pass" else 1


if __name__ == '__main__':
    raise SystemExit(main())
