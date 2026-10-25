"""Read-only market coverage and scanning-lag telemetry."""
import time


def ensure_tables(con):
    con.execute('''CREATE TABLE IF NOT EXISTS scan_coverage (
      exchange TEXT NOT NULL, symbol TEXT NOT NULL, scanned_at INTEGER NOT NULL,
      candle_close_time INTEGER, error TEXT, duration_ms INTEGER NOT NULL DEFAULT 0,
      PRIMARY KEY(exchange,symbol))''')
    con.commit()


def update(con, results, timestamp=None):
    stamp=int(time.time() if timestamp is None else timestamp)
    con.executemany('''INSERT INTO scan_coverage(exchange,symbol,scanned_at,candle_close_time,error,duration_ms)
      VALUES(?,?,?,?,?,?) ON CONFLICT(exchange,symbol) DO UPDATE SET
      scanned_at=excluded.scanned_at,candle_close_time=excluded.candle_close_time,
      error=excluded.error,duration_ms=excluded.duration_ms''',
      [(r['exchange'],r['symbol'],stamp,r.get('candle_close_time'),r.get('error'),int(r.get('duration_ms',0))) for r in results])
    con.commit()


def snapshot(con, universe, timestamp=None):
    stamp=int(time.time() if timestamp is None else timestamp)
    rows={(r['exchange'],r['symbol']):r for r in con.execute('SELECT * FROM scan_coverage')}
    total=len(universe)
    seen=[rows[(x[0],x[1])] for x in universe if (x[0],x[1]) in rows]
    fresh=[r for r in seen if stamp-r['scanned_at']<=300]
    errors=sum(bool(r['error']) for r in fresh)
    ages=sorted(stamp-r['scanned_at'] for r in seen)
    candle_lags=sorted(max(0,stamp-r['candle_close_time']) for r in fresh if r['candle_close_time'])
    return {'universe':total,'ever_scanned':len(seen),'scanned_last_5m':len(fresh),
            'coverage_5m_pct':round(100*len(fresh)/total,1) if total else 0,
            'errors_last_5m':errors,'oldest_scan_age_s':max(ages) if ages else None,
            'p95_candle_age_s':candle_lags[min(len(candle_lags)-1,int(.95*len(candle_lags)))] if candle_lags else None}
