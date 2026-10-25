"""Egonia Altcoin Radar: observed, closed-candle events (not predictive signals)."""
import json, math, time, sqlite3, logging, threading

_publish_lock = threading.RLock()

KINDS=('UNUSUAL_VOLUME','EARLY_MOMENTUM','BREAKOUT','TREND_SHIFT','PUMP_DUMP_REVERSAL')

def analyze(rows):
    """One quality-ranked event per last completed 5m candle, no forward data."""
    if len(rows)<55:return None
    bars=rows[-55:]
    if any(bars[i]['time']-bars[i-1]['time']!=300 for i in range(1,len(bars))):return None
    last=bars[-1];prev=bars[-2];window=bars[-25:-1]
    close=float(last['close']);prev_close=float(prev['close'])
    if min(close,prev_close)<=0:return None
    vol=float(last.get('quote_volume',0));baseline=sum(float(x.get('quote_volume',0)) for x in window)/len(window)
    if baseline<=0:return None
    ratio=vol/baseline;move=100*(close/prev_close-1)
    older=[x['close'] for x in bars[-23:-3]]
    prior_hi=max(x['high'] for x in window);prior_lo=min(x['low'] for x in window)
    mean20=sum(x['close'] for x in bars[-21:-1])/20
    mean50=sum(x['close'] for x in bars[-51:-1])/50
    old20=sum(x['close'] for x in bars[-22:-2])/20
    last_range=max(float(last['high'])-float(last['low']),1e-12)
    typical_range=sum(max(x['high']-x['low'],1e-12) for x in window)/len(window)
    three_move=100*(close/bars[-4]['close']-1) if bars[-4]['close']>0 else 0
    # Event points are explainable priority, NOT win probabilities.
    matches=[]
    if ratio>=3 and vol>=25000 and abs(move)>=.35:
        matches.append(('UNUSUAL_VOLUME', min(35,15+min(12,(ratio-3)*4)+min(8,abs(move)*2))))
    if ratio>=1.8 and vol>=25000 and .7<=abs(three_move)<=7 and abs(move)>=.2:
        matches.append(('EARLY_MOMENTUM',min(31,13+min(10,ratio*3)+min(8,abs(three_move)*2))))
    if vol>=25000 and ratio>=1.5 and (close>prior_hi or close<prior_lo):
        matches.append(('BREAKOUT',min(35,20+min(9,ratio*3)+min(6,abs(move)*2))))
    trend_cross=(prev_close<=old20 and close>mean20 and mean20>mean50) or (prev_close>=old20 and close<mean20 and mean20<mean50)
    if trend_cross and ratio>=1.6 and vol>=25000:
        matches.append(('TREND_SHIFT',min(29,15+min(9,ratio*3)+min(5,abs(move)*2))))
    prior_move=100*(prev_close/bars[-5]['close']-1) if bars[-5]['close']>0 else 0
    if abs(prior_move)>=2.5 and move*prior_move<0 and abs(move)>=.8 and last_range>=typical_range*1.3 and ratio>=1.5 and vol>=25000:
        matches.append(('PUMP_DUMP_REVERSAL',min(34,17+min(9,abs(prior_move)*2)+min(8,ratio*2))))
    if not matches:return None
    # Liquidity and signal agreement raise alert priority, never imply probability.
    points=max(x[1] for x in matches)+min(18,7*(len(matches)-1))+min(15,max(0,math.log10(max(vol,1))-4)*7)
    score=min(100,round(35+points))
    primary=max(matches,key=lambda x:x[1])[0]
    direction='UP' if move>=0 else 'DOWN'
    return {'kind':primary,'kinds':[k for k,_ in matches],'direction':direction,
            'score':score,'volume_ratio':round(ratio,2),'move_pct':round(move,2),
            'three_bar_move_pct':round(three_move,2),'quote_volume':round(vol,2),
            'price':close,'origin_ts':int(last['time'])}

def ensure_tables(con):
    con.execute('''CREATE TABLE IF NOT EXISTS radar_events (
      id INTEGER PRIMARY KEY, exchange TEXT NOT NULL,symbol TEXT NOT NULL,origin_ts INTEGER NOT NULL,
      kind TEXT NOT NULL, direction TEXT NOT NULL,score INTEGER NOT NULL,details TEXT NOT NULL,
      created_at INTEGER NOT NULL, UNIQUE(exchange,symbol,origin_ts))''')
    con.execute('''CREATE TABLE IF NOT EXISTS radar_delivery (
      id INTEGER PRIMARY KEY, radar_id INTEGER NOT NULL,channel TEXT NOT NULL,
      status TEXT NOT NULL DEFAULT 'pending',external_id TEXT,last_error TEXT,
      created_at INTEGER NOT NULL,UNIQUE(radar_id,channel))''')
    con.execute('CREATE INDEX IF NOT EXISTS radar_del_by_status ON radar_delivery(status,created_at)')
    con.commit()

