import unittest,sqlite3,tempfile,os
from unittest.mock import patch
from market_feeds import fetch, normalize
import signal_bot as b

class FeedTests(unittest.TestCase):
    def test_gate_mapping_and_sort(self):
        bars=[['1200','300','102','103','98','100','3','true'],['900','400','100','102','97','99','4','true']]
        z=normalize('Gate',bars,'5m')
        self.assertEqual([r['time'] for r in z],[900,1200]);self.assertEqual(z[-1]['open'],100);self.assertEqual(z[-1]['quote_volume'],300)
    def test_binance_and_mexc(self):
        x=[900000,'99','103','98','101','10',1199999,'1000']
        for name in ('Binance','MEXC'):
            z=normalize(name,[x],'5m')[0]
            self.assertEqual((z['time'],z['close'],z['quote_volume']),(900,101.,1000.))
    def test_endpoint_mapping(self):
        seen=[]
        def getter(url):
            seen.append(url)
            return [['900','100','100','101','98','99','3','true']] if 'gateio' in url else [[900000,99,101,98,100,20,1199999,2000]]
        for name in ('Binance','MEXC','Gate'):
            fetch(name,'BTCUSDT','1h',getter)
        self.assertIn('interval=60m',seen[1]);self.assertIn('BTC_USDT',seen[2]);self.assertIn('interval=1h',seen[2]);self.assertIn('interval=1h',seen[0])
    def test_bad_feed_rejected(self):
        with self.assertRaises(ValueError):normalize('Gate',[['900','2','110','101','98','100','1']],'5m')
    def test_cross_exchange_cooldown(self):
        with tempfile.TemporaryDirectory() as d:
            database=os.path.join(d,'a.sqlite')
            with patch.object(b,'DB',database),patch.object(b,'ROOT',__import__('pathlib').Path(d)):
                con=b.db()
                cfg=dict(b.DEFAULT,enable_charts=False,enable_x=False,enable_telegram=False,enable_telegram_free=False,enable_telegram_vip=False)
                t=b.now();detail={'side':'LONG','origin_ts':t//300*300-300,'entry':100.,'strength':65.,'reason':'test'}
                self.assertTrue(b.new_signal(con,'BTCUSDT',detail,cfg,exchange='Binance'))
                self.assertFalse(b.new_signal(con,'BTCUSDT',detail,cfg,exchange='Gate'))
                self.assertEqual(con.execute('SELECT exchange FROM signals').fetchone()[0],'Binance')
                con.close()
if __name__=='__main__':unittest.main()
