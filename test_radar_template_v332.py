import json, unittest
from radar_engine import channel_message,message

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
    def test_free_channel_vip_call_to_action(self):
        cfg={'subscription_price_usdt':'9.90','subscription_days':30,'telegram_sales_bot_username':'EgoniaSignalsBot'}
        text=channel_message(self.make(),'telegram_free',cfg)
        self.assertIn('9.90 USDT / 30 days',text)
        self.assertIn('https://t.me/EgoniaSignalsBot?start=vip',text)
        self.assertNotIn('Unlock EGONIA VIP',channel_message(self.make(),'telegram_vip',cfg))

if __name__=='__main__':unittest.main()
