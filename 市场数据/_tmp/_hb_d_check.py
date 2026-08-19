# -*- coding: utf-8 -*-
"""hb-d 心跳:交易日校验(替代被禁的 python -c)"""
import sys, datetime, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from trading_calendar import load_trading_calendar

cal = load_trading_calendar()
t = datetime.date.today().strftime('%Y%m%d')
print('TODAY:', t)
print('IN_CAL:', t in cal)
print('LAST5:', cal[-5:] if cal else None)
