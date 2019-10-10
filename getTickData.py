import sys
import weakref
import pandas as pd
from jinja2 import Template
from dateutil.parser import parse as dateparse
sys.path.append("D:\\Program Files\\Tinysoft\\Analyse.NET")
import TSLPy3 as ts
import datetime as dt


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
    
def download_one_year_data(ticker, year):
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
    print(data)
    # data.to_csv(ticker + '_' + year + ".csv", index=False)
    return data

if __name__ == '__main__':
    ticker = "SH600519"
    df1 = download_one_year_data(ticker, "2017")
    df2 = download_one_year_data(ticker, "2018")
    df3 = download_one_year_data(ticker, "2019")
    df = pd.concat([df1, df2, df3])
    df.to_csv(ticker + ".csv", index=None)
    print(df)