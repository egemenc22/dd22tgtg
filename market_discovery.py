"""Read-only spot USDT discovery; conservative ranking and capped request budget."""
import math
from altcoin_focus import focus_rank
from product_filters import allowed_spot_instrument, classify_spot_instrument

URLS={
 'Binance':('https://api.binance.com/api/v3/exchangeInfo','https://api.binance.com/api/v3/ticker/24hr'),
 'MEXC':('https://api.mexc.com/api/v3/exchangeInfo','https://api.mexc.com/api/v3/ticker/24hr'),
 'Gate':('https://api.gateio.ws/api/v4/spot/currency_pairs','https://api.gateio.ws/api/v4/spot/tickers'),
}
EXCLUDE={'USDC','FDUSD','TUSD','USDP','BUSD','DAI','EUR','TRY','BRL','GBP','AUD','USD','USDE','USDD','PYUSD','AEUR','EURC','USTC','XAUT','PAXG','XAG','XAU','USD1','USDF','USDY','USDG','USDB','USDT0'}

def eligible_base(base):
    return bool(base) and base not in EXCLUDE and allowed_spot_instrument(base)

def discover(exchange,get_json,min_quote_volume=1_000_000,max_pairs=75,focus=False,max_quote_volume=150_000_000):
    if exchange not in URLS:raise ValueError('Unknown exchange')
    info=get_json(URLS[exchange][0]); ticks=get_json(URLS[exchange][1]); tradable=set()
    if exchange=='Gate':
        for x in info:
            pair=x.get('id',''); base=x.get('base','')
            if x.get('quote')=='USDT' and x.get('trade_status')=='tradable' and eligible_base(base) and allowed_spot_instrument(base,x):
                tradable.add(pair)
    else:
        for x in info.get('symbols',[]):
            base=x.get('baseAsset','')
            if x.get('quoteAsset')=='USDT' and x.get('status') in ('TRADING','1') and x.get('isSpotTradingAllowed',True) and eligible_base(base) and allowed_spot_instrument(base,x):
                tradable.add(x['symbol'])
    found=[]
    for x in ticks:
        ticker=x.get('currency_pair','') if exchange=='Gate' else x.get('symbol','')
        if ticker not in tradable:continue
        try:
            volume=float(x.get('quoteVolume',0) if exchange!='Gate' else x.get('quote_volume',0))
        except (TypeError,ValueError):continue
        if not math.isfinite(volume) or volume<min_quote_volume:continue
        sym=ticker.replace('_','') if exchange=='Gate' else ticker
        if not sym.isalnum() or not sym.endswith('USDT'):continue
        if focus:
            score=focus_rank(exchange,sym,x,volume,min_quote_volume=min_quote_volume,max_quote_volume=max_quote_volume)
            if score is None:continue
            found.append((sym,volume,score))
        else:found.append((sym,volume))
    found.sort(key=(lambda z:(-z[2],-z[1],z[0])) if focus else (lambda z:(-z[1],z[0])))
    return found[:max_pairs]

def discover_all(exchanges,get_json,min_quote_volume=1_000_000,max_pairs_per_exchange=75,focus=False,max_quote_volume=150_000_000):
    markets=[];errors={}
    for exchange in exchanges:
        try:
            if focus:
                markets.extend((exchange,sym,volume,score) for sym,volume,score in discover(exchange,get_json,min_quote_volume,max_pairs_per_exchange,True,max_quote_volume))
            else:
                markets.extend((exchange,sym,volume) for sym,volume in discover(exchange,get_json,min_quote_volume,max_pairs_per_exchange))
        except Exception as exc:errors[exchange]=str(exc)
    # Balance exchange coverage: each source gets a turn before the next tier.
    # Ranking INSIDE each exchange remains governed by focus_rank / volume.
    buckets={ex:[m for m in markets if m[0]==ex] for ex in exchanges}
    balanced=[]
    for i in range(max((len(v) for v in buckets.values()),default=0)):
        for ex in exchanges:
            if i<len(buckets[ex]):balanced.append(buckets[ex][i])
    return balanced,errors
