import numpy as np
from scipy.stats import norm

def black_scholes_price(S,K,T,r,sigma,option_type = "call"):
    if T<=0:
        if option_type == "call":
            return max(S-K,0)
        return max(K-S,0)
    
    sqrt_T = np.sqrt(T)
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T)/(sigma*sqrt_T)

    d2 = d1 - sigma*sqrt_T

    N_d1 = norm.cdf(d1)
    N_d2 = norm.cdf(d2)

    if option_type == "call":
        return S*N_d1 - K*np.exp(-r*T)*N_d2
    return K*np.exp(-r*T)*(1-N_d2) - S*(1-N_d1)


def calc_greeks(S,K,T,r,sigma,option_type ="call"):
    if T<=0:
        return {
            "delta":1.0 if option_type=="call" else -1.0,
            "gamma":0.0,
            "theta":0.0,
            "vega":0.0,
            "rho":0.0
        }
    sqrt_T = np.sqrt(T)
    d1 = (np.log(S/K) + (r + 0.5*sigma**2)*T)/(sigma*sqrt_T)

    d2 = d1 - sigma*sqrt_T

    N_d1 = norm.cdf(d1)
    N_d2 = norm.cdf(d2)
    n_d1 = norm.pdf(d1)

    delta = N_d1
    if option_type == "put":
        delta-=1
    
    gamma = n_d1/(S*sigma*sqrt_T)

    theta = -(S*n_d1*sigma)/(2*sqrt_T)
    if option_type == "call":
        theta -= r*K*np.exp(-r*T)*N_d2
    else:
        theta+=r*K*np.exp(-r*T)*(1-N_d2)

    rho = 0
    if option_type=="call":
        rho = K*T*np.exp(-r*T)*N_d2
    else:
        rho = -K*T*np.exp(-r*T)*(1-N_d2)

    vega = S*sqrt_T*n_d1

    return {
        'delta': round(delta, 4),
        'gamma': round(gamma, 4),
        'theta': round(theta / 365, 4),  # per day
        'vega': round(vega / 100, 4),    # per 1% change
        'rho': round(rho / 100, 4)       # per 1% change
    }  
    
    
if __name__ == "__main__":
    S = 100
    K = 105
    T = 30 / 365
    r = 0.05
    sigma = 0.2

    print("Call Price:", black_scholes_price(S, K, T, r, sigma, "call"))
    print("Put Price:", black_scholes_price(S, K, T, r, sigma, "put"))
    print("Call Greeks:", calc_greeks(S, K, T, r, sigma, "call"))
    print("Put Greeks:", calc_greeks(S, K, T, r, sigma, "put"))

