"""Deterministic consolidation and channel selection; does not claim predictive accuracy."""
from collections import defaultdict

WEIGHTS={'VOLUME_BREAKOUT':16,'VOLUME_ACCELERATION':14,'DONCHIAN_20':12,'BB_SQUEEZE':11,'MOMENTUM_IGNITION':10,'ATR_CHANNEL':6,'MACD_MOMENTUM':5,'EMA_TREND':4,'RSI_BB_REVERSION':3}
TIMEFRAME={'5m':0,'15m':3,'1h':5}

def consolidate(candidates):
    """Choose at most one side per symbol per scan, rejecting conflicting directions.
    Group independent triggers from same side but never invent extra evidence.
    """
    if not candidates:return None
    groups=defaultdict(list)
    for p in candidates:
        if p.get('side') in ('LONG','SHORT') and p.get('strategy') in WEIGHTS:
            groups[p['side']].append(p)
    if not groups:return None
    if len(groups)>1:return None  # disagreement isn't a confirmation
    side,picks=next(iter(groups.items()))
    picks=sorted(picks,key=lambda p:(float(p['strength'])+WEIGHTS[p['strategy']]+TIMEFRAME.get(p.get('timeframe','5m'),0),p['strategy']),reverse=True)
    head=dict(picks[0]);names=sorted({p['strategy'] for p in picks})
    head['strategy']=picks[0]['strategy']
    head['strength']=min(95,round(float(head['strength'])+min(9,3*(len(names)-1)),1))
    head['reason']=head['reason']+' | CONFIRMING_STRATEGIES: '+','.join(names)
    head['confirmations']=len(names)
    return head

def channel_allowed(signal,channel,cfg):
    if channel=='x':
        return (float(signal['strength'])>=float(cfg.get('x_min_signal_strength',75))
                and any(n in signal['reason'] for n in cfg.get('x_featured_strategies',[])))
    if channel=='telegram_free':
        return float(signal['strength'])>=float(cfg.get('free_min_signal_strength',65))
    return True
