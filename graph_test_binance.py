import ccxt
import time
from datetime import datetime, timedelta
import requests
import pandas as pd
binance = ccxt.binance()
print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

ending_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
starting_time = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
start = int(time.mktime(datetime.strptime(starting_time, '%Y-%m-%d %H:%M:%S').timetuple()))*1000
ohlcvs = binance.fetch_ohlcv('BTC/USDT','5m', start, 1000)
print(ohlcvs)
print(len(ohlcvs))

chart = []
index_list=[]
for ohlcv in ohlcvs:
    index_list.append(datetime.fromtimestamp(ohlcv[0]/1000))

#원래 이 index_list는 index를 타임형태로 나타내주기 위해 작성했으나 사실상 필요없어졌다가 다시 부활시킴.
for ohlcv in ohlcvs:
    chart.append([datetime.fromtimestamp(ohlcv[0]/1000).strftime('%m-%d'), ohlcv[1], ohlcv[4], ohlcv[3], ohlcv[2], ohlcv[5]])
'''여기서 크롤링한 리스트들을 활용하여 pandas 표를 만들기 위한 리스트를 새로 만든다.
첫번째 for문은 index 만들어주는거고 두번째 for문은 나머지 값들 리스트다.'''
columns = ['time', 'open', 'close', 'low', 'high', 'volume']
stock_ds = pd.DataFrame.from_records(chart, index=index_list, columns=columns)
#여기서 index=index_list로 넣어주면 인덱스가 타임형태.
#print(stock_ds)
stock_ds[['open', 'close', 'low', 'high', 'volume']] = stock_ds[['open', 'close', 'low', 'high', 'volume']].astype(float)
#stock_ds.index=stock_ds.index.astype(str)
stock_ds['time'] = stock_ds['time'].astype(str)
#time열을 string으로 나머지 값들은 int로 바꿔주는 절차.

print(stock_ds)

print(binance.fetch_last_prices(['BTC/USDT'])['BTC/USDT']['price'])