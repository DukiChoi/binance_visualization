import websocket
import json
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import gc
# 캔들스틱 데이터를 저장할 데이터프레임 생성
columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
df = pd.DataFrame(columns=columns)
# 비트코인 가격을 저장할 변수
current_price = None
def plot_candlestick():
    # 캔들스틱 그래프 생성

    kwargs = dict(type='candle', volume=True, figratio=(10, 5), title=f'Current Price: ${current_price}')
    mc = mpf.make_marketcolors(up='g', down='r')
    s = mpf.make_mpf_style(marketcolors=mc)
    mpf.plot(df, **kwargs, style='charles')
def on_message(ws, message):
    global df, current_price

    # JSON 메시지 파싱
    data = json.loads(message)

    # 캔들 데이터 확인
    if 'k' in data:
        candle = data['k']

        # 캔들 정보 추출
        timestamp = pd.to_datetime(candle['t'], unit='ms')
        open_price = float(candle['o'])
        high_price = float(candle['h'])
        low_price = float(candle['l'])
        close_price = float(candle['c'])
        volume = float(candle['v'])

        # 데이터프레임에 추가
        df.loc[timestamp] = [timestamp, open_price, high_price, low_price, close_price, volume]

        # 캔들스틱 그래프 업데이트
        plot_candlestick()
        plt.pause(0.001)

    # 현재 비트코인 가격 업데이트
    if 'c' in candle:
        current_price = float(candle['c'])
        gc.collect()
def on_error(ws, error):
    print(f"WebSocket Error: {error}")

def on_close(ws):
    print("WebSocket Connection Closed")

def on_open(ws):
    print("WebSocket Connection Opened")

    # 구독 요청 메시지 생성
    symbol = 'btcusdt'  # 비트코인과 Tether 마켓
    timeframe = '1m'  # 1분봉
    stream_name = f"{symbol}@kline_{timeframe}"

    # 구독 요청 전송
    subscribe_msg = json.dumps({
        "method": "SUBSCRIBE",
        "params": [stream_name],
        "id": 1
    })
    ws.send(subscribe_msg)

# WebSocket 연결
websocket.enableTrace(True)
ws_url = "wss://stream.binance.com:9443/ws"
ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
ws.on_open = on_open


# WebSocket 스트리밍 및 그래프 업데이트
ws.run_forever()
plt.ticklabel_format(useOffset=False, style='plain')
# 그래프 표시
plt.show()
