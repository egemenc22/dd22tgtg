import unittest
from market_intelligence import volume_regime,orderbook_binance,enrich_signal
class IntelligenceTests(unittest.TestCase):
 def rows(self):
  return [dict(open=10,high=10.2,low=9.8,close=10,quote_volume=(1200 if i>=55 else 1000),time=i*300,close_time=i*300+299) for i in range(60)]
 def book(self,symbol,url):
  return {'bids':[['10','1000'],['9.99','500']],'asks':[['10.01','900'],['10.02','600']]}
 def test_regime(self):self.assertTrue(volume_regime(self.rows())['valid'])
 def test_short_series(self):self.assertFalse(volume_regime(self.rows()[:10])['valid'])
 def test_depth(self):self.assertGreater(orderbook_binance('PEPEUSDT',lambda u:self.book('',u))['depth_usdt'],10000)
 def test_wide_spread_rejection(self):
  sig=dict(side='LONG',strength=65,reason='test')
  self.assertIsNone(enrich_signal(sig,self.rows(),'Binance','PEPEUSDT',lambda u:{'bids':[['10','1000']],'asks':[['10.05','1000']]},{'enable_orderbook_filter':True}))
 def test_unavailable_is_labeled(self):
  def bad(u):raise OSError('offline')
  out=enrich_signal(dict(side='LONG',strength=65,reason='test'),self.rows(),'Binance','PEPEUSDT',bad,{'enable_orderbook_filter':True})
  self.assertIn('ORDERBOOK_UNAVAILABLE',out['reason'])
 def test_fail_closed(self):
  def bad(u):raise OSError('offline')
  self.assertIsNone(enrich_signal(dict(side='LONG',strength=65,reason='test'),self.rows(),'Binance','PEPEUSDT',bad,{'enable_orderbook_filter':True,'require_orderbook':True}))
if __name__=='__main__':unittest.main()
