import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from data import get_time_to_expiry
from pricing import calc_greeks

sns.set_style("whitegrid")
sns.set_palette("husl")

def plot_iv_surface(iv_surface, option_type="call", title="Implied Volatility Surface (3D)"):
    fig = plt.figure(figsize=(12,8))
    ax = fig.add_subplot(projection='3d')

    all_strikes, all_expiries, all_ivs = [], [], []

    for expiry, (strikes, call_ivs, put_ivs) in iv_surface.items():
        T = get_time_to_expiry(expiry)
        ivs = call_ivs if option_type.lower() == "call" else put_ivs
        for K, iv in zip(strikes, ivs):
            if iv is not None:  # Only plot valid IVs
                all_strikes.append(K)
                all_expiries.append(T)
                all_ivs.append(iv)
    
    ax.scatter(all_strikes, all_expiries, all_ivs, c=all_ivs, cmap='viridis', s=30)

    ax.set_title(title)
    ax.set_xlabel("Strike Price")
    ax.set_ylabel("Time to Expire (Years)")
    ax.set_zlabel("Implied Volatility")
    ax.grid(True)

    plt.colorbar(ax.collections[0], ax=ax, shrink=0.5, aspect=10, label="IV Values")
    plt.tight_layout()
    return fig


def plot_bs_price_heatmap(strikes,times,prices,title):
    fig,ax = plt.subplots(figsize=(10,6))

    sns.heatmap(prices,xticklabels=[f"${k:.0f}" for k in strikes],yticklabels=[f"{t*365:.0f}d" for t in times],annot=True,fmt='.2f',linewidths=0.5,linecolor="black",ax = ax,cmap='OrRd',cbar_kws={"label": "Black Scholes Prices ($)"})
    ax.set_title(title)
    ax.set_xlabel('Strike Price ($)')
    ax.set_ylabel('Days to Expiry')

    return fig


def plot_pnl_heatmap(strikes,times,pnl,title):
    fig,ax = plt.subplots(figsize=(10,6))

    max_abs = np.max(np.abs(pnl))
    sns.heatmap(pnl,xticklabels=[f'${k:.0f}' for k in strikes],yticklabels=[f'{t*365:.0f}d' for t in times],cmap='RdYlGn',center = 0,vmin=-max_abs,vmax=max_abs,annot=True,fmt='.2f',linewidths=0.5,linecolor="black",ax = ax,cbar_kws={"label": "Profit and Loss ($)"})
    ax.set_title(title)
    ax.set_xlabel('Strike Price ($)')
    ax.set_ylabel('Days to Expiry')

    return fig


def plot_greeks(S,K,T,r,sigma,greeks,greek_name,option_type):
    spot_range = np.linspace(S*0.5,S*1.3,100)
    greek_val = []

    for spot in spot_range:
        greeks = calc_greeks(spot,K,T,r,sigma,option_type)
        greek_val.append(greeks[greek_name])

    fig, ax = plt.subplots(figsize=(6, 4))
    sns.lineplot(x=spot_range, y=greek_val, linewidth=2)
    plt.axvline(x=S, color='black', linestyle='--', alpha=0.5)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.2)
    ax.set_xlabel('Spot Price')
    ax.set_ylabel(greek_name)
    ax.set_title(f'{greek_name} vs Spot Price ({option_type.title()})')
    plt.tight_layout()
    return fig


def plot_volatility_smile(strikes, predicted_ivs, actual_ivs, spot_price, selected_strike, title="Implied Volatility Smile"):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(strikes, predicted_ivs, label='Predicted IV (Model)', marker='o')
    ax.plot(strikes, actual_ivs, label='Actual IV (Market)', marker='o')
    ax.axvline(spot_price, linestyle='--',color = 'r', label='Current Price')
    ax.axvline(selected_strike, linestyle='--',color = 'g', label='Selected Strike')
    ax.set_xlabel('Strike Price ($)')
    ax.set_ylabel('Implied Volatility (0-1)')
    ax.set_ylim(0, 1)
    ax.legend()
    ax.set_title(title)
    plt.tight_layout()
    return fig