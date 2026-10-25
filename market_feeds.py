"""Read-only public spot OHLCV feeds; no keys or order endpoints."""
import urllib.parse

STEPS={'5m':300,'15m':900,'1h':3600}

def normalize(exchange, raw, tf, limit=100):
    if tf not in STEPS: raise ValueError('Unsupported timeframe')
    step=STEPS[tf]; out=[]
    for x in raw:
        if exchange in ('Binance','MEXC'):
            t=int(x[0])//1000
            row=dict(time=t,open=float(x[1]),high=float(x[2]),low=float(x[3]),close=float(x[4]),volume=float(x[5]),quote_volume=float(x[7]),close_time=int(x[6])//1000)
        elif exchange=='Gate':
            t=int(x[0]);row=dict(time=t,open=float(x[5]),high=float(x[3]),low=float(x[4]),close=float(x[2]),volume=float(x[6]) if len(x)>6 else 0.,quote_volume=float(x[1]),close_time=t+step-1)
        else: raise ValueError('Unknown exchange')
        if min(row['open'],row['high'],row['low'],row['close'])<=0 or row['high']<max(row['open'],row['close']) or row['low']>min(row['open'],row['close']):
            raise ValueError('Invalid OHLC')
        out.append(row)
    out.sort(key=lambda r:r['time'])
    if any(out[i]['time']<=out[i-1]['time'] for i in range(1,len(out))):raise ValueError('Duplicate candle timestamps')
    return out[-limit:]

def fetch(exchange,symbol,tf,get_json,limit=100):
    if tf not in STEPS:raise ValueError('Unsupported timeframe')
    if not symbol.endswith('USDT') or not symbol.isalnum():raise ValueError('Invalid USDT symbol')
    if exchange=='Gate':
        market=symbol[:-4]+'_USDT';url='https://api.gateio.ws/api/v4/spot/candlesticks?'+urllib.parse.urlencode({'currency_pair':market,'interval':tf,'limit':limit})
    elif exchange in ('Binance','MEXC'):
        base='https://api.binance.com' if exchange=='Binance' else 'https://api.mexc.com'
        url=base+'/api/v3/klines?'+urllib.parse.urlencode({'symbol':symbol,'interval':('60m' if exchange=='MEXC' and tf=='1h' else tf),'limit':limit})
    else:raise ValueError('Unknown exchange')
    raw=get_json(url)
    if not isinstance(raw,list):raise ValueError('Exchange did not return candle array')
    return normalize(exchange,raw,tf,limit)
