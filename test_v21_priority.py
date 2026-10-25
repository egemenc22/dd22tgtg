import unittest,sqlite3
from signal_priority import consolidate,channel_allowed
from signal_bot import SCHEMA,queue
class TestV21(unittest.TestCase):
 def setUp(self):
  self.a={'strategy':'VOLUME_BREAKOUT','side':'LONG','strength':78,'reason':'5m VOLUME_BREAKOUT: spike','entry':1,'origin_ts':12,'timeframe':'5m'}
 def test_empty(self):self.assertIsNone(consolidate([]))
 def test_merge(self):
  b=dict(self.a,strategy='EMA_TREND',reason='1h EMA_TREND: cross',strength=70,timeframe='1h')
  p=consolidate([self.a,b]);self.assertEqual(p['confirmations'],2);self.assertIn('EMA_TREND',p['reason'])
 def test_conflict(self):self.assertIsNone(consolidate([self.a,dict(self.a,side='SHORT')]))
 def test_one(self):self.assertEqual(consolidate([self.a])['strength'],78)
 def test_x(self):self.assertTrue(channel_allowed(self.a,'x',{'x_min_signal_strength':75,'x_featured_strategies':['VOLUME_BREAKOUT']}))
 def test_x_no(self):self.assertFalse(channel_allowed(self.a,'x',{'x_min_signal_strength':90,'x_featured_strategies':['VOLUME_BREAKOUT']}))
 def test_route_caps(self):
  c=sqlite3.connect(':memory:');c.executescript(SCHEMA)
  import time
  t=int(time.time());d=(('Binance','ABCUSDT','LONG',1,t,1,1.05,.98,240,t+240*60,'ACTIVE',80,'5m VOLUME_BREAKOUT: spike'))
  c.execute('INSERT INTO signals(exchange,symbol,side,origin_ts,created_at,entry,target,stop,horizon_minutes,expires_at,status,strength,reason) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',d)
  cfg={'enable_telegram':False,'enable_telegram_free':True,'enable_telegram_vip':True,'enable_x':True,'free_open_per_day':0,'vip_open_per_day':1,'x_open_per_day':1,'x_min_signal_strength':75,'x_featured_strategies':['VOLUME_BREAKOUT']}
  queue(c,1,cfg);self.assertEqual({r[0] for r in c.execute('SELECT channel FROM delivery')},{'x','telegram_vip'})
if __name__=='__main__':unittest.main()
