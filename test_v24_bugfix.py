import sqlite3, unittest
from signal_bot import SCHEMA, operations_snapshot

class BugfixTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.row_factory=sqlite3.Row
        self.db.executescript(SCHEMA)
    def tearDown(self):self.db.close()
    def test_scanning_is_not_wrongly_not_started(self):
        self.db.execute("INSERT INTO system VALUES('cycle_started','1000')")
        o=operations_snapshot(self.db, clock=1060)
        self.assertTrue(o['scanner_running'])
        self.assertTrue(o['scanner_fresh'])
        self.assertIsNone(o['last_cycle_utc'])
    def test_stale_hung_scan(self):
        self.db.execute("INSERT INTO system VALUES('cycle_started','1000')")
        self.assertFalse(operations_snapshot(self.db,clock=3001)['scanner_running'])
    def test_finished_scan_with_errors(self):
        for k,v in [('cycle_started','1000'),('last_cycle','1020'),('last_cycle_scanned','18'),('last_cycle_errors','3')]:
            self.db.execute('INSERT INTO system VALUES(?,?)',(k,v))
        o=operations_snapshot(self.db,clock=1030)
        self.assertEqual((o['last_cycle_scanned'],o['last_cycle_errors']),(18,3))
        self.assertFalse(o['scanner_running'])
if __name__=='__main__':unittest.main()
