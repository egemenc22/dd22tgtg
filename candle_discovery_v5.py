"""Raw candle-window model tournament. Historical research only; no trading or live alerts.

Strict chronological train/validation/test. All labels calculated forward of signal,
all input features from completed candles at/before signal.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, os, sqlite3, sys, time, traceback
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor, ExtraTreesRegressor, RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import joblib

for stream in (sys.stdout,sys.stderr):
    if hasattr(stream,'reconfigure'):
        stream.reconfigure(errors='backslashreplace')

VERSION='5.0.0'
BAR_MS=300000
HORIZONS={'30m':6,'2h':24,'12h':144}
TARGETS=(.03,.05,.10,.15,.30,.60)
WINDOW=48
CHANNELS=('logret','range','body','upper_wick','lower_wick','logvol','volume_delta')


def atomic_json(path,obj):
    path=Path(path);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False,allow_nan=False),encoding='utf-8');os.replace(tmp,path)


def get_schema(db):
    cols={r[1] for r in db.execute('PRAGMA table_info(candles)')}
    expected={'exchange','symbol','interval','open_ms','open','high','low','close','volume'}
    if not expected.issubset(cols):raise RuntimeError('Unexpected candles schema, missing: '+str(expected-cols))


def raw_rows(rows,limits,per_split,seed=42):
    a=np.asarray(rows,dtype='float64')
    if a.ndim!=2 or len(a)<WINDOW+max(HORIZONS.values())+3:return [],None
    ts=a[:,0].astype('int64');o,h,l,c,v=(a[:,j] for j in range(1,6))
    good=np.isfinite(a).all(axis=1)&(o>0)&(h>=np.maximum(o,c))&(l>0)&(l<=np.minimum(o,c))&(c>0)&(v>=0)
    continuous=np.zeros(len(ts),dtype=bool);continuous[1:]=(np.diff(ts)==BAR_MS)&good[1:]&good[:-1]
    gap=np.cumsum(~continuous)
    sc=np.maximum(c,1e-12)
    lr=np.zeros(len(a));lr[1:]=np.log(sc[1:]/sc[:-1]);lr=np.clip(lr,-2,2)
    rng=np.clip((h-l)/sc,0,3)
    body=np.clip((c-o)/np.maximum(o,1e-12),-2,2)
    upper=np.clip((h-np.maximum(c,o))/sc,0,3)
    lower=np.clip((np.minimum(c,o)-l)/sc,0,3)
    logv=np.log1p(v)
    dv=np.zeros(len(a));dv[1:]=np.clip(logv[1:]-logv[:-1],-10,10)
    # volume normalized relative to the *past* 48 candles only
    logvol_normalized=np.clip(logv-np.convolve(logv,np.ones(WINDOW)/WINDOW,mode='full')[:len(a)],-12,12)
    channels=np.stack((lr,rng,body,upper,lower,logvol_normalized,dv),axis=1).astype('float32')
    H=max(HORIZONS.values()); candidates=np.arange(WINDOW,len(a)-H-1,1)
    candidates=candidates[good[candidates] & (gap[candidates]==gap[candidates-WINDOW+1]) & (gap[candidates]==gap[candidates+H])]
    split=np.searchsorted(limits[1:-1],ts[candidates],side='right')
    keep=(ts[candidates]>=limits[0]) & (ts[candidates+H]<np.asarray(limits)[np.minimum(split+1,3)])
    candidates=candidates[keep];split=split[keep]
    results=[]
    for part in range(3):
        inds=candidates[split==part]
        if len(inds)>per_split:
            # stratify over time, not heavily overlapping adjacent windows
            inds=inds[np.linspace(0,len(inds)-1,per_split,dtype=int)]
        if len(inds)==0:continue
        input_ix=inds[:,None]-np.arange(WINDOW-1,-1,-1)[None,:]
        window=channels[input_ix]
        x=window.reshape(len(inds),-1)
        entry=o[inds+1]
        future={}
        for hz,bars in HORIZONS.items():
            highs=np.maximum.reduce([h[inds+j] for j in range(1,bars+1)])
            lows=np.minimum.reduce([l[inds+j] for j in range(1,bars+1)])
            future[hz]=np.stack((np.clip(highs/entry-1,0,3),np.clip(1-lows/entry,0,3)),axis=1).astype('float32')
        results.append((part,ts[inds],x,future))
    # Final fully closed window is used for a dated historical snapshot only.
    now=len(a)-2
    latest=None
    if now>=WINDOW and good[now] and gap[now]==gap[now-WINDOW+1]:
        latest=(int(ts[now]),channels[np.arange(now-WINDOW+1,now+1)].reshape(-1))
    return results,latest

def barrier_outcomes(rows,dates,horizon_bars=24,target_pct=.012,stop_pct=.007):
    """Conservative first-touch scalp labels; ambiguous same-bar hits are losses."""
    a=np.asarray(rows,dtype='float64');ts=a[:,0].astype('int64');o=a[:,1];h=a[:,2];l=a[:,3]
    positions={int(value):i for i,value in enumerate(ts)}
    long=[];short=[]
    for date in dates:
        i=positions[int(date)];entry=float(o[i+1]);end=min(len(a),i+1+int(horizon_bars))
        long_result=0.;short_result=0.;long_open=True;short_open=True
        for j in range(i+1,end):
            if long_open:
                stop_hit=l[j]<=entry*(1-stop_pct);target_hit=h[j]>=entry*(1+target_pct)
                if stop_hit:long_open=False
                elif target_hit:long_result=1.;long_open=False
            if short_open:
                stop_hit=h[j]>=entry*(1+stop_pct);target_hit=l[j]<=entry*(1-target_pct)
                if stop_hit:short_open=False
                elif target_hit:short_result=1.;short_open=False
            if not long_open and not short_open:break
        long.append(long_result);short.append(short_result)
    return np.asarray(long,dtype='float32'),np.asarray(short,dtype='float32')


def make_model(name,seed=42):
    typ,param=name.split(':',1)
    if typ=='hist':return HistGradientBoostingRegressor(max_iter=100,max_leaf_nodes=int(param),learning_rate=.06,l2_regularization=10,min_samples_leaf=45,random_state=seed)
    if typ=='extra':return ExtraTreesRegressor(n_estimators=70,max_depth=int(param),min_samples_leaf=8,max_features=.65,n_jobs=-1,random_state=seed)
    if typ=='forest':return RandomForestRegressor(n_estimators=55,max_depth=int(param),min_samples_leaf=10,max_features=.7,n_jobs=-1,random_state=seed)
    if typ=='ridge':return make_pipeline(StandardScaler(),Ridge(alpha=float(param)))
    raise ValueError(name)


def candidate_names():
    return ['hist:7','hist:15','hist:31','extra:8','extra:14','forest:8','forest:14','ridge:100','ridge:1000']


def validation_score(pred,true):
    # High movement candidate ranking using top-decile risk-adjusted realized event (not a trade PnL).
    k=max(20,int(len(pred)*.10));idx=np.argpartition(pred,-k)[-k:]
    return float(np.mean(np.clip(true[idx],0,1))-0.4*np.std(true[idx])/max(np.sqrt(k),1))


def cal_bin(p,y,tgt):
    edges=np.unique(np.quantile(p,np.linspace(0,1,11)))
    if len(edges)<2:edges=np.array([float(p.min())-1,float(p.max())+1])
    grp=np.searchsorted(edges[1:-1],p,side='right');base=float(np.mean(y>=tgt))
    bins=[]
    for j in range(len(edges)-1):
        flag=grp==j;count=int(flag.sum());hits=int(np.sum(y[flag]>=tgt))
        bins.append((hits+25*base)/(count+25))
    return edges,np.asarray(bins)


def cal_predict(pred,edges,bins):
    return bins[np.searchsorted(edges[1:-1],pred,side='right')]


def report_at(probs,truth,thresh,cutoff,markets):
    yes=probs>=cutoff;n=int(yes.sum());hits=int(np.sum(truth[yes]>=thresh))
    return {'signals':n,'hits':hits,'precision_pct':round(100*hits/n,3) if n else None,'base_rate_pct':round(100*float(np.mean(truth>=thresh)),3),'market_breadth':len(set(np.asarray(markets)[yes]))}


def fit_tournament(xtrain,xval,ytrain,yval,configs,root,key):
    attempts=[];winner=None;best=-1e99
    for num,name in enumerate(configs,1):
        print(f'  {key} model {num}/{len(configs)} {name}',flush=True)
        model=make_model(name)
        try:
            model.fit(xtrain,np.log1p(ytrain));p=np.clip(np.expm1(model.predict(xval)),0,3)
            score=validation_score(p,yval)
            attempts.append({'name':name,'score':round(score,7),'status':'ok'})
            if score>best:
                best=score;winner=name;joblib.dump(model,root/(key+'_winner.joblib'))
        except Exception as e:
            attempts.append({'name':name,'status':'error','error':str(e)})
    if winner is None:raise RuntimeError(f'No model fitted for {key}: {attempts}')
    return winner,attempts


def run(args):
    start=time.time();out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=True)
    db_path=Path(args.db).resolve()
    if not db_path.is_file():raise FileNotFoundError(f'Missing SQLite database: {db_path}')
    db=sqlite3.connect('file:'+db_path.as_posix()+'?mode=ro',uri=True);db.execute('PRAGMA query_only=ON');get_schema(db)
    low,high=db.execute("SELECT MIN(open_ms),MAX(open_ms) FROM candles WHERE interval='5m'").fetchone()
    if low is None:raise RuntimeError('No 5m candles found')
    end=int(high+BAR_MS);span=end-int(low);bounds=[int(low),int(low+span*.6),int(low+span*.8),end]
    markets=db.execute("SELECT exchange,symbol,COUNT(*) FROM candles WHERE interval='5m' GROUP BY exchange,symbol ORDER BY exchange,symbol").fetchall()
    if args.limit_markets:markets=markets[:args.limit_markets]
    X=[[],[],[]];Ys={h:[[[],[]] for _ in range(3)] for h in HORIZONS};M=[[],[],[]];last=[];stats=[]
    for n,(ex,sym,count) in enumerate(markets,1):
        rows=db.execute("SELECT open_ms,open,high,low,close,volume FROM candles WHERE exchange=? AND symbol=? AND interval='5m' ORDER BY open_ms",(ex,sym)).fetchall()
        groups,latest=raw_rows(rows,bounds,args.samples_per_market)
        if latest is not None:last.append((ex,sym,latest[0],latest[1]))
        observed=0
        for part,dates,features,target in groups:
            observed+=len(features);X[part].append(features);M[part].extend([f'{ex}:{sym}']*len(features))
            for hz in HORIZONS:
                for direction in (0,1):Ys[hz][part][direction].append(target[hz][:,direction])
        stats.append({'exchange':ex,'symbol':sym,'candles':count,'samples':observed})
        if n%5==0 or n==1 or n==len(markets):
            el=time.time()-start
            print(f'\rRaw candles {n}/{len(markets)} ({n/len(markets):.1%}) elapsed {el:.0f}s ETA {el/n*(len(markets)-n):.0f}s {ex}:{sym:<20}',end='',flush=True)
            atomic_json(out/'progress.json',{'stage':'extract','n':n,'total':len(markets),'elapsed_s':round(el,1)})
    print();db.close()
    if any(len(group)==0 for group in X):raise RuntimeError('Chronological training/validation/test segment empty; need more historical candles')
    X=[np.concatenate(group).astype('float32') for group in X]
    Ys={hz:[[np.concatenate(vals) for vals in split] for split in Ys[hz]] for hz in HORIZONS}
    last_features=np.stack([i[3] for i in last]) if last else np.empty((0,WINDOW*len(CHANNELS)),dtype='float32')
    configs=candidate_names();results=[];tournament=[];alerts=[]
    for hz in HORIZONS:
        for side,label in ((0,'LONG'),(1,'SHORT')):
            key=hz+'_'+label;yy=Ys[hz];ytr=yy[0][side];yval=yy[1][side];ytest=yy[2][side]
            print(f'\nSelecting {key}: {len(X[0])} train, {len(X[1])} validation, {len(X[2])} test',flush=True)
            winner,attempts=fit_tournament(X[0],X[1],ytr,yval,configs,out,key)
            model=joblib.load(out/(key+'_winner.joblib'))
            pv=np.clip(np.expm1(model.predict(X[1])),0,3);pt=np.clip(np.expm1(model.predict(X[2])),0,3)
            tournament.append({'task':key,'best_model':winner,'candidates':attempts})
            for target in TARGETS:
                edges,bins=cal_bin(pv,yval,target)
                cv=cal_predict(pv,edges,bins);ct=cal_predict(pt,edges,bins)
                choices=[];base=float(np.mean(yval>=target))
                for cutoff in (.25,.35,.45,.55,.65,.75,.85,.90):
                    rr=report_at(cv,yval,target,cutoff,M[1]);
                    if rr['signals']>=args.min_validation_signals and rr['market_breadth']>=args.min_markets:
                        choices.append((rr['precision_pct']/100-base,cutoff,rr))
                picked=max(choices,key=lambda a:a[0]) if choices else None
                if picked:
                    cutoff=picked[1];vr=picked[2];tr=report_at(ct,ytest,target,cutoff,M[2])
                else:cutoff=None;vr=tr=None
                results.append({'horizon':hz,'direction':label,'target_pct':round(target*100,2),'model':winner,'validation_cutoff':cutoff,'validation':vr,'historical_test':tr})
                if cutoff is not None and len(last_features):
                    pred=np.clip(np.expm1(model.predict(last_features)),0,3)
                    probabilities=cal_predict(pred,edges,bins)
                    for i in np.flatnonzero(probabilities>=cutoff):
                        ex,sym,ts,_=last[int(i)];alerts.append({'exchange':ex,'symbol':sym,'last_candle_utc':datetime.fromtimestamp(ts/1000,timezone.utc).isoformat(),'direction':label,'horizon':hz,'target_pct':target*100,'estimated_probability':round(float(probabilities[i]),4),'test_precision_pct':tr['precision_pct'] if tr else None})
            atomic_json(out/'progress.json',{'stage':'models','finished':key,'elapsed_s':round(time.time()-start,1)})
    alerts.sort(key=lambda a:a['estimated_probability'],reverse=True)
    for fn,arr in [('snapshot_watchlist.csv',alerts),('market_coverage.csv',stats)]:
        with (out/fn).open('w',newline='',encoding='utf-8-sig') as f:
            if arr:writer=csv.DictWriter(f,fieldnames=arr[0].keys());writer.writeheader();writer.writerows(arr)
    summary={'version':VERSION,'status':'complete','architecture':'Raw 48x7 OHLCV candle window flattened into 336 input dimensions; automated estimator tournament',
      'feature_channels':CHANNELS,'window_bars':WINDOW,'model_candidates_per_task':len(configs),'trained_candidates':len(tournament)*len(configs),
      'samples_per_split':[len(x) for x in X],'market_count':len(markets),'time_bounds_utc':[datetime.fromtimestamp(x/1000,timezone.utc).isoformat() for x in bounds],
      'tournament':tournament,'results':results,'watchlist_rows':len(alerts),'duration_seconds':round(time.time()-start,1),
      'limitations':['Snapshot only; not live signal bot','Results are future OHLC extremes, not executable PnL','Coin price can move against position before hitting target','Historical test has been studied in earlier versions','Only 5m candle windows; no neural LSTM/CNN or genetic symbolic trees','Model search is finite 9 configurations x 6 tasks','Training time samples are subsampled per market','No exchange book liquidity, slippage or fills verified']}
    atomic_json(out/'candle_discovery_report.json',summary)
    print(f'COMPLETE {out} | candidates={len(tournament)*len(configs)} | watchlist={len(alerts)} | {time.time()-start:.0f}s',flush=True)
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='scalp_research.sqlite');p.add_argument('--output',default='candle_discovery_results')
    p.add_argument('--samples-per-market',type=int,default=120);p.add_argument('--limit-markets',type=int,default=0);p.add_argument('--min-validation-signals',type=int,default=30);p.add_argument('--min-markets',type=int,default=8)
    run(p.parse_args())

if __name__=='__main__':main()
