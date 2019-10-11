import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt
import math

if __name__ == "__main__":
    from multiprocessing import Process, Queue
    import sys
    import os
    import pandas as pd
    from jinja2 import Template
    from dateutil.parser import parse as dateparse
    from hyperopt import fmin, tpe, hp
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

    def ticks(self, code, start_date, end_date):
        ts_template = Template('''setsysparam(pn_stock(),'SH510500');
                                  begT:= StrToDate('{{start_date}}');
                                  endT:= StrToDate('{{end_date}}');
                                  setsysparam(pn_cycle(),cy_1s());
                                  setsysparam(pn_rate(),0);
                                  setsysparam(pn_RateDay(),rd_lastday);
                                  r:= select ["StockID"] as 'ticker', datetimetostr(["date"]) as "time", ["price"],
                                             ["buy1"], ["bc1"], ["buy2"],["bc2"], ["buy3"],["bc3"],
                                             ["sale1"],["sc1"], ["sale2"],["sc2"], ["sale3"],["sc3"]
                                      from markettable datekey begT to endT of "{{code}}" end;
                                  return r;''')
        ts_sql = ts_template.render(start_date=dateparse(start_date).strftime('%Y-%m-%d'),
                                    end_date=dateparse(end_date).strftime('%Y-%m-%d'),
                                    code=code)
        fail, data, _ = ts.RemoteExecute(ts_sql, {})

        def gbk_decode(strlike):
            if isinstance(strlike, (str, bytes)):
                strlike = strlike.decode('gbk')
            return strlike

        def bytes_to_unicode(record):
            return dict(map(lambda s: (gbk_decode(s[0]), gbk_decode(s[1])), record.items()))

        if not fail:
            unicode_data = list(map(bytes_to_unicode, data))
            return pd.DataFrame(unicode_data).set_index(['time', 'ticker'])
        else:
            raise Exception("Error when execute tsl")


def backtest_slice(q, name, i, arg_dict):
    obj = Strategy(name, False)
    obj.defaultParam(arg_dict)
    obj.backtest(plot=True)
    stat_df = obj.stat_df
    q.put(stat_df)
    # print("Process end", i)



