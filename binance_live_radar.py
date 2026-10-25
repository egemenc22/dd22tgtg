"""Binance spot partial 1m candle radar; read-only, separate from REST coverage."""
import collections
import concurrent.futures
import json
import logging
import math
import queue
import threading
import time
import urllib.parse


def detect_partial(k, baseline, cfg, clock_ms=None):
    """Detect real intra-minute acceleration against PREVIOUS completed 1m volumes."""
    if len(baseline) < 15 or any(not math.isfinite(float(v)) for v in baseline):
        return None
    avg=sum(baseline[-20:])/len(baseline[-20:])
    if avg<=0:return None
    start=int(k['t']); now=int(clock_ms if clock_ms is not None else k['T'] if k.get('x') else time.time()*1000)
    elapsed=max(1,min(60,(now-start)/1000))
    if elapsed < int(cfg.get('live_min_elapsed_seconds',15)):
        return None
    op=float(k['o']);close=float(k['c']);q=float(k['q'])
    if not all(math.isfinite(v) for v in (op,close,q)) or op<=0 or close<=0 or q<=0:return None
    move=100*(close/op-1)
    projected_ratio=(q/max(elapsed,1)*60)/avg
    if not math.isfinite(projected_ratio) or not math.isfinite(move):return None
    if (abs(move)<float(cfg.get('live_min_move_pct',0.65)) or
        projected_ratio<float(cfg.get('live_min_volume_ratio',3.5)) or
        q<float(cfg.get('live_min_quote_volume',12000))):return None
    score=min(100,round(61+min(18,projected_ratio*2.5)+min(20,abs(move)*13)))
    return dict(kind='EARLY_MOMENTUM' if abs(move)>=1 else 'UNUSUAL_VOLUME',kinds=['LIVE_1M'],
                direction='UP' if move>0 else 'DOWN',score=score,
                volume_ratio=round(projected_ratio,2),move_pct=round(move,2),
                three_bar_move_pct=round(move,2),quote_volume=round(q,2),
                price=close,origin_ts=start//1000,partial_candle=True,
                elapsed_seconds=round(elapsed,1))

