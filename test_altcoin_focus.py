import unittest
from market_discovery import discover, discover_all
from altcoin_focus import focus_rank

class AltcoinFocusTests(unittest.TestCase):
    def setUp(self):
        self.info={'symbols':[{'symbol':s+'USDT','baseAsset':s,'quoteAsset':'USDT','status':'TRADING'} for s in ['BTC','MOON','ALTX','DUST']]}
        self.ticks=[{'symbol':'BTCUSDT','quoteVolume':'80000000','priceChangePercent':'3','highPrice':'95000','lowPrice':'92000'},
                    {'symbol':'MOONUSDT','quoteVolume':'800000','priceChangePercent':'18','highPrice':'0.30','lowPrice':'0.20'},
                    {'symbol':'ALTXUSDT','quoteVolume':'5000000','priceChangePercent':'2','highPrice':'2.04','lowPrice':'1.99'},
                    {'symbol':'DUSTUSDT','quoteVolume':'20000','priceChangePercent':'50','highPrice':'0.3','lowPrice':'0.1'}]
    def get(self,url): return self.info if 'exchangeInfo' in url else self.ticks
    def test_alt_focus_excludes_majors_illiquid_and_prefers_movement(self):
        got=discover('Binance',self.get,120000,10,True,150000000)
        self.assertEqual([z[0] for z in got],['MOONUSDT','ALTXUSDT'])
        self.assertEqual(len(got[0]),3)
    def test_default_compatibility(self):
        got=discover('Binance',self.get,120000,10)
        self.assertEqual(got[0],('BTCUSDT',80000000.))
    def test_focus_all_tuples(self):
        got,err=discover_all(['Binance'],self.get,120000,10,True)
        self.assertFalse(err)
        self.assertEqual(got[0][1],'MOONUSDT')
        self.assertEqual(len(got[0]),4)
    def test_missing_volatility_safe(self):
        score=focus_rank('Gate','ABCUSDT',{},500000)
        self.assertGreater(score,0)
        self.assertIsNone(focus_rank('Gate','BTCUSDT',{},500000))

if __name__=='__main__':unittest.main()
