import os
import yfinance as yf
import pandas as pd
import time

def get_ticker_path():
    folder = os.path.dirname(__file__)
    
    return os.path.join(folder,'tickers.csv')


def fetch_tickers():
    urls = ['https://en.wikipedia.org/wiki/List_of_S%26P_500_companies','https://en.wikipedia.org/wiki/Nasdaq-100']

    tickers = {}

    for url in urls:
        tables = pd.read_html(url)
        df = tables[0]
        
        # Security in S&P 500
        if 'Symbol' in df.columns and 'Security' in df.columns:
            symbol_col = 'Symbol'
            name_col = 'Security'
        # Company in NASDAQ 100
        elif 'Ticker' in df.columns and 'Company' in df.columns:
            symbol_col = 'Ticker'
            name_col = 'Company'
        else:
            continue
        
        for _,row in df.iterrows():
            ticker = str(row[symbol_col]).strip()
            name = str(row[name_col]).strip()
            if ticker and name and ticker!='nan' and name!='nan':
                tickers[ticker] = name
        time.sleep(1) # avoid request timeout

    return tickers


def verify_ticker(ticker):
    # Check if valid and active
    stock = yf.Ticker(ticker)
    info = stock.info

    if info and 'regularMarketPrice' in info and info['regularMarketPrice'] is not None:
        return True
    return False


if __name__ == "__main__":
    all_tickers = fetch_tickers()
    final = {}

    for ticker,name in all_tickers.items():
        if verify_ticker(ticker):
            final[ticker] = name
        time.sleep(0.1) # avoid request timeout

    file_path = get_ticker_path()
    df = pd.DataFrame(list(final.items()),columns = ['Symbol','Name'])
    df.to_csv(file_path,index = False)
    
    print("Saved ",len(final), " tickers to .csv file.")