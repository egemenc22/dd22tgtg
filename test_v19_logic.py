import unittest, sqlite3
from signal_bot import SCHEMA, queue, should_publish_x
class VersionTest(unittest.TestCase):
 def test_x_curation(self):
  cfg={'x_min_signal_strength':75,'x_featured_strategies':['VOLUME_BREAKOUT']}
  self.assertTrue(should_publish_x({'strength':81,'reason':'5m VOLUME_BREAKOUT: volume spike'},cfg))
  self.assertFalse(should_publish_x({'strength':60,'reason':'5m VOLUME_BREAKOUT: spike'},cfg))
  self.assertFalse(should_publish_x({'strength':90,'reason':'5m EMA_TREND: cross'},cfg))
 def test_vip_kept_if_x_filtered(self):
  con=sqlite3.connect(':memory:');con.executescript(SCHEMA)
  con.execute("INSERT INTO signals(exchange,symbol,side,origin_ts,created_at,entry,target,stop,horizon_minutes,expires_at,status,strength,reason) VALUES('MEXC','FOOUSDT','LONG',1,1,1,2,0.5,240,241,'ACTIVE',65,'5m EMA_TREND: x')")
  cfg={'enable_telegram':False,'enable_telegram_free':False,'enable_telegram_vip':True,'enable_x':True,'x_min_signal_strength':75,'x_featured_strategies':['VOLUME_BREAKOUT']}
  queue(con,1,cfg)
  self.assertEqual([r[0] for r in con.execute('select channel from delivery')],['telegram_vip'])
if __name__=='__main__':unittest.main()
