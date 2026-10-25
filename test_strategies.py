import unittest
from strategies import evaluate
import signal_bot as b

class StrategyTests(unittest.TestCase):
    def rows(self,n=100,step=300):
        start=((b.now()-step*3)//step)*step-n*step
        return [{'time':start+i*step,'close_time':start+(i+1)*step-1,'open':100.,'close':100.,'high':100.2,'low':99.8,'quote_volume':300000.,'volume':3000.} for i in range(n)]
    def test_flat_market_no_strategy(self):
        self.assertEqual(evaluate(self.rows()),[])
    def test_breakout_detected(self):
        r=self.rows();r[-1].update(close=103.,high=103.2)
        found=evaluate(r,'5m')
        self.assertIn('DONCHIAN_20',[x['strategy'] for x in found])
    def test_no_noncontiguous_bars(self):
        r=self.rows();r[-3]['time']+=1;r[-3]['close_time']+=1
        self.assertEqual(evaluate(r),[])
    def test_selected_strategy_filter(self):
        r=self.rows();r[-1].update(close=103.,high=103.2)
        self.assertEqual(evaluate(r,'5m',{'RSI_BB_REVERSION'}),[])
    def test_timeframe_interval(self):
        r=self.rows(step=900);r[-1].update(close=103.,high=103.2)
        self.assertTrue(evaluate(r,'15m'))

if __name__=='__main__':unittest.main()
