# -*- coding: utf-8 -*-
import sys, io, csv
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
B = r"D:/股票数据/市场数据"
codes = ["002881","603386","002164","603626","600267","600178","603278","600487","600522","601869","001283","003029","603236","603893","301313","600293"]
for c in codes:
    try:
        rows = list(csv.DictReader(open(f"{B}/_学习/_bars_cache/{c}.csv", encoding='utf-8')))
        rows = [r for r in rows if r["close"] not in ("", None)]
        if not rows:
            print(c, "empty"); continue
        last = rows[-1]
        close = float(last["close"])
        n20 = rows[-21] if len(rows) > 21 else rows[0]
        n60 = rows[-61] if len(rows) > 61 else rows[0]
        n250 = rows[-251] if len(rows) > 251 else rows[0]
        hi250 = max(float(r["high"]) for r in rows[-250:] if r["high"])
        lo250 = min(float(r["low"]) for r in rows[-250:] if r["low"])
        r20 = close/float(n20["close"])-1
        r60 = close/float(n60["close"])-1
        r250 = close/float(n250["close"])-1
        print(f"{c} date={last['date']} close={close:.2f} r20={r20*100:+.1f}% r60={r60*100:+.1f}% r250={r250*100:+.1f}% 距高={((close/hi250)-1)*100:+.1f}% 距低={((close/lo250)-1)*100:+.1f}% 样本={len(rows)}")
    except Exception as e:
        print(c, "FAIL", e)
