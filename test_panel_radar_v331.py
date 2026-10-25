import unittest, sqlite3, json
from unittest.mock import patch
import signal_bot,radar_engine

class TestRadarPanel331(unittest.TestCase):
    def test_operations_exposes_delivery_status(self):
        con=sqlite3.connect(':memory:');con.row_factory=sqlite3.Row
        con.executescript(signal_bot.SCHEMA);signal_bot.init_tables(con);radar_engine.ensure_tables(con)
        con.execute('INSERT INTO radar_events(exchange,symbol,origin_ts,kind,direction,score,details,created_at) VALUES(?,?,?,?,?,?,?,?)',('binance','BMTUSDT',123,'BREAKOUT','UP',95,'{}',1234))
        con.execute('INSERT INTO radar_delivery(radar_id,channel,status,created_at) VALUES(?,?,?,?)',(1,'telegram_free','sent',1234))
        ops=signal_bot.operations_snapshot(con,clock=1300)
        self.assertEqual(ops['radar_recent'][0]['telegram_status'],'sent')
        self.assertEqual(ops['radar_recent'][0]['symbol'],'BMTUSDT')
        con.close()

if __name__=='__main__': unittest.main()
