"""Train only the two fixed v5 winners on user's historical 5m candle SQLite."""
import argparse,sqlite3,json,os
from pathlib import Path
import numpy as np
import joblib
from candle_discovery_v5 import raw_rows,barrier_outcomes,make_model,cal_bin,cal_predict,report_at, BAR_MS

PRODUCT_VERSION='scalp_2h_v1'
HORIZON='2h'
TARGET_PCT=.012
STOP_PCT=.007
PROBABILITY_THRESHOLD=.65

p=argparse.ArgumentParser()
p.add_argument('--db',required=True);p.add_argument('--limit-markets',type=int,default=0);p.add_argument('--samples-per-market',type=int,default=120)
a=p.parse_args()
path=Path(a.db)
if not path.is_file():raise SystemExit('Historical candle database not found: '+str(path))
con=sqlite3.connect('file:'+path.resolve().as_posix()+'?mode=ro',uri=True)
col={r[1] for r in con.execute('PRAGMA table_info(candles)')}
if not {'exchange','symbol','interval','open_ms','open','high','low','close','volume'}.issubset(col):raise SystemExit('Expected research candles schema absent')
low,high=con.execute("SELECT MIN(open_ms),MAX(open_ms) FROM candles WHERE interval='5m'").fetchone()
if low is None:raise SystemExit('No 5m candles in database')
span=high+BAR_MS-low;bounds=[int(low),int(low+span*.6),int(low+span*.8),int(high+BAR_MS)]
markets=con.execute("SELECT exchange,symbol FROM candles WHERE interval='5m' GROUP BY exchange,symbol ORDER BY exchange,symbol").fetchall()
if a.limit_markets:markets=markets[:a.limit_markets]
xs=[[],[],[]];ys={k:[[],[],[]] for k in ('short_extra','long_forest')};names=[[],[],[]]
for i,(ex,sym) in enumerate(markets,1):
    candles=con.execute("SELECT open_ms,open,high,low,close,volume FROM candles WHERE exchange=? AND symbol=? AND interval='5m' ORDER BY open_ms",(ex,sym)).fetchall()
    groups,_=raw_rows(candles,bounds,a.samples_per_market)
    for part,dates,x,targets in groups:
        xs[part].append(x)
        long_result,short_result=barrier_outcomes(candles,dates,24,TARGET_PCT,STOP_PCT)
        ys['short_extra'][part].append(short_result);ys['long_forest'][part].append(long_result)
        names[part].extend([ex+':'+sym]*len(x))
    if i%20==0:print('Prepared',i,'/',len(markets),flush=True)
con.close()
if any(not x for x in xs):raise SystemExit('Insufficient chronological data for three partitions; need longer candle history')
xs=[np.concatenate(x).astype('float32') for x in xs]
out=Path(__file__).parent/'two_models';out.mkdir(exist_ok=True)
report={}
for name,kind in [('short_extra','extra:8'),('long_forest','forest:8')]:
    y=[np.concatenate(z) for z in ys[name]]
    model=make_model(kind)
    print('Training',name,'train samples',len(y[0]),flush=True)
    model.fit(xs[0],np.log1p(y[0]))
    pv=np.clip(np.expm1(model.predict(xs[1])),0,3)
    pt=np.clip(np.expm1(model.predict(xs[2])),0,3)
    edges,bins=cal_bin(pv,y[1],.5)
    probs=cal_predict(pt,edges,bins)
    holdout=report_at(probs,y[2],.5,PROBABILITY_THRESHOLD,names[2])
    approved=bool(holdout['signals']>=30 and holdout['market_breadth']>=5 and (holdout['precision_pct'] or 0)>=55)
    report[name]={'product_version':PRODUCT_VERSION,'model':kind,'train':len(y[0]),'validation':len(y[1]),'test':len(y[2]),'threshold':PROBABILITY_THRESHOLD,
                  'horizon':HORIZON,'target_pct':TARGET_PCT*100,'stop_pct':STOP_PCT*100,
                  'holdout':holdout,'approved_for_live':approved,'edges':edges.tolist(),'bins':bins.tolist()}
    joblib.dump(model,out/(name+'.joblib'))
(out/'calibration.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print('TWO MODELS TRAINED. Holdout report:',json.dumps({k:v['holdout'] for k,v in report.items()},indent=2),flush=True)
