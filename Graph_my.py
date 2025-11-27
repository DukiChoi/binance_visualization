import sys
import warnings
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import finplot as fplt
from matplotlib.axis import YAxis
import datetime as dt
from datetime import datetime, timedelta
import time
import pandas as pd
import ccxt
import traceback
import random
fplt.display_timezone = dt.timezone.utc
fplt.candle_bull_color = "#FF0000"
fplt.candle_bull_body_color = "#FF0000"
fplt.candle_bear_color = "#0000FF"

URL = 'https://api.binance.com/api/v3/klines'


warnings.filterwarnings("ignore", category=FutureWarning)
price = 0
date = ""
class Worker(QThread):
    timeout = pyqtSignal(pd.DataFrame)

    def __init__(self):
        super().__init__()
    def safe_fetch(self, func, *args, retries=3, **kwargs):
        """네트워크 요청 안전하게 재시도"""
        for i in range(retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"[Error] {e} (retry {i+1}/{retries})")
                traceback.print_exc()
                time.sleep(random.uniform(1, 3))  # 1~3초 랜덤 대기
        return None
    
    def get_ohlcv(self):
        binance = ccxt.binance()
        starting_time = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        start = int(time.mktime(datetime.strptime(starting_time, '%Y-%m-%d %H:%M:%S').timetuple())) * 1000

        ohlcvs = self.safe_fetch(binance.fetch_ohlcv, 'BTC/USDT', '1h', start, 1500)
        if not ohlcvs:
            print("[Error] Failed to fetch OHLCV data")
            return

        chart, index_list = [], []
        for ohlcv in ohlcvs:
            index_list.append(datetime.timestamp(datetime.fromtimestamp(ohlcv[0] / 1000) + timedelta(hours=9)))
            chart.append([
                (datetime.fromtimestamp(ohlcv[0] / 1000)+timedelta(hours=9)).strftime('%m-%d'),
                ohlcv[1], ohlcv[4], ohlcv[3], ohlcv[2], ohlcv[5]
            ])
        columns = ['time', 'open', 'close', 'low', 'high', 'volume']
        stock_ds = pd.DataFrame.from_records(chart, index=index_list, columns=columns)
        stock_ds[['open', 'close', 'low', 'high', 'volume']] = stock_ds[['open', 'close', 'low', 'high', 'volume']].astype(float)
        stock_ds['time'] = stock_ds['time'].astype(str)
        self.df = stock_ds[['open', 'high', 'low', 'close']]
        self.df.columns = ['Open', 'High', 'Low', 'Close']

    def run(self):
        self.get_ohlcv()
        while True:
            try:
                global price, date
                date = datetime.now().strftime("%H:%M:%S")
                last_price_data = self.safe_fetch(ccxt.binance().fetch_last_prices, ['BTC/USDT'])
                if not last_price_data:
                    continue
                price = last_price_data['BTC/USDT']['price']

                cur_min_dt = dt.datetime.fromtimestamp(int((datetime.now()+timedelta(hours=9)).timestamp()))

                if self.df is not None and cur_min_dt > dt.datetime.fromtimestamp(self.df.index[-1]):
                    self.get_ohlcv()
                elif self.df is not None:
                    self.df.at[self.df.index[-1], 'Close'] = price
                    self.df.at[self.df.index[-1], 'High'] = max(self.df.iloc[-1]['High'], price)
                    self.df.at[self.df.index[-1], 'Low'] = min(self.df.iloc[-1]['Low'], price)

                if self.df is not None:
                    self.timeout.emit(self.df)

                print(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " - BTC Price: " + str(price))

            except Exception as e:
                print(f"[Worker Error] {e}")
                traceback.print_exc()
                time.sleep(2)


class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.df = None
        self.plot = None

        # thread
        self.w = Worker()
        self.w.timeout.connect(self.update_data)
        self.w.start()

        # timer
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.update)

        view = QGraphicsView()
        grid_layout = QGridLayout(view)
        self.setCentralWidget(view)
        self.resize(1200, 600)
        self.ax = fplt.create_plot('Bitcoin price: ' + str(price), init_zoom_periods=100)
        # fplt.add_text(pos = , s='Bitcoin price: '+str(price))
        self.setWindowTitle("BTCUSDT Price in Binance")

        self.text = QPlainTextEdit(self)
        self.text.isReadOnly()
        self.text.move(10, 10)
        self.text.resize(450, 110)
        style_sheet = "QPlainTextEdit { font-size: 40px;}"
        self.text.setStyleSheet(style_sheet)




        # 여기 쭉
        # plot_candles.colors.update(dict(
        #     bull_shadow='#388d53',
        #     bull_frame='#205536',
        #     bull_body='#089981',
        #     bear_shadow='#d56161',
        #     bear_frame='#5c1a10',
        #     bear_body='#f23645'))
        # self.axs = [self.ax]                                 # finplot requres this property
        grid_layout.addWidget(self.ax.vb.win, 0, 0)          # ax.vb     (finplot.FinViewBox)

    def update(self):
        now = dt.datetime.now()
        # self.statusBar().showMessage(str(now))

        if self.df is not None:
            if self.plot is None:
                #여기 한 라인
                # self.plot = plot_candles.candlestick_ochl(self.df[['Open', 'Close', 'High', 'Low']])
                self.plot = fplt.candlestick_ochl(self.df[['Open', 'Close', 'High', 'Low']])
                self.text.setPlainText("BTCUSDT: $" + str(price) + "\n(" + date + ")")
                fplt.show(qt_exec=False)
            else:
                self.plot.update_data(self.df[['Open', 'Close', 'High', 'Low']])
                self.text.setPlainText("BTCUSDT: $" + str(price) + "\n(" + date + ")")

    @pyqtSlot(pd.DataFrame)
    def update_data(self, df):
        self.df = df


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 여기 한 라인
    # plot_candles = fplt.Live()
    window = MyWindow()
    # print("Hi")
    window.show()
    app.exec_()

