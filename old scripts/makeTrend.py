import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt


def plotSecondPrice(whole_df):
    date_list = sorted(list(set(whole_df["date"])))
    xtick = list(range(0, 14401, 1800))
    x = list(range(14400))
    xticklabel = ["9:30", "10:00", "10:30", "11:00", "11:30/1:00", "1:30", "2:00", "2:30", "3:00"]
    xM = x[ : : 60]
    for date in date_list:
        df = whole_df[whole_df["date"] == date].copy()
        df.sort_values(by="time", inplace=True)
        yM = df["price"].tolist()[ : : 60]
        slope_list = [int(round(1000 * z)) for z in np.diff(yM) ]
        y_medium = df["price"].median()
        plt.rcParams['figure.figsize'] = (100.0, 40.0)
        plt.plot(x, df["price"], color = "darkgray", linewidth=0.5)
        plt.plot(xM, yM, color = "dodgerblue", linewidth=2)
        plt.plot(xM, yM, ".b", markersize=8)
        for xpos, ypos, value in zip(xM[1:], yM[1:], slope_list):
            if abs(value) > 2:
                if value > 0:
                    cl = "red"
                else:
                    cl = "green"
                plt.text(xpos - 25, ypos + 0.0005, str(abs(value)), fontsize=30, color=cl, fontweight="bold")
        plt.xticks(xtick, xticklabel, size=40)
        plt.yticks(size=40)
        plt.ylim(y_medium - 0.1, y_medium + 0.1)
        plt.title(date, size=60)
        plt.savefig("trend/" + date + ".png")
        plt.close()
        print(date)



if __name__ == "__main__":
    # whole_df = pd.read_csv("SH510500_2019.csv")
    whole_df = pd.read_csv("SH510500.csv")
    whole_df["bc"] = whole_df["bc1"] + whole_df["bc2"] + whole_df["bc3"]
    whole_df["sc"] = whole_df["sc1"] + whole_df["sc2"] + whole_df["sc3"]
    # plotMinutePriceDot(whole_df)
    plotSecondPrice(whole_df)