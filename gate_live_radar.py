"""Gate spot 1m candle stream using public Gate API v4. No trade credentials."""
import concurrent.futures, json, logging, math, threading, time, urllib.parse
from binance_live_radar import BinanceLiveRadar, detect_partial

class GateLiveRadar(BinanceLiveRadar):
    def configure(self,universe):
        symbols=tuple(sorted(set(s for ex,s,*_ in universe if ex=='Gate')))
        with self.lock:
            changed=symbols!=self.symbols
            self.symbols=symbols
            app=self.active_app if changed else None
        if app: app.close()
        return len(symbols)

    def _bootstrap(self,symbol):
        pair=symbol[:-4]+'_USDT'
        url='https://api.gateio.ws/api/v4/spot/candlesticks?'+urllib.parse.urlencode({'currency_pair':pair,'interval':'1m','limit':24})
        raw=self.fetch_json(url)
        now=int(time.time())
        values=[]
        for r in raw:
            try:
                if int(r[0])+60 >= now:continue
                volume=float(r[1]) # Gate candlestick quote amount
                if math.isfinite(volume) and volume>=0:values.append((int(r[0]),volume))
            except (ValueError,TypeError,IndexError):continue
        values.sort()
        if len(values)>=15:
            with self.lock:self.baselines[symbol]=[v for _,v in values[-20:]]

    def _opened(self,ws):
        super()._opened(ws)
        with self.lock:symbols=self.symbols
        for sym in symbols:
            ws.send(json.dumps({'time':int(time.time()),'channel':'spot.candlesticks','event':'subscribe','payload':['1m',sym[:-4]+'_USDT']}))
        logging.info('LIVE Gate subscribed symbols=%d',len(symbols))

    def _message(self,ws,message):
        try:
            obj=json.loads(message)
            if obj.get('channel')!='spot.candlesticks' or obj.get('event')!='update':return
            r=obj.get('result') or {}
            name=r.get('n','')
            if not name.startswith('1m_') or not name.endswith('_USDT'):return
            sym=name[3:].replace('_','')
            t=int(r['t'])*1000
            k={'t':t,'s':sym,'o':r['o'],'c':r['c'],'q':r['a'],'x':bool(r.get('w',False))}
            with self.lock:
                if sym not in self.symbols:return
                self.ws_messages+=1;self.last_ws_at=int(time.time());baseline=self.baselines.get(sym)
            if baseline is None:return
            event=detect_partial(k,baseline,self.cfg,clock_ms=int(obj.get('time_ms') or time.time()*1000))
            if k['x']:
                v=float(k['q'])
                if math.isfinite(v) and v>=0:
                    with self.lock:self.baselines[sym]=(baseline+[v])[-20:]
            if not event:return
            ident=(sym,t)
            with self.lock:
                if ident in self.last_notice:return
                self.last_notice[ident]=int(time.time())
                if len(self.last_notice)>1000:
                    cutoff=int(time.time())-900
                    self.last_notice={key:v for key,v in self.last_notice.items() if v>=cutoff}
            try:self.events.put_nowait((sym,event))
            except __import__('queue').Full:
                with self.lock:self.queue_dropped+=1
                logging.warning('LIVE Gate event queue full %s',sym)
        except (TypeError,ValueError,KeyError,OverflowError) as exc:logging.warning('LIVE Gate parse: %s',exc)

    def _consume(self):
        import radar_engine, queue
        while self.running:
            try:sym,event=self.events.get(timeout=2)
            except queue.Empty:continue
            try:
                con=self.db_factory()
                try:
                    ident=radar_engine.record(con,'Gate',sym,event,self.cfg)
                    if ident:
                        with self.lock:self.events_recorded+=1
                        logging.info('LIVE Gate RADAR %s %s score=%s',sym,event['kind'],event['score'])
                        radar_engine.publish(con,self.cfg,self.send)
                finally:con.close()
            except Exception as exc:logging.warning('LIVE Gate store/publish failed %s: %s',sym,exc)
            finally:self.events.task_done()

    def _loop(self):
        try:import websocket
        except ImportError:
            logging.error('Gate LIVE requires websocket-client');return
        while self.running:
            try:
                with self.lock:symbols=self.symbols
                if not symbols:
                    time.sleep(2);continue
                missing=[s for s in symbols if s not in self.baselines]
                if missing:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
                        list(pool.map(self._safe_bootstrap,missing))
                app=websocket.WebSocketApp('wss://api.gateio.ws/ws/v4/',on_message=self._message,on_open=self._opened,on_error=self._errored,on_close=self._closed)
                with self.lock:self.active_app=app
                logging.info('LIVE Gate connecting symbols=%d seeded=%d',len(symbols),len(self.baselines))
                timer=threading.Timer(3*3600,app.close);timer.daemon=True;timer.start()
                try:app.run_forever(ping_interval=25,ping_timeout=10)
                finally:
                    timer.cancel()
                    with self.lock:self.active_app=None;self.connected=False
            except Exception as exc:logging.warning('LIVE Gate reconnect %s',exc)
            time.sleep(5)
