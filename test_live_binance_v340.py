import unittest
import json
from binance_live_radar import detect_partial, BinanceLiveRadar
import radar_engine

class LiveBinanceTests(unittest.TestCase):
    def setUp(self):
        self.k={'t':600000,'o':'1','c':'1.011','q':'40000','x':False}
        self.cfg={'live_min_elapsed_seconds':15,'live_min_move_pct':.65,'live_min_volume_ratio':3.5,'live_min_quote_volume':12000}
    def test_partial_detected_without_close(self):
        e=detect_partial(self.k,[18000]*20,self.cfg,clock_ms=630000)
        self.assertIsNotNone(e)
        self.assertEqual(e['direction'],'UP')
        self.assertTrue(e['partial_candle'])
        self.assertGreaterEqual(e['score'],86)
    def test_no_early_false_alert(self):
        self.assertIsNone(detect_partial(self.k,[18000]*20,self.cfg,clock_ms=607000))
    def test_no_low_volume(self):
        k={**self.k,'q':'500'}
        self.assertIsNone(detect_partial(k,[18000]*20,self.cfg,clock_ms=630000))
    def test_no_low_move(self):
        k={**self.k,'c':'1.001'}
        self.assertIsNone(detect_partial(k,[18000]*20,self.cfg,clock_ms=630000))
    def test_message_accurate_timeframe(self):
        e=detect_partial(self.k,[18000]*20,self.cfg,clock_ms=630000)
        row={'details':json.dumps(e),'direction':'UP','symbol':'TESTUSDT','kind':e['kind'],'exchange':'Binance'}
        self.assertIn('1m Live:',radar_engine.message(row))
        self.assertIn('🟢 BUY',radar_engine.message(row))
    def test_configure_all_binance(self):
        r=BinanceLiveRadar({},lambda:None,lambda url:None,lambda a,b:None)
        count=r.configure([('Binance','AAAUSDT'),('MEXC','CCCUSDT'),('Binance','BBBUSDT')])
        self.assertEqual(count,2)
        self.assertEqual(r.symbols,('AAAUSDT','BBBUSDT'))

if __name__=='__main__': unittest.main()
