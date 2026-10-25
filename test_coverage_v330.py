import sqlite3,unittest
import coverage_monitor

class CoverageTests(unittest.TestCase):
    def test_universe_coverage_and_errors(self):
        c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
        coverage_monitor.ensure_tables(c)
        coverage_monitor.update(c,[{'exchange':'Binance','symbol':'AAAUSDT','candle_close_time':900,'duration_ms':33},{'exchange':'Gate','symbol':'BBBUSDT','error':'timeout'}],timestamp=1000)
        v=coverage_monitor.snapshot(c,[('Binance','AAAUSDT'),('Gate','BBBUSDT'),('MEXC','CCCUSDT')],timestamp=1010)
        self.assertEqual(v['universe'],3);self.assertEqual(v['scanned_last_5m'],2)
        self.assertEqual(v['errors_last_5m'],1);self.assertEqual(v['coverage_5m_pct'],66.7)
        self.assertEqual(v['p95_candle_age_s'],110)
    def test_stale_excluded(self):
        c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
        coverage_monitor.ensure_tables(c)
        coverage_monitor.update(c,[{'exchange':'Binance','symbol':'AAAUSDT'}],timestamp=1000)
        self.assertEqual(coverage_monitor.snapshot(c,[('Binance','AAAUSDT')],timestamp=1400)['scanned_last_5m'],0)
if __name__=='__main__':unittest.main()
