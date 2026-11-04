# -*- coding: utf-8 -*-
"""东财全A快照_curl取数.py —— 绕过 requests/urllib3 被 RST 的问题, 直接用 curl --noproxy 分页拉。
2026-10-28 实测: akshare(requests) 对 82.push2 TLS 窗口 RST; curl 直连同 URL 返回 200。
输出: 与 ak.stock_zh_a_spot_em 同结构的 DataFrame(列名对齐: 代码/名称/今开/昨收/最新价/最高/最低/成交额/换手率/流通市值/涨跌幅)
"""
import json, subprocess, sys
import pandas as pd

URL = "https://82.push2.eastmoney.com/api/qt/clist/get"
FIELDS = "f2,f3,f5,f6,f8,f12,f14,f15,f16,f17,f18,f20,f21"
FS = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"


def _curl(params: dict) -> dict:
    q = "&".join("%s=%s" % (k, v) for k, v in params.items())
    cmd = ["curl", "-s", "--noproxy", "*", "-m", "20",
           "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36",
           "-H", "Referer: https://quote.eastmoney.com/",
           "%s?%s" % (URL, q)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError("curl失败 rc=%s %s" % (r.returncode, r.stderr[:200]))
    return json.loads(r.stdout)


def fetch_all() -> pd.DataFrame:
    base = dict(pn=1, pz=100, po=1, np=1, ut="bd1d9ddb04089700cf9c27f6f7426281",
                fltt=2, invt=2, fid="f12", fs=FS, fields=FIELDS)
    rows, total, page = [], None, 1
    while True:
        base["pn"] = page
        j = _curl(base)
        data = j.get("data")
        if not data or not data.get("diff"):
            break
        total = data.get("total")
        diff = data["diff"]
        rows.extend(diff.values() if isinstance(diff, dict) else diff)
        if total and len(rows) >= int(total):
            break
        page += 1
        if page > 120:
            break
    if not rows:
        raise RuntimeError("东财返回空")
    df = pd.DataFrame(rows)
    df = df.rename(columns={"f12": "代码", "f14": "名称", "f17": "今开", "f18": "昨收", "f2": "最新价",
                            "f15": "最高", "f16": "最低", "f6": "成交额", "f8": "换手率",
                            "f21": "流通市值", "f3": "涨跌幅"})
    for c in ["今开", "昨收", "最新价", "最高", "最低", "成交额", "换手率", "流通市值", "涨跌幅"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["代码"] = df["代码"].astype(str).str.zfill(6)
    df.attrs["total"] = total
    return df


if __name__ == "__main__":
    d = fetch_all()
    print("条数", len(d), "总数", d.attrs.get("total"))
    print(d.head(3).to_string())
