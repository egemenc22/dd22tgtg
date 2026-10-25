import json, unittest
from unittest.mock import Mock
from product_filters import allowed_spot_instrument
from market_discovery import discover_all
from gate_live_radar import GateLiveRadar

class V350Tests(unittest.TestCase):
    def test_equity_block(self):
        for base in ['SNXXB','MRNA','AXTI','AAOIB','SOXSB','NVDA','TSLAX']:
            self.assertFalse(allowed_spot_instrument(base),base)
    def test_metadata(self):
        self.assertFalse(allowed_spot_instrument('RANDOM',{'name':'Tokenized Stock'}))
        self.assertTrue(allowed_spot_instrument('SHIB',{'name':'Shiba Inu'}))
    def test_gate_normalization(self):
        x=GateLiveRadar({},Mock(),Mock(),Mock())
        x.configure([('Gate','PEPEUSDT',1000,2),('Binance','SOLUSDT',1000,2)])
        self.assertEqual(x.symbols,('PEPEUSDT',))
    def test_gate_message(self):
        x=GateLiveRadar({'live_min_elapsed_seconds':15,'live_min_move_pct':.65,'live_min_volume_ratio':3.5,'live_min_quote_volume':12000},Mock(),Mock(),Mock())
        x.configure([('Gate','PEPEUSDT',1000,2)])
        x.baselines['PEPEUSDT']=[1000.0]*20
        from unittest.mock import patch
        now=2000000000
        msg={'channel':'spot.candlesticks','event':'update','time_ms':now*1000+30000,'result':{'n':'1m_PEPE_USDT','t':str(now),'o':'0.01','c':'0.0102','a':'15000','w':False}}
        x._message(None,json.dumps(msg))
        self.assertEqual(x.events.qsize(),1)
    def test_exchange_balance(self):
        data={
        'Binance':[{'symbol':'AAAUSDT','quoteVolume':'1200000'}],
        'MEXC':[{'symbol':'BBBUSDT','quoteVolume':'1200000'}],
        'Gate':[{'currency_pair':'CCC_USDT','quote_volume':'1200000'}]}
        infos={'Binance':{'symbols':[{'symbol':'AAAUSDT','baseAsset':'AAA','quoteAsset':'USDT','status':'TRADING'}]},'MEXC':{'symbols':[{'symbol':'BBBUSDT','baseAsset':'BBB','quoteAsset':'USDT','status':'TRADING'}]},'Gate':[{'id':'CCC_USDT','base':'CCC','quote':'USDT','trade_status':'tradable'}]}
        def get(url):
            for ex,key in [('Binance','binance'),('MEXC','mexc'),('Gate','gateio')]:
                if key in url:return data[ex] if ('ticker' in url) else infos[ex]
            raise Exception(url)
        out,err=discover_all(['Binance','MEXC','Gate'],get,1000,5)
        self.assertFalse(err)
        self.assertEqual([r[0] for r in out],['Binance','MEXC','Gate'])

if __name__=='__main__':unittest.main()
