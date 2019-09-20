import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import math
import sys
sys.path.append("D:\\Program Files\\Tinysoft\\Analyse.NET")
import TSLPy3 as ts
import win32api
import win32con

if __name__ == "__main__":
    from multiprocessing import Process, Queue
    import time
    import os
    import random
    from threading import Thread
    from matplotlib.widgets import Button



class TsTickData(object):

    def __enter__(self):
        if ts.Logined() is False:
            # print('天软未登陆或客户端未打开，将执行登陆操作')
            self.__tsLogin()
            return self

    def __tsLogin(self):
        ts.ConnectServer("tsl.tinysoft.com.cn", 443)
        dl = ts.LoginServer("fzzqjyb", "fz123456")
        # print('天软登陆成功')

    def __exit__(self, *arg):
        ts.Disconnect()
        # print('天软连接断开')



    def ticks(self):
        ts_sql = ''' 
        setsysparam(pn_stock(),'SH510500');
        setsysparam(pn_precision(),3);   
        rds := rd(6);
        return rds;
        '''
        fail, value, _ = ts.RemoteExecute(ts_sql, {})
        return value



class Strategy():
    def __init__(self, mode = "real") -> None:
        self.mode = mode
        if mode == "history":
            df = pd.read_csv("SH510500_2019.csv")
            self.fake_df = df[df["date"] == "2019-02-28"]
            self.fake_count = 0
        Thread(target=self.draw).start()
        Thread(target=self.start).start()

    def initDailyParam(self, pos_type="all") -> None:
        if pos_type == "all":
            self.signal_list = list()
            self.close_list = list()
            self.date = str(dt.datetime.now().date())
            self.pnl = 0
            self.refresh = True

        if pos_type == "long" or pos_type == "all":
            self.long_num = 0
            self.long_sig_type = None
            self.long_start_pos = None
            self.long_start_price = None
            self.long_peak_pos = None
            self.long_peak_price = None
            self.long_h1 = 0
            self.long_reach_6 = False
            self.long_trigger_price = None
        if pos_type == "short" or pos_type == "all":
            self.short_num = 0
            self.short_sig_type = None
            self.short_start_pos = None
            self.short_start_price = None
            self.short_nadir_pos = None
            self.short_nadir_price = None
            self.short_h1 = 0
            self.short_reach_6 = False
            self.short_trigger_price = None

    def checkCloseSignal(self, n: int, xpos: int, ypos: float, delta: int) -> (bool, int):
        # check close long part
        if self.long_num > 0:
            if delta > 0:
                if round(1000 * (ypos - self.long_start_price)) >= 6:
                    self.long_reach_6 = True
                if ypos > self.long_peak_price:
                    self.long_peak_pos = n
                    self.long_peak_price = ypos
                self.long_trigger_price = self.calTriggerPrice(pos_type="long", n=n)
            else:
                self.long_trigger_price = self.calTriggerPrice(pos_type="long", n=n)
                if ypos < self.long_trigger_price:
                    self.closePosition("long", xpos, ypos)

        # Close short part
        if self.short_num > 0:
            if delta < 0:
                if round(1000 * (ypos - self.short_start_price)) <= -6:
                    self.short_reach_6 = True
                if ypos < self.short_nadir_price:
                    self.short_nadir_pos = n
                    self.short_nadir_price = ypos
                # self.short_trigger_price = self.calTriggerPrice(pos_type="short", n=n)
            else:
                self.short_trigger_price = self.calTriggerPrice(pos_type="short", n=n)
                if ypos > self.short_trigger_price:
                    self.closePosition("short", xpos, ypos)

    def calTriggerPrice(self, pos_type: str, n: int) -> float:
        if pos_type == "long":
            start = self.long_start_price
            point = self.long_peak_price
            sig_type = self.long_sig_type
            reach_6 = self.long_reach_6
            start_shift_1 = self.yMl[self.long_start_pos - 1]
            time_pass = n - self.long_start_pos
            h1 = self.long_h1
            sign = 1
        else:
            start = self.short_start_price
            point = self.short_nadir_price
            sig_type = self.short_sig_type
            reach_6 = self.short_reach_6
            start_shift_1 = self.yMl[self.short_start_pos - 1]
            time_pass = n - self.short_start_pos
            h1 = self.short_h1
            sign = -1
        H1 = round(1000 * (point - start))
        trigger_price = start

        if  not reach_6 and sig_type == "RAP":
            if time_pass <= 4:
                trigger_price = start - 0.006 * sign
            else:
                trigger_price = start
        elif not reach_6:
            if abs(h1) > 8:
                trigger_price = start - 2 / 3 * h1 / 1000 * sign
            elif sig_type == "CON1" or sig_type == "CON2" or sig_type == "CON3":
                trigger_price = start_shift_1
        else:
            if abs(H1) <= 15:
                trigger_price = start + 0.6 * H1 / 1000
            elif abs(H1) <= 30:
                trigger_price = start + 0.8 * H1  / 1000 - 0.001 * sign
            else:
                trigger_price = point - 0.001 * 12 * sign

        return round(trigger_price, 3)

    def closePosition(self, close_type: str, xpos: int, ypos: float):
        start_price = self.long_start_price if close_type == "long" else self.short_start_price
        pos = self.long_start_pos if close_type == "long" else self.short_start_pos
        x = self.xMl[pos]
        self.close_list.append((xpos, ypos, close_type, x, start_price))
        # Thread(target=self.message, args=("close", xpos, ypos, close_type)).start()
        msg = dt.datetime.strftime(dt.datetime.now(), "%H:%M:%S") + " Close " + close_type + " position @ " + str(
            xpos) + " with price: " + str(ypos)
        Thread(target=self.message, args=(msg,)).start()
        print(msg)
        if close_type == "long":
            self.pnl += ypos - start_price
        else:
            self.pnl += start_price - ypos
        self.initDailyParam(pos_type=close_type)

    def checkOpenSignal(self,  n: int, xpos: int, ypos: float) -> (str, str):
        if n >= 3 and n <= 234 * 2:
            if self.long_num < 1:
                if sum(self.slope_list[n - 1 : n + 1]) >= 3: # RAPB   9
                    self.openPosition('B', "RAP", n, xpos, ypos, sum(self.slope_list[n - 1: n + 1]))
                else:
                    d1, d2, h1 = self.slope_list[n - 2: n + 1]
                    if d1 >= 1 and d2 >= 0 and h1 >= 1 and abs(h1) >= abs(d2) + 2: # CON1B   2, 2
                        self.openPosition('B', "CON1", n, xpos, ypos, self.slope_list[n])
            if self.short_num < 1:
                d1, d2, h1 = self.slope_list[n - 2: n + 1]
                if d1 <= -1 and d2 <= 0 and h1 <= -1 and abs(h1) >= abs(d2) + 2: # CON1S     2, 2
                    self.openPosition('S', "CON1", n, xpos, ypos, self.slope_list[n])

    def openPosition(self, direction: str, sig_type: str, n: int, xpos: int, ypos:float, h1):
        if direction == 'B':
            self.long_sig_type = sig_type
            self.long_num += 1
            self.long_start_pos = n
            self.long_start_price = ypos
            self.long_peak_pos = n
            self.long_peak_price = ypos
            self.long_h1 = h1
            msg = dt.datetime.strftime(dt.datetime.now(), "%H:%M:%S") + " Open long position @ " + str(
                xpos) + " with price: " + str(ypos)
            Thread(target=self.message, args=(msg,)).start()
            print(msg)
        elif direction == 'S':
            self.short_num += 1
            self.short_sig_type = sig_type
            self.short_start_pos = n
            self.short_start_price = ypos
            self.short_nadir_pos = n
            self.short_nadir_price = ypos
            self.short_h1 = h1
            msg = dt.datetime.strftime(dt.datetime.now(), "%H:%M:%S") + " Open short position @ " + str(
                xpos) + " with price: " + str(ypos)
            Thread(target=self.message, args=(msg,)).start()
            print(msg)
        shift = 3 if sig_type == "CON1" else 2
        self.signal_list.append((self.xMl[n - shift: n + 1], self.yMl[n - shift: n + 1], xpos, ypos, sig_type))

    def getCurrentPrice(self):
        with TsTickData() as tslobj:
            return tslobj.ticks()


    def start(self):
        self.initDailyParam("all")
        if self.mode == "mock":
            price = 5.550
        date = str(dt.datetime.now().date())
        df = pd.DataFrame(columns=["time","price"])


        while True:
            time.sleep(0.9)
            now = dt.datetime.now()
            # if now.microsecond < 999 and now.second % 2 == 0:
            t = dt.datetime.strftime(now, "%H:%M:%S")
            if self.mode == "real":
                price = self.getCurrentPrice()
                while price is None:
                    price = self.getCurrentPrice()


            elif self.mode == "mock":
                change = random.randint(-8, 8)
                if abs(change) < 4:
                    price += change * 0.001
                    price = round(price, 3)
            elif self.mode == "history":
                price = self.fake_df.iloc[self.fake_count, 3]
                self.fake_count += 1
            else:
                raise ValueError("Wrong mode: " + self.mode)
            print("\r" + str(now), end = " ")
            df = df.append(pd.DataFrame([[t, price],], columns=["time","price"]))
            df.index = range(df.shape[0])
            if now.second == 0:
                df.to_csv("log/new_" + date + ".csv", index=False)
            self.xM = list(df[df["time"].apply(lambda s: s.endswith("0"))].index)
            if len(self.xM) < 2:
                continue
            self.yM = df[df["time"].apply(lambda s: s.endswith("0"))]["price"].tolist()
            self.xMl = self.xM[1:]
            self.yMl = self.yM[1:]
            self.Nl = list(range(len(self.xMl)))
            try:
                self.slope_list = [int(round(1000 * z)) for z in np.diff(self.yM)]
            except ValueError as e:
                print(self.xM)
                print(self.yM)
                raise(e)
            self.y_min = df["price"].min()
            self.y_max = df["price"].max()
            self.y_span = self.y_max - self.y_min
            if t.endswith("0"):
                n = len(self.xMl) - 1
                xpos = self.xMl[-1]
                ypos = self.yMl[-1]
                delta = self.slope_list[-1]
                self.checkCloseSignal(n, xpos, ypos, delta)
                self.checkOpenSignal(n, xpos, ypos)



    def refresh_func(self, event):
        self.refresh = not self.refresh
        if self.refresh:
            print("Resume refreshing")
            plt.close()
            self.draw()
        else:
            print("Stop refreshing")


    def draw(self):
        while True:
            try:
                _ = self.xMl
                break
            except:
                time.sleep(5)
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(1, 1, 1)
        plt.subplots_adjust(bottom=0.25)
        axnext = plt.axes([0.6, 0.05, 0.1, 0.075])
        bnext = Button(axnext, 'Refresh')
        bnext.on_clicked(self.refresh_func)
        while True:
            if self.refresh:
                self.ax.lines = list()
                self.ax.texts = list()
                self.ax.plot(self.xM, self.yM, color="black", linewidth=1)
                for n, xpos, ypos, value in zip(self.Nl, self.xMl, self.yMl, self.slope_list):
                    self.ax.text(xpos - 1, ypos + self.y_span * 0.05, str(abs(value)), fontsize=6, color="gray", fontweight="bold")
                for x_slice, y_slice, x_point, y_point, sig_type in self.signal_list:
                    self.ax.plot(x_slice, y_slice, color="steelblue", linewidth=1)
                    self.ax.text(x_point, self.y_min - 0.1 * self.y_span, sig_type, fontsize=5, color="steelblue",
                                 fontweight="bold")
                for xpos, ypos, close_type, x, start_price in self.close_list:
                    self.ax.plot([xpos, ], [ypos, ], "*k", markersize=5)
                    if ypos != start_price:
                        if close_type == "long":
                            color = "red" if ypos > start_price else "green"
                            y_2_points = [start_price, ypos]
                        else:
                            color = "red" if ypos < start_price else "green"
                            y_2_points = [start_price, 2 * start_price - ypos]
                        self.ax.plot([x, x + 0.001], y_2_points, color=color, linewidth=2)
                if self.long_trigger_price is not None:
                    self.ax.plot(self.xM, [self.long_trigger_price, ] * len(self.xM), "--r", linewidth=0.5)
                if self.short_trigger_price is not None:
                    self.ax.plot(self.xM, [self.short_trigger_price, ] * len(self.xM), "--g", linewidth=0.5)
                self.ax.set_title(str(round(self.pnl, 3)))
                self.ax.set_ylim(self.y_min - self.y_span * 0.2, self.y_max + self.y_span * 0.1)
                plt.pause(5)
            else:
                plt.pause(100000)


    def message(self, msg):
        win32api.MessageBox(0, msg, "Signal", win32con.MB_OK, win32con.MB_SYSTEMMODAL)



if __name__ == "__main__":
    obj = Strategy(mode="history")




