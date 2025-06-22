import streamlit as st
import numpy as np
import seaborn as sns

from data import get_tickers,get_ticker_info,get_expiries,get_valid,get_iv_surface,get_market_data,get_smile_values
from pricing import black_scholes_price,calc_greeks
from plot import plot_bs_price_heatmap,plot_pnl_heatmap,plot_iv_surface,plot_greeks,plot_volatility_smile

sns.set_style("whitegrid")
sns.set_palette("husl")


GREEKS_DESC = {
    'delta': {
        'desc': "Rate of change in option price relative to underlying price.",
        'call': "Ranges from 0 to 1; estimates probability of finishing in-the-money.",
        'put': "Ranges from -1 to 0; negative of the probability of finishing in-the-money."
    },
    'gamma': {
        'desc': "Rate of change in Delta relative to underlying price.\n\nAlways positive.\nHigher Gamma means faster Delta changes."
    },
    'theta': {
        'desc': "Rate of change in option value with respect to time.\n\nUsually negative.\nRepresents value lost per day due to time decay."
    },
    'vega': {
        'desc': "Rate of change in option value with respect to implied volatility.\n\nHigher Vega means more sensitivity.\nMeasures impact of volatility changes."
    },
    'rho': {
        'desc': "Rate of change in option value with respect to interest rate.\n\nCalls have positive Rho.\nPuts usually have negative Rho."
    }
}


def show_company_info(company):
    cols = st.columns(3)
    
    with cols[0]:
        st.write("**Market Cap**")
        st.write(currency(company['market_cap']))
        st.write("**P/E Ratio**")
        st.write(f"{company['pe_ratio']:.2f}")
    
    with cols[1]:
        st.write("**Sector**")
        st.write(company['sector'])
        st.write("**Industry**")
        st.write(company['industry'])
    
    with cols[2]:
        st.write("**Dividend Yield**")
        st.write(percent(company['dividend_yield']))
        st.write("**Beta**")
        st.write(f"{company['beta']:.2f}")



def currency(val):
    val = float(val)
    if val == "N/A":
        return val
    
    ans = "$"

    if val>=1_000_000_000:
        val/=1_000_000_000
        ans+= str(round(val,2)) + "B"
    elif val>=1_000_000:
        val/=1_000_000
        ans+= str(round(val,2)) + "M"
    else:
        ans+=str(round(val,2))
    
    return ans
    

def percent(val):
    if val == "N/A":
        return val
    
    return str(round(val*100,2)) + "%"


def desc(text):
    if not text:
        return ""
    
    text = text.replace(". ",'. \n\n')

    return text.strip()



st.set_page_config(
    page_title="Primetrics",
    page_icon="💎",
    layout="centered"
)


def show_company_tab(ticker,spot,vol_source,sigma,days):
    with st.spinner('Loading company information...'):
        company = get_ticker_info(ticker)
        if not company:
            st.warning("Company information not available")
            return
        
        st.subheader(company['name'])
        
        st.markdown("### Company Information")
        show_company_info(company)
        
        st.markdown("### Market Data")
        cols = st.columns(3)
        with cols[0]:
            st.metric("Price",f"${spot:.2f}")
        with cols[1]:
            st.metric(f"{vol_source} Vol", f"{sigma*100:.2f}%")
        with cols[2]:
            st.metric("Days to Expiry",str(days))
        
        st.markdown("### Business Description")
        st.markdown(desc(company['description']))


def show_pricing_tab(spot, strike, T, r, sigma, option_type):
    with st.spinner('Calculating option price and Greeks...'):
        price = black_scholes_price(spot, strike, T, r, sigma, option_type)
        greeks = calc_greeks(spot, strike, T, r, sigma, option_type)
        
        cols = st.columns(4)
        with cols[0]:
            st.metric("Option Price", f"${price:.2f}", help="Theoretical price calculated using Black-Scholes model")
        with cols[1]:
            st.metric("Strike Price", f"${strike:.2f}", help="Price at which the option can be exercised")
        with cols[2]:
            st.metric("Spot Price", f"${spot:.2f}", help="Current market price of the underlying stock")
        with cols[3]:
            st.metric("Days to Expiry", f"{int(T*365)}", help="Number of days until the option expires")
        
        st.markdown("### Greeks Analysis")
        for name, value in greeks.items():
            if name == 'delta':
                st.markdown(f"### {name.title()}: {value:.4f}")
            else:
                st.markdown(f"#### {name.title()}: {value:.4f}")
            desc = GREEKS_DESC[name]
            if name == 'delta':
                st.write(desc['desc'])
                st.write(desc['call' if option_type == 'Call' else 'put'])
            else:
                st.write(desc['desc'])
            
            with st.expander("View Graph"):
                fig = plot_greeks(spot, strike, T, r, sigma, greeks, name, option_type)
                st.pyplot(fig)
            st.markdown("---")  


