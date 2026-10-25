"""Deterministic candle-close strategies, stdlib only. Research-style alerts, not profits."""
import math

def ema(v,n):
    a=2/(n+1); out=[]; e=None
    for x in v:
        e=x if e is None else e+a*(x-e);out.append(e)
    return out

def rsi(v,n=14):
    ds=[v[i]-v[i-1] for i in range(1,len(v))]
    if len(ds)<n:return 50.
    up=sum(max(x,0) for x in ds[:n])/n;down=sum(max(-x,0) for x in ds[:n])/n
    for x in ds[n:]:up=(up*(n-1)+max(x,0))/n;down=(down*(n-1)+max(-x,0))/n
    return 100 if down==0 else 100-100/(1+up/down)

def atr(rows,n=14):
    trs=[]
    for i in range(1,len(rows)):
        c=rows[i-1]['close'];x=rows[i];trs.append(max(x['high']-x['low'],abs(x['high']-c),abs(x['low']-c)))
    return sum(trs[-n:])/n if len(trs)>=n else 0

def std(v):
    m=sum(v)/len(v);return math.sqrt(sum((x-m)**2 for x in v)/len(v))

def evaluate(rows,tf='5m',selected=None):
    """Closed consecutive bars only. One latest-candle event max, no lookahead."""
    if len(rows)<65:return []
    step={'5m':300,'15m':900,'1h':3600}.get(tf,300)
    if any(rows[i]['time']-rows[i-1]['time']!=step for i in range(len(rows)-65+1,len(rows))):return []
    c=[x['close'] for x in rows];h=[x['high'] for x in rows];l=[x['low'] for x in rows]
    e20=ema(c,20);e50=ema(c,50);a=atr(rows);out=[]
    if a<=0:return []
    def put(name,side,why):
        if selected is None or name in selected:out.append({'strategy':name,'side':side,'reason':f'{tf} {name}: {why}', 'origin_ts':rows[-1]['time'],'entry':c[-1], 'strength':round(min(95,55+abs(c[-1]-e20[-1])/a*9),1)})
    # Moving average trend + a direction-strength proxy; named EMA trend rather than ADX.
    if c[-2]<=e20[-2] and c[-1]>e20[-1] and e20[-1]>e50[-1] and e20[-1]>e20[-4]:put('EMA_TREND','LONG','close reclaimed EMA20 above rising EMA50')
    if c[-2]>=e20[-2] and c[-1]<e20[-1] and e20[-1]<e50[-1] and e20[-1]<e20[-4]:put('EMA_TREND','SHORT','close rejected EMA20 below falling EMA50')
    upper=max(h[-21:-1]);lower=min(l[-21:-1])
    if c[-2]<=upper and c[-1]>upper:put('DONCHIAN_20','LONG','20-bar high breakout')
    if c[-2]>=lower and c[-1]<lower:put('DONCHIAN_20','SHORT','20-bar low breakdown')
    # Current BB width must expand from a preceding low-volatility regime.
    widths=[]
    for i in range(40,len(c)+1):
        v=c[i-20:i];m=sum(v)/20;widths.append(4*std(v)/m if m>0 else 0)
    if len(widths)>10:
        base=sorted(widths[-11:-1])[2];recent=widths[-2];present=widths[-1]
        m=sum(c[-20:])/20;s=std(c[-20:])
        if recent<=base and present>recent*1.15:
            if c[-1]>m+2*s:put('BB_SQUEEZE','LONG','BB compression released above upper band')
            if c[-1]<m-2*s:put('BB_SQUEEZE','SHORT','BB compression released below lower band')
    # Cross back inside previous Bollinger band, RSI confirms reversion.
    old=c[-21:-1];mo=sum(old)/20;so=std(old);mn=sum(c[-20:])/20;sn=std(c[-20:])
    if c[-2]<mo-2*so and c[-1]>mn-2*sn and rsi(c)<42:put('RSI_BB_REVERSION','LONG','re-entered lower BB, RSI below 42')
    if c[-2]>mo+2*so and c[-1]<mn+2*sn and rsi(c)>58:put('RSI_BB_REVERSION','SHORT','re-entered upper BB, RSI above 58')
    # ATR trailing channel transition (Supertrend-inspired; not labeled exact Supertrend).
    if c[-2]<=e20[-2]+a*1.5 and c[-1]>e20[-1]+a*1.5:put('ATR_CHANNEL','LONG','break above EMA20 + 1.5 ATR')
    if c[-2]>=e20[-2]-a*1.5 and c[-1]<e20[-1]-a*1.5:put('ATR_CHANNEL','SHORT','break below EMA20 - 1.5 ATR')
    fast=ema(c,12);slow=ema(c,26);mac=[x-y for x,y in zip(fast,slow)];sig=ema(mac,9)
    if mac[-2]<=sig[-2] and mac[-1]>sig[-1] and mac[-1]>0:put('MACD_MOMENTUM','LONG','positive MACD signal crossover')
    if mac[-2]>=sig[-2] and mac[-1]<sig[-1] and mac[-1]<0:put('MACD_MOMENTUM','SHORT','negative MACD signal crossover')
    # Early altcoin impulse: last closed candle breaks the prior range with unusual quote volume.
    vol=[max(0,float(x.get('quote_volume',0))) for x in rows]
    prior=vol[-21:-1]
    baseline=sum(prior)/len(prior) if prior else 0
    if baseline>0 and vol[-1]>=baseline*3 and vol[-1]>=15000:
        recent_high=max(h[-21:-1]);recent_low=min(l[-21:-1]);movement=abs(c[-1]/c[-2]-1)*100
        if 0.8<=movement<=15:
            if c[-1]>recent_high and c[-1]>rows[-1]['open']:put('VOLUME_BREAKOUT','LONG',f'20-bar breakout with {vol[-1]/baseline:.1f}x quote-volume spike')
            if c[-1]<recent_low and c[-1]<rows[-1]['open']:put('VOLUME_BREAKOUT','SHORT',f'20-bar breakdown with {vol[-1]/baseline:.1f}x quote-volume spike')
    # Early-stage altcoin alerts. These require a closed candle and prior-period evidence.
    # Volume acceleration looks for a rising sequence BEFORE the more restrictive 20-bar breakout.
    baseline_vol=vol[-31:-7] if len(vol)>=31 else []
    if len(baseline_vol)>=20:
        baseline=sorted(baseline_vol)[len(baseline_vol)//2]
        last3=vol[-3:]
        prev3=vol[-6:-3]
        if baseline>0 and len(prev3)==3:
            last3_avg=sum(last3)/3
            prev3_avg=sum(prev3)/3
            growth=last3_avg/max(prev3_avg,1)
            high_lookback=max(h[-21:-1]); low_lookback=min(l[-21:-1])
            relative_range=max(high_lookback-low_lookback,1e-12)
            impulse=(c[-1]/c[-4]-1)*100 if c[-4]>0 else 0
            # Avoid already fully extended candles and spoof-like single-candle volume jumps.
            supporting_bars=sum(v>baseline*1.3 for v in last3)
            if last3_avg>=baseline*2.0 and growth>=1.5 and supporting_bars>=2 and vol[-1]>=10000:
                if 0.35<=impulse<=7.0 and c[-1]<high_lookback and c[-1]>(high_lookback-relative_range*.25):
                    put('VOLUME_ACCELERATION','LONG',f'volume accelerating {growth:.1f}x vs previous 3 bars near 20-bar resistance')
                if -7.0<=impulse<=-0.35 and c[-1]>low_lookback and c[-1]<(low_lookback+relative_range*.25):
                    put('VOLUME_ACCELERATION','SHORT',f'volume accelerating {growth:.1f}x vs previous 3 bars near 20-bar support')
    # Momentum ignition: 3 consecutive directional closes plus expanding price range.
    recent_ranges=[x['high']-x['low'] for x in rows[-4:]]
    older_ranges=[x['high']-x['low'] for x in rows[-24:-4]]
    reference_range=sum(older_ranges)/len(older_ranges) if older_ranges else 0
    if reference_range>0 and sum(recent_ranges[-3:])/3>=reference_range*1.5:
        up3=all(c[i]>c[i-1] for i in (-3,-2,-1))
        down3=all(c[i]<c[i-1] for i in (-3,-2,-1))
        move_pct=(c[-1]/c[-4]-1)*100 if c[-4]>0 else 0
        if up3 and .6<=move_pct<=6 and c[-1]>e20[-1] and vol[-1]>=10000:
            put('MOMENTUM_IGNITION','LONG',f'3 rising closes and 1.5x expanding candle range; move {move_pct:+.1f}%')
        if down3 and -6<=move_pct<=-.6 and c[-1]<e20[-1] and vol[-1]>=10000:
            put('MOMENTUM_IGNITION','SHORT',f'3 falling closes and 1.5x expanding candle range; move {move_pct:+.1f}%')
    return out
