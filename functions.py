import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq


def black_price(F, K, T, r, sigma, option_type):
    d1 = (np.log(F / K) + (0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if option_type == 'C':
        price = np.exp(-r * T) * (F * norm.cdf(d1) - K * norm.cdf(d2))
    elif option_type == 'P':
        price = np.exp(-r * T) * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
    else:
        raise ValueError("option_type must be 'C' or 'P'")
    return price


def implied_vol(price, F, K, T, r, option_type):
    def difference(sigma):
        return black_price(F, K, T, r, sigma, option_type) - price
    try:
        return brentq(difference, 0.0001, 10)
    except ValueError:
        return np.nan


def svi(k, a, b, rho, m, sig):
    x = k - m
    return a + b * (rho * x + np.sqrt(x**2 + sig**2))


def svi_g(k, a, b, rho, m, sig):
    x = k - m
    root = np.sqrt(x**2 + sig**2)
    w = svi(k, a, b, rho, m, sig)
    w1 = b * (rho + x / root)
    w2 = b * sig**2 / root**3
    return (1 - k * w1 / (2 * w))**2 - (w1**2 / 4) * (1 / w + 1 / 4) + w2 / 2