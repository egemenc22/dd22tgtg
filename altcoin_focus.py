"""Altcoin universe scoring; no market-cap claims without cap data."""
import math
from product_filters import allowed_crypto_base
MAJORS={'BTC','ETH','BNB','SOL','XRP','ADA','DOGE','TRX','LTC','BCH','LINK','AVAX','DOT'}

def focus_rank(exchange, symbol, ticker_data, volume, *, min_quote_volume=120000, max_quote_volume=150000000, exclude_majors=True):
    base=symbol.replace('_','').removesuffix('USDT')
    if not allowed_crypto_base(base): return None
    if exclude_majors and base in MAJORS: return None
    if not (min_quote_volume<=volume<=max_quote_volume): return None
    # Genuine exchange-reported 24h movement and high/low range when available.
    def val(*keys):
        for k in keys:
            try:
                v=float(ticker_data.get(k))
                if math.isfinite(v):return v
            except (ValueError,TypeError):pass
        return None
    ticker_data=ticker_data if isinstance(ticker_data,dict) else {}
    change=val('priceChangePercent','change_percentage')
    high=val('highPrice','high_24h')
    low=val('lowPrice','low_24h')
    fluct=100*(high-low)/low if high and low and low>0 else 0.
    change_abs=abs(change) if change is not None else 0.
    # Boost dynamic markets without ranking solely by the largest candles.
    score=round(min(10,math.log10(max(volume,1)/min_quote_volume+1))*15 + min(35,change_abs*1.5)+min(35,fluct*1.2),3)
    return score
