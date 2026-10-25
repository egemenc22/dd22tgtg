import json, math, unittest
from binance_live_radar import BinanceLiveRadar, detect_partial

class LiveFixTests(unittest.TestCase):
    def setUp(self):
        self.r=BinanceLiveRadar({'live_min_elapsed_seconds':15,'live_min_move_pct':.65,'live_min_volume_ratio':3.5,'live_min_quote_volume':12000},lambda:None,lambda _:None,lambda *_:None)
        self.r.configure([('Binance','BMTUSDT')]);self.r.baselines['BMTUSDT']=[18000]*20
        self.k={'t':600000,'T':659999,'s':'BMTUSDT','o':'1','c':'1.011','q':'40000','x':True}
    def test_candle_self_volume_excluded_from_scoring(self):
        self.r._message(None,json.dumps({'data':{'k':self.k,'E':630000}}))
        self.assertEqual(self.r.events.qsize(),1)
        self.assertEqual(self.r.baselines['BMTUSDT'][-1],40000)
    def test_zero_or_nonfinite_price_rejected(self):
        for val in ('nan','inf','0','-1'):
            self.assertIsNone(detect_partial({**self.k,'c':val},[18000]*20,self.r.cfg,clock_ms=630000))
    def test_connected_status_and_message_count(self):
        self.r._opened(None)
        self.r._message(None,json.dumps({'data':{'k':self.k,'E':630000}}))
        snap=self.r.snapshot()
        self.assertTrue(snap['connected'])
        self.assertEqual(snap['messages'],1)
        self.assertEqual(snap['seeded'],1)
        self.r._closed(None,1000,'normal')
        self.assertFalse(self.r.snapshot()['connected'])
    def test_closed_volume_not_included_twice(self):
        self.r._message(None,json.dumps({'data':{'k':self.k,'E':630000}}))
        self.assertEqual(len(self.r.baselines['BMTUSDT']),20)
    def test_radar_operations_exposes_stream_status(self):
        import signal_bot
        self.assertIn('live_binance',signal_bot.operations_snapshot(signal_bot.db()))

if __name__=='__main__':unittest.main()
