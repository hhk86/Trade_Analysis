import pandas as pd
import numpy as np
import datetime as dt
import matplotlib.pyplot as plt


def plotSignal(whole_df):
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
        y_min = df["price"].min()
        y_max = df["price"].max()
        y_mid = 0.5 * (y_min + y_max)
        plt.rcParams['figure.figsize'] = (16.0, 8.0)
        # plt.plot(x, df["price"], color = "darkgray", linewidth=0.5)
        plt.plot(xM, yM, color = "lightgray", linewidth=1)
        plt.plot(xM, yM, ".", color="lightgray", markersize=3)
        xMl = xM[1:]
        yMl = yM[1:]
        Nls = list(range(len(xM)))
        for n, xpos, ypos, value in zip(Nls[: -1], xMl, yMl, slope_list):
            if abs(value) > 2:
                cl = "red" if value > 0 else "green"
                plt.text(xpos - 30, ypos + 0.0005, str(abs(value)), fontsize=6, color=cl, fontweight="bold")


            if n >= 4:
                ### NStyleOS part ###
                sig, sig_type = getNStyleOS(slope_list[n - 3: n + 1])
                if sig:
                    shift = 3 if sig_type == "NS1" else 4
                    plt.plot(xMl[n - shift: n + 1], yMl[n - shift: n + 1], color="orangered", linewidth=2)
                    plt.text(xpos - 30, ypos - 0.004, sig, fontsize=12, color="orangered", fontweight="bold")
                    plt.text(xpos - 120, ypos - 0.03, sig_type, fontsize=6, color="orangered", fontweight="bold")


                ### ContinousOS part ###
                sig, sig_type = getContinousOS(slope_list[n - 3: n + 1])
                if sig:
                    shift = 3 if sig_type == "CON1" else 4
                    plt.plot(xMl[n - shift: n + 1], yMl[n - shift: n + 1] , color="gold", linewidth=2)
                    plt.text(xpos - 30, ypos - 0.004, sig, fontsize=12, color="gold", fontweight="bold")
                    plt.text(xpos - 120, ypos - 0.03, sig_type, fontsize=6, color="gold", fontweight="bold")

            if n >= 2:
                ### RapidOS part ###
                sig, sig_type = getRapidOS(slope_list[n - 1: n + 1])
                if sig:
                    plt.plot(xMl[n - 1: n + 1], yMl[n - 1: n + 1], color="violet", linewidth=2)
                    plt.text(xpos - 30, ypos - 0.004, sig, fontsize=12, color="violet", fontweight="bold")
                    plt.text(xpos - 120, ypos - 0.03, sig_type, fontsize=6, color="violet", fontweight="bold")

        plt.xticks(xtick, xticklabel, size=8)
        plt.yticks(size=8)
        if y_max - y_min <= 0.1:
            plt.ylim(y_mid - 0.05, y_mid+ 0.05)
        plt.title(date, size=15)
        plt.savefig("signal/" + date + ".png")
        plt.close()
        print(date)


def getNStyleOS(ls: list) -> (str, str):
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

    :return: str, str. first str: 1 for open long, -1 for open short, 0 for no signal; second str: signal type
    '''


    z1, z2, z3, z4 = ls
    #Type 1
    d1, d2, h1 = z2, z3, z4
    if d1 >= 3 and d2 < 0 and h1 >= 3 and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
        return 'B', "NS1"
    if d1 <= -3 and d2 > 0 and h1 <= -3 and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
        return 'S', "NS1"
    #Type2
    d1, d2, h1 = z1 + z2, z3, z4
    if d1 >= 6 and d2 < 0 and h1 >= 3 and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
        return 'B', "NS2"
    if d1 <= -6 and d2 > 0 and h1 <= -3 and abs(d2) <= abs(d1) / 2 and abs(h1) >= 2 * abs(d2):
        return 'S', "NS2"
    else:
        return None, None


def getContinousOS(ls):
    '''
    Get Continous Open Signal

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

    :return: str, str. first str: 1 for open long, -1 for open short, 0 for no signal; second str: signal type
    '''


    z1, z2, z3, z4 = ls
    #Type 1
    d1, d2, h1 = z2, z3, z4
    if d1 >= 3 and d2 >= 0 and d2 <= 2 and h1 >= 3 and abs(h1) >= abs(d2) + 2:
        return 'B', "CON1"
    if d1 <= -3 and d2 <= 0 and d2 >= -2 and h1 <= -3 and abs(h1) >= abs(d2) + 2:
        return 'S', "CON1"
    #Type2
    d1, d2, h1 = z1 + z2, z3, z4
    if d1 >= 6 and d2 >= 0 and d2 <= 2 and h1 >= 3 and abs(h1) >= abs(d2) + 2:
        return 'B', "CON2"
    if d1 <= -6 and d2 <= 0 and d2 >= -2 and h1 <= -3 and abs(h1) >= abs(d2) + 2:
        return 'S', "CON2"
    else:
        return None, None


def getRapidOS(ls):
    '''
    Get Rapid Open Signal

    ls: list, list of slope: [ -1 min, 0 min]

    condition: (Assume Open Long)
               1. x1 = 2
               2. h1 >= 12
    :return: str, str. first str: 1 for open long, -1 for open short, 0 for no signal; second str: signal type
    '''
    z1, z2 = ls
    h1 = z1 + z2
    if h1 >= 12:
        return 'B', "RAP"
    if h1 <= -12:
        return 'S', "RAP"
    else:
        return None, None





if __name__ == "__main__":
    whole_df = pd.read_csv("SH510500_2019.csv")
    # whole_df = pd.read_csv("SH510500.csv")
    whole_df["bc"] = whole_df["bc1"] + whole_df["bc2"] + whole_df["bc3"]
    whole_df["sc"] = whole_df["sc1"] + whole_df["sc2"] + whole_df["sc3"]
    # plotMinutePriceDot(whole_df)
    plotSignal(whole_df)