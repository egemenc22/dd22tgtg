import json, unittest
from radar_engine import message

class RadarTemplateTest(unittest.TestCase):
    def make(self, direction='UP', kind='BREAKOUT', price=0.02633):
        return {'symbol':'BMTUSDT','exchange':'Binance','kind':kind,'direction':direction,'details':json.dumps({'score':95,'price':price,'move_pct':3.8,'volume_ratio':4.2,'quote_volume':89123,'kinds':[kind]})}
    def test_buy(self):
        msg=message(self.make())
        self.assertIn('⚡ ALTCOIN RADAR\n\n🟢 BUY BMT/USDT',msg)
        self.assertTrue(msg.endswith('BMT/USDT — Binance Breakout'))
        self.assertTrue(msg.startswith('⚡ ALTCOIN RADAR'))
        self.assertIn('#BMT #USDT',msg)
        self.assertNotIn('EGONIA ALERT',msg)
        self.assertIn('BMT/USDT',msg)
        self.assertIn('$0.02633',msg)
        self.assertIn('4.2×',msg)
        self.assertIn('95/100',msg)
        self.assertNotIn('Confidence:',msg)
    def test_sell(self):
        msg=message(self.make('DOWN'))
        self.assertIn('⚡ ALTCOIN RADAR\n\n🔴 SELL BMT/USDT',msg)
        self.assertTrue(msg.endswith('BMT/USDT — Binance Breakout'))
        self.assertNotIn('🟢 BUY',msg)
    def test_microcap_precision(self):
        msg=message(self.make(price=0.00000076))
        self.assertIn('$0.00000076',msg)
    def test_event_name(self):
        self.assertIn('Pump / Dump Reversal',message(self.make(kind='PUMP_DUMP_REVERSAL')))

if __name__=='__main__':unittest.main()
