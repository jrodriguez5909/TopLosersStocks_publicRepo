import pandas as pd
import yfinance as yf

from tqdm import tqdm
from requests_html import HTMLSession
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from ta.trend import sma_indicator


def force_float(elt):
    try:
        return float(elt)
    except:
        return elt


def raw_get_daily_info(site):
    """
    description:
    Grabs a provided site and transforms HTML to a pandas df

    site:
    YahooFinance! top losers website provided in the get_day_losers() function below

    other notes:
    Commented out the conversion of market cap and volume from string to float since this threw an error.
    Can grab this from the yfinance API if needed or come back to this function and fix later.
    """
    session = HTMLSession()
    response = session.get(site)

    tables = pd.read_html(response.html.raw_html)
    df = tables[0].copy()
    df.columns = tables[0].columns

    del df["52 Week Range"]
    df["% Change"] = df["% Change"].map(lambda x: float(x.strip("%")))

    #     fields_to_change = [x for x in df.columns.tolist() if "Vol" in x or x == "Market Cap"]

    #     for field in fields_to_change:
    #         if type(df[field][0]) == str:
    #             df[field] = df[field].str.strip("B").map(force_float)
    #             df[field] = df[field].map(lambda x: x if type(x) == str else x * 1e9)
    #             df[field] = df[field].map(lambda x: x if type(x) == float else force_float(x.strip("M")) * 1e6)

    session.close()
    return df


def get_day_gainers(n=None):
    df = []
    i = 0
    while True:
        try:
            df.append(raw_get_daily_info("https://finance.yahoo.com/gainers?offset={}&count=100".format(i)))
            i += 100
        except:
            break

    df = pd.concat(df).sort_values('Market Cap', ascending=False)

    if n:
        df = df.head(n)

    return df


def get_day_losers(n=None):
    """
    description:
    Grabs df from raw_get_daily_info() and provides just the top "n" losers declared by user in main.py

    n:
    Number of top losers to analyze per YahooFinance! top losers site.

    other notes:
    Commented out prior code which was meant to grab all top losers shown on site but threw errors.
    """
    df = raw_get_daily_info("https://finance.yahoo.com/losers?offset=0&count=100")

    if n:
        df = df.head(n)

    return df


#     df = []
#     i = 0
#     while True:
#         try:
#             df.append(raw_get_daily_info("https://finance.yahoo.com/losers?offset={}&count=100".format(i)))
#             i += 100
#         except:
#             break

#     df = pd.concat(df)

#     if n:
#         df = df.head(n)

#     return df


def get_stock_info(Tickers):
    # Grab fundamental stock info:
    df_fund = []

    for i, symbol in tqdm(enumerate(Tickers),
                          desc='• Grabbing fundamental metrics for ' + str(len(Tickers)) + ' stocks'):
        try:
            Ticker = yf.Ticker(symbol).info
            Sector = Ticker.get('sector')
            Industry = Ticker.get('industry')
            P2B = Ticker.get('priceToBook')
            ShortPct = Ticker.get('shortPercentOfFloat')
            # print(symbol, Sector, Industry, P2B, P2E)

            df_fund_temp = pd.DataFrame({'Symbol': [symbol],
                                         'Sector': [Sector],
                                         'Industry': [Industry],
                                         'PriceToBook': [P2B],
                                         'ShortPct': [ShortPct]
                                         })

            df_fund.append(df_fund_temp)
        except:
            KeyError
        pass

    df_fund = pd.concat(df_fund)

    # Grab technical stock info:
    df_tech = []

    for i, symbol in tqdm(enumerate(Tickers),
                          desc='• Grabbing technical metrics for ' + str(len(Tickers)) + ' stocks'):
        try:
            Ticker = yf.Ticker(symbol)
            Hist = Ticker.history(period="1y", interval="1d")

            for n in [14, 30, 50, 200]:
                # Initialize MA Indicator
                Hist['ma' + str(n)] = sma_indicator(close=Hist['Close'], window=n, fillna=False)
                # Initialize RSI Indicator
                Hist['rsi' + str(n)] = RSIIndicator(close=Hist["Close"], window=n).rsi()
                # Initialize Hi BB Indicator
                Hist['bbhi' + str(n)] = BollingerBands(close=Hist["Close"], window=n,
                                                       window_dev=2).bollinger_hband_indicator()
                # Initialize Lo BB Indicator
                Hist['bblo' + str(n)] = BollingerBands(close=Hist["Close"], window=n,
                                                       window_dev=2).bollinger_lband_indicator()

            df_tech_temp = Hist.iloc[-1:, -16:].reset_index(drop=True)
            df_tech_temp.insert(0, 'Symbol', Ticker.ticker)
            df_tech.append(df_tech_temp)
        except:
            KeyError
        pass

    df_tech = [x for x in df_tech if not x.empty]
    df_tech = pd.concat(df_tech)

    df = pd.merge(df_fund, df_tech, on='Symbol', how="left").round(2)

    return df # TODO format the dataframe to show percentages and a bunch of other things like rearranging columns to show Symbol, Name, Sector, Industry etc.


def prepare_df(df, df_financial_info):
    df = pd.merge(df, df_financial_info, on='Symbol', how="left")

    df.rename(columns={'Change':'$ Change'}, inplace=True)

    df['% Change'] = df['% Change']/100
    df['ShortPct'] = df['ShortPct']/100

    cols = df.columns.to_list()

    cols1 = cols[:2] # Symbol, Name
    cols2 = cols[9:11] # Sector, Industry
    cols3 = cols[2:9]  # Price thru PE
    cols4 = cols[11:]  # PB thru end

    cols = cols1+cols2+cols3+cols4

    df = df[cols]

    return df


# day_losers = prepare_df(day_losers, losers_financial_info)