def show_analysis_tab(ticker,spot,strike,T,r,sigma,option_type):
    with st.spinner('Loading IV surface data...'):
        iv_surface = get_iv_surface(ticker)

        if option_type == "Call":
            strikes_heatmap = np.linspace(spot, spot * 1.5, 10)  
        else:
            strikes_heatmap = np.linspace(spot * 0.5, spot, 10) 
        
        times_heatmap = np.linspace(1/365, T, 10)
        K_heatmap, t_heatmap = np.meshgrid(strikes_heatmap, times_heatmap)
        
        
        with st.spinner('Calculating option prices...'):
            prices = np.zeros_like(K_heatmap)
            for i in range(len(times_heatmap)):
                for j in range(len(strikes_heatmap)):
                    prices[i,j] = black_scholes_price(spot, K_heatmap[i,j], t_heatmap[i,j], r, sigma, option_type)
        # Plot Pricing Heatmap

        st.subheader("Option Price Heatmap", help="Shows option prices across different strikes and times. Darker colors mean higher prices.")
        fig = plot_bs_price_heatmap(strikes_heatmap, times_heatmap, prices, f"{option_type.title()} Option Prices")
        st.pyplot(fig)
        
        current_price = black_scholes_price(spot, strike, T, r, sigma, option_type)
        pnl = prices - current_price

        # Plot PnL Heatmap
        st.subheader("Profit/Loss Heatmap", help="Shows potential profits (green) and losses (red) across different scenarios.")
        fig = plot_pnl_heatmap(strikes_heatmap, times_heatmap, pnl, f"{option_type.title()} P&L Analysis")
        st.pyplot(fig)

        # Plot Volatility Smile
        st.subheader("Volatility Smile", help="Shows how implied volatility changes with strike price. Compares predicted (model) and actual (market) IV.")
        with st.spinner('Generating Volatility Smile plot...'):
            valid_strikes, predicted_ivs, actual_ivs_filtered = get_smile_values(ticker, expiry, option_type, r)
            if len(valid_strikes) > 1:
                fig = plot_volatility_smile(valid_strikes, predicted_ivs, actual_ivs_filtered, spot, float(strike), title=f"Volatility Smile ({option_type.title()})")
                st.pyplot(fig)
            else:
                st.info("Not enough data to plot volatility smile.")
        
        # Plot IV Surface Points
        st.subheader("Implied Volatility", help="Shows market's expected volatility. Yellow means higher volatility, purple means lower.")
        with st.spinner('Generating IV surface plot...'):
            iv_surface = get_iv_surface(ticker)
            if iv_surface:
                fig = plot_iv_surface(iv_surface)
                st.pyplot(fig)

    
def show_help_tab():
    st.markdown("""### How to Use 

#### Introduction

Welcome to **Prismetrics**, an interactive dashboard for exploring options pricing and market behaviour.

I was inspired to create this through my course in Computational Finance. Prismetrics is designed to help you understand how various factors—such as market data, volatility, and interest rates—affect option prices.

---
#### Quick Guide 

1. **Select a Stock:** Choose from a list of tickers to start your analysis.  
2. **Select an Expiry Date:** Choose how long you want the option contract to run.  
3. **Set Strike Price and Other Parameters:** Adjust values like strike price, interest rate, volatility, and option type (call or put).  
4. **Navigate Through Tabs:**  
    - **Company Information:** View key fundamentals of the selected company.  
    - **Pricing and Greeks:** Get theoretical pricing from the Black-Scholes model and explore the Greeks to understand risk.
    - **Analysis:** Visualize pricing and P&L heatmaps; plot model vs. market implied volatility to track changes.

---
#### How It Works
- Built using **Python** and **Streamlit**.  
- Uses **real market data** for accurate and insightful analysis.  
- All visuals are generated from scratch using **Matplotlib** and **Seaborn**.

This is a great learning tool for anyone curious about how options function—or anyone who enjoys working with data, like I do.  
It's designed to be **highly visual and intuitive**, making options pricing easier to grasp, even for those without a financial background.

---
**Disclaimer:** This project is for educational purposes only and does not constitute financial advice.
    """)


