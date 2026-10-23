import urllib.request, json
u="https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sh603278,day,2026-10-10,2026-10-24,20,qfq"
try:
    r=urllib.request.urlopen(u, timeout=10).read().decode('utf-8')
    d=json.loads(r)
    k=d["data"]["sh603278"].get("qfqday") or d["data"]["sh603278"].get("day")
    print("OK", len(k)); print(k[-4:])
except Exception as e:
    print("FAIL", type(e).__name__, e)
