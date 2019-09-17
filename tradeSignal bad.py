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

def backtest_slice(q, backtest_data, plot=False):
    obj = Strategy(backtest_data=backtest_data)
    obj.backtest(plot)
    q.put(obj.stat_df)
    print("Process end")



class Strategy():
    def __init__(self, backtest_data=None) -> None:
        if backtest_data is None:
            return
        self.all_data = pd.read_csv(backtest_data)
        self.all_data["price"] = self.all_data["price"].apply(lambda x: round(x, 3))
        self.all_data = self.all_data[["date", "time", "price"]]
        self.date_list = sorted(list(set(self.all_data["date"])))
        self.plot = True

    def getRapidOS(self, ls: list) -> (str, str, int):
        '''
        Get Rapid Open Signal

        ls: list, list of slope: [ -1 min, 0 min]

        condition: (Assume Open Long)
                   1. x1 = 2
                   2. h1 >= 12
        :return: (str, str, int). first str: 1 for open long, -1 for open short, 0 for no signal;
                second str: signal type; int: h2
        '''
        h1 = sum(ls)
        if h1 >= 9:
            return 'B', "RAP", h1
        else:
            return None, None, 0

    def getContinuousOS(self, ls: list) -> (str, str, int):
        '''
        Get Continuous Open Signal

        ls: list, list of slope: [ -3 min, -2 min, -1 min, 0 min]

        Type 1 condition: (Assume Open Long)
                   1. x1 = x2 = x3 = 1
                   2. d1 >= 6, h1 >= 3, d2 < 0
                   3. abs(d2) <= 1 / 2 * d1
                   4. h1 >= 2 * abs(d2)

        :return: (str, str, int). first str: 1 for open long, -1 for open short, 0 for no signal;
                second str: signal type; int: h2
        '''

        z1, z2, z3, z4 = ls
        # Type 1
        d1, d2, h1 = z2, z3, z4
        if d1 >= 2 and d2 >= 0 and h1 >= 2 and abs(h1) >= abs(d2) + 2:
            return 'B', "CON1", h1
        if d1 <= -2 and d2 <= 0  and h1 <= -2 and abs(h1) >= abs(d2) + 2:
            return 'S', "CON1", h1
        else:
            return None, None, 0

    def initDailyParam(self, pos_type="all", date=None) -> None:
        if pos_type == "all":
            self.date = date
            df = self.all_data[self.all_data["date"] == date].copy()
            if df.shape[0] < 14400:
                raise ValueError("Data is not complete or data is missing on " + date)
            df.sort_values(by="time", inplace=True)
            self.xtick = list(range(0, 14401, 1800))
            self.xticklabel = ["9:30", "10:00", "10:30", "11:00", "11:30/1:00", "1:30", "2:00", "2:30", "3:00"]
            self.xM = list(range(14400))[:: 30]
            self.yM = df["price"].tolist()[:: 30]
            self.xMl = self.xM[1:]  # x minute list without first nan i.e. start @ 9:31
            self.yMl = self.yM[1:]  # price minute list without first nan i.e. start @ 9:31
            self.Nl = list(range(len(self.xMl)))
            self.slope_list = [int(round(1000 * z)) for z in np.diff(self.yM)]
            self.y_min = df["price"].min()
            self.y_max = df["price"].max()
            self.y_mid = 0.5 * (self.y_min + self.y_max)
            self.pnl = 0
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

    def initPlot(self) -> (plt, plt):
        fig, ax = plt.subplots(figsize=(16, 8))
        ax.plot(self.xM, self.yM, color="lightgray", linewidth=1)
        ax.plot(self.xM, self.yM, ".", color="lightgray", markersize=3)
        for n, xpos, ypos, value in zip(self.Nl, self.xMl, self.yMl, self.slope_list):
            if abs(value) > 2:
                cl = "red" if value > 0 else "green"
                cl = "darkgray"
                ax.text(xpos - 30, ypos + 0.0005, str(abs(value)), fontsize=6, color=cl, fontweight="bold")
        ax.set_xticks(self.xtick, self.xticklabel)
        # plt.set_yticks(fontsize=8)
        if self.y_max - self.y_min <= 0.1:
            ax.set_ylim(self.y_mid - 0.05, self.y_mid + 0.05)
        plt.title(self.date, size=15)
        return fig, ax

    def closeLongPosition(self, ax: plt, n: int, xpos: int, ypos: float, sig_type: int) -> None:
        if self.plot is True:
            if sig_type == 0:
                marker = "*k"
            elif sig_type == 1:
                marker = "xk"
            else:
                raise ValueError("Wrong sig_type:" + sig_type)
            ax.plot([xpos, ], [ypos, ], marker, markersize=5)
            if ypos != self.long_start_price:
                color = "red" if ypos > self.long_start_price else "blue"
                x = self.xMl[self.long_start_pos]
                ax.plot([x, x + 0.001], [self.long_start_price, ypos], color=color, linewidth =1)
        # print("close at", "\tn:", n, "\txpos:", xpos, "\typos:", ypos, "\tslope:",self.slope_list[n], "\tpick:", self.long_peak_price)
        self.pnl += ypos - self.long_start_price
        self.update_stat_df(pos_type = "long", close_price=ypos)
        self.initDailyParam(pos_type="long")

    def closeShortPosition(self, ax: plt, n: int, xpos: int, ypos: float, sig_type: int) -> None:
        if self.plot is True:
            if sig_type == 0:
                marker = "*k"
            elif sig_type == 1:
                marker = "xk"
            else:
                raise ValueError("Wrong sig_type:" + sig_type)
            ax.plot([xpos, ], [ypos,], marker, markersize=5)
            if ypos != self.short_start_price:
                color = "red" if ypos < self.short_start_price else "blue"
                x = self.xMl[self.short_start_pos]
                ax.plot([x, x + 0.001], [self.short_start_price, 2 * self.short_start_price - ypos], color=color, linewidth =1)
        # print("close at", "\tn:", n, "\txpos:", xpos, "\typos:", ypos, "\tslope:",self.slope_list[n], "\tnadir:", self.short_nadir_price)
        self.pnl += self.short_start_price - ypos
        self.update_stat_df(pos_type="short", close_price=ypos)
        self.initDailyParam(pos_type="short")

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

    def plotSignal(self, ax: plt, n: int, xpos: int, ypos: float, sig: str, sig_type: str) -> None:
        if sig_type == "CON1":
            shift = 3
        elif sig_type == "CON3":
            shift = 4
        elif sig_type == "RAP":
            shift = 2
        else:
            raise ValueError("Wrong sig_type:" + sig_type)
        ax.plot(self.xMl[n - shift: n + 1], self.yMl[n - shift: n + 1], color="gray",linewidth=1)
        ax.text(xpos - 120, ypos - 0.03, sig_type, fontsize=6, color="gray", fontweight="bold")

    def checkCloseSignal(self, ax: plt, n: int, xpos: int, ypos: float, delta: int) -> (bool, int):
        if n > 236* 2 :
            if self.long_num > 0:
                self.closeLongPosition(ax, n, xpos, ypos, 1)
            if self.short_num > 0:
                self.closeShortPosition(ax, n, xpos, ypos, 1)
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
                    self.closeLongPosition(ax, n, xpos, ypos, 1)

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
                    self.closeShortPosition(ax, n, xpos, ypos, 1)


    def checkCloseLongSignal(self, n: int, ypos: float, delta: int) -> (bool, int):
        if n > 236:
            return True, 1
        if delta > 0:
            if round(1000 * (ypos - self.long_start_price)) >= 6:
                self.long_reach_6 = True
            if ypos > self.long_peak_price:
                self.long_peak_pos = n
                self.long_peak_price = ypos
            return False, -1

        trigger_price = self.calTriggerPrice(pos_type="long", n=n)

        if ypos < trigger_price:
            return True, 0
        else:
            return False, -1

    def checkCloseShortSignal(self, n: int, ypos: float, delta: int) -> (bool, int):
        if n > 236:
            return True, 1
        if delta < 0:
            if round(1000 * (ypos - self.short_start_price)) <= -6:
                self.short_reach_6 = True
            if ypos < self.short_nadir_price:
                self.short_nadir_pos = n
                self.short_nadir_price = ypos
            return False, 1

        trigger_price = self.calTriggerPrice(pos_type="short", n=n)

        if ypos > round(trigger_price, 3):
            return True, 0
        else:
            return False, -1

    def checkOpenSignal(self,  n: int) -> (str, str):
        if n >= 4 and n <= 234 * 2:
            sig, sig_type, h1 = self.getRapidOS(self.slope_list[n - 1: n + 1])
            if sig:
                return sig, sig_type, h1
            sig, sig_type, h1 = self.getContinuousOS(self.slope_list[n - 3: n + 1])
            if sig:
                return sig, sig_type, h1

        return None, None, 0

    def backtest(self, plot=True) -> None:
        self.plot = plot
        self.stat_df = pd.DataFrame(columns= ["sig_type", "direction", "open_price", "close_price", "pnl", "date"])
        for date in self.date_list:
            self.backtest_oneday(date)

    def backtest_oneday(self, date: str) -> None:
        self.initDailyParam(pos_type="all", date=date)
        ax = None
        if self.plot is True:
            fig, ax = self.initPlot()
        for n, xpos, ypos, delta in zip(self.Nl, self.xMl, self.yMl, self.slope_list):
            # Check close signal when we have positions
            # if self.long_num > 0:
            #     self.checkCloseSignal(ax, n, xpos, ypos, delta)
            if self.long_num > 0:
                sig, close_type = self.checkCloseLongSignal(n, ypos, delta)
                if sig is True:
                    self.closeLongPosition(ax, n, xpos, ypos, close_type)
            if self.short_num > 0:
                sig, close_type = self.checkCloseShortSignal(n, ypos, delta)
                if sig is True:
                    self.closeShortPosition(ax, n, xpos, ypos, close_type)


            if self.long_num < 1 or self.short_num < 1:
                # Check open signals when we do not have full position
                sig, sig_type, h1 = self.checkOpenSignal(n)
                if sig == 'B' and self.long_num < 1:
                    self.long_sig_type = sig_type
                    self.long_num += 1
                    self.long_start_pos = n
                    self.long_start_price = ypos
                    self.long_peak_pos = n
                    self.long_peak_price = ypos
                    self.long_h1 = h1
                    if self.plot is True:
                        self.plotSignal(ax, n, xpos, ypos, sig, sig_type)
                elif sig == 'S' and self.short_num < 1:
                    self.short_num += 1
                    self.short_sig_type = sig_type
                    self.short_start_pos = n
                    self.short_start_price = ypos
                    self.short_nadir_pos = n
                    self.short_nadir_price = ypos
                    self.short_h1 = h1
                    if self.plot is True:
                        self.plotSignal(ax, n, xpos, ypos, sig, sig_type)
        if self.plot is True:
            ax.set_xticks(self.xtick, self.xticklabel)
            re = round((math.exp( 252 * self.pnl / 5 / 10) - 1) * 100,1)
            ax.set_title(date + " PNL:" + str(round(self.pnl, 3)) + " R: " + str(re) + '%')
            fig.savefig("backtest/" + self.date + ".png")
            plt.close()
        print(date)

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
        df = pd.DataFrame()
        q = Queue()
        jobs = list()
        for i in range(0, n):
            backtest_data = "data_slice/data_slice_" + str(i) + ".csv"
            p = Process(target=backtest_slice, args = (q, backtest_data, plot))
            jobs.append(p)
            p.start()
            print("Start process", i)
        for i in range(0, n):
            df = df.append(q.get())
        for job in jobs:
            job.join()
        self.stat_df = df

    def slice(self, process_num=10):
        n = process_num
        N = len(self.date_list)
        for parent, dirnames, filenames in os.walk("data_slice/"):
            file_list = filenames
        for file in file_list:
            os.remove("data_slice/" + file)
        for i in range(0, n):
            date_scope = self.date_list[math.floor(i * (N / n)): math.floor((i + 1) * (N / n))]
            data_slice = self.all_data[self.all_data["date"].apply(lambda s: True if s in date_scope else False)]
            data_slice.to_csv("data_slice/data_slice_" + str(i) + ".csv", index=False)
        print("Slice data into", str(n), "part.")

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
    obj = Strategy()
    obj.multi_backtest(plot=True)
    obj.printStat()


