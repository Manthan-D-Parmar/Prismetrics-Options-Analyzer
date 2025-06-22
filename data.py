import os
import pandas as pd
import yfinance as yf
from datetime import datetime 
import streamlit as st
from volatility import live_historical_volatility,implied_volatility

@st.cache_data(ttl=3600)
def get_tickers():
    folder = os.path.dirname(__file__)
    file_path = os.path.join(folder,'tickers.csv')

    df = pd.read_csv(file_path)

    return dict(zip(df['Symbol'],df['Name']))


@st.cache_data(ttl=3600)
def get_ticker_info(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info

    return {
        'name': info.get('longName', 'N/A'),
        'sector': info.get('sector', 'N/A'),
        'industry': info.get('industry', 'N/A'),
        'market_cap': info.get('marketCap', 'N/A'),
        'pe_ratio': info.get('forwardPE', 'N/A'),
        'dividend_yield': info.get('dividendYield', 'N/A'),
        'beta': info.get('beta', 'N/A'),
        'description': info.get('longBusinessSummary', 'N/A')
    }


@st.cache_data(ttl=3600)
def get_spot_price(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period='1d')

    if not data.empty:
        return data['Close'].iloc[-1]
    return None


@st.cache_data(ttl=3600)
def get_expiries(ticker):
    try:
        stock = yf.Ticker(ticker)
        expiries = stock.options
        valid = []
        for expiry in expiries:
            if datetime.strptime(expiry, '%Y-%m-%d') > datetime.now():
                valid.append(expiry)
        return valid
    except Exception as e:
        print(f"Error fetching expiries for {ticker}: {str(e)}")
        return []


@st.cache_data(ttl=3600)
def get_option_chain(ticker, expiry):
    stock = yf.Ticker(ticker)
    chain = stock.option_chain(expiry)

    call_df = pd.DataFrame(chain.calls)
    put_df = pd.DataFrame(chain.puts)

    return {'calls':call_df,'puts':put_df}


@st.cache_data(ttl=3600)
def get_valid(ticker, expiry, r=0.05):
    chain = get_option_chain(ticker, expiry)
    spot = get_spot_price(ticker)

    if chain is None or spot is None:
        return None, None, None

    call_strikes = chain['calls']['strike'].unique()
    put_strikes = chain['puts']['strike'].unique()
    all_strikes = sorted(set(call_strikes) | set(put_strikes))

    final_valid_strike = []
    call_ivs = []
    put_ivs = []

    for strike in all_strikes:
        if 0.5 * spot <= strike <= 1.5 * spot:
            call = chain['calls'][chain['calls']['strike'] == strike]   
            put = chain['puts'][chain['puts']['strike'] == strike]

            call_iv = None
            put_iv = None

            if not call.empty:
                call_price = call['lastPrice'].iloc[0]
                T = get_time_to_expiry(expiry)
                call_iv = implied_volatility(spot, strike, T, r, call_price, "call")
            if not put.empty:
                put_price = put['lastPrice'].iloc[0]
                T = get_time_to_expiry(expiry)
                put_iv = implied_volatility(spot, strike, T, r, put_price, "put")

            if (call_iv is not None and call_iv > 0) or (put_iv is not None and put_iv > 0):
                final_valid_strike.append(strike)
                call_ivs.append(call_iv)
                put_ivs.append(put_iv)

    if not final_valid_strike:
        return None, None, None

    return final_valid_strike, call_ivs, put_ivs


def get_time_to_expiry(expiry_date):
    today = datetime.now()
    expiry = datetime.strptime(expiry_date,"%Y-%m-%d")

    days = (expiry - today).days
    time = (days/365)
    
    return round(time,4)


@st.cache_data(ttl=3600)
def get_iv_surface(ticker):
    expiries = get_expiries(ticker)

    if not expiries:
        print("No option data")
        return None
    
    iv_surface = {}

    for expiry in expiries:
        strikes, call_ivs, put_ivs = get_valid(ticker,expiry)

        if strikes is not None and len(strikes) >=2:
            iv_surface[expiry] = (strikes, call_ivs, put_ivs)

    if not iv_surface:
        return None
    return iv_surface


@st.cache_data(ttl=3600)
def get_market_data(ticker,expiry,strike,r,option_type):
    spot = get_spot_price(ticker)
    chain = get_option_chain(ticker,expiry)
    if chain is None or spot is None:
        return None,None,None,None

    options = chain['calls'] if option_type=="call" else chain['puts'] 
    T = get_time_to_expiry(expiry)

    hist_vol = live_historical_volatility(ticker,'1y')

    option_data = options[options['strike'] == strike]
    if not option_data.empty:
        price = option_data['lastPrice'].values[0]
        imp_vol = implied_volatility(spot, strike, T, r, price, option_type)
        if imp_vol is None:
            imp_vol = hist_vol
    else:
        imp_vol = hist_vol
        
    return spot, T, hist_vol, imp_vol


@st.cache_data(ttl=3600)
def get_smile_values(ticker, expiry, option_type, r):
    strikes, call_ivs, put_ivs = get_valid(ticker, expiry, r)
    if strikes is None:
        return [], [], []

    if option_type.lower() == 'call':
        predicted_ivs = call_ivs
    else:
        predicted_ivs = put_ivs

    chain = get_option_chain(ticker, expiry)
    if chain is None:
        return [], [], []
    options = chain['calls'] if option_type.lower() == 'call' else chain['puts']
 
    final_actual_iv = []
    for strike in strikes:
        option_row = options[options['strike'] == strike]
        if not option_row.empty:
            actual_iv = option_row['impliedVolatility'].iloc[0]
            final_actual_iv.append(actual_iv)
        else:
            final_actual_iv.append(None)

    return strikes, predicted_ivs, final_actual_iv
