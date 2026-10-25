import unittest
from strategies import evaluate

class EarlyMoveTests(unittest.TestCase):
    def rows(self):
        return [dict(time=i*300,close_time=(i+1)*300-1,open=100.,high=101.,low=99.,close=100.,quote_volume=30000.,volume=300.) for i in range(100)]
    def test_momentum_ignition_long(self):
        rows=self.rows()
        for i,(close,high,low) in enumerate([(100.4,102.5,99.4),(101.0,103.0,99.5),(101.7,104.0,99.7)],-3):
            rows[i].update(close=close,high=high,low=low,quote_volume=55000.)
        picks=evaluate(rows,'5m',{'MOMENTUM_IGNITION'})
        self.assertTrue(any(x['strategy']=='MOMENTUM_IGNITION' and x['side']=='LONG' for x in picks))
    def test_volume_acceleration_long(self):
        rows=self.rows()
        # A distinct prior resistance near 102, last close slightly below it.
        for r in rows[-21:-1]:r['high']=102.
        rows[-6]['quote_volume']=14000.
        rows[-5]['quote_volume']=15000.
        rows[-4]['quote_volume']=16000.
        for i,(v,c) in enumerate([(70000,100.15),(85000,100.5),(100000,101.5)],-3):
            rows[i].update(quote_volume=v,close=c,high=102.,low=99.)
        picks=evaluate(rows,'5m',{'VOLUME_ACCELERATION'})
        self.assertTrue(any(x['strategy']=='VOLUME_ACCELERATION' for x in picks))
    def test_no_lookahead_or_gaps(self):
        rows=self.rows();rows[-2]['time']+=1
        self.assertEqual(evaluate(rows,'5m',{'VOLUME_ACCELERATION','MOMENTUM_IGNITION'}),[])
    def test_steady_flat_market(self):
        self.assertEqual(evaluate(self.rows(),'5m',{'VOLUME_ACCELERATION','MOMENTUM_IGNITION'}),[])

if __name__=='__main__':unittest.main()
