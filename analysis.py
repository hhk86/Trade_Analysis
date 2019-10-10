import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt


def plotSecondPriceCount(whole_df):
    date_list = sorted(list(set(whole_df["date"])))
    xtick = list(range(0, 14401, 1800))
    x = list(range(14400))
    xticklabel = ["9:30", "10:00", "10:30", "11:00", "11:30/1:00", "1:30", "2:00", "2:30", "3:00"]
    for date in date_list:
        df = whole_df[whole_df["date"] == date]
        df.sort_values(by="time", inplace=True)
        plt.rcParams['figure.figsize'] = (16.0, 8.0)
        fig = plt.figure()
        ax1 = fig.add_subplot(111)
        ax1.plot(x, df["price"])
        ax1.set_xticks(xtick, xticklabel)
        ax2 = ax1.twinx()
        ax2.plot(x, df["bc"] - df["sc"], "lightgray", linestyle="dotted")
        ax2.plot(x, [0,] * 14400, "darkgray", linestyle="dashed")
        ax2.set_xticks(xtick, xticklabel)
        plt.title(date)
        plt.savefig("pictures/" + date + ".png")
        plt.close()
        print(date)


def plotMinutePrice(whole_df):
    whole_df = whole_df[whole_df["time"].apply(lambda s: True if s.endswith("00") else False)]
    date_list = sorted(list(set(whole_df["date"])))
    xtick = list(range(0, 241, 30))
    x = list(range(240))
    xticklabel = ["9:30", "10:00", "10:30", "11:00", "11:30/1:00", "1:30", "2:00", "2:30", "3:00"]
    for date in date_list:
        df = whole_df[whole_df["date"] == date]
        df.sort_values(by="time", inplace=True)
        plt.rcParams['figure.figsize'] = (16.0, 8.0)
        plt.plot(x, df["price"])
        plt.xticks(xtick, xticklabel)
        plt.title(date)
        plt.savefig("pictures_minute/" + date + ".png")
        plt.close()
        print(date)


def plot30sPrice(whole_df):
    whole_df = whole_df[whole_df["time"].apply(lambda s: True if s.endswith("00") or s.endswith("30")  else False)]
    date_list = sorted(list(set(whole_df["date"])))
    xtick = list(range(0, 481, 30))
    x = list(range(480))
    xticklabel = ["9:30", "10:00", "10:30", "11:00", "11:30/1:00", "1:30", "2:00", "2:30", "3:00"]
    for date in date_list:
        df = whole_df[whole_df["date"] == date]
        df.sort_values(by="time", inplace=True)
        plt.rcParams['figure.figsize'] = (16.0, 8.0)
        plt.plot(x, df["price"])
        plt.xticks(xtick, xticklabel)
        plt.title(date)
        plt.savefig("pictures_30s/" + date + ".png")
        plt.close()
        print(date)


def plot10sPrice(whole_df):
    whole_df = whole_df[whole_df["time"].apply(lambda s: True if s.endswith('0') else False)]
    date_list = sorted(list(set(whole_df["date"])))
    xtick = list(range(0, 1441, 30))
    x = list(range(1440))
    xticklabel = ["9:30", "10:00", "10:30", "11:00", "11:30/1:00", "1:30", "2:00", "2:30", "3:00"]
    for date in date_list:
        df = whole_df[whole_df["date"] == date]
        df.sort_values(by="time", inplace=True)
        plt.rcParams['figure.figsize'] = (16.0, 8.0)
        plt.plot(x, df["price"])
        plt.xticks(xtick, xticklabel)
        plt.title(date)
        plt.savefig("pictures_10s/" + date + ".png")
        plt.close()
        print(date)


def plotMinutePriceDot(whole_df):
    whole_df = whole_df[whole_df["time"].apply(lambda s: True if s.endswith("00") else False)]
    date_list = sorted(list(set(whole_df["date"])))
    xtick = list(range(0, 241, 30))
    x = list(range(240))
    xticklabel = ["9:30", "10:00", "10:30", "11:00", "11:30/1:00", "1:30", "2:00", "2:30", "3:00"]
    for date in date_list:
        df = whole_df[whole_df["date"] == date].copy()
        df.sort_values(by="time", inplace=True)
        df["change"] = df["price"].diff()
        df["slope"] = df["change"] * 1000
        df["slope"] = df["slope"].apply(lambda x: round(x) if not pd.isna(x) else 0 )
        plt.rcParams['figure.figsize'] = (16.0, 8.0)
        plt.plot(x, df["price"], "-")
        plt.plot(x,df["price"], ".r", markersize=2)
        for xpos, ypos, value in zip(x, df["price"].tolist(), df["slope"].tolist()):
            if abs(value) > 2:
                plt.text(xpos - 1, ypos + 0.0005, str(value), fontsize=8)
        plt.xticks(xtick, xticklabel)
        plt.title(date)
        plt.savefig("pictures_minute_dot/" + date + ".png")
        plt.close()
        print(date)


def calculateSlope(whole_df, interval, save=False):
    whole_df = whole_df[whole_df["time"] >= "09:31:00"]
    print(whole_df)
    df = whole_df[whole_df["time"].apply(lambda s: True if int(s[-2:]) % interval == 0 else False)]
    df["change"] = df["price"].diff()
    df["slope"] = df["change"] / interval
    df = df.sort_values(by="slope")
    df = df[["date", "time", "price", "slope"]]
    if save is True:
        df.to_csv("slope/" + str(interval) + ".csv")


def plot30sPrice_new(whole_df):
    whole_df = whole_df[whole_df["time"].apply(lambda s: True if s.endswith("00") or s.endswith("30")  else False)]
    date_list = sorted(list(set(whole_df["date"])))
    xtick = list(range(0, 481, 30))
    x = list(range(480))
    xticklabel = ["9:30", "10:00", "10:30", "11:00", "11:30/1:00", "1:30", "2:00", "2:30", "3:00"]
    for date in date_list:
        df = whole_df[whole_df["date"] == date]
        df.sort_values(by="time", inplace=True)
        plt.rcParams['figure.figsize'] = (16.0, 8.0)
        y_max = df["price"].max()
        y_min = df["price"].min()
        y_medium = 0.5 * (y_max + y_min)
        plt.ylim(y_medium - 0.1, y_medium + 0.1)
        plt.plot(x, df["price"])
        plt.xticks(xtick, xticklabel)
        plt.title(date)
        plt.savefig("pictures_30s_new/" + date + ".png")
        plt.close()
        print(date)



if __name__ == "__main__":
    whole_df = pd.read_csv("SH600519.csv")
    # whole_df["bc"] = whole_df["bc1"] + whole_df["bc2"] + whole_df["bc3"]
    # whole_df["sc"] = whole_df["sc1"] + whole_df["sc2"] + whole_df["sc3"]
    plot30sPrice(whole_df)