class BinanceLiveRadar:
    def __init__(self,cfg,db_factory,fetch_json,send):
        self.cfg=cfg;self.db_factory=db_factory;self.fetch_json=fetch_json;self.send=send
        self.symbols=();self.baselines={};self.last_ws_at=0;self.last_notice={}
        self.events=queue.Queue(maxsize=400);self.running=False;self.thread=None;self.worker=None
        self.lock=threading.RLock();self.active_app=None
        self.connected=False;self.ws_messages=0;self.queue_dropped=0;self.events_recorded=0;self.last_error=None

    def configure(self,universe):
        symbols=tuple(sorted(set(s for ex,s,*_ in universe if ex=='Binance')))
        with self.lock:
            changed=symbols!=self.symbols
            self.symbols=symbols
            app=self.active_app if changed else None
        if app:app.close()
        return len(symbols)

    def start(self):
        if self.running:return
        self.running=True
        self.worker=threading.Thread(target=self._consume,daemon=True,name='EgoniaLivePublisher');self.worker.start()
        self.thread=threading.Thread(target=self._loop,daemon=True,name='EgoniaBinanceLive');self.thread.start()

    def _bootstrap(self,symbol):
        url='https://api.binance.com/api/v3/klines?'+urllib.parse.urlencode({'symbol':symbol,'interval':'1m','limit':24})
        raw=self.fetch_json(url)
        current=int(time.time()*1000)
        values=[float(r[7]) for r in raw if int(r[6])<current-2000]
        if len(values)>=15:
            with self.lock:self.baselines[symbol]=values[-20:]

    def snapshot(self):
        with self.lock:
            return {'enabled':self.running,'connected':self.connected,
                    'symbols':len(self.symbols),'seeded':sum(s in self.baselines for s in self.symbols),
                    'last_message_age_seconds':int(time.time())-self.last_ws_at if self.last_ws_at else None,
                    'messages':self.ws_messages,'queued':self.events.qsize(),
                    'queue_dropped':self.queue_dropped,'events_recorded':self.events_recorded,
                    'last_error':self.last_error}

    def _opened(self,ws):
        with self.lock:self.connected=True
        logging.info('LIVE WebSocket connected symbols=%d',len(self.symbols))

    def _closed(self,ws,code,msg):
        with self.lock:self.connected=False
        logging.warning('LIVE WS closed: %s %s',code,msg)

    def _errored(self,ws,error):
        with self.lock:self.connected=False;self.last_error=str(error)[:200]
        logging.warning('LIVE WS error: %s',error)

    def _message(self,ws,message):
        try:
            obj=json.loads(message);k=obj.get('data',obj).get('k')
            if not k:return
            sym=k.get('s'); t=int(k['t']);
            with self.lock:
                if sym not in self.symbols:return
                baseline=self.baselines.get(sym)
            with self.lock:
                self.last_ws_at=int(time.time());self.ws_messages+=1
            if baseline is None:return
            # Evaluate the candle against PREVIOUS candles; append the closing
            # volume only after evaluation, so it never dilutes its own baseline.
            event=detect_partial(k,baseline,self.cfg,clock_ms=int(obj.get('data',obj).get('E') or time.time()*1000))
            if k.get('x'):
                volume=float(k['q'])
                if math.isfinite(volume) and volume>=0:
                    with self.lock:self.baselines[sym]=(baseline+[volume])[-20:]
            if not event:return
            ident=(sym,t)
            with self.lock:
                if ident in self.last_notice:return
                self.last_notice[ident]=int(time.time())
                if len(self.last_notice)>1000:
                    cutoff=int(time.time())-900
                    self.last_notice={key:v for key,v in self.last_notice.items() if v>=cutoff}
            try:self.events.put_nowait((sym,event))
            except queue.Full:
                with self.lock:self.queue_dropped+=1
                logging.warning('LIVE event queue full: dropped %s',sym)
        except (ValueError,TypeError,KeyError,OverflowError) as exc:
            logging.warning('LIVE parse: %s',exc)

    def _consume(self):
        import radar_engine
        while self.running:
            try:sym,event=self.events.get(timeout=2)
            except queue.Empty:continue
            try:
                con=self.db_factory()
                try:
                    ident=radar_engine.record(con,'Binance',sym,event,self.cfg)
                    if ident:
                        with self.lock:self.events_recorded+=1
                        logging.info('LIVE RADAR %s %s score=%s',sym,event['kind'],event['score'])
                        radar_engine.publish(con,self.cfg,self.send)
                finally:con.close()
            except Exception as exc:
                logging.warning('LIVE radar store/publish failed %s: %s',sym,exc)
            finally:self.events.task_done()

    def _loop(self):
        try:import websocket
        except ImportError:
            logging.error('LIVE WebSocket requires websocket-client from requirements.txt');return
        while self.running:
            try:
                with self.lock:symbols=self.symbols
                if not symbols:
                    time.sleep(2);continue
                missing=[s for s in symbols if s not in self.baselines]
                if missing:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
                        list(pool.map(self._safe_bootstrap,missing))
                streams='/'.join(s.lower()+'@kline_1m' for s in symbols)
                url='wss://stream.binance.com:9443/stream?streams='+streams
                app=websocket.WebSocketApp(url,on_message=self._message,
                    on_open=self._opened,on_error=self._errored,on_close=self._closed)
                with self.lock:self.active_app=app
                timer=threading.Timer(4*3600,app.close);timer.daemon=True;timer.start()
                logging.info('LIVE WebSocket connecting Binance symbols=%d seeded=%d',len(symbols),len(self.baselines))
                try:app.run_forever(ping_interval=25,ping_timeout=10)
                finally:
                    timer.cancel()
                    with self.lock:self.active_app=None;self.connected=False
            except Exception as exc:logging.warning('LIVE WS reconnect: %s',exc)
            time.sleep(5)

    def _safe_bootstrap(self,symbol):
        try:self._bootstrap(symbol)
        except Exception as exc:logging.warning('LIVE bootstrap %s: %s',symbol,exc)
