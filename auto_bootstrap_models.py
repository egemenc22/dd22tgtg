"""One-click model bootstrapping: public historic coin candles, no user paths.
Run once if no model artifacts; cached results for later restarts.
"""
from pathlib import Path
import json,sqlite3,subprocess,sys,time,random,traceback
from concurrent.futures import ThreadPoolExecutor,as_completed
from market_discovery import discover_all
from market_feeds import fetch
from product_filters import allowed_crypto_base
from signal_bot import get_json
import two_model_engine
ROOT=Path(__file__).resolve().parent
DB=ROOT/'coin_training_cache.sqlite'

def main():
    if two_model_engine.ready():
        print('Two ML models: cached and ready.',flush=True);return 0
    config=json.loads((ROOT/'config.json').read_text('utf-8'))
    print('Fetching recent historical coin candles automatically (first launch)...',flush=True)
    markets,errors=discover_all(config.get('exchanges',['Binance','MEXC','Gate']),get_json,min_quote_volume=15000,max_pairs_per_exchange=250,focus=True,max_quote_volume=50000000)
    if not markets:print('Exchange discovery unavailable:',errors,flush=True);return 1
    wanted=max(30,int(config.get('ml_bootstrap_markets',60)))
    # Balanced selection across CEXs; deterministic for reproducibility.
    markets=markets[:max(wanted*5,500)]
    markets=markets[::max(1,len(markets)//wanted)][:wanted]
    con=sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS candles(exchange TEXT, symbol TEXT, interval TEXT, open_ms INTEGER, open REAL, high REAL, low REAL, close REAL, volume REAL, PRIMARY KEY(exchange,symbol,interval,open_ms))')
    con.commit()
    def grab(rec):
        ex,sym=rec[:2]
        try:
            rows=fetch(ex,sym,'5m',get_json,limit=min(950,int(config.get('ml_bootstrap_candles',900))))
            rows=[r for r in rows if r['close_time']<=time.time()-2]
            if len(rows)<850:return (ex,sym,[], 'insufficient history for chronological splits')
            return (ex,sym,rows,'')
        except Exception as exc:return (ex,sym,[],str(exc)[:100])
    ok=0
    with ThreadPoolExecutor(max_workers=5) as pool:
        for f in as_completed([pool.submit(grab,m) for m in markets]):
            ex,sym,rows,err=f.result()
            if rows:
                con.executemany('INSERT OR REPLACE INTO candles VALUES(?,?,?,?,?,?,?,?,?)',[(ex,sym,'5m',int(r['time']*1000),r['open'],r['high'],r['low'],r['close'],r['volume']) for r in rows]);ok+=1
            elif err:print('Data skipped',ex,sym,err,flush=True)
    con.commit();con.close()
    print('Candle history loaded for',ok,'coin pairs',flush=True)
    if ok<12:print('Not enough trading history to initialize models.',flush=True);return 1
    cmd=[sys.executable,str(ROOT/'train_two_models.py'),'--db',str(DB),'--samples-per-market','40']
    result=subprocess.run(cmd,cwd=ROOT)
    if result.returncode: return result.returncode
    if not two_model_engine.ready():return 1
    print('Two models ready. Launching live scanner.',flush=True)
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('Auto-bootstrap failed:',type(exc).__name__,str(exc),flush=True)
        traceback.print_exc();sys.exit(1)
