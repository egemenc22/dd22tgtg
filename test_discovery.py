import unittest
from market_discovery import discover,discover_all
class DiscoveryTests(unittest.TestCase):
 def test_binance_market_filter_ranking(self):
  info={'symbols':[{'symbol':'BTCUSDT','baseAsset':'BTC','quoteAsset':'USDT','status':'TRADING'}, {'symbol':'ETHUSDT','baseAsset':'ETH','quoteAsset':'USDT','status':'TRADING'},{'symbol':'USDCUSDT','baseAsset':'USDC','quoteAsset':'USDT','status':'TRADING'},{'symbol':'FAKEUSDT','baseAsset':'FAKE','quoteAsset':'USDT','status':'BREAK'}]}
  ticks=[{'symbol':'BTCUSDT','quoteVolume':'9000000'},{'symbol':'ETHUSDT','quoteVolume':'5000000'},{'symbol':'USDCUSDT','quoteVolume':'100000000'},{'symbol':'FAKEUSDT','quoteVolume':'100000000'}]
  def get(url):return info if 'exchangeInfo' in url else ticks
  self.assertEqual(discover('Binance',get),[('BTCUSDT',9000000.),('ETHUSDT',5000000.)])
 def test_gate(self):
  info=[{'id':'SOL_USDT','base':'SOL','quote':'USDT','trade_status':'tradable'},{'id':'BAD_USDT','base':'BAD','quote':'USDT','trade_status':'untradable'}]
  ticks=[{'currency_pair':'SOL_USDT','quote_volume':'2500000'},{'currency_pair':'BAD_USDT','quote_volume':'9000000'}]
  def get(url):return info if 'currency_pairs' in url else ticks
  self.assertEqual(discover('Gate',get),[('SOLUSDT',2500000.)])
 def test_failure_isolation(self):
  def get(url):raise RuntimeError('offline')
  m,e=discover_all(['Binance','Gate'],get)
  self.assertFalse(m);self.assertEqual(set(e),{'Binance','Gate'})
 def test_low_liquidity(self):
  i={'symbols':[{'symbol':'AAAUSDT','baseAsset':'AAA','quoteAsset':'USDT','status':'TRADING'}]}
  def get(url):return i if 'exchangeInfo' in url else [{'symbol':'AAAUSDT','quoteVolume':'99'}]
  self.assertEqual(discover('MEXC',get),[])
if __name__=='__main__':unittest.main()