class Strategy():
    def __init__(self, ticker, fake=False) -> None:
        self.ticker = ticker
        if fake is True:
            return
        try:
            self.all_data = pd.read_csv("E:\\tickdata\\" + ticker + ".csv")
        except FileNotFoundError:
            if ticker.startswith("E:\\data_slice"):
                path = ticker
                self.all_data = pd.read_csv(path)
            else:
                print("The tick data of", ticker, "does not exit.\nAutomatically downloading data...\nIt will take about 15 minutes.")
                self.download_tickdata(ticker)
                self.all_data = pd.read_csv("E:\\tickdata\\" + ticker + ".csv")
        self.all_data["price"] = self.all_data["price"].apply(lambda x: round(x, 3))
        self.all_data = self.all_data[["date", "time", "price"]]
        self.date_list = sorted(list(set(self.all_data["date"])))
        x = list(range(14400))
        self.xM = x[:: 30]
        self.xtick = list(range(0, 14401, 1800))
        self.xticklabel = ["9:30", "10:00", "10:30", "11:00", "11:30/1:00", "1:30", "2:00", "2:30", "3:00"]
        self.plot = True
        # self.defaultParam()

    def defaultParam(self, arg_dict=None) -> None:
        if arg_dict is None:
            print("arg_dict is None")
        elif len(arg_dict) == 0:
            print("arg_dict is empty")
        else:
            self.multiplier = arg_dict["multiplier"]

        ################ Minute data
        # self.P_NS_1 = 3
        # self.P_NS_2 = 6
        # self.P_NS_3 = 3
        # self.P_NS_4 = 3
        # self.P_NS_5 = 4
        # self.P_CON_1 = 3
        # self.P_CON_2 = 6
        # self.P_CON_3 = 3
        # self.P_CON_4 = 3
        # self.P_CON_5 = 4
        # self.P_RAPB_1 = 12
        # self.P_RAPS_1 = 12
        # self.P_W_1 = 2 / 3
        # self.P_W_2 = 3 / 4
        # self.P_L_1 = 15
        # self.P_L_2 = 30
        # self.P_L_3 = 12
        # self.P_h1_W = 0
        # self.P_R_ADJ = 0


        # self.P_NS_1 = 4
        # self.P_NS_2 = 6
        # self.P_NS_3 = 3
        # self.P_NS_4 = 3
        # self.P_NS_5 = 4
        # self.P_CON_1 = 3
        # self.P_CON_2 = 6
        # self.P_CON_3 = 3
        # self.P_CON_4 = 4
        # self.P_CON_5 = 4
        # self.P_RAPB_1 = 9
        # self.P_RAPS_1 = 13
        # self.P_W_1 = 0.7
        # self.P_W_2 = 0.8
        # self.P_L_1 = 15
        # self.P_L_2 = 30
        # self.P_L_3 = 12
        # self.P_h1_W = 0
        # self.P_R_ADJ = 0
        # # self.switch= [True, True,    False, False, False, False, True, True,    True,True, False,True,True, True]
        # self.switch= [True, True,    False, False, False, False, True, False,    False, False, False,True,True, False]

        ###################### 30S data
        # self.P_NS_1 = 3
        # self.P_NS_2 = 5
        # self.P_NS_3 = 3
        # self.P_NS_4 = 3
        # self.P_NS_5 = 3
        # self.P_CON_1 = 3
        # self.P_CON_2 = 5
        # self.P_CON_3 = 3
        # self.P_CON_4 = 3
        # self.P_CON_5 = 3
        # self.P_RAPB_1 = 9
        # self.P_RAPS_1 = 9
        # self.P_W_1 = 0.6
        # self.P_W_2 = 0.8
        # self.P_L_1 = 15
        # self.P_L_2 = 30
        # self.P_L_3 = 12
        # self.P_h1_W = 0
        # self.P_R_ADJ = 0
        # self.switch = [True, True,   True, True, True, True, True, True,       True, True, True, True, True, True]
        self.P_NS_1 = int(round(3 * self.multiplier))
        self.P_NS_2 = int(round(6 * self.multiplier))
        self.P_NS_3 = int(round(3 * self.multiplier))
        self.P_NS_4 = int(round(4 * self.multiplier))
        self.P_NS_5 = int(round(4 * self.multiplier))
        self.P_CON_1 = int(round(2 * self.multiplier)) # 3 is a little bit better than 2, but its frequency is only 1/3 of P_CON_2 =3
        self.P_CON_2 = int(round(6 * self.multiplier))
        self.P_CON_3 = int(round(3 * self.multiplier))
        self.P_CON_4 = int(round(2 * self.multiplier))
        self.P_CON_5 = int(round(5 * self.multiplier))
        self.P_RAPB_1 = int(round(9 * self.multiplier))
        self.P_RAPS_1 = int(round(9 * self.multiplier))
        self.P_W_1 = 0.6
        self.P_W_2 = 0.8
        self.P_L_1 = int(round(15 * self.multiplier))
        self.P_L_2 = int(round(30 * self.multiplier))
        self.P_L_3 = int(round(12 * self.multiplier))
        self.P_h1_W = 0
        self.P_R_ADJ = 0
        # self.switch = [True, False,   False, False, False, False, False, False,  True, True, False, False, False, True] # best parameters when only use morning data
        self.switch = [True,] * 14
        # self.switch = [True, False,    False, False, False, False, False, False,   True, True, False, False, False, False]

    def get_oneday_data(self, date: str) -> pd.DataFrame:
        df = self.all_data[self.all_data["date"] == date].copy()
        if df.shape[0] < 14400:
            raise ValueError("Data is not complete or data is missing on " + date)
        return self.all_data[self.all_data["date"] == date].copy()

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
        pb1 = self.P_RAPB_1
        ps1 = self.P_RAPS_1
        switch = self.switch

        z1, z2 = ls
        h1 = z1 + z2
        if switch[0] and h1 >= pb1:
            return 'B', "RAP", h1
        if switch[1] and h1 <= -ps1:
            return 'S', "RAP", h1
        else:
            return None, None, 0

    def getNStyleOS(self, ls: list) -> (str, str, int):
        '''
        Get N-style Open Signal

        ls: list, list of slope: [ -3 min, -2 min, -1 min, 0 min]

        Type 1 condition: (Assume Open Long)
                   1. x1 = x2 = x3 = 1
                   2. d1 >= 6, h1 >= 3, d2 < 0
                   3. abs(d2) <= 1 / 2 * d1
                   4. h1 >= 2 * abs(d2)

        Type 2 condition: (Assume Open Long)
                   1. x1 = 2, x2 = x3 = 1
                   2. d1 >= 6, h1 >= 3, d2 < 0
                   3. abs(d2) <= 1 / 2 * d1
                   4. h1 >= 2 * abs(d2)

        :return: (str, str, int). first str: 1 for open long, -1 for open short, 0 for no signal;
                second str: signal type; int: h2
        '''
        p1 = self.P_NS_1
        p2 = self.P_NS_2
        p3 = self.P_NS_3
        p4 = self.P_NS_4
        p5 = self.P_NS_5
        switch = self.switch

        z1, z2, z3, z4 = ls
        # Type 1
        d1, d2, h1 = z2, z3, z4
        if switch[2] and d1 >= p1 and d2 < 0 and h1 >= p1  and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
            return 'B', "NS1", h1
        if switch[3] and d1 <= - p1  and d2 > 0 and h1 <= - p1  and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
            return 'S', "NS1", h1
        # Type2 - should be closed
        d1, d2, h1 = z1 + z2, z3, z4
        if switch[4] and d1 >= p2 and d2 < 0 and h1 >= p3 and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
            return 'B', "NS2", h1
        if switch[5] and d1 <= -p2 and d2 > 0 and h1 <= -p3 and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
            return 'S', "NS2", h1
        # Type3
        d1, d2, h1 = z1, z2 + z3, z4
        # if d1 >= p4 and d2 < 0 and h1 >= p5 and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
        #     return 'B', "NS3", h1
        # if d1 <= -p4 and d2 > 0 and h1 <= -p5 and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
        #     return 'S', "NS3", h1
        if switch[6] and d1 >= p4 and d2 < 0 and h1 >= p5 and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
            return 'B', "NS3", h1
        if switch[7] and d1 <= -p5 and d2 > 0 and h1 <= -p4 and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
            return 'S', "NS3", h1

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

        Type 2 condition: (Assume Open Long)
                   1. x1 = 2, x2 = x3 = 1
                   2. d1 >= 6, h1 >= 3, d2 < 0
                   3. abs(d2) <= 1 / 2 * d1
                   4. h1 >= 2 * abs(d2)

        :return: (str, str, int). first str: 1 for open long, -1 for open short, 0 for no signal;
                second str: signal type; int: h2
        '''
        p1 = self.P_CON_1
        p2 = self.P_CON_2
        p3 = self.P_CON_3
        p4 = self.P_CON_4
        p5 = self.P_CON_5
        switch = self.switch

        z1, z2, z3, z4 = ls
        # Type 1
        d1, d2, h1 = z2, z3, z4
        if switch[8] and d1 >= p1 and d2 >= 0 and h1 >= p1 and abs(h1) >= abs(d2) + 2:
            return 'B', "CON1", h1
        if switch[9] and d1 <= -p1 and d2 <= 0  and h1 <= -p1 and abs(h1) >= abs(d2) + 2:
            return 'S', "CON1", h1
        # Type2
        d1, d2, h1 = z1 + z2, z3, z4
        if switch[10] and d1 >= p2 and d2 >= 0  and h1 >= p3 and abs(h1) >= abs(d2) + 2:
            return 'B', "CON2", h1
        if switch[11] and d1 <= -p2 and d2 <= 0 and h1 <= -p3 and abs(h1) >= abs(d2) + 2:
            return 'S', "CON2", h1
        # Type3
        d1, d2, h1 = z1, z2 + z3, z4
        if switch[12] and d1 >= p4 and d2 >= 0  and h1 >= p5 and abs(h1) >= abs(d2) + 2:
            return 'B', "CON3", h1
        if switch[13] and d1 <= -p4 and d2 <= 0 and h1 <= -p5 and abs(h1) >= abs(d2) + 2:
            return 'S', "CON3", h1


        else:
            return None, None, 0

    def initDailyParam(self, pos_type="all", date=None) -> None:
        if pos_type == "all":
            self.date = date
            df = self.get_oneday_data(self.date)
            df.sort_values(by="time", inplace=True)
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
            start_shift_2 = self.yMl[self.long_start_pos - 2]
            start_shift_3 = self.yMl[self.long_start_pos - 3]
            time_pass = n - self.long_start_pos
            h1 = self.long_h1
            sign = 1
        else:
            start = self.short_start_price
            point = self.short_nadir_price
            sig_type = self.short_sig_type
            reach_6 = self.short_reach_6
            start_shift_1 = self.yMl[self.short_start_pos - 1]
            start_shift_2 = self.yMl[self.short_start_pos - 2]
            start_shift_3 = self.yMl[self.short_start_pos - 3]
            time_pass = n - self.short_start_pos
            h1 = self.short_h1
            sign = -1
        H1 = round(1000 * (point - start))
        trigger_price = start


        w1 = self.P_W_1
        w2 = self.P_W_2
        l1 = self.P_L_1
        l2 = self.P_L_2
        l3 = self.P_L_3
        h1w = self.P_h1_W
        adjust = self.P_R_ADJ

        if  not reach_6 and sig_type == "RAP":
            if time_pass <= 2:
                trigger_price = start - 0.006 * sign
            else:
                trigger_price = start + 0.001 * adjust * sign
        elif not reach_6:
            if abs(h1) > 8:
                trigger_price = start - 2 / 3 * h1 / 1000 * sign
            elif sig_type == "NS1":
                trigger_price = start_shift_2
            elif sig_type == "NS2" or sig_type == "NS3":
                trigger_price = start_shift_3
            elif sig_type == "CON1" or sig_type == "CON2" or sig_type == "CON3":
                trigger_price = start_shift_1
        else:
            if abs(H1) <= l1:
                trigger_price = start + w1 * (H1 + h1w * h1) / 1000
            elif abs(H1) <= l2:
                trigger_price = start + w2 *  (H1 + h1w * h1)  / 1000 - 0.001 * sign
            else:
                trigger_price = point - 0.001 * l3 * sign

        return round(trigger_price, 3)

    def plotSignal(self, ax: plt, n: int, xpos: int, ypos: float, sig: str, sig_type: str) -> None:
        if sig_type == "NS1":
            color = "deepskyblue"
            shift = 3
        elif sig_type == "NS2":
            color = "deepskyblue"
            shift = 4
        elif sig_type == "NS3":
            color = "deepskyblue"
            shift = 4
        elif sig_type == "CON1":
            color = "goldenrod"
            shift = 3
        elif sig_type == "CON2":
            color = "goldenrod"
            shift = 4
        elif sig_type == "CON3":
            color = "goldenrod"
            shift = 4
        elif sig_type == "RAP":
            color = "violet"
            shift = 2
        else:
            raise ValueError("Wrong sig_type:" + sig_type)
        color = "gray"
        ax.plot(self.xMl[n - shift: n + 1], self.yMl[n - shift: n + 1], color=color,linewidth=1)
        # ax.text(xpos - 30, ypos - 0.004, sig, fontsize=12, color=color, fontweight="bold")
        ax.text(xpos - 120, ypos - 0.03, sig_type, fontsize=6, color=color, fontweight="bold")

    def checkCloseLongSignal(self, n: int, ypos: float, delta: int) -> (bool, int):
        if n > 236 * 2:
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
        if n > 236 * 2:
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
            sig, sig_type, h1 = self.getNStyleOS(self.slope_list[n - 3: n + 1])
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
        # print(date)

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

    def calibrate_old(self) -> None:
        # # NS1
        # for x in range(2, 5):
        #     self.multi_backtest(x, 0, 0)
        #     obj.printStat("P_NS_1_is_" +  str(x))
        # # NS2
        # for (x, y) in zip([4, 5, 6, 4, 5, 6], [3, 3, 3, 4, 4, 4]):
        #     self.multi_backtest(x, y, 0)
        #     obj.printStat("P_NS_2_is_" +  str(x) + "_P_NS_3_is_" + str(y))
        # #NS3
        # for (x, y) in zip([2, 3, 3, 4, 4], [3, 3, 4, 3, 4]):
        #     self.multi_backtest(x, y, 0)
        #     obj.printStat("P_NS_4_is_" +  str(x) + "_P_NS_5_is_" + str(y))
        # # CON1
        # for x in [2, 3, 4]:
        #     self.multi_backtest(x, 0, 0)
        #     obj.printStat("P_CON_1_is_" +  str(x))
        # # CON2
        # for (x, y) in zip([4, 5, 6, 4, 5, 6], [3, 3, 3, 4, 4, 4]):
        #     self.multi_backtest(x, y, 0)
        #     obj.printStat("P_CON_2_is_" +  str(x) + "_P_CON_3_is_" + str(y))
        # #CON3
        # for (x, y) in zip([2, 3, 3, 4, 4], [3, 3, 4, 3, 4]):
        #     self.multi_backtest(x, y, 0)
        #     obj.printStat("P_CON_4_is_" +  str(x) + "_P_CON_5_is_" + str(y))
        # #RAPB
        # for x in range(6, 13):
        #     self.multi_backtest(x, 0, 0)
        #     obj.printStat("P_RAPB_1_is_" +  str(x))
        # #RAPS
        # for x in range(4, 6):
        #     self.multi_backtest(x, 0, 0)
        #     obj.printStat("P_RAPS_1_is_" +  str(x))
        # self.defaultParam()
        # self.P_RAPB_1 = 9
        # self.multi_backtest(plot=False)
        # obj.printStat("P_RAPB_1_is_9")
        # self.defaultParam()
        # self.P_RAPB_1 = 10
        # self.multi_backtest(plot=False)
        # obj.printStat("P_RAPB_1_is_10")
        # self.defaultParam()
        # self.P_RAPB_1 = 11
        # self.multi_backtest(plot=False)
        # obj.printStat("P_RAPB_1_is_11")
        # self.defaultParam()
        # self.P_RAPB_1 = 13
        # self.multi_backtest(plot=False)
        # obj.printStat("P_RAPB_1_is_13")
        # self.defaultParam()
        # self.P_RAPS_1 = 7
        # self.multi_backtest(plot=False)
        # obj.printStat("P_RAPS_1_is_7")
        # self.defaultParam()
        # self.P_RAPS_1 = 8
        # self.multi_backtest(plot=False)
        # obj.printStat("P_RAPS_1_is_8")
        # self.defaultParam()
        # self.P_RAPS_1 = 9
        # self.multi_backtest(plot=False)
        # obj.printStat("P_RAPS_1_is_9")
        # self.defaultParam()
        # self.P_RAPS_1 = 10
        # self.multi_backtest(plot=False)
        # obj.printStat("P_RAPS_1_is_10")
        # self.defaultParam()
        # self.P_RAPS_1 = 11
        # self.multi_backtest(plot=False)
        # obj.printStat("P_RAPS_1_is_11")
        # self.defaultParam()
        # self.P_RAPS_1 = 13
        # self.multi_backtest(plot=False)
        # obj.printStat("P_RAPS_1_is_13")



        ################ Hyper Parameters #######################
        # self.defaultParam()
        # self.P_R_ADJ = 2
        # self.multi_backtest(plot=False)
        # obj.printStat("P_R_ADJ_is_2")
        # self.defaultParam()
        # self.P_L_3 = 8
        # self.multi_backtest(plot=False)
        # obj.printStat("P_L3_is_8")
        # self.defaultParam()
        # self.P_L_3 = 10
        # self.multi_backtest(plot=False)
        # obj.printStat("P_L3_is_10")


        # for (P_W_1, P_W_2) in zip([0.55, 0.55, 0.6, 0.6, 0.7, 0.7, 0.75, 0.75], [0.7, 0.75, 0.75, 0.8, 0.85, 0.8, 0.85]):
        #     self.multi_backtest(P_W_1, P_W_2, 1)
        #     obj.printStat("X_" + str(P_W_1) + "Y_" + str(P_W_2))
        pass


    def multi_backtest(self, arg_dict=None):
        if not os.path.exists("E:\\data_slice\\" + self.ticker +"\\data_slice_9.csv"):
            self.slice()
        df = pd.DataFrame()
        q = Queue()
        jobs = list()
        for i in range(0, 10):
            ticker = "E:\\data_slice\\" + self.ticker +"\\data_slice_" + str(i) + ".csv"
            p = Process(target=backtest_slice, args = (q, ticker, i, arg_dict))
            jobs.append(p)
            p.start()
            # print("Start process" + str(i))
        for i in range(0, 10):
            df = df.append(q.get())
        for job in jobs:
            job.join()
        self.stat_df = df


    def slice(self, process_num=10):
        n = process_num
        N = len(self.date_list)
        try:
            os.removedirs("E:\\data_slice\\" + self.ticker)
            print("Re-writing the data slice of", self.ticker)
        except:
            print("Writing new data slice of", self.ticker)
        os.makedirs("E:\\data_slice\\" + self.ticker )
        # for parent, dirnames, filenames in os.walk("E:\\data_slice\\" + ticker):
        #     file_list = filenames
        # for file in file_list:
        #     os.remove("E:\\data_slice\\" + ticker +'\\' + file)
        for i in range(0, n):
            date_scope = self.date_list[math.floor(i * (N / n)): math.floor((i + 1) * (N / n))]
            data_slice = self.all_data[self.all_data["date"].apply(lambda s: True if s in date_scope else False)]
            data_slice.to_csv("E:\\data_slice\\" + self.ticker + "\\data_slice_" + str(i) + ".csv", index=False)
        print("Slice data into " + str(n) + " part.\n Save data slice to: " + "E:\\data_slice\\" + self.ticker)


    def makeHyperParam(self):
        std = self.all_data.groupby("date").std()["price"].mean()
        self.multiplier_base = std / 0.0214


    def download_one_year_data(self, ticker, year):
        start_date = year + "0101"
        if year == "2019":
            end_date = "20190910"
        else:
            end_date = year + "1231"
        with TsTickData() as obj:
            data = obj.ticks(code=ticker, start_date=start_date, end_date=end_date)
        pd.set_option("display.max_columns", None)
        data["datetime"] = data.index
        data["datetime"] = data["datetime"].apply(lambda t: dt.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S"))
        data["date"] = data["datetime"].apply(lambda datetime: datetime.date())
        data["time"] = data["datetime"].apply(lambda datetime: datetime.time())
        data.index = data["datetime"]
        # data = data[["date", "time", "price", 'buy1', 'buy2', 'buy3', 'sale1', 'sale2',
        #              'sale3', 'bc1', 'bc2', 'bc3', 'sc1', 'sc2', 'sc3']]
        data = data[["date", "time", "price"]]
        # data.to_csv(ticker + '_' + year + ".csv", index=False)
        return data

    def download_tickdata(self, ticker):
        df1 = self.download_one_year_data(ticker, "2017")
        df2 = self.download_one_year_data(ticker, "2018")
        df3 = self.download_one_year_data(ticker, "2019")
        df = pd.concat([df1, df2, df3])
        df.to_csv("E:\\tickdata\\" + ticker + ".csv", index=None)
        print("Data saved to: " + "E:\\tickdata\\" + ticker + ".csv")

    def opt_func(self, arg_dict):
        self.multi_backtest(arg_dict)
        return - self.printStat()["sum"].sum()

    def calibrate(self):
        self.makeHyperParam()
        arg_dict  = {"multiplier":hp.uniform("multiplier", self.multiplier_base, 5 * self.multiplier_base), "eta":hp.uniform("eta",0.05,0.5)}
        best = fmin(self.opt_func, arg_dict, algo=tpe.suggest, max_evals=5)
        return best




if __name__ == "__main__":
    obj = Strategy("SH510500", fake=False)
    print(obj.calibrate())
    # obj.multi_backtest()
    # obj.printStat()


