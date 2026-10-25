"""Exact v5 raw 48x7 features, ExtraTrees SHORT and RandomForest LONG only."""
from pathlib import Path
import json,time,logging,math,threading
_load_lock=threading.RLock()
MODELS=Path(__file__).resolve().parent/'two_models'
_cache={}

def ready():
    return all((MODELS/(k+'.joblib')).is_file() for k in ('short_extra','long_forest')) and (MODELS/'calibration.json').is_file()

def features(rows):
    import numpy as np
    from candle_discovery_v5 import WINDOW,BAR_MS
    if len(rows)<WINDOW*2:return None
    a=rows[-(WINDOW*2):]
    times=[int(x['time']) for x in a]
    if any(times[i]-times[i-1]!=300 for i in range(1,len(times))):return None
    o=np.array([float(x['open']) for x in a]);h=np.array([float(x['high']) for x in a]);l=np.array([float(x['low']) for x in a]);c=np.array([float(x['close']) for x in a]);v=np.array([float(x['volume']) for x in a])
    if not (np.isfinite(o).all() and np.isfinite(h).all() and np.isfinite(l).all() and np.isfinite(c).all() and np.isfinite(v).all()):return None
    if not ((o>0).all() and (c>0).all() and (v>=0).all() and (h>=np.maximum(o,c)).all() and (l<=np.minimum(o,c)).all() and (l>0).all()):return None
    sc=np.maximum(c,1e-12)
    lr=np.zeros(len(a));lr[1:]=np.log(sc[1:]/sc[:-1]);lr=np.clip(lr,-2,2)
    rng=np.clip((h-l)/sc,0,3)
    body=np.clip((c-o)/np.maximum(o,1e-12),-2,2)
    upper=np.clip((h-np.maximum(c,o))/sc,0,3)
    lower=np.clip((np.minimum(c,o)-l)/sc,0,3)
    logv=np.log1p(v)
    dv=np.zeros(len(a));dv[1:]=np.clip(logv[1:]-logv[:-1],-10,10)
    normalized=np.clip(logv-np.convolve(logv,np.ones(WINDOW)/WINDOW,mode='full')[:len(a)],-12,12)
    channels=np.stack((lr,rng,body,upper,lower,normalized,dv),axis=1).astype('float32')
    return channels[-WINDOW:].reshape(1,-1)

def analyze(rows, cfg=None):
    if not ready():return None
    import joblib, numpy as np
    from candle_discovery_v5 import cal_predict
    cfg=cfg or {}
    x=features(rows)
    if x is None:return None
    with _load_lock:
        if not _cache:
            c=json.loads((MODELS/'calibration.json').read_text(encoding='utf-8'))
            for side in ('short_extra','long_forest'):
                model=joblib.load(MODELS/(side+'.joblib'))
                if hasattr(model,'n_jobs'):model.n_jobs=1
                _cache[side]=(model,c[side])
    threshold=float(cfg.get('ml_probability_threshold',0.6))
    matched=[]
    for name,dir_ in [('short_extra','DOWN'),('long_forest','UP')]:
        model,cal=_cache[name]
        raw=float(np.clip(np.expm1(model.predict(x)[0]),0,3))
        prob=float(cal_predict(np.array([raw]),np.array(cal['edges']),np.array(cal['bins']))[0])
        if prob>=threshold:matched.append((prob,name,dir_))
    if not matched:return None
    # If both models fire, avoid contradictory publication unless one probability clearly wins.
    matched.sort(reverse=True)
    if len(matched)>1 and matched[0][0]-matched[1][0]<float(cfg.get('ml_direction_min_margin',0.08)):
        return None
    prob,name,direction=matched[0]
    last=rows[-1]
    return dict(kind='ML_EXTRA_TREES_SHORT' if direction=='DOWN' else 'ML_RANDOM_FOREST_LONG',
                direction=direction,score=round(prob*100),move_pct=100*(float(last['close'])/float(rows[-2]['close'])-1),
                quote_volume=float(last.get('quote_volume',0)),volume_ratio=round(float(last.get('quote_volume',0))/max(1.0,sum(float(t.get('quote_volume',0)) for t in rows[-25:-1])/24),2),price=float(last['close']),origin_ts=int(last['time']),
                ml_probability=round(prob,4),ml_model=name,ml_horizon='12h',ml_target_pct=3.0)