def show_about_tab():
    st.markdown("""
    ### About Me

    Hi, I'm **Manthan Parmar** — currently pursuing a B.Tech. (Honours) in **Information and Communication Technology** (2022–2026), with a **minor in Computational Science** at Dhirubhai Ambani Institute of Information and Communication Technology (DA-IICT), now known as **DAU**.

    I'm passionate about building at the intersection of **code, math, and data**. I particularly enjoy working on **data analytics** and **visualization**, turning raw information into interactive tools and intuitive insights.

    My current focus lies in **Machine Learning**, especially **Supervised Learning** and **Reinforcement Learning**. I've also been exploring **Neural Networks**, **Deep Learning**, and **Financial Analytics** — and I'm fascinated by how **Generative AI** is transforming creative fields like **art** and **music**.

    Beyond the technical world, I enjoy keeping up with trends in **music**, **gaming**, and **fine arts**, always looking for ways to blend creativity with computation.

    I love learning, building, and collaborating on meaningful tech projects.  
    Thanks for exploring **Prismetrics** — I hope you enjoy using it as much as I enjoyed creating it!

    ---

    ### Connect with me:

    - 🔗 [LinkedIn](https://www.linkedin.com/in/manthan-d-parmar/)  
    - 🌐 [GitHub](https://github.com/Manthan-D-Parmar)

    *Prismetrics is released for educational purposes—feel free to dive into the code, experiment, and learn!*
    """)


if __name__ == "__main__":

    st.title("💎 Prismetrics : Option Analysis \n Your Strategic Lens into Option Markets")

    st.sidebar.header("Visualisation Parameters")

    with st.spinner('Loading available tickers...'):
        if 'tickers' not in st.session_state:
            st.session_state.tickers = get_tickers()

    tickers_list = [f"{k} ({v})" for k,v in st.session_state.tickers.items()]
    
    selected = st.sidebar.selectbox("Stock", tickers_list,help="Select a company to analyze. Ticker symbol followed by company name.")
    ticker = selected.split("(")[0].strip()

    with st.spinner('Loading expiry dates...'):
        expiries = get_expiries(ticker)

    expiry = st.sidebar.selectbox("Expiry",expiries,help="Option expiration date. Longer dates cost more but give more time.")

    standard_rates = [round(x, 4) for x in np.arange(0.00, 0.1501, 0.0025)]

    default_r_index = standard_rates.index(0.05) if 0.05 in standard_rates else 0

    r = st.sidebar.selectbox("Select Risk-Free Rate",standard_rates,index=default_r_index,format_func=lambda x: f"{x*100:.2f}%",help="Current interest rate used in option pricing calculations."
    )

    
    with st.spinner('Loading valid strikes...'):
        strikes, call_ivs, put_ivs = get_valid(ticker, expiry, r)
        if not strikes:
            st.error("No valid strikes available.")
            exit()
    
    strike  = st.sidebar.selectbox("Strike",strikes,help="Price at which you can buy or sell the stock.")

    vol_source = st.sidebar.radio("Volatility",["Historical","Implied"],help="Past price movements or market's future expectations.")

    option_type = st.sidebar.radio("Type",["Call","Put"],help="Call: Right to buy. Put: Right to sell.")


    with st.spinner('Loading market data...'):
        spot,T,hist_vol,imp_vol = get_market_data(ticker,expiry,strike,r,option_type)

        if None in (spot,T,hist_vol,imp_vol):
            st.error("Could not load market data")
            exit()

    sigma = hist_vol if vol_source == "Historical" else imp_vol
    days = int(T*365)
    
    tab_options,tab_pricing,tab_analysis,tab_help,tab_about = st.tabs(["Company Info","Pricing & Greeks","Analysis","Help","About"])

    with tab_options:
        show_company_tab(ticker,spot,vol_source,sigma,days)
    
    with tab_pricing:
        show_pricing_tab(spot,strike,T,r,sigma,option_type)
    
    with tab_analysis:
        show_analysis_tab(ticker,spot,strike,T,r,sigma,option_type)

    with tab_help:
        show_help_tab()

    with tab_about:
        show_about_tab()




