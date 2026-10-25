"""Windows-first market signal publisher. No orders. stdlib only."""
import argparse, base64, hashlib, hmac, html, json, logging, os, sqlite3, sys, threading, time, urllib.error, urllib.parse, urllib.request, secrets
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from strategies import evaluate
from chart_media import draw_chart, telegram_photo, x_photo
from market_feeds import fetch as exchange_candles
from market_discovery import discover_all
from derivatives import discover_contracts
from signal_priority import consolidate, channel_allowed
from market_intelligence import enrich_signal
from realtime_radar import EarlyRadar, init_tables, early_message
from binance_live_radar import BinanceLiveRadar
from gate_live_radar import GateLiveRadar
from publishing_setup import readiness, verify_telegram, verify_x
from x_local_bridge import submit as x_local_submit
import radar_engine
import coverage_monitor
import two_model_engine
import payment_service
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT=Path(__file__).resolve().parent
DB=ROOT/'signal_service.sqlite'
LOG=ROOT/'signal_service.log'
LIVE_MONITOR=None
GATE_MONITOR=None
API='https://api.binance.com/api/v3/klines'
SCHEMA='''
CREATE TABLE IF NOT EXISTS signals (id INTEGER PRIMARY KEY AUTOINCREMENT, exchange TEXT NOT NULL, symbol TEXT NOT NULL, side TEXT NOT NULL, origin_ts INTEGER NOT NULL, created_at INTEGER NOT NULL, entry REAL NOT NULL, target REAL NOT NULL, stop REAL NOT NULL, horizon_minutes INTEGER NOT NULL, expires_at INTEGER NOT NULL, status TEXT NOT NULL, exit_price REAL, exit_time INTEGER, exit_reason TEXT, net_pct REAL, strength REAL NOT NULL, reason TEXT NOT NULL, UNIQUE(exchange,symbol,side,origin_ts));
CREATE TABLE IF NOT EXISTS delivery (id INTEGER PRIMARY KEY AUTOINCREMENT, signal_id INTEGER NOT NULL, channel TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending', attempts INTEGER NOT NULL DEFAULT 0, next_attempt INTEGER NOT NULL DEFAULT 0, external_id TEXT, last_error TEXT, UNIQUE(signal_id,channel,kind));
CREATE TABLE IF NOT EXISTS system (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS observed_markets (exchange TEXT NOT NULL, symbol TEXT NOT NULL, first_seen INTEGER NOT NULL, last_seen INTEGER NOT NULL, PRIMARY KEY(exchange,symbol));
CREATE TABLE IF NOT EXISTS members (user_id INTEGER PRIMARY KEY, username TEXT, expires_at INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'active', updated_at INTEGER NOT NULL, invite_link TEXT, last_error TEXT);
CREATE TABLE IF NOT EXISTS sales_events (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, event TEXT NOT NULL, created_at INTEGER NOT NULL, note TEXT);
'''
DEFAULT={'dry_run':True,'enable_x':False,'enable_telegram':False,'enable_telegram_free':False,'enable_telegram_vip':False,'free_open_per_day':2,'enable_vip_member_enforcement':False,'vip_invite_expire_hours':24,'vip_invite_max_uses':1,'vip_join_request_mode':True,'vip_sales_url':'','telegram_sales_bot_username':'EgoniaSignalsBot','enable_trc20_payments':False,'subscription_price_usdt':'9.90','subscription_days':30,'payment_order_expiry_minutes':120,'trc20_recipient_address':'','min_volume_usdt':100000,'min_volume_ratio':4.0,'min_move_pct':0.8,'max_move_pct':8.0,'max_signals_per_day':18,'cooldown_hours':2,'target_pct':5.0,'stop_pct':2.5,'horizon_minutes':240,'roundtrip_cost_pct':0.4,'poll_seconds':60,'max_spread_pct':0.2,'allow_unvalidated_publication':False,'exchanges':['Binance','MEXC','Gate'],'strategy_mode':True,'strategy_timeframes':['5m','15m','1h'],'strategy_names':['EMA_TREND','DONCHIAN_20','BB_SQUEEZE','RSI_BB_REVERSION','ATR_CHANNEL','MACD_MOMENTUM','VOLUME_BREAKOUT','VOLUME_ACCELERATION','MOMENTUM_IGNITION'],'enable_result_tracking':False,'enable_charts':True,'chart_timeframe':'auto','panel_port':8787,'auto_discovery':True,'min_daily_quote_volume_usdt':1000000,'max_pairs_per_exchange':60,'markets_per_cycle':12,'discovery_refresh_seconds':3600,'altcoin_focus':False,'max_daily_quote_volume_usdt':150000000,'symbols':['BTCUSDT','ETHUSDT','SOLUSDT','XRPUSDT','DOGEUSDT','SUIUSDT','PEPEUSDT','BNBUSDT','ADAUSDT','AVAXUSDT']}

