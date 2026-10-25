import unittest,sqlite3
from signal_bot import SCHEMA,operations_snapshot,commercial_msg
class TestV22(unittest.TestCase):
 def setUp(self):
  self.db=sqlite3.connect(':memory:');self.db.row_factory=sqlite3.Row;self.db.executescript(SCHEMA)
 def tearDown(self):self.db.close()
 def test_initial_state(self):
  d=operations_snapshot(self.db,clock=1000);self.assertFalse(d['scanner_fresh']);self.assertEqual(d['signals_total'],0);self.assertEqual(d['brand'],'Egonia')
 def test_fresh_cycle(self):
  self.db.execute("INSERT INTO system(key,value) VALUES('last_cycle','950')")
  d=operations_snapshot(self.db,clock=1000);self.assertTrue(d['scanner_fresh']);self.assertEqual(d['last_cycle_age_seconds'],50)
 def test_stale_cycle(self):
  self.db.execute("INSERT INTO system(key,value) VALUES('last_cycle','50')")
  self.assertFalse(operations_snapshot(self.db,clock=1000)['scanner_fresh'])
 def test_delivery_alert(self):
  self.db.execute("INSERT INTO delivery(signal_id,channel,kind,status,last_error) VALUES(1,'x','open','needs_review','timeout')")
  d=operations_snapshot(self.db,clock=1000);self.assertEqual(len(d['attention_required']),1);self.assertEqual(d['deliveries']['needs_review'],1)
 def test_no_sensitive_token_in_status(self):
  d=operations_snapshot(self.db,clock=1000);self.assertNotIn('bot_token',str(d).lower())
if __name__=='__main__':unittest.main()
