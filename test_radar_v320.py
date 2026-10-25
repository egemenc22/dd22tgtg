import unittest,sqlite3, time
from radar_engine import ensure_tables,record,publish

class RadarReliabilityTests(unittest.TestCase):
 def fixture(self):
  con=sqlite3.connect(':memory:');con.row_factory=sqlite3.Row;ensure_tables(con)
  cfg={'enable_telegram_free':True,'radar_min_score':60,'radar_free_min_score':60,'radar_free_daily_cap':1,'dry_run':False,'allow_unvalidated_publication':True,'radar_max_alert_age_seconds':720}
  return con,cfg
 def event(self,ts,score=90):
  return {'score':score,'kind':'UNUSUAL_VOLUME','kinds':['UNUSUAL_VOLUME'],'direction':'UP','volume_ratio':4.2,'move_pct':2.3,'quote_volume':80000,'price':1.23,'origin_ts':ts}
 def test_expired_not_sent(self):
  con,cfg=self.fixture();record(con,'Binance','AAAUSDT',self.event(300),cfg,clock=1000)
  publish(con,cfg,lambda *a:self.fail('expired alert should not send'),clock=2000)
  self.assertEqual(con.execute('select status from radar_delivery').fetchone()[0],'expired')
 def test_fresh_sent(self):
  con,cfg=self.fixture();record(con,'Binance','AAAUSDT',self.event(900),cfg,clock=1000)
  delivered=[];publish(con,cfg,lambda c,m:delivered.append(m) or '123',clock=1100)
  self.assertEqual(len(delivered),1)
  self.assertEqual(con.execute('select status from radar_delivery').fetchone()[0],'sent')
 def test_expired_consumes_same_day_capacity(self):
  con,cfg=self.fixture();record(con,'Binance','AAAUSDT',self.event(300),cfg,clock=1000)
  publish(con,cfg,lambda *a:self.fail('expired alert should not send'),clock=2000)
  record(con,'Binance','BBBUSDT',self.event(1800),cfg,clock=2000)
  self.assertEqual(con.execute('select count(*) from radar_delivery').fetchone()[0],1)
if __name__=='__main__':unittest.main()