def record(con,exchange,symbol,event,cfg,clock=None):
    t=int(clock if clock is not None else time.time());score=int(event['score'])
    if score<int(cfg.get('radar_min_score',78)):return None
    # Cross-exchange duplicate suppression: strongest first seen event wins.
    cooldown=max(30,int(cfg.get('radar_symbol_cooldown_minutes',180)))*60
    if con.execute('SELECT 1 FROM radar_events WHERE symbol=? AND created_at>? LIMIT 1',(symbol,t-cooldown)).fetchone():return None
    try:
        cur=con.execute('INSERT INTO radar_events(exchange,symbol,origin_ts,kind,direction,score,details,created_at) VALUES(?,?,?,?,?,?,?,?)',
                 (exchange,symbol,event['origin_ts'],event['kind'],event['direction'],score,json.dumps(event),t))
    except sqlite3.IntegrityError:return None
    ident=cur.lastrowid
    if cfg.get('enable_telegram_free') and score>=int(cfg.get('radar_free_min_score',86)):
        cap=int(cfg.get('radar_free_daily_cap',2))
        if cap<=0 or con.execute("SELECT COUNT(*) FROM radar_delivery WHERE channel='telegram_free' AND created_at>=?",(t//86400*86400,)).fetchone()[0]<cap:
            con.execute('INSERT INTO radar_delivery(radar_id,channel,created_at) VALUES(?,?,?)',(ident,'telegram_free',t))
    if cfg.get('enable_telegram_vip'):
        cap=int(cfg.get('radar_vip_daily_cap',16))
        used=con.execute("SELECT COUNT(*) FROM radar_delivery WHERE channel='telegram_vip' AND created_at>=?",(t//86400*86400,)).fetchone()[0]
        if used<cap:con.execute('INSERT INTO radar_delivery(radar_id,channel,created_at) VALUES(?,?,?)',(ident,'telegram_vip',t))
    con.commit();return ident

def _price_text(value):
    """Preserve precision for low-priced coins without artificial zero rounding."""
    value=float(value)
    if value<=0:return f"${value:g}"
    return f"${value:,.8f}".rstrip('0').rstrip('.') if value < 0.01 else f"${value:,.6f}".rstrip('0').rstrip('.')

def _pair(symbol):
    for quote in ('USDT','USDC','BTC','ETH'):
        if symbol.endswith(quote) and len(symbol)>len(quote):
            return symbol[:-len(quote)]+'/'+quote
    return symbol

def message(row):
    """Concise Telegram template approved for the public Altcoin Radar channel."""
    e=json.loads(row['details'])
    up=row['direction']=='UP'
    label='🟢 BUY' if up else '🔴 SELL'
    pair=_pair(row['symbol'])
    kind=('Extra Trees SHORT · 12h / -3%' if row['kind']=='ML_EXTRA_TREES_SHORT' else 'Random Forest LONG · 12h / +3%' if row['kind']=='ML_RANDOM_FOREST_LONG' else row['kind'].replace('_',' ').title().replace('Pump Dump','Pump / Dump'))
    quote=pair.split('/')[-1] if '/' in pair else ''
    base=pair.split('/')[0]
    hashtags=' '.join('#'+''.join(c for c in token if c.isalnum()) for token in (base,quote) if token)
    change_label='1m Live' if e.get('partial_candle') else '5m'
    return (f"⚡ ALTCOIN RADAR\n\n"
            f"{label} {pair}\n\n"
            f"💰 Price: {_price_text(e['price'])}\n"
            f"📈 {change_label}: {e['move_pct']:+.2f}%\n"
            f"📊 Volume: {e['volume_ratio']:.1f}×\n"
            f"🔥 Strength: {e['score']}/100\n\n"
            f"{hashtags}\n\n"
            f"{pair} — {row['exchange']} {kind}")

def publish(con,cfg,send,clock=None):
    with _publish_lock:
        return _publish_locked(con,cfg,send,clock)

def _publish_locked(con,cfg,send,clock=None):
    jobs=con.execute("SELECT d.id AS job_id,d.channel,r.* FROM radar_delivery d JOIN radar_events r ON r.id=d.radar_id WHERE d.status='pending' ORDER BY d.id LIMIT 8").fetchall()
    for job in jobs:
        channel=job['channel']
        # Late activity alerts have no subscriber value. Never publish an old event.
        max_age=max(60,int(cfg.get('radar_max_alert_age_seconds',720)))
        if int(clock if clock is not None else time.time()) - (int(job['origin_ts'])+(0 if json.loads(job['details']).get('partial_candle') else 299)) > max_age:
            con.execute('UPDATE radar_delivery SET status=?,last_error=? WHERE id=?',
                        ('expired','Radar event aged out before delivery',job['job_id']))
            con.commit()
            logging.info('RADAR expired %s %s',channel,job['symbol'])
            continue
        # Persist in-flight BEFORE network I/O; uncertain results are not automatically retried.
        live=not cfg.get('dry_run',True) and cfg.get('allow_unvalidated_publication',False)
        if not live:
            logging.info('RADAR DRY RUN %s: %s',channel,message(job))
            con.execute('UPDATE radar_delivery SET status=? WHERE id=?',('dry_run',job['job_id']));con.commit();continue
        con.execute('UPDATE radar_delivery SET status=? WHERE id=?',('in_flight',job['job_id']));con.commit()
        try:
            ext=send(channel,message(job))
            con.execute('UPDATE radar_delivery SET status=?,external_id=? WHERE id=?',('sent',str(ext),job['job_id']))
            logging.info('RADAR SENT %s %s %s',channel,job['symbol'],job['kind'])
        except Exception as exc:
            con.execute('UPDATE radar_delivery SET status=?,last_error=? WHERE id=?',('needs_review',str(exc)[:450],job['job_id']))
            logging.warning('RADAR delivery needs review %s: %s',channel,exc)
        con.commit()
