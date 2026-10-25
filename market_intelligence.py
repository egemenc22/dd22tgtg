"""Read-only market microstructure features. Evidence and heuristics, not probabilities."""
import math
import urllib.parse

def volume_regime(rows):
    if len(rows)<45: return {'valid':False,'reason':'insufficient candles'}
    v=[float(r.get('quote_volume',0)) for r in rows]
    if any(not math.isfinite(x) or x<0 for x in v):return {'valid':False,'reason':'invalid volume'}
    old=v[-45:-5]; recent=v[-5:]
    base=sorted(old)[len(old)//2]
    if base<=0:return {'valid':False,'reason':'zero baseline'}
    ratio=sum(recent)/len(recent)/base
    participation=sum(x>=base*1.4 for x in recent)
    atr_old=sum((r['high']-r['low'])/r['close'] for r in rows[-45:-5])/40
    atr_new=sum((r['high']-r['low'])/r['close'] for r in rows[-5:])/5
    volatility=atr_new/max(atr_old,1e-12)
    return {'valid':True,'volume_ratio':round(ratio,2),'participation':participation,
            'volatility_ratio':round(volatility,2),'active':ratio>=1.5 and participation>=3,
            'expanding':volatility>=1.25}

def orderbook_binance(symbol,get_json):
    url='https://api.binance.com/api/v3/depth?'+urllib.parse.urlencode({'symbol':symbol,'limit':100})
    data=get_json(url)
    def levels(name):
        result=[]
        for p,q in data[name]:
            p=float(p);q=float(q)
            if not math.isfinite(p*q) or p<=0 or q<=0:raise ValueError('invalid depth')
            result.append((p,q))
        if not result:raise ValueError('empty depth')
        return result
    bids=levels('bids');asks=levels('asks')
    spread=100*(asks[0][0]-bids[0][0])/((asks[0][0]+bids[0][0])/2)
    if spread<0:raise ValueError('crossed orderbook')
    mid=(asks[0][0]+bids[0][0])/2
    cap=0.005 # liquidity measured within 0.5% of midpoint
    buy=sum(p*q for p,q in bids if p>=mid*(1-cap))
    sell=sum(p*q for p,q in asks if p<=mid*(1+cap))
    total=buy+sell
    if total<=0:raise ValueError('zero near-touch depth')
    return {'spread_pct':round(spread,4),'bid_usdt':round(buy,2),'ask_usdt':round(sell,2),
            'imbalance':round((buy-sell)/total,3),'depth_usdt':round(total,2)}

def enrich_signal(signal,rows,exchange,symbol,get_json,cfg):
    """Reject unreasonable execution conditions; annotate scores transparently."""
    result=dict(signal)
    regime=volume_regime(rows)
    if not regime['valid']:return None
    # Wide volatility without participation often indicates noisy microcap prints.
    if cfg.get('intelligence_require_activity',False) and not regime['active']:return None
    bonus=min(8,max(0,(regime['volume_ratio']-1)*3))
    if regime['expanding']:bonus+=3
    result['strength']=round(min(95,result['strength']+bonus),1)
    result['reason']+=f" | VOLUME_REGIME {regime['volume_ratio']:.2f}x; VOLATILITY {regime['volatility_ratio']:.2f}x"
    if exchange=='Binance' and cfg.get('enable_orderbook_filter',True):
        try:
            book=orderbook_binance(symbol,get_json)
        except Exception as e:
            result['reason']+=' | ORDERBOOK_UNAVAILABLE'
            if cfg.get('require_orderbook',False):return None
        else:
            if book['spread_pct']>float(cfg.get('intelligence_max_spread_pct',0.35)):return None
            if book['depth_usdt']<float(cfg.get('intelligence_min_depth_usdt',10000)):return None
            result['reason']+=f" | BOOK spread={book['spread_pct']:.3f}%; imbalance={book['imbalance']:+.2f}"
            if (result['side']=='LONG' and book['imbalance']>=0.2) or (result['side']=='SHORT' and book['imbalance']<=-0.2):
                result['strength']=round(min(95,result['strength']+4),1)
    return result
