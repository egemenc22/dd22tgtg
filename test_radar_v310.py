import unittest,sqlite3
from radar_engine import analyze,ensure_tables,record,message,publish

class RadarTests(unittest.TestCase):
 def bars(self,volume=10000,close=100):
  a=[]
  for i in range(60):
   p=100.;a.append({'time':i*300,'close':p,'open':p,'high':p+0.1,'low':p-0.1,'quote_volume':10000.,'close_time':i*300+299})
  a[-1].update({'open':100.,'close':close,'high':max(close,100)+.2,'low':min(close,100)-.2,'quote_volume':volume})
  return a
 def test_unusual_volume(self):
  r=analyze(self.bars(80000,101));self.assertIsNotNone(r);self.assertIn('UNUSUAL_VOLUME',r['kinds']);self.assertEqual(r['direction'],'UP')
 def test_no_spam_low_volume(self):self.assertIsNone(analyze(self.bars(12000,100.1)))
 def test_gap_rejected(self):
  b=self.bars(80000,101);b[-1]['time']+=300;self.assertIsNone(analyze(b))
 def test_dedup_cap_and_delivery(self):
  con=sqlite3.connect(':memory:');con.row_factory=sqlite3.Row;ensure_tables(con)
  cfg={'enable_telegram_free':True,'enable_telegram_vip':False,'radar_min_score':50,'radar_free_min_score':50,'radar_free_daily_cap':1,'radar_symbol_cooldown_minutes':180,'dry_run':False,'allow_unvalidated_publication':True}
  ev=analyze(self.bars(80000,101));a=record(con,'Binance','AAAUSDT',ev,cfg,clock=1000000)
  self.assertIsNotNone(a);self.assertIsNone(record(con,'MEXC','AAAUSDT',ev,cfg,clock=1000100))
  other=dict(ev,origin_ts=ev['origin_ts']+300);record(con,'Binance','BBBUSDT',other,cfg,clock=1000100)
  self.assertEqual(con.execute('SELECT COUNT(*) FROM radar_delivery').fetchone()[0],1)
  received=[];publish(con,cfg,lambda c,m:received.append(m) or '456',clock=ev['origin_ts']+301)
  self.assertEqual(len(received),1);self.assertIn('Volume:',received[0]);self.assertEqual(con.execute("SELECT status FROM radar_delivery").fetchone()[0],'sent')
 def test_dry_run(self):
  con=sqlite3.connect(':memory:');con.row_factory=sqlite3.Row;ensure_tables(con)
  cfg={'enable_telegram_free':True,'radar_min_score':50,'radar_free_min_score':50,'dry_run':True}
  record(con,'Binance','AAAUSDT',analyze(self.bars(80000,101)),cfg,clock=1000000)
  publish(con,cfg,lambda *a:self.fail('should not call network'),clock=18000)
  self.assertEqual(con.execute('SELECT status FROM radar_delivery').fetchone()[0],'dry_run')
 def test_vip_unlimited_but_same_direction_is_cooled_down(self):
  con=sqlite3.connect(':memory:');con.row_factory=sqlite3.Row;ensure_tables(con)
  cfg={'enable_telegram_free':False,'enable_telegram_vip':True,'radar_min_score':50,
       'radar_vip_daily_cap':0,'radar_symbol_cooldown_minutes':60}
  ev=analyze(self.bars(80000,101))
  self.assertIsNotNone(record(con,'Binance','AAAUSDT',ev,cfg,clock=1000000))
  repeated=dict(ev,origin_ts=ev['origin_ts']+300)
  self.assertIsNone(record(con,'MEXC','AAAUSDT',repeated,cfg,clock=1000300))
  reversed_event=dict(ev,direction='DOWN',origin_ts=ev['origin_ts']+600)
  self.assertIsNotNone(record(con,'Binance','AAAUSDT',reversed_event,cfg,clock=1000600))
  for i in range(30):
   other=dict(ev,origin_ts=ev['origin_ts']+900+i*300)
   self.assertIsNotNone(record(con,'Binance',f'COIN{i}USDT',other,cfg,clock=1000900+i))
  self.assertEqual(con.execute("SELECT COUNT(*) FROM radar_delivery WHERE channel='telegram_vip'").fetchone()[0],32)
 def test_calibrated_ml_event_is_not_rejected_by_generic_radar_score(self):
  con=sqlite3.connect(':memory:');con.row_factory=sqlite3.Row;ensure_tables(con)
  cfg={'enable_telegram_free':False,'enable_telegram_vip':True,'radar_min_score':75,
       'radar_vip_daily_cap':0,'radar_symbol_cooldown_minutes':60}
  event={'score':61,'kind':'ML_RANDOM_FOREST_LONG','direction':'UP','origin_ts':900,
         'volume_ratio':1.2,'move_pct':.3,'quote_volume':50000,'price':1.0}
  self.assertIsNotNone(record(con,'Binance','AAAUSDT',event,cfg,clock=1000))
  self.assertEqual(con.execute("SELECT COUNT(*) FROM radar_delivery WHERE channel='telegram_vip'").fetchone()[0],1)
if __name__=='__main__':unittest.main()
