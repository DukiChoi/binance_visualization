import websocket
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
from datetime import datetime

# WebSocket 서버의 URL
websocket_url = 'wss://stream.binance.com:9443/ws/btcusdt@kline_1m'

# 선 차트의 X, Y 데이터를 저장할 리스트
x_data = []
y_data = []


# WebSocket으로 메시지를 수신할 때 호출되는 콜백 함수
def on_message(ws, message):
    # 수신한 메시지를 JSON 형태로 파싱
    data = json.loads(message)

    # 데이터에서 시간과 가격 추출
    timestamp = data['k']['t']
    price = float(data['k']['c'])

    # 타임스탬프를 날짜와 시간으로 변환
    dt = datetime.fromtimestamp(timestamp / 1000)

    # X, Y 데이터에 추가
    x_data.append(dt.strftime("%H:%M:%S"))
    y_data.append(price)


# 애니메이션 업데이트 함수
def update_chart(frame):
    # 차트 초기화
    plt.clf()

    # X, Y 데이터를 기반으로 선 차트 그리기
    plt.plot(x_data, y_data)

    # # X축 형식을 날짜 형식으로 설정
    # plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
    # plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
    # plt.gcf().autofmt_xdate()


# WebSocket 연결 및 메시지 수신 대기
def run_websocket():
    ws = websocket.WebSocketApp(websocket_url, on_message=on_message)
    ws.run_forever()


# 프로그램 실행
if __name__ == '__main__':
    # 애니메이션 설정
    ani = animation.FuncAnimation(plt.gcf(), update_chart, interval=1000)

    # WebSocket 연결 및 메시지 수신 대기를 별도의 쓰레드로 실행
    import threading

    ws_thread = threading.Thread(target=run_websocket)
    ws_thread.start()

    # 차트 표시
    plt.show()
