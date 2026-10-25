"""Optional Binance 1m WebSocket early activity radar; no trading or order placement.
Only completed 1m candles are scored. Separate alerts from LONG/SHORT trade signals.
"""
import collections
import json
import logging
import math
import threading
import time
import urllib.parse

MIN_POINTS = 20


def detect_early(closed, cfg):
    """Return an observation only for a high relative volume + material minute move."""
    if len(closed) < MIN_POINTS + 1:
        return None
    recent = list(closed)[-MIN_POINTS - 1:]
    base = recent[:-1]
    last = recent[-1]
    if not all(math.isfinite(float(x[k])) for x in recent for k in ('open', 'close', 'quote_volume')):
        return None
    average = sum(float(x['quote_volume']) for x in base) / MIN_POINTS
    if average <= 0 or last['open'] <= 0:
        return None
    ratio = float(last['quote_volume']) / average
    move = 100.0 * (float(last['close']) / float(last['open']) - 1)
    if (ratio < float(cfg.get('early_min_volume_ratio', 3.0)) or
        abs(move) < float(cfg.get('early_min_move_pct', 0.7)) or
        float(last['quote_volume']) < float(cfg.get('early_min_minute_quote_volume', 12000))):
        return None
    return {'side': 'UP' if move > 0 else 'DOWN', 'price': float(last['close']),
            'volume_ratio': round(ratio, 2), 'move_pct': round(move, 3),
            'candle_time': int(last['time'])}


class EarlyRadar:
    def __init__(self, cfg, db_fn, fetch_json, notifier):
        self.cfg, self.db_fn, self.fetch_json, self.notifier = cfg, db_fn, fetch_json, notifier
        self.markets = []
        self.lock = threading.RLock()
        self.thread = None
        self.observed = {}
        self.running = False
        self.last_stream_event = None

    def configure(self, universe):
        chosen = []
        for item in universe:
            exchange, sym = item[:2]
            if exchange == 'Binance' and sym not in chosen:
                chosen.append(sym)
            if len(chosen) >= int(self.cfg.get('early_ws_symbols', 20)):
                break
        with self.lock:
            self.markets = chosen

    def start(self):
        if self.thread is not None:
            return
        self.running = True
        self.thread = threading.Thread(target=self._loop, name='EgoniaEarlyRadar', daemon=True)
        self.thread.start()

    def _record(self, symbol, row):
        with self.lock:
            history = self.observed.setdefault(symbol, collections.deque(maxlen=45))
            if history and row['time'] < history[-1]['time']:
                return
            if history and row['time'] == history[-1]['time']:
                history[-1] = row
            else:
                history.append(row)
            result = detect_early(history, self.cfg)
        if result:
            self._store(symbol, result)

    def _store(self, symbol, result):
        con = self.db_fn()
        try:
            stamp = int(time.time())
            cooldown = max(60, int(self.cfg.get('early_cooldown_minutes', 45)) * 60)
            if con.execute('SELECT 1 FROM early_alerts WHERE symbol=? AND created_at>? LIMIT 1',
                           (symbol, stamp-cooldown)).fetchone():
                return
            cap = int(self.cfg.get('early_daily_cap', 12))
            if con.execute('SELECT COUNT(*) FROM early_alerts WHERE created_at>=?', (stamp//86400*86400,)).fetchone()[0] >= cap:
                return
            cur = con.execute('INSERT OR IGNORE INTO early_alerts(symbol,side,price,volume_ratio,move_pct,candle_time,created_at,status) VALUES(?,?,?,?,?,?,?,?)',
                (symbol, result['side'], result['price'], result['volume_ratio'], result['move_pct'], result['candle_time'], stamp, 'pending'))
            con.commit()
            if cur.rowcount:
                logging.info('EARLY ALERT %s %s volume=%.1fx move=%+.2f%%', symbol,result['side'],result['volume_ratio'],result['move_pct'])
        finally:
            con.close()

    def _bootstrap(self, sym):
        params = urllib.parse.urlencode({'symbol':sym,'interval':'1m','limit':35})
        data = self.fetch_json('https://api.binance.com/api/v3/klines?'+params)
        current = int(time.time())
        history = collections.deque(maxlen=45)
        for x in data:
            if int(x[6]) // 1000 > current - 2:
                continue
            history.append({'time': int(x[0])//1000,'open':float(x[1]),'close':float(x[4]),'quote_volume':float(x[7])})
        with self.lock:
            self.observed[sym] = history

    def _handle_message(self, ws, message):
        try:
            payload = json.loads(message)
            k = payload.get('data',payload).get('k')
            if not k or not k.get('x'):
                return
            symbol = k['s']
            with self.lock:
                if symbol not in self.markets:
                    return
            self.last_stream_event = int(time.time())
            self._record(symbol, {'time': int(k['t'])//1000,'open':float(k['o']),
                                  'close':float(k['c']),'quote_volume':float(k['q'])})
        except Exception as exc:
            logging.warning('Early WebSocket data error: %s',exc)

    def _loop(self):
        try:
            import websocket
        except ImportError:
            logging.warning('Early radar unavailable: install websocket-client from requirements.txt')
            self.running = False
            return
        previous = None
        while self.running:
            try:
                with self.lock:
                    selected = tuple(self.markets)
                if not selected:
                    time.sleep(5)
                    continue
                if selected != previous:
                    for symbol in selected:
                        if symbol not in self.observed:
                            try: self._bootstrap(symbol)
                            except Exception as exc: logging.warning('Early radar seed %s: %s',symbol,exc)
                    previous=selected
                streams='/'.join(f'{s.lower()}@kline_1m' for s in selected)
                url='wss://stream.binance.com:9443/stream?streams='+streams
                app=websocket.WebSocketApp(url,on_message=self._handle_message,
                                          on_error=lambda ws,error: logging.warning('Early radar socket: %s', error))
                logging.info('Early radar WebSocket watching %d Binance pairs',len(selected))
                # Periodic reconnect also picks up a refreshed market universe.
                timer=threading.Timer(240,app.close)
                timer.daemon=True
                timer.start()
                try: app.run_forever(ping_interval=25,ping_timeout=10)
                finally: timer.cancel()
            except Exception as exc:
                logging.warning('Early radar reconnect: %s',exc)
            time.sleep(5)


def init_tables(con):
    con.execute('''CREATE TABLE IF NOT EXISTS early_alerts(
        id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT NOT NULL, side TEXT NOT NULL,
        price REAL NOT NULL, volume_ratio REAL NOT NULL, move_pct REAL NOT NULL,
        candle_time INTEGER NOT NULL, created_at INTEGER NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending', last_error TEXT,
        UNIQUE(symbol,candle_time,side))''')
    con.commit()


def early_message(row):
    return (f"EGONIA | EARLY ACTIVITY ALERT\n{row['symbol']} | 1m {row['side']}\n"
            f"Volume: {row['volume_ratio']:.1f}x 20-min baseline\n"
            f"1m move: {row['move_pct']:+.2f}% | Ref: {row['price']:.8g}\n"
            f"Activity alert, not a LONG/SHORT trade entry. #{row['id']}")
