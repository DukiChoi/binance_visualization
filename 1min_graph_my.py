import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import finplot as fplt
from matplotlib.axis import YAxis
import datetime as dt
from datetime import datetime, timedelta
import time
import pandas as pd
import ccxt
fplt.display_timezone = dt.timezone.utc
fplt.candle_bull_color = "#FF0000"
fplt.candle_bull_body_color = "#FF0000"
fplt.candle_bear_color = "#0000FF"

URL = 'https://api.binance.com/api/v3/klines'


price = 0
class Worker(QThread):
    global price
    timeout = pyqtSignal(pd.DataFrame)

    def __init__(self):
        super().__init__()

    def get_ohlcv(self):
        binance = ccxt.binance()
        ending_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        starting_time = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        start = int(time.mktime(datetime.strptime(starting_time, '%Y-%m-%d %H:%M:%S').timetuple())) * 1000
        ohlcvs = binance.fetch_ohlcv('BTC/USDT', '15m', start, 1500)
        chart = []
        index_list = []
        for ohlcv in ohlcvs:
            index_list.append(datetime.timestamp(datetime.fromtimestamp(ohlcv[0] / 1000) + timedelta(hours=9)))
        # 원래 이 index_list는 index를 타임형태로 나타내주기 위해 작성했으나 사실상 필요없어졌다가 다시 부활시킴.
        for ohlcv in ohlcvs:
            chart.append(
                [(datetime.fromtimestamp(ohlcv[0] / 1000)+timedelta(hours=9)).strftime('%m-%d'), ohlcv[1], ohlcv[4], ohlcv[3], ohlcv[2],
                 ohlcv[5]])
        '''여기서 크롤링한 리스트들을 활용하여 pandas 표를 만들기 위한 리스트를 새로 만든다.
        첫번째 for문은 index 만들어주는거고 두번째 for문은 나머지 값들 리스트다.'''
        columns = ['time', 'open', 'close', 'low', 'high', 'volume']
        stock_ds = pd.DataFrame.from_records(chart, index=index_list, columns=columns)
        # 여기서 index=index_list로 넣어주면 인덱스가 타임형태.
        # print(stock_ds)
        stock_ds[['open', 'close', 'low', 'high', 'volume']] = stock_ds[
            ['open', 'close', 'low', 'high', 'volume']].astype(float)
        # stock_ds.index=stock_ds.index.astype(str)
        stock_ds['time'] = stock_ds['time'].astype(str)
        # time열을 string으로 나머지 값들은 int로 바꿔주는 절차.
        self.df = stock_ds
        self.df = self.df[['open', 'high', 'low', 'close']]
        self.df.columns = ['Open', 'High', 'Low', 'Close']
        # print(self.df)
    def run(self):
        self.get_ohlcv()
        while True:
            price = ccxt.binance().fetch_last_prices(['BTC/USDT'])['BTC/USDT']['price']
            cur_min_dt = dt.datetime.fromtimestamp(int((datetime.now()+timedelta(hours=9)).timestamp()))
            # 여기서 왜 프린트하면 9시간 후의 지금이 나올까? 분명 외국시간기준으로 가져와서 거기에다가 9시간 더하지 않았나...
            # print(cur_min_dt)
            # print(dt.datetime.fromtimestamp((self.df.index[-1])))
            print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            # fplt.add_text((self.df.index[-1], 30300), s='BTC:\n$' + str(price))
            if cur_min_dt > dt.datetime.fromtimestamp(self.df.index[-1]):
                self.get_ohlcv()
            else:
                # update last candle
                self.df.iloc[-1]['Close'] = price
                if price > self.df.iloc[-1]['High']:
                    self.df.iloc[-1]['High'] = price
                if price < self.df.iloc[-1]['Low']:
                    self.df.iloc[-1]['Low'] = price

            self.timeout.emit(self.df)
            time.sleep(1)


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
        plot_candles.colors.update(dict(
            bull_shadow='#388d53',
            bull_frame='#205536',
            bull_body='#089981',
            bear_shadow='#d56161',
            bear_frame='#5c1a10',
            bear_body='#f23645'))
        self.axs = [self.ax]                                 # finplot requres this property
        grid_layout.addWidget(self.ax.vb.win, 0, 0)          # ax.vb     (finplot.FinViewBox)

    def update(self):
        now = dt.datetime.now()
        # self.statusBar().showMessage(str(now))

        if self.df is not None:
            if self.plot is None:
                self.plot = plot_candles.candlestick_ochl(self.df[['Open', 'Close', 'High', 'Low']])
                fplt.show(qt_exec=False)
            else:
                self.plot.update_data(self.df[['Open', 'Close', 'High', 'Low']])

    @pyqtSlot(pd.DataFrame)
    def update_data(self, df):
        self.df = df


if __name__ == "__main__":
    app = QApplication(sys.argv)
    plot_candles = fplt.live(1)
    window = MyWindow()
    # print("Hi")
    #
    # plot_candles = fplt.live(1)
    # plot_candles.colors.update(dict(
    #     bull_shadow='#388d53',
    #     bull_frame='#205536',
    #     bull_body='#52b370',
    #     bear_shadow='#d56161',
    #     bear_frame='#5c1a10',
    #     bear_body='#e8704f'))
    window.show()
    app.exec_()
