import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import math

if __name__ == "__main__":
    from multiprocessing import Process, Queue
    import time
    import sys
    import os
    sys.path.append("D:\\Program Files\\Tinysoft\\Analyse.NET")
    import TSLPy3 as ts



class TsTickData(object):

    def __enter__(self):
        if ts.Logined() is False:
            print('天软未登陆或客户端未打开，将执行登陆操作')
            self.__tsLogin()
            return self

    def __tsLogin(self):
        ts.ConnectServer("tsl.tinysoft.com.cn", 443)
        dl = ts.LoginServer("fzzqjyb", "fz123456")
        print('天软登陆成功')

    def __exit__(self, *arg):
        ts.Disconnect()
        print('天软连接断开')



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
    def __init__(self, backtest_data=None) -> None:
        if backtest_data is None:
            return
        self.all_data = pd.read_csv(backtest_data)
        self.all_data["price"] = self.all_data["price"].apply(lambda x: round(x, 3))
        self.all_data = self.all_data[["date", "time", "price"]]
        self.date_list = sorted(list(set(self.all_data["date"])))
        self.plot = True

    def initDailyParam(self, pos_type="all", date=None) -> None:
        if pos_type == "all":
            self.date = date
            df = self.all_data[self.all_data["date"] == date].copy()
            if df.shape[0] < 14400:
                raise ValueError("Data is not complete or data is missing on " + date)
            df.sort_values(by="time", inplace=True)
            x = list(range(14400))
            self.xM = x[:: 30]
            self.xtick = list(range(0, 14401, 1800))
            self.xticklabel = ["9:30", "10:00", "10:30", "11:00", "11:30/1:00", "1:30", "2:00", "2:30", "3:00"]
            self.plot = True
            self.yM = df["price"].tolist()[:: 30]
            self.xMl = self.xM[1:]  # x minute list without first nan i.e. start @ 9:31
            self.yMl = self.yM[1:]  # price minute list without first nan i.e. start @ 9:31
            self.Nl = list(range(len(self.xMl)))
            self.slope_list = [int(round(1000 * z)) for z in np.diff(self.yM)]
            self.y_min = df["price"].min()
            self.y_max = df["price"].max()
            self.y_mid = 0.5 * (self.y_min + self.y_max)
            self.pnl = 0
            if self.plot is True:
                self.fig, self.ax = plt.subplots(figsize=(16, 8))
                self.ax.plot(self.xM, self.yM, color="lightgray", linewidth=1)
                self.ax.plot(self.xM, self.yM, ".", color="lightgray", markersize=3)
                for n, xpos, ypos, value in zip(self.Nl, self.xMl, self.yMl, self.slope_list):
                    if abs(value) > 2:
                        self.ax.text(xpos - 30, ypos + 0.0005, str(abs(value)), fontsize=6, color="darkgray", fontweight="bold")
                self.ax.set_xticks(self.xtick, self.xticklabel)
                if self.y_max - self.y_min <= 0.1:
                    self.ax.set_ylim(self.y_mid - 0.05, self.y_mid + 0.05)
                plt.title(self.date, size=15)

        if pos_type == "long" or pos_type == "all":
            self.long_num = 0
            self.long_sig_type = None
            self.long_start_pos = None
            self.long_start_price = None
            self.long_peak_pos = None
            self.long_peak_price = None
            self.long_h1 = 0
            self.long_reach_6 = False
        if pos_type == "short" or pos_type == "all":
            self.short_num = 0
            self.short_sig_type = None
            self.short_start_pos = None
            self.short_start_price = None
            self.short_nadir_pos = None
            self.short_nadir_price = None
            self.short_h1 = 0
            self.short_reach_6 = False

    def closePosition(self, close_type: str, xpos: int, ypos: float, marker: str):
        start_price = self.long_start_price if close_type == "long" else self.short_start_price
        pos = self.long_start_pos if close_type == "long" else self.short_start_pos
        if self.plot is True:
            self.ax.plot([xpos, ], [ypos, ], marker, markersize=5)
            if ypos != start_price:
                color = "red" if ypos > start_price else "blue"
                x = self.xMl[pos]
                self.ax.plot([x, x + 0.0001], [start_price, ypos], color=color, linewidth =1)
        self.pnl += ypos - start_price
        self.update_stat_df(pos_type=close_type, close_price=ypos)
        self.initDailyParam(pos_type=close_type)

    def update_stat_df(self, pos_type: str, close_price: float) -> None:
        if pos_type == "long":
            df = pd.DataFrame([[self.long_sig_type, "B", self.long_start_price, \
                                close_price, close_price - self.long_start_price, self.date], ], \
                              columns=["sig_type", "direction", "open_price", "close_price", "pnl", "date"])
            self.stat_df = self.stat_df.append(df)
        elif pos_type == "short":
            df = pd.DataFrame([[self.short_sig_type, "S", self.short_start_price, \
                                close_price, self.short_start_price - close_price, self.date], ], \
                              columns=["sig_type", "direction", "open_price", "close_price", "pnl", "date"])
            self.stat_df = self.stat_df.append(df)
        else:
            raise ValueError("Wrong pos_type: ", pos_type)

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

    def checkCloseSignal(self, n: int, xpos: int, ypos: float, delta: int) -> (bool, int):
        if n > 236* 2 :
            if self.long_num > 0:
                self.closePosition("long", xpos, ypos, 'xk')
            if self.short_num > 0:
                self.closePosition("short", xpos, ypos, 'xk')
            return

        # check close long part
        if self.long_num > 0:
            if delta > 0:
                if round(1000 * (ypos - self.long_start_price)) >= 6:
                    self.long_reach_6 = True
                if ypos > self.long_peak_price:
                    self.long_peak_pos = n
                    self.long_peak_price = ypos
            else:
                trigger_price = self.calTriggerPrice(pos_type="long", n=n)
                if ypos < trigger_price:
                    self.closePosition("long", xpos, ypos, '*k')

        # Close short part
        if self.short_num > 0:
            if delta < 0:
                if round(1000 * (ypos - self.short_start_price)) <= -6:
                    self.short_reach_6 = True
                if ypos < self.short_nadir_price:
                    self.short_nadir_pos = n
                    self.short_nadir_price = ypos
            else:
                trigger_price = self.calTriggerPrice(pos_type="short", n=n)
                if ypos > round(trigger_price, 3):
                    self.closePosition("short", xpos, ypos, '*k')

    def checkOpenSignal(self,  n: int, xpos: int, ypos: float) -> (str, str):
        if n >= 4 and n <= 234 * 2:
            if self.long_num < 1:
                if sum(self.slope_list[n - 1 : n + 1]) >= 9: # RAPB
                    self.openPosition('B', "RAP", n, xpos, ypos, sum(self.slope_list[n - 1: n + 1]))
                else:
                    d1, d2, h1 = self.slope_list[n - 2: n + 1]
                    if d1 >= 2 and d2 >= 0 and h1 >= 2 and abs(h1) >= abs(d2) + 2: # CON1B
                        self.openPosition('B', "CON1", n, xpos, ypos, self.slope_list[n])
            if self.short_num < 1:
                d1, d2, h1 = self.slope_list[n - 2: n + 1]
                if d1 <= -2 and d2 <= 0 and h1 <= -2 and abs(h1) >= abs(d2) + 2: # CON1S
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
        elif direction == 'S':
            self.short_num += 1
            self.short_sig_type = sig_type
            self.short_start_pos = n
            self.short_start_price = ypos
            self.short_nadir_pos = n
            self.short_nadir_price = ypos
            self.short_h1 = h1
        if self.plot is True:
            shift = 3 if sig_type == "CON1" else 2
            self.ax.plot(self.xMl[n - shift: n + 1], self.yMl[n - shift: n + 1], color="gray",linewidth=1)
            self.ax.text(xpos - 120, ypos - 0.03, sig_type, fontsize=6, color="gray", fontweight="bold")

    def backtest(self, plot=True) -> None:
        self.plot = plot
        self.stat_df = pd.DataFrame(columns= ["sig_type", "direction", "open_price", "close_price", "pnl", "date"])
        for date in self.date_list:
            self.initDailyParam(pos_type="all", date=date)
            for n, xpos, ypos, delta in zip(self.Nl, self.xMl, self.yMl, self.slope_list):
                self.checkCloseSignal(n, xpos, ypos, delta)
                self.checkOpenSignal(n, xpos, ypos)
            if self.plot is True:
                re = round((math.exp(252 * self.pnl / 5 / 10) - 1) * 100, 1)
                self.ax.set_title(date + " PNL:" + str(round(self.pnl, 3)) + " R: " + str(re) + '%')
                self.fig.savefig("backtest/" + self.date + ".png")
                plt.close()
            print(date)
        return self.stat_df

    def printStat(self, name=None, printSave=True) -> None:
        df1 = self.stat_df.groupby(by=["sig_type", "direction"]).mean()
        df2 = self.stat_df.groupby(by=["sig_type", "direction"]).count()
        df = pd.merge(df1, df2, on=["sig_type", "direction"])
        df = df[["pnl_x", "pnl_y"]]

        df.columns = ["mean", "count"]
        df["mean"] = df["mean"].apply(lambda x: round(x, 6))
        df["sum"] = df["mean"].mul(df["count"])
        mean = round(df["sum"].sum() / df["count"].sum(), 6)
        self.stat = df
        if printSave is True:
            print(self.stat)
            if name is None:
                self.stat.to_csv("stat.csv")
            else:
                self.stat.to_csv("calibration/stat_"+ name + '_' + str(mean) + ".csv")
        return self.stat

    def multi_backtest(self,  process_num=10, plot=False):
        n = process_num
        for parent, dirnames, filenames in os.walk("data_slice/"):
            file_list = filenames
        if len(file_list) != process_num:
            N = len(self.date_list)
            for file in file_list:
                os.remove("data_slice/" + file)
            for i in range(0, n):
                date_scope = self.date_list[math.floor(i * (N / n)): math.floor((i + 1) * (N / n))]
                data_slice = self.all_data[self.all_data["date"].apply(lambda s: True if s in date_scope else False)]
                data_slice.to_csv("data_slice/data_slice_" + str(i) + ".csv", index=False)
            print("Slice data into", str(n), "part.")
        df = pd.DataFrame()
        q = Queue()
        jobs = list()
        for i in range(0, n):
            backtest_data = "data_slice/data_slice_" + str(i) + ".csv"
            p = Process(target=self.subBacktest, args = (q, backtest_data, plot))
            jobs.append(p)
            p.start()
            print("Start process", i)
        for i in range(0, n):
            df = df.append(q.get())
        for job in jobs:
            job.join()
        self.stat_df = df

    def subBacktest(self, q, backtest_data, plot=False, process_num=10):
        obj = Strategy(backtest_data=backtest_data)
        obj.backtest(plot)
        q.put(obj.stat_df)
        print("Process end")

    def getCurrentPrice(self):
        data = TsTickData().ticks()
        print(data)
        time.sleep(0.5)

    def timer(self):
        while True:
            now = dt.datetime.now()
            if now.microsecond < 999:
                print(now)
                self.getCurrentPrice()
                time.sleep(0.3)






if __name__ == "__main__":
    obj=Strategy()
    obj.multi_backtest(plot=True)
    obj.printStat()



