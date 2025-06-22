import numpy as np
from scipy.optimize import brentq
import yfinance as yf

from pricing import black_scholes_price


def historical_volatility(prices):
    prices_ratio = prices[1:]/prices[:-1]
    returns = np.log(prices_ratio)
    daily_vol = np.std(returns)
    annual_vol =daily_vol*np.sqrt(252)

    return round(annual_vol,4)


def live_historical_volatility(ticker,period = "6mo"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    close_prices = data["Close"].values
    
    return historical_volatility(close_prices)


def implied_volatility(S,K,T,r,market_price,option_type = "call"):
    def fun(sigma):
        return black_scholes_price(S,K,T,r,sigma,option_type) - market_price

    try:
        iv = brentq(fun,1e-6,5)
        return round(iv,4)
    except ValueError:
        return None
    

if __name__ == "__main__":
    from data import get_spot_price,get_expiries,get_time_to_expiry,get_option_chain
    
    arr = np.array([100,101,102,103,99,98,105])
    print("Dummy HV: ",historical_volatility(arr))

    ticker = "AAPL"
    print("Live HV: ",live_historical_volatility(ticker))

    S = 100
    K = 105
    T = 30/365
    r = 0.05
    market_price = 2.5

    print("Call IV: ",implied_volatility(S,K,T,r,market_price,"call"))
    
    print("Put IV: ",implied_volatility(S,K,T,r,market_price+5,"put"))

    spot_price = get_spot_price(ticker)
    expiries = get_expiries(ticker)
        
    expiry = expiries[0]
    chain = get_option_chain(ticker,expiry)["calls"]

    call_option = chain[chain['strike']>=spot_price].iloc[0]

    K = call_option['strike']
    market_price = call_option['lastPrice']
    T = get_time_to_expiry(expiry)

    iv = implied_volatility(spot_price,K,T,r,market_price,option_type="call")

    print("Ticker:",ticker,"\nSpot Price: ",spot_price,"\nStrike Price: ",K,"\nExpiry: ",expiry,"\nPrice: ",market_price,"\nIV: ",iv)



