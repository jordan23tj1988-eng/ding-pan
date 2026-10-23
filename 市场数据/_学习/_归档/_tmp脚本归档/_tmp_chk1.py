# -*- coding: utf-8 -*-
import io, json, csv, re, os
B = r"D:/股票数据/市场数据"; L = os.path.join(B,"_学习")
src = open(os.path.join(B,"review_pages.py"), encoding="utf-8").read()
print("== review_pages.py lines:", src.count("\n"))
i = src.find("HEADING_MAP")
print("== HEADING_MAP context ==")
print(src[i-200:i+2200])