def now(): return int(time.time())
def utc(t):return datetime.fromtimestamp(t,timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
def db():
    c=sqlite3.connect(DB, timeout=30,check_same_thread=False);c.row_factory=sqlite3.Row;c.execute('PRAGMA journal_mode=WAL');c.executescript(SCHEMA);payment_service.ensure_tables(c);return c

def get_json(url,timeout=15):
    req=urllib.request.Request(url,headers={'User-Agent':'EgoniaRadar/2.2'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.load(r)

def candles(symbol,limit=100,interval="5m"):
    query=urllib.parse.urlencode({'symbol':symbol,'interval':interval,'limit':limit})
    data=get_json(API+'?'+query)
    return [{'time':int(x[0])//1000,'open':float(x[1]),'high':float(x[2]),'low':float(x[3]),'close':float(x[4]),'volume':float(x[5]),'quote_volume':float(x[7]),'close_time':int(x[6])//1000} for x in data]

def decide(rows,cfg):
    if len(rows)<65:return None
    completed=[r for r in rows if r['close_time']<=now()-2]
    if len(completed)<65:return None
    r=completed[-1];prior=completed[-25:-1]
    if not prior:return None
    if any(completed[k+1]['time']-completed[k]['time']!=300 for k in range(len(completed)-26,len(completed)-1)):
        return None
    if now()-r['close_time']>900:return None
    volume_avg=sum(x['quote_volume'] for x in prior)/len(prior)
    if volume_avg<=0:return None
    ratio=r['quote_volume']/volume_avg
    pct=100*(r['close']/r['open']-1)
    if r['quote_volume']<cfg['min_volume_usdt'] or ratio<cfg['min_volume_ratio'] or not(cfg['min_move_pct']<=abs(pct)<=cfg['max_move_pct']):return None
    side='LONG' if pct>0 else 'SHORT'
    # Pure activity trigger, not proven predictive alpha.
    strength=min(100,round(25+ratio*7+abs(pct)*3,1))
    return {'side':side,'origin_ts':r['time'],'entry':r['close'],'strength':strength,'ratio':ratio,'pct':pct,'reason':f'5m volume {ratio:.1f}x baseline; candle {pct:+.2f}%; price-activity heuristic (unvalidated)'}

def should_publish_x(signal,cfg):
    strength=float(signal['strength'] if isinstance(signal,sqlite3.Row) else signal[0] if isinstance(signal,tuple) else signal['strength'])
    reason=signal['reason'] if isinstance(signal,(sqlite3.Row,dict)) else signal[1]
    return strength>=float(cfg.get('x_min_signal_strength',75)) and any(
        name in reason for name in cfg.get('x_featured_strategies',['VOLUME_BREAKOUT','DONCHIAN_20','BB_SQUEEZE','VOLUME_ACCELERATION','MOMENTUM_IGNITION']))

def queue(con,id_,cfg,kind='open'):
    enabled_routes=[('telegram',cfg['enable_telegram']),('telegram_free',cfg.get('enable_telegram_free',False)),('telegram_vip',cfg.get('enable_telegram_vip',False)),('x',cfg['enable_x'])]
    raw=con.execute('SELECT strength,reason FROM signals WHERE id=?',(id_,)).fetchone()
    signal={'strength':raw[0],'reason':raw[1]}
    for channel,enabled in enabled_routes:
        if not enabled:continue
        if kind=='open' and channel=='x' and cfg.get('x_featured_strategies') and not channel_allowed(signal,channel,cfg):continue
        if kind=='open' and channel=='telegram_free' and 'free_min_signal_strength' in cfg and not channel_allowed(signal,channel,cfg):continue
        if kind=='open' and channel in ('x','telegram_free','telegram_vip'):
            day=now()//86400
            limits={'x':'x_open_per_day','telegram_free':'free_open_per_day','telegram_vip':'vip_open_per_day'}
            field=limits[channel]
            cap=max(0,int(cfg.get(field,{'x':5,'telegram_free':2,'telegram_vip':24}[channel])))
            used=con.execute("SELECT COUNT(*) FROM delivery d JOIN signals s ON s.id=d.signal_id WHERE d.channel=? AND d.kind='open' AND s.created_at>=? AND s.created_at<?",(channel,day*86400,(day+1)*86400)).fetchone()[0]
            if used>=cap:continue
        con.execute('INSERT OR IGNORE INTO delivery(signal_id,channel,kind) VALUES(?,?,?)',(id_,channel,kind))

def new_signal(con,symbol,detail,cfg,source_rows=None,exchange='Binance'):
    tick=now(); cutoff=tick-86400
    if con.execute('SELECT COUNT(*) FROM signals WHERE created_at>=?',(cutoff,)).fetchone()[0]>=cfg['max_signals_per_day']:return False
    if con.execute('SELECT 1 FROM signals WHERE symbol=? AND created_at>? LIMIT 1',(symbol,tick-int(cfg['cooldown_hours']*3600))).fetchone():return False
    price=detail['entry'];sgn=1 if detail['side']=='LONG' else -1
    target=price*(1+sgn*cfg['target_pct']/100);stop=price*(1-sgn*cfg['stop_pct']/100)
    try:
        con.execute('INSERT INTO signals(exchange,symbol,side,origin_ts,created_at,entry,target,stop,horizon_minutes,expires_at,status,strength,reason) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(exchange,symbol,detail['side'],detail['origin_ts'],tick,price,target,stop,cfg['horizon_minutes'],tick+cfg['horizon_minutes']*60,'ACTIVE',detail['strength'],detail['reason']))
    except sqlite3.IntegrityError:return False
    ident=con.execute('SELECT last_insert_rowid()').fetchone()[0]
    if cfg.get('enable_charts',True) and source_rows is not None:
        try:
            signal=dict(con.execute('SELECT * FROM signals WHERE id=?',(ident,)).fetchone())
            draw_chart(source_rows,signal,ROOT/'charts'/f'signal_{ident}.png')
        except Exception as ex:logging.warning('Chart for signal #%s not generated: %s',ident,ex)
    queue(con,ident,cfg)
    con.commit();logging.info('NEW SIGNAL #%s %s %s at %s',ident,symbol,detail['side'],price);return True

def close_signals(con,data,cfg):
    for s in con.execute("SELECT * FROM signals WHERE status='ACTIVE'").fetchall():
        rows=data.get(s['symbol'])
        if not rows:continue
        # Use only subsequent completed bars; OHLC cannot resolve stop/target tie -> stop-first.
        bars=[b for b in rows if b['time']>s['origin_ts'] and b['close_time']<=now()-2]
        bars.sort(key=lambda x:x['time'])
        # A gap makes the stop/target order unknowable; do not synthesize a result.
        if bars and (bars[0]['time'] != s['origin_ts']+300 or any(bars[i]['time']-bars[i-1]['time']!=300 for i in range(1,len(bars)))):
            con.execute("UPDATE signals SET status='CLOSED',exit_reason='DATA_INVALID',exit_time=? WHERE id=?",(now(),s['id']))
            queue(con,s['id'],cfg,'close')
            continue
        why=None;price=None;exit_time=None
        for b in bars:
            if s['side']=='LONG': stop_hit=b['low']<=s['stop'];target_hit=b['high']>=s['target']
            else:stop_hit=b['high']>=s['stop'];target_hit=b['low']<=s['target']
            if stop_hit:why='STOP';price=s['stop'];exit_time=b['time'];break
            if target_hit:why='TARGET';price=s['target'];exit_time=b['time'];break
            if b['close_time']>=s['expires_at']:why='TIMEOUT';price=b['close'];exit_time=b['close_time'];break
        if not why and now()>s['expires_at']+600:
            # Missing continuous data is unknown, never fabricated as a win/loss.
            why='DATA_INVALID';price=None;exit_time=now()
        if not why:continue
        net=(100*(price/s['entry']-1)*(1 if s['side']=='LONG' else -1)-cfg['roundtrip_cost_pct']) if price is not None else None
        con.execute('UPDATE signals SET status=?,exit_price=?,exit_time=?,exit_reason=?,net_pct=? WHERE id=?',('CLOSED',price,exit_time,why,net,s['id']))
        queue(con,s['id'],cfg,'close');logging.info('CLOSED #%s %s net %s',s['id'],why,net)
    con.commit()

def format_msg(s,kind):
    if kind=='open':
        return f"EGONIA SIGNAL #{s['id']} | {s['symbol']} {s['side']}\nExchange: {s['exchange']}\nEntry reference: {s['entry']:.10g}\nTarget: {s['target']:.10g}\nStop: {s['stop']:.10g}\nHorizon: {s['horizon_minutes']}m\nDetected: {utc(s['created_at'])}\nReason: {s['reason']}\nResearch alert; not an executed order."
    p=f"{s['net_pct']:+.2f}%" if s['net_pct'] is not None else 'UNVERIFIED'
    return f"EGONIA SIGNAL CLOSED #{s['id']} | {s['symbol']} {s['side']}\nReason: {s['exit_reason']}\nSimulated net: {p}\nResearch simulation; no orders executed."

def telegram_call(token,method,params):
    data=urllib.parse.urlencode(params).encode('utf-8')
    req=urllib.request.Request(f'https://api.telegram.org/bot{token}/{method}',data=data)
    with urllib.request.urlopen(req,timeout=20) as r:
        out=json.load(r)
        if not out.get('ok'):raise RuntimeError(str(out))
        return out['result']

def process_vip_join_requests(con, updates, vip_id, token, clock=None):
    """Approve only the explicitly paid/current user. All outcomes are persisted."""
    timestamp=now() if clock is None else clock
    handled=0
    for update in updates:
        try:
            req=update.get('chat_join_request')
            if not req or str(req.get('chat',{}).get('id'))!=str(vip_id):continue
            uid=int(req['from']['id'])
            record=con.execute('SELECT status,expires_at FROM members WHERE user_id=?',(uid,)).fetchone()
            good=bool(record and record['status']=='active' and record['expires_at']>timestamp)
            action='approveChatJoinRequest' if good else 'declineChatJoinRequest'
            telegram_call(token,action,{'chat_id':vip_id,'user_id':uid})
            con.execute('INSERT INTO sales_events(user_id,event,created_at,note) VALUES(?,?,?,?)',(uid,'join_approved' if good else 'join_declined',timestamp,'telegram_join_request'))
            handled+=1
        except Exception as exc:
            logging.warning('VIP join request handling failed: %s',exc)
            raise  # caller must NOT advance update offset on failure
    con.commit()
    return handled

def process_payment_message(con,event,cfg,token,clock=None):
    msg=event.get('message') or {}
    chat=msg.get('chat') or {};sender=msg.get('from') or {}
    if chat.get('type')!='private' or not sender.get('id'):return 0
    text=str(msg.get('text','')).strip();uid=int(sender['id']);stamp=now() if clock is None else clock
    username=str(sender.get('username',''))
    if text.startswith('/start'):
        set_payment_state(con,uid,'idle')
        keyboard={'inline_keyboard':[
          [{'text':'🔐 Unlock VIP — 9.90 USDT','callback_data':'buy_vip'}],
          [{'text':'📡 Free Signals','url':'https://t.me/EgoniaSignalsFree'},{'text':'How It Works','callback_data':'how_it_works'}]]}
        telegram_send(token,uid,"⚡ EGONIA VIP\n\nAI-powered LONG & SHORT crypto scalp alerts.\n\n✓ Entry, target and stop levels\n✓ Up to 6 curated alerts per day\n✓ Instant private-channel access\n✓ 30 days for 9.90 USDT\n\nPayment: USDT on TRON (TRC20)\n\nResearch alerts only. Trading involves risk.",keyboard)
    elif text.startswith(('/abonelik','/subscribe')):
        parts=text.split()
        if len(parts)==1:
            set_payment_state(con,uid,'awaiting_sender')
            telegram_send(token,uid,"Send the TRON address you will pay from.\n\nIt starts with T and can be copied from Trust Wallet. Never send your seed phrase or private key.")
        elif len(parts)==2:create_payment_order(con,uid,username,parts[1],cfg,token,stamp)
        else:raise ValueError('Usage: /subscribe YOUR_TRON_SENDER_ADDRESS')
    elif text.startswith(('/odeme','/payment')):
        parts=text.split()
        if len(parts)!=2:raise ValueError('Usage: /payment 64_CHARACTER_TXID')
        expiry=payment_service.claim_order(con,uid,parts[1],cfg,clock=stamp)
        try:link=ensure_vip_invite(con,uid,cfg,token,stamp)
        except Exception as exc:
            logging.warning('Payment confirmed but invite creation failed for %s: %s',uid,exc)
            telegram_send(token,uid,f"Payment confirmed. Your VIP membership is active until {utc(expiry)}. Send /invite to retry your private join link.")
        else:
            telegram_send(token,uid,f"✅ Payment confirmed\nVIP active until: {utc(expiry)}\n\nYour private VIP join link:\n{link}")
        set_payment_state(con,uid,'paid')
    elif text.startswith(('/davet','/invite')):
        link=ensure_vip_invite(con,uid,cfg,token,stamp)
        telegram_send(token,uid,'Your private VIP join link: '+link)
    elif get_payment_state(con,uid)=='awaiting_sender' and text.startswith('T'):
        create_payment_order(con,uid,username,text,cfg,token,stamp)
    elif get_payment_state(con,uid)=='awaiting_txid' and len(text)==64 and all(c in '0123456789abcdefABCDEF' for c in text):
        expiry=payment_service.claim_order(con,uid,text,cfg,clock=stamp)
        try:link=ensure_vip_invite(con,uid,cfg,token,stamp)
        except Exception as exc:
            logging.warning('Payment confirmed but invite creation failed for %s: %s',uid,exc)
            telegram_send(token,uid,f"Payment confirmed. Your VIP membership is active until {utc(expiry)}. Send /invite to retry your private join link.")
        else:telegram_send(token,uid,f"✅ Payment confirmed\nVIP active until: {utc(expiry)}\n\nYour private VIP join link:\n{link}")
        set_payment_state(con,uid,'paid')
    else:return 0
    return 1

def payment_state_key(uid):return f'payment_state:{int(uid)}'
def set_payment_state(con,uid,state):
    con.execute('INSERT OR REPLACE INTO system(key,value) VALUES(?,?)',(payment_state_key(uid),state));con.commit()
def get_payment_state(con,uid):
    row=con.execute('SELECT value FROM system WHERE key=?',(payment_state_key(uid),)).fetchone()
    return row['value'] if row else 'idle'

def create_payment_order(con,uid,username,sender_address,cfg,token,stamp):
    order=payment_service.create_order(con,uid,username,sender_address,cfg,stamp)
    price=int(order['expected_atomic'])/1_000_000;set_payment_state(con,uid,'awaiting_txid')
    telegram_send(token,uid,f"🧾 EGONIA VIP ORDER #{order['id']}\n\nNetwork: TRON (TRC20)\nExact amount: {price:.2f} USDT\nRecipient:\n{order['recipient_address']}\n\nAfter sending, paste the 64-character TXID here. No command is required.\n\n⏱ This order expires in 2 hours. Send the exact amount from the address you registered.")

def process_payment_callback(con,event,cfg,token,clock=None):
    query=event.get('callback_query') or {};sender=query.get('from') or {};uid=sender.get('id')
    if not uid:return 0
    telegram_call(token,'answerCallbackQuery',{'callback_query_id':query.get('id','')})
    data=query.get('data','')
    if data=='buy_vip':
        set_payment_state(con,uid,'awaiting_sender')
        telegram_send(token,uid,"🔐 START YOUR VIP MEMBERSHIP\n\nSend the TRON address you will pay from. It starts with T and can be copied from Trust Wallet.\n\nNever send your seed phrase or private key.")
    elif data=='how_it_works':
        telegram_send(token,uid,"HOW IT WORKS\n\n1. Send your TRON wallet address.\n2. Pay exactly 9.90 USDT via TRC20.\n3. Paste the transaction TXID.\n4. Receive your private VIP link automatically.\n\nAccess lasts 30 days. Network fees are paid separately in TRX.")
    else:return 0
    return 1

def poll_vip_join_requests(con, cfg):
    joins=cfg.get('enable_vip_member_enforcement',False) and cfg.get('vip_join_request_mode',True)
    payments=cfg.get('enable_trc20_payments',False)
    if not joins and not payments:return 0
    token=os.getenv('TELEGRAM_BOT_TOKEN','');vip=os.getenv('TELEGRAM_VIP_CHAT_ID','')
    if not token or not vip:raise RuntimeError('Missing Telegram bot token / VIP chat')
    row=con.execute("SELECT value FROM system WHERE key='telegram_update_offset'").fetchone()
    offset=int(row['value']) if row else 0
    result=telegram_call(token,'getUpdates',{'offset':offset,'limit':100,'timeout':0,'allowed_updates':json.dumps(['chat_join_request','message','callback_query'])})
    count=0
    for event in result:
        try:
            if event.get('chat_join_request') and joins:count+=process_vip_join_requests(con,[event],vip,token)
            elif event.get('message') and payments:count+=process_payment_message(con,event,cfg,token)
            elif event.get('callback_query') and payments:count+=process_payment_callback(con,event,cfg,token)
        except ValueError as exc:
            chat=(event.get('message') or {}).get('chat',{}).get('id')
            if chat:telegram_send(token,chat,'Payment could not be verified: '+str(exc))
        con.execute("INSERT OR REPLACE INTO system(key,value) VALUES('telegram_update_offset',?)",(str(int(event['update_id'])+1),))
        con.commit()
    return count

def run_membership_bot(cfg,once=False):
    """The sole Telegram getUpdates consumer for payments and VIP join requests."""
    con=db()
    try:
        while True:
            try:poll_vip_join_requests(con,cfg)
            except Exception as exc:
                logging.warning('Membership bot polling failed: %s',exc)
                if once:raise
            if once:break
            time.sleep(max(2,int(cfg.get('membership_poll_seconds',3))))
    finally:con.close()

def telegram_send(token,chat_id,msg,reply_markup=None):
    params={'chat_id':chat_id,'text':msg,'disable_web_page_preview':'true'}
    if reply_markup is not None:params['reply_markup']=json.dumps(reply_markup)
    return str(telegram_call(token,'sendMessage',params)['message_id'])

def vip_sales_cta(cfg):
    username=str(cfg.get('telegram_sales_bot_username','EgoniaSignalsBot')).strip().lstrip('@')
    price=str(cfg.get('subscription_price_usdt','9.90'))
    days=int(cfg.get('subscription_days',30))
    return (f"🔐 Unlock EGONIA VIP — {price} USDT / {days} days\n"
            f"Full entry, target and stop alerts.\n"
            f"👉 https://t.me/{username}?start=vip")

def ensure_vip_invite(con,uid,cfg,token,stamp):
    member=con.execute("SELECT * FROM members WHERE user_id=? AND status='active' AND expires_at>?",(uid,stamp)).fetchone()
    if not member:raise ValueError('No active VIP membership was found')
    vip=os.getenv('TELEGRAM_VIP_CHAT_ID','')
    if not vip:raise RuntimeError('VIP chat is not configured')
    link=member['invite_link']
    if not link:
        link=telegram_call(token,'createChatInviteLink',{'chat_id':vip,'name':f'VIP-{uid}','expire_date':stamp+max(1,int(cfg.get('vip_invite_expire_hours',24)))*3600,'creates_join_request':'true'})['invite_link']
        con.execute('UPDATE members SET invite_link=?,updated_at=? WHERE user_id=?',(link,stamp,uid));con.commit()
    return link

def configure_membership_bot(cfg):
    token=os.getenv('TELEGRAM_BOT_TOKEN','');vip=os.getenv('TELEGRAM_VIP_CHAT_ID','')
    if not token or not vip:raise RuntimeError('Missing Telegram bot token / VIP chat')
    bot=telegram_call(token,'getMe',{})
    commands=[{'command':'start','description':'View VIP subscription details'},
              {'command':'subscribe','description':'Create a 9.90 USDT payment order'},
              {'command':'payment','description':'Verify your TRC20 payment TXID'},
              {'command':'invite','description':'Get your active VIP join link'}]
    telegram_call(token,'setMyCommands',{'commands':json.dumps(commands),'scope':json.dumps({'type':'all_private_chats'})})
    membership=telegram_call(token,'getChatMember',{'chat_id':vip,'user_id':bot['id']})
    creator=membership.get('status')=='creator'
    capable=membership.get('status')=='administrator' and membership.get('can_invite_users') and membership.get('can_restrict_members')
    if not (creator or capable):
        raise RuntimeError('Bot needs VIP channel admin permissions to invite and remove members')
    logging.info('Membership bot ready: @%s | VIP chat %s',bot.get('username','unknown'),vip)
    return bot

def x_auth_header(method,uri):
    credentials={k:os.getenv(k,'') for k in ('X_API_KEY','X_API_SECRET','X_ACCESS_TOKEN','X_ACCESS_TOKEN_SECRET')}
    if not all(credentials.values()):raise RuntimeError('Missing X API credentials')
    key,secret,token,toksecret=[credentials[k] for k in credentials]
    oauth={'oauth_consumer_key':key,'oauth_nonce':secrets.token_hex(16),'oauth_signature_method':'HMAC-SHA1','oauth_timestamp':str(now()),'oauth_token':token,'oauth_version':'1.0'}
    enc=lambda v:urllib.parse.quote(str(v),safe='~-._')
    # Include query parameters in OAuth signature base string.
    base_url=urllib.parse.urlsplit(uri);target=urllib.parse.urlunsplit((base_url.scheme,base_url.netloc,base_url.path,'',''))
    params=list(oauth.items())+urllib.parse.parse_qsl(base_url.query,keep_blank_values=True)
    parameter='&'.join(f'{enc(k)}={enc(v)}' for k,v in sorted(params,key=lambda item:(enc(item[0]),enc(item[1]))))
    base='&'.join((enc(method.upper()),enc(target),enc(parameter)))
    oauth['oauth_signature']=base64.b64encode(hmac.new((enc(secret)+'&'+enc(toksecret)).encode(),base.encode(),hashlib.sha1).digest()).decode()
    return 'OAuth '+', '.join(f'{enc(k)}="{enc(v)}"' for k,v in sorted(oauth.items()))

def x_send(text_msg,config):
    uri='https://api.x.com/2/tweets'
    req=urllib.request.Request(uri,data=json.dumps({'text':text_msg[:280]},ensure_ascii=False).encode('utf-8'),headers={'Authorization':x_auth_header('POST',uri),'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=20) as r:return str(json.load(r)['data']['id'])


def commercial_msg(s,kind,channel,cfg):
    text=format_msg(s,kind)
    if channel=='telegram_free':
        if kind=='open':
            text=(f"FREE EGONIA SIGNAL #{s['id']} | {s['symbol']} {s['side']}\n"
                  f"Detected: {utc(s['created_at'])}\n"
                  f"Public alert: unusual trading activity. Detailed entry/target/stop: VIP.")
        else:
            text=f"FREE SIGNAL UPDATE #{s['id']} | {s['symbol']}: {s['exit_reason']} | net simulated: {s['net_pct']:+.2f}%" if s['net_pct'] is not None else f"FREE SIGNAL UPDATE #{s['id']} | {s['symbol']}: UNVERIFIED"
        text+='\n\n'+vip_sales_cta(cfg)
    elif channel=='telegram_vip':
        text=text.replace('PAPER SIGNAL', 'EGONIA VIP SIGNAL',1)
    elif channel=='x':
        if kind=='open':
            text=f"EGONIA {s['side']} {s['symbol']} | {s['exchange']}\nEntry ref: {s['entry']:.8g} | TP: {s['target']:.8g} | SL: {s['stop']:.8g}\n#{s['id']} {utc(s['created_at'])}\nTrack outcomes; not guaranteed."
        else:
            text=f"SIGNAL #{s['id']} CLOSED {s['symbol']} {s['side']}: {s['exit_reason']} | simulated net {s['net_pct']:+.2f}%" if s['net_pct'] is not None else f"SIGNAL #{s['id']} CLOSED: UNVERIFIED"
        url=cfg.get('vip_sales_url','').strip()
        if url and len(text)+len(url)+7<=280:text+='\nVIP: '+url
    return text

def deliveries(con,cfg):
    jobs=con.execute("SELECT d.*,s.id AS signal_uid,s.exchange,s.symbol,s.side,s.origin_ts,s.created_at,s.entry,s.target,s.stop,s.horizon_minutes,s.expires_at,s.status AS signal_status,s.exit_price,s.exit_time,s.exit_reason,s.net_pct,s.strength,s.reason,d.id AS delivery_id FROM delivery d JOIN signals s ON s.id=d.signal_id WHERE d.status='pending' AND d.next_attempt<=? ORDER BY d.id LIMIT 15",(now(),)).fetchall()
    for job in jobs:
        channel=job['channel'];msg=commercial_msg(dict(job)|{'id':job['signal_uid']},job['kind'],channel,cfg);err=None;ext=None
        # Mark a live delivery BEFORE contacting a third-party API. If the network
        # times out after acceptance we must not silently post it twice.
        live=not cfg['dry_run'] and cfg.get('allow_unvalidated_publication',False)
        if live:
            con.execute("UPDATE delivery SET status='in_flight',attempts=attempts+1 WHERE id=?",(job['delivery_id'],))
            con.commit()
        try:
            if not live:
                logging.info('DRY_RUN %s %s\n%s',channel,job['kind'],msg);ext='dry-run'
            elif channel in ('telegram','telegram_free','telegram_vip'):
                tok=os.getenv('TELEGRAM_BOT_TOKEN','');chat=os.getenv({'telegram':'TELEGRAM_CHAT_ID','telegram_free':'TELEGRAM_FREE_CHAT_ID','telegram_vip':'TELEGRAM_VIP_CHAT_ID'}[channel],'')
                if not(tok and chat):raise RuntimeError('Missing Telegram token or configured channel ID')
                chart=ROOT/'charts'/f"signal_{job['signal_uid']}.png"
                if cfg.get('enable_charts',True) and job['kind']=='open' and chart.is_file():ext=telegram_photo(tok,chat,msg,chart)
                else:ext=telegram_send(tok,chat,msg)
            elif channel=='x':
                chart=ROOT/'charts'/f"signal_{job['signal_uid']}.png"
                if cfg.get('x_backend','official')=='local_xpm':
                    ext=x_local_submit(msg,chart if cfg.get('enable_charts',True) and job['kind']=='open' and chart.is_file() else None, cfg.get('xpm_origin','http://127.0.0.1:5000'),bool(cfg.get('xpm_auto_publish',False)))
                elif cfg.get('enable_charts',True) and job['kind']=='open' and chart.is_file():ext=x_photo(msg,chart,x_auth_header)
                else:ext=x_send(msg,cfg)
            else:raise RuntimeError('Unknown channel')
        except Exception as ex:err=f'{type(ex).__name__}: {ex}'[:700];logging.warning('Delivery failed %s: %s',channel,err)
        if err:
            attempts=job['attempts']+1
            # Ambiguous remote acceptance is not automatically retried.
            # A human can reconcile it using the provider's posting history.
            status='needs_review' if live else ('failed' if attempts>=6 else 'pending')
            con.execute('UPDATE delivery SET status=?,attempts=?,next_attempt=?,last_error=? WHERE id=?',(status,attempts,now()+min(3600,60*2**min(attempts,6)),err,job['delivery_id']))
        else:
            # A local XPM draft or background queue acceptance is NOT a published tweet.
            delivery_status = ('draft' if isinstance(ext,str) and ext.startswith('xpm-draft:')
                               else 'queued_external' if isinstance(ext,str) and ext.startswith('xpm-queued:')
                               else 'sent')
            con.execute("UPDATE delivery SET status=?,attempts=attempts+1,external_id=?,last_error=NULL WHERE id=?",(delivery_status,ext,job['delivery_id']))
        con.commit()

def early_deliveries(con, cfg):
    if not cfg.get('enable_early_alerts', True):return
    for alert in con.execute("SELECT * FROM early_alerts WHERE status='pending' ORDER BY id LIMIT 10").fetchall():
        message=early_message(alert)
        live=not cfg['dry_run'] and cfg.get('allow_unvalidated_publication',False)
        if not live:
            logging.info('DRY_RUN EARLY ALERT\n%s',message)
            con.execute("UPDATE early_alerts SET status='dry_run' WHERE id=?",(alert['id'],))
            con.commit()
            continue
        if not (cfg.get('enable_telegram_vip',False) or (cfg.get('early_publish_x',False) and cfg.get('enable_x',False))):
            con.execute("UPDATE early_alerts SET status='not_configured' WHERE id=?",(alert['id'],));con.commit()
            continue
        # No auto retry after a possibly accepted remote request.
        con.execute("UPDATE early_alerts SET status='in_flight' WHERE id=?",(alert['id'],));con.commit()
        try:
            if cfg.get('enable_telegram_vip',False):
                telegram_send(os.environ['TELEGRAM_BOT_TOKEN'],os.environ['TELEGRAM_VIP_CHAT_ID'],message)
            if cfg.get('early_publish_x',False) and cfg.get('enable_x',False):
                if cfg.get('x_backend','official') == 'local_xpm':
                    x_local_submit(message, None, cfg.get('xpm_origin','http://127.0.0.1:5000'), bool(cfg.get('xpm_auto_publish',False)))
                else:
                    x_send(message,cfg)
            con.execute("UPDATE early_alerts SET status='sent' WHERE id=?",(alert['id'],))
        except Exception as exc:
            con.execute("UPDATE early_alerts SET status='needs_review',last_error=? WHERE id=?",(str(exc)[:500],alert['id']))
        con.commit()


def operations_snapshot(con, clock=None):
    init_tables(con)
    radar_engine.ensure_tables(con)
    coverage_monitor.ensure_tables(con)
    tick=now() if clock is None else clock
    last_row=con.execute("SELECT value FROM system WHERE key='last_cycle'").fetchone()
    last=int(last_row[0]) if last_row else None
    started_row=con.execute("SELECT value FROM system WHERE key='cycle_started'").fetchone()
    started=int(started_row[0]) if started_row else None
    errors_row=con.execute("SELECT value FROM system WHERE key='last_cycle_errors'").fetchone()
    scanned_row=con.execute("SELECT value FROM system WHERE key='last_cycle_scanned'").fetchone()
    cycle_running=bool(started and (last is None or started>last) and tick-started<1800)
    counts={r['status']:r['n'] for r in con.execute('SELECT status,COUNT(*) n FROM delivery GROUP BY status')}
    routes={r['channel']:r['n'] for r in con.execute('SELECT channel,COUNT(*) n FROM delivery GROUP BY channel')}
    errors=[dict(r) for r in con.execute("SELECT id,channel,signal_id,status,attempts,last_error FROM delivery WHERE status IN ('needs_review','failed') ORDER BY id DESC LIMIT 20")]
    return {'live_binance':LIVE_MONITOR.snapshot() if LIVE_MONITOR is not None else {'enabled':False},'live_gate':GATE_MONITOR.snapshot() if GATE_MONITOR is not None else {'enabled':False},'brand':'Egonia','last_cycle_utc':utc(last) if last else None,'last_cycle_age_seconds':tick-last if last else None,
            'scanner_fresh':bool(cycle_running or (last and tick-last<=900)),'scanner_running':cycle_running,'cycle_started_utc':utc(started) if started else None,'last_cycle_scanned':int(scanned_row[0]) if scanned_row else None,'last_cycle_errors':int(errors_row[0]) if errors_row else None,'deliveries':counts,'routes':routes,
            'attention_required':errors,'signals_total':con.execute('SELECT COUNT(*) FROM signals').fetchone()[0],
            'observed_markets':con.execute('SELECT COUNT(*) FROM observed_markets').fetchone()[0],
            'early_alerts_total':con.execute('SELECT COUNT(*) FROM early_alerts').fetchone()[0],
            'early_alerts_recent':[dict(x) for x in con.execute('SELECT id,symbol,side,move_pct,volume_ratio,status FROM early_alerts ORDER BY id DESC LIMIT 20')],
            'coverage':json.loads((con.execute("SELECT value FROM system WHERE key='coverage_json'").fetchone() or ['{}'])[0]),
            'radar_events_total':con.execute('SELECT COUNT(*) FROM radar_events').fetchone()[0],
            'radar_recent':[dict(x) for x in con.execute("""SELECT r.id,r.exchange,r.symbol,r.kind,r.direction,r.score,r.origin_ts,r.created_at,
                  COALESCE(d.status, 'not_queued') AS telegram_status,d.last_error
                  FROM radar_events r LEFT JOIN radar_delivery d ON d.radar_id=r.id AND d.channel='telegram_free'
                  ORDER BY r.id DESC LIMIT 50""")],
            'radar_delivery':{r['status']:r['n'] for r in con.execute('SELECT status,COUNT(*) n FROM radar_delivery GROUP BY status')},
            'vip_active':con.execute("SELECT COUNT(*) FROM members WHERE status='active' AND expires_at>?",(tick,)).fetchone()[0]}

def serve(port):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            from urllib.parse import urlsplit
            path=urlsplit(self.path).path
            if path not in ('/','/health','/api/signals','/api/operations','/api/early-alerts','/api/radar'):
                self.send_error(404);return
            con=db()
            try:
                init_tables(con)
                ops=operations_snapshot(con)
                if path=='/health':
                    data={'ok':ops['scanner_fresh'],'server_time':now(),'last_cycle_age_seconds':ops['last_cycle_age_seconds']}
                    body=json.dumps(data).encode();typ='application/json'
                elif path=='/api/operations':
                    body=json.dumps(ops,ensure_ascii=False).encode();typ='application/json'
                elif path=='/api/radar':
                    body=json.dumps({'events':ops['radar_recent'],'deliveries':ops['radar_delivery'],'coverage':ops['coverage'],'events_total':ops['radar_events_total']}).encode();typ='application/json'
                elif path=='/api/early-alerts':
                    body=json.dumps({'alerts':[dict(x) for x in con.execute('SELECT * FROM early_alerts ORDER BY id DESC LIMIT 100')]}).encode();typ='application/json'
                elif path=='/api/signals':
                    items=[dict(x) for x in con.execute('SELECT * FROM signals ORDER BY id DESC LIMIT 100')]
                    body=json.dumps({'signals':items}).encode();typ='application/json'
                else:
                    items=[dict(x) for x in con.execute('SELECT id,symbol,side,exchange,entry,target,stop,reason FROM signals ORDER BY id DESC LIMIT 50')]
                    cols=['id','symbol','side','exchange','entry','target','stop','reason']
                    rows=''.join('<tr>'+''.join('<td>'+html.escape(str(x.get(k,'')))+'</td>' for k in cols)+'</tr>' for x in items)
                    early_rows=''.join('<tr>'+''.join('<td>'+html.escape(str(x.get(k,'')))+'</td>' for k in ['id','symbol','side','volume_ratio','move_pct','status'])+'</tr>' for x in ops['early_alerts_recent'])
                    errors=''.join('<tr>'+''.join('<td>'+html.escape(str(x.get(k,'')))+'</td>' for k in ['id','channel','signal_id','status','last_error'])+'</tr>' for x in ops['attention_required'])
                    radar_cols=['id','exchange','symbol','kind','direction','score','telegram_status','created_at']
                    radar_rows=''.join('<tr>'+''.join('<td>'+html.escape(str(x.get(k,'')))+'</td>' for k in radar_cols)+'</tr>' for x in ops['radar_recent'])
                    radar_rows=radar_rows or '<tr><td colspan="8">No Radar events recorded yet</td></tr>'
                    coverage=ops['coverage']
                    coverage_text=html.escape(json.dumps(coverage,ensure_ascii=False))
                    body=("<!doctype html><html><head><meta charset='utf-8'><meta http-equiv='refresh' content='30'><title>Egonia | Signal Operations</title><style>body{background:#17232d;color:#e8f4ef;font:14px Arial,sans-serif;max-width:1300px;margin:36px auto;padding:0 24px}h1{letter-spacing:.16em}strong{color:#14c38e}section{background:#223641;border:1px solid #3d5360;border-radius:10px;padding:17px;margin:18px 0}table{width:100%;border-collapse:collapse}td,th{padding:9px;border-bottom:1px solid #465963;text-align:left;font-size:12px}small{color:#bed3d1}a{color:#8fd8c1}</style></head><body><h1>EGONIA <strong>•</strong> SIGNAL OPERATIONS</h1><small>Local status panel · automatic refresh 30s · not a trading terminal</small><section><b>Scanner:</b> "+('SCANNING' if ops['scanner_running'] else ('FRESH' if ops['scanner_fresh'] else 'STALE / NOT STARTED'))+" | <b>Last cycle:</b> "+html.escape(str(ops['last_cycle_utc']))+" | <b>Last scanned:</b> "+str(ops['last_cycle_scanned'])+" | <b>Last errors:</b> "+str(ops['last_cycle_errors'])+" | <b>Markets seen:</b> "+str(ops['observed_markets'])+" | <b>Signals:</b> "+str(ops['signals_total'])+" | <b>VIP active:</b> "+str(ops['vip_active'])+"</section><section><b>Delivery statuses:</b> "+html.escape(str(ops['deliveries']))+" <small>Pending / sent / needs_review / failed</small></section><section><h3>Attention required</h3><table><tr><th>ID</th><th>Channel</th><th>Signal</th><th>Status</th><th>Error</th></tr>"+errors+"</table></section><section><h3>Recent signals</h3><table><tr>"+''.join('<th>'+html.escape(k)+'</th>' for k in cols)+"</tr>"+rows+"</table></section><section><h3>Altcoin Radar — LIVE ACTIVITY</h3><p>Recorded events: "+str(ops['radar_events_total'])+" | Telegram statuses: "+html.escape(str(ops['radar_delivery']))+"</p><p><small>Coverage (last 5m): "+coverage_text+"</small></p><table><tr>"+''.join('<th>'+html.escape(k.replace('_',' ').title())+'</th>' for k in radar_cols)+"</tr>"+radar_rows+"</table><p><a href='/api/radar'>Radar JSON &amp; delivery details</a></p></section><section><h3>Early activity alerts</h3><table><tr><th>ID</th><th>Symbol</th><th>Direction</th><th>Volume x</th><th>1m move %</th><th>Status</th></tr>"+early_rows+"</table></section><small><a href='/api/early-alerts'>Early Alerts JSON</a> · <a href='/api/operations'>Operations JSON</a> · <a href='/api/signals'>Signals JSON</a></small></body></html>").encode();typ='text/html; charset=utf-8'
            finally:con.close()
            self.send_response(200)
            self.send_header('Content-Type',typ);self.send_header('Content-Length',str(len(body)))
            self.end_headers();self.wfile.write(body)
        def log_message(self,*args):pass
    ThreadingHTTPServer(('127.0.0.1',port),Handler).serve_forever()

def run(cfg,once=False,offline=False):
    con=db()
    init_tables(con)
    radar_engine.ensure_tables(con)
    coverage_monitor.ensure_tables(con)
    con.execute("UPDATE radar_delivery SET status='needs_review', last_error='Previous publishing attempt interrupted' WHERE status='in_flight'")
    con.execute("UPDATE radar_delivery SET status='disabled_old_radar' WHERE status='pending' AND radar_id IN (SELECT id FROM radar_events WHERE kind NOT IN ('ML_EXTRA_TREES_SHORT','ML_RANDOM_FOREST_LONG'))")
    con.execute("UPDATE early_alerts SET status='needs_review',last_error='Interrupted during publication' WHERE status='in_flight'")
    con.commit()
    radar=EarlyRadar(cfg,db,get_json,None) if cfg.get('enable_early_alerts',True) and not cfg.get('radar_mode',False) and not once else None
    if radar: radar.start()
    def radar_send(channel,msg):
        token=os.getenv('TELEGRAM_BOT_TOKEN','')
        chat=os.getenv('TELEGRAM_FREE_CHAT_ID' if channel=='telegram_free' else 'TELEGRAM_VIP_CHAT_ID','')
        if not token or not chat:raise RuntimeError('Missing Telegram credentials')
        result=telegram_send(token,chat,msg)
        if channel=='telegram_free':
            admin_id=os.getenv('EGONIA_ADMIN_CHAT_ID','').strip()
            if admin_id:
                try:
                    tweet=' '.join(msg.splitlines())
                    tweet=urllib.parse.quote(tweet[:210],safe='')
                    link='https://twitter.com/intent/tweet?text='+tweet
                    payload={'chat_id':admin_id,'text':msg,'reply_markup':{'inline_keyboard':[[{'text':'🐦 Tweetle','url':link}]]}}
                    req=urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage',data=json.dumps(payload).encode('utf-8'),headers={'Content-Type':'application/json'},method='POST')
                    with urllib.request.urlopen(req,timeout=20) as response:
                        posted=json.load(response)
                        if not posted.get('ok'):raise RuntimeError('Telegram private message not accepted')
                except Exception as exc:logging.warning('Admin Tweet button failed (public Telegram delivery succeeded): %s',exc)
        return result
    live=BinanceLiveRadar(cfg,db,get_json,radar_send) if cfg.get('radar_mode',False) and cfg.get('binance_live_ws',True) and not once else None
    global LIVE_MONITOR, GATE_MONITOR
    LIVE_MONITOR=live
    gate=GateLiveRadar(cfg,db,get_json,radar_send) if cfg.get('radar_mode',False) and cfg.get('gate_live_ws',True) and not once else None
    GATE_MONITOR=gate
    if live:live.start()
    if gate:gate.start()
    if not two_model_engine.ready():logging.warning('TWO-MODEL ENGINE unavailable; check auto_bootstrap.log; no BUY/SELL will be published')
    # Older processes may have died while publishing; do not retry blindly.
    con.execute("UPDATE delivery SET status='needs_review',last_error='Process interrupted during remote delivery; reconcile manually' WHERE status='in_flight'")
    con.commit()
    threading.Thread(target=serve,args=(int(cfg['panel_port']),),daemon=True).start()
    logging.info('Panel http://127.0.0.1:%s | dry_run=%s | public_live=%s',cfg['panel_port'],cfg['dry_run'],cfg.get('allow_unvalidated_publication',False))
    last_member_sync=0
    universe=[];last_discovery=0;market_cursor=0;futures={}
    while True:
        if not cfg.get('enable_trc20_payments',False):
            try:poll_vip_join_requests(con,cfg)
            except Exception as exc:logging.warning("VIP join polling failed: %s",exc)
        if cfg.get('enable_vip_member_enforcement',False) and now()-last_member_sync>=3600:
            try:
                members_command(argparse.Namespace(members_action='sync',user_id=None,days=30,username=''),cfg)
            except Exception as exc:logging.warning('VIP membership sync failed: %s',exc)
            last_member_sync=now()
        con.execute("INSERT OR REPLACE INTO system VALUES('cycle_started',?)",(str(now()),));con.commit()
        scan_errors=0
        data={}
        if cfg.get('auto_discovery',False) and (not universe or now()-last_discovery>=max(300,int(cfg.get('discovery_refresh_seconds',3600)))):
            fresh,errors=discover_all(cfg.get('exchanges',['Binance','MEXC','Gate']),get_json,
                    float(cfg.get('min_daily_quote_volume_usdt',1000000)),int(cfg.get('max_pairs_per_exchange',60)),bool(cfg.get('altcoin_focus',False)),float(cfg.get('max_daily_quote_volume_usdt',150000000)))
            if fresh:
                futures,future_errors=discover_contracts(cfg.get('exchanges',['Binance','MEXC','Gate']),get_json)
                if future_errors:logging.warning('Perpetual contract discovery issues: %s',future_errors)
                stamp=now()
                for record in fresh:
                    exchange,sym=record[:2]
                    con.execute('INSERT OR IGNORE INTO observed_markets(exchange,symbol,first_seen,last_seen) VALUES(?,?,?,?)',(exchange,sym,stamp,stamp))
                    con.execute('UPDATE observed_markets SET last_seen=? WHERE exchange=? AND symbol=?',(stamp,exchange,sym))
                con.commit()
                # Keep round-robin progress when the universe is refreshed.
                next_market=(universe[market_cursor%len(universe)][0],universe[market_cursor%len(universe)][1]) if universe else None
                universe=fresh
                market_cursor=next((i for i,m in enumerate(universe) if (m[0],m[1])==next_market),market_cursor%len(universe)) if universe else 0
                last_discovery=now()
                if radar: radar.configure(universe)
                if live: logging.info("LIVE Binance universe=%d",live.configure(universe))
                if gate: logging.info("LIVE Gate universe=%d",gate.configure(universe))
                logging.info('Discovery markets=%d errors=%s',len(universe),errors)
            else:
                logging.warning('Discovery yielded no markets; retaining previous markets. Errors=%s',errors)
                last_discovery=now()  # retry at next refresh, no tight loop
        if cfg.get('auto_discovery',False):
            budget=max(1,int(cfg.get('markets_per_cycle',12)))
            work=[(universe[(market_cursor+i)%len(universe)][0],universe[(market_cursor+i)%len(universe)][1]) for i in range(min(budget,len(universe)))] if universe else []
            if universe:market_cursor=(market_cursor+len(work))%len(universe)
        else:
            work=[(ex,sym) for sym in cfg['symbols'] for ex in cfg.get('exchanges',['Binance','MEXC','Gate'])]
        radar_candidates=[]
        scan_telemetry=[]
        if cfg.get('radar_mode',False):
            def scan_one(pair):
                exchange,symbol=pair
                started=time.monotonic()
                info={'exchange':exchange,'symbol':symbol}
                try:
                    rows=exchange_candles(exchange,symbol,'5m',get_json,100)
                    completed=[r for r in rows if r['close_time']<=now()-2]
                    if completed:
                        info['candle_close_time']=int(completed[-1]['close_time'])
                    event=two_model_engine.analyze(completed,cfg) if completed and now()-completed[-1]['close_time']<=650 else None
                    return info,event
                except Exception as exc:
                    info['error']=str(exc)[:180]
                    return info,None
                finally:
                    info['duration_ms']=round((time.monotonic()-started)*1000)
            with ThreadPoolExecutor(max_workers=max(1,min(12,int(cfg.get('radar_scan_workers',8))))) as pool:
                futures_list=[pool.submit(scan_one,pair) for pair in work]
                for future in as_completed(futures_list):
                    info,event=future.result()
                    scan_telemetry.append(info)
                    if info.get('error'):
                        scan_errors+=1
                        logging.warning('Market %s %s: %s',info['exchange'],info['symbol'],info['error'])
                    if event:
                        radar_candidates.append((info['exchange'],info['symbol'],event))
            coverage_monitor.update(con,scan_telemetry)
            metrics=coverage_monitor.snapshot(con,universe if cfg.get('auto_discovery') else work)
            logging.info('COVERAGE 5m=%s/%s (%.1f%%), failures=%s, p95 candle age=%ss',
                metrics['scanned_last_5m'],metrics['universe'],metrics['coverage_5m_pct'],
                metrics['errors_last_5m'],metrics['p95_candle_age_s'])
            con.execute('INSERT OR REPLACE INTO system(key,value) VALUES(?,?)',('coverage_json',json.dumps(metrics)))
            con.commit()
        for exchange,symbol in ([] if cfg.get('radar_mode',False) else work):
            try:
                if cfg.get('radar_mode',False):
                    rows=exchange_candles(exchange,symbol,'5m',get_json,100)
                    completed=[r for r in rows if r['close_time']<=now()-2]
                    if completed and now()-completed[-1]['close_time']<=650:
                        event=two_model_engine.analyze(completed,cfg)
                        if event:
                            radar_candidates.append((exchange,symbol,event))
                elif cfg.get('strategy_mode',True):
                    candidates=[]
                    rows_by_tf={}
                    for tf in cfg.get('strategy_timeframes',['5m','15m','1h']):
                        rows=exchange_candles(exchange,symbol,tf,get_json,100)
                        completed=[r for r in rows if r['close_time']<=now()-2]
                        if not completed:continue
                        step={'5m':300,'15m':900,'1h':3600}.get(tf,300)
                        if now()-completed[-1]['close_time']>step*2:continue
                        rows_by_tf[tf]=completed
                        for pick in evaluate(completed,tf,set(cfg.get('strategy_names',[]))):
                            if pick['side']=='SHORT' and cfg.get('require_futures_for_short',True) and symbol not in futures.get(exchange,set()):
                                continue
                            candidates.append(dict(pick,timeframe=tf))
                        if cfg.get('enable_result_tracking',False) and tf=='5m' and exchange=='Binance':data[symbol]=rows
                    chosen=consolidate(candidates)
                    if chosen:
                        signal_rows=rows_by_tf.get(chosen.get('timeframe'))
                        if signal_rows:
                            chosen=enrich_signal(chosen,signal_rows,exchange,symbol,get_json,cfg)
                        if chosen:
                            new_signal(con,symbol,chosen,cfg,signal_rows,exchange=exchange)
                else:
                    rows=exchange_candles(exchange,symbol,'5m',get_json,100);data[symbol]=rows
                    detail=decide(rows,cfg)
                    if detail:new_signal(con,symbol,detail,cfg,[r for r in rows if r['close_time']<=now()-2],exchange=exchange)
            except Exception as e:
                scan_errors+=1
                logging.warning('Market %s %s: %s',exchange,symbol,e)
        if cfg.get('radar_mode',False):
            # Process highest-quality observed events first, regardless of market scan order.
            radar_candidates.sort(key=lambda item:(-item[2]['score'],-item[2]['quote_volume'],item[1],item[0]))
            for exchange,symbol,event in radar_candidates:
                ident=radar_engine.record(con,exchange,symbol,event,cfg)
                if ident:logging.info('RADAR EVENT #%s %s %s score=%s',ident,symbol,event['kind'],event['score'])
            logging.info('RADAR scan candidates=%d recorded=%d',len(radar_candidates),con.execute('SELECT COUNT(*) FROM radar_events').fetchone()[0])
        if cfg.get('enable_result_tracking',False):close_signals(con,data,cfg)
        if cfg.get('radar_mode',False):
            # Do not replay old trading-signal delivery queue in radar product mode.
            radar_engine.publish(con,cfg,radar_send)
        else:
            deliveries(con,cfg)
            early_deliveries(con,cfg)
        con.executemany('INSERT OR REPLACE INTO system(key,value) VALUES(?,?)', [('last_cycle',str(now())),('last_cycle_scanned',str(len(work))),('last_cycle_errors',str(scan_errors))]);con.commit()
        logging.info('Cycle complete markets=%s universe=%s active=%s',len(work),len(universe) if cfg.get('auto_discovery',False) else len(work),con.execute("SELECT COUNT(*) FROM signals WHERE status='ACTIVE'").fetchone()[0])
        if once:break
        time.sleep(max(15,int(cfg['poll_seconds'])))
    con.close()

def members_command(args,cfg):
    con=db()
    try:
        if args.members_action=='list':
            for r in con.execute('SELECT * FROM members ORDER BY expires_at DESC'):
                print(dict(r))
        elif args.members_action=='grant':
            if not args.user_id or args.days<=0:raise ValueError('--user-id and positive --days required')
            expiry=now()+args.days*86400
            con.execute("INSERT INTO members(user_id,username,expires_at,status,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET username=excluded.username,expires_at=excluded.expires_at,status='active',updated_at=excluded.updated_at,invite_link=NULL,last_error=NULL",(args.user_id,args.username or '',expiry,'active',now()))
            con.execute('INSERT INTO sales_events(user_id,event,created_at,note) VALUES(?,?,?,?)',(args.user_id,'manual_grant',now(),f'{args.days} days; manually confirmed'))
            con.commit();print('MANUAL membership grant:',args.user_id,utc(expiry))
        elif args.members_action=='revoke':
            if not args.user_id:raise ValueError('--user-id required')
            con.execute("UPDATE members SET status='revoked',updated_at=? WHERE user_id=?",(now(),args.user_id));con.commit()
            print('Marked revoked. Run members sync to enforce VIP removal.')
        elif args.members_action=='sync':
            if not cfg.get('enable_vip_member_enforcement',False):raise RuntimeError('Set enable_vip_member_enforcement=true to perform remote membership actions')
            token=os.getenv('TELEGRAM_BOT_TOKEN','');vip=os.getenv('TELEGRAM_VIP_CHAT_ID','')
            if not token or not vip:raise RuntimeError('Missing TELEGRAM_BOT_TOKEN / TELEGRAM_VIP_CHAT_ID')
            for m in con.execute('SELECT * FROM members').fetchall():
                uid=m['user_id'];expired=m['status']!='active' or m['expires_at']<=now()
                try:
                    if expired:
                        telegram_call(token,'banChatMember',{'chat_id':vip,'user_id':uid,'revoke_messages':'false'})
                        status='expired' if m['status']=='active' else m['status']
                        con.execute("UPDATE members SET status=?,updated_at=?,last_error=NULL WHERE user_id=?",(status,now(),uid))
                        print('Removed expired/revoked member:',uid)
                    elif not m['invite_link']:
                        telegram_call(token,'unbanChatMember',{'chat_id':vip,'user_id':uid,'only_if_banned':'true'})
                        link=telegram_call(token,'createChatInviteLink',{'chat_id':vip,'name':f'VIP-{uid}','expire_date':now()+max(1,int(cfg.get('vip_invite_expire_hours',24)))*3600,**({'creates_join_request':'true'} if cfg.get('vip_join_request_mode',True) else {'member_limit':1})})['invite_link']
                        con.execute('UPDATE members SET invite_link=?,updated_at=?,last_error=NULL WHERE user_id=?',(link,now(),uid))
                        print('Invite created for user',uid,'(stored in members table; do not share publicly)')
                except Exception as e:
                    con.execute('UPDATE members SET last_error=?,updated_at=? WHERE user_id=?',(str(e)[:600],now(),uid))
                    print('Membership sync failed for',uid,type(e).__name__,str(e))
                con.commit()
        else:raise ValueError('Unknown membership action')
    finally:con.close()

def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(errors='backslashreplace')
    p=argparse.ArgumentParser();p.add_argument('--check-publishing',action='store_true');p.add_argument('--check-remote',action='store_true');p.add_argument('--once',action='store_true');p.add_argument('--init',action='store_true');p.add_argument('--self-test',action='store_true');p.add_argument('--membership-bot',action='store_true');p.add_argument('--members-action',choices=['list','grant','revoke','sync']);p.add_argument('--user-id',type=int);p.add_argument('--days',type=int,default=30);p.add_argument('--username',default='');a=p.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(levelname)s %(message)s',handlers=[logging.StreamHandler(sys.stdout),logging.FileHandler(LOG,encoding='utf-8')])
    path=ROOT/'config.json'
    if not path.exists():path.write_text(json.dumps(DEFAULT,indent=2),encoding='utf-8')
    cfg={**DEFAULT,**json.loads(path.read_text(encoding='utf-8'))}
    if a.check_publishing or a.check_remote:
        result={'local':readiness(cfg)}
        if a.check_remote:
            result['telegram']=verify_telegram(cfg) if cfg.get('enable_telegram_free') or cfg.get('enable_telegram_vip') else {'skipped':True}
            result['x']=verify_x(cfg) if cfg.get('enable_x') else {'skipped':True}
        print(json.dumps(result,indent=2,ensure_ascii=False));return
    if a.members_action:
        members_command(a,cfg);return
    if a.membership_bot:
        run_membership_bot(cfg,a.once);return
    if a.self_test:
        end=((now()-305)//300)*300
        test_rows=[{'time':end-(79-i)*300,'open':100.,'close':100.1,
          'high':100.2,'low':99.9,'quote_volume':150000.,
          'close_time':end-(79-i)*300+299} for i in range(80)]
        test_rows[-1].update({'quote_volume':1200000.,'close':102.,'high':102.1})
        assert decide(test_rows,cfg) is not None
        c=db();assert c.execute('PRAGMA integrity_check').fetchone()[0]=='ok';c.close();print('SELF TEST OK');return
    if a.init:db().close();print('Initialized: '+str(DB));return
    readiness_state=readiness(cfg)
    if not cfg.get('dry_run',True) and cfg.get('allow_unvalidated_publication',False):
        required=[route for route,v in readiness_state.items() if route in ('x','telegram_free','telegram_vip') and v['enabled'] and not v['ready']]
        if required:raise RuntimeError('Live publication blocked: missing credentials for '+', '.join(required))
    run(cfg,once=a.once)
if __name__=='__main__':main()
