import sqlite3
import unittest
from realtime_radar import detect_early, init_tables, early_message, EarlyRadar
from signal_bot import early_deliveries, operations_snapshot

class EarlyTests(unittest.TestCase):
    def setUp(self):
        self.c=sqlite3.connect(':memory:')
        self.c.row_factory=sqlite3.Row
        init_tables(self.c)
    def tearDown(self):self.c.close()
    def rows(self, lastvol=10000, endclose=100):
        a=[dict(time=i*60,open=100,close=100,quote_volume=1000) for i in range(20)]
        a.append(dict(time=1200,open=100,close=endclose,quote_volume=lastvol))
        return a
    def test_up_spike(self):
        r=detect_early(self.rows(15000,102),{'early_min_minute_quote_volume':10000})
        self.assertEqual(r['side'],'UP');self.assertEqual(r['volume_ratio'],15)
    def test_down_spike(self):
        r=detect_early(self.rows(15000,98),{'early_min_minute_quote_volume':10000})
        self.assertEqual(r['side'],'DOWN')
    def test_no_volume(self): self.assertIsNone(detect_early(self.rows(1500,102),{}))
    def test_no_price_move(self): self.assertIsNone(detect_early(self.rows(15000,100.1),{}))
    def test_min_history(self): self.assertIsNone(detect_early(self.rows()[:10],{}))
    def test_message(self):
        self.c.execute('INSERT INTO early_alerts(symbol,side,price,volume_ratio,move_pct,candle_time,created_at) VALUES(?,?,?,?,?,?,?)',('PEPEUSDT','UP',0.001,5.1,1.2,100,100))
        r=self.c.execute('SELECT * FROM early_alerts').fetchone()
        self.assertIn('5.1x',early_message(r))
        self.assertIn('not a LONG/SHORT',early_message(r))
    def test_dry_run(self):
        self.c.execute('INSERT INTO early_alerts(symbol,side,price,volume_ratio,move_pct,candle_time,created_at) VALUES(?,?,?,?,?,?,?)',('PEPEUSDT','UP',0.001,5.1,1.2,100,100))
        early_deliveries(self.c,{'dry_run':True,'enable_early_alerts':True})
        self.assertEqual(self.c.execute('SELECT status FROM early_alerts').fetchone()[0],'dry_run')
    def test_idempotent(self):
        db=self.c
        class Radar(EarlyRadar):
            pass
        radar=Radar({'early_daily_cap':12},lambda:db,None,None)
        # The database itself enforces unique candle alerts.
        db.execute('INSERT INTO early_alerts(symbol,side,price,volume_ratio,move_pct,candle_time,created_at) VALUES(?,?,?,?,?,?,?)',('PEPEUSDT','UP',0.001,5.1,1.2,100,100))
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute('INSERT INTO early_alerts(symbol,side,price,volume_ratio,move_pct,candle_time,created_at) VALUES(?,?,?,?,?,?,?)',('PEPEUSDT','UP',0.001,5.1,1.2,100,100))
