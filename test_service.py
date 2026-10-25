import json, sqlite3, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import signal_bot as b
class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.old=b.DB;b.DB=Path(self.t.name)/'db.sqlite';self.con=b.db();self.cfg=dict(b.DEFAULT);self.cfg.update(enable_telegram=True,enable_x=True)
    def tearDown(self):self.con.close();b.DB=self.old;self.t.cleanup()
    def create(self):
        d={'side':'LONG','origin_ts':b.now()-900,'entry':100.,'strength':80.,'reason':'test'}
        return b.new_signal(self.con,'BTCUSDT',d,self.cfg)
    def test_deduplicate(self):
        self.assertTrue(self.create());self.assertFalse(self.create());self.assertEqual(self.con.execute('select count(*) from signals').fetchone()[0],1)
    def test_delivery_identity_and_dryrun(self):
        self.create();b.deliveries(self.con,self.cfg)
        rows=self.con.execute('select status,external_id from delivery').fetchall();self.assertEqual(len(rows),2);self.assertTrue(all(x['status']=='sent' and x['external_id']=='dry-run' for x in rows))
    def test_stop_first(self):
        self.create();s=self.con.execute('select * from signals').fetchone();bar={'time':s['origin_ts']+300,'close_time':s['origin_ts']+599,'open':100,'high':110,'low':90,'close':101}
        b.close_signals(self.con,{'BTCUSDT':[bar]},self.cfg)
        out=self.con.execute('select exit_reason,net_pct from signals').fetchone();self.assertEqual(out['exit_reason'],'STOP');self.assertAlmostEqual(out['net_pct'],-2.9)
    def test_no_signal_flat(self):
        rows=[{'time':b.now()-300*(80-i),'open':100.,'close':100.,'high':101.,'low':99.,'quote_volume':200000.,'close_time':b.now()-300*(80-i)+299} for i in range(80)]
        self.assertIsNone(b.decide(rows,self.cfg))
    def test_missed_credentials_retries(self):
        self.create();self.cfg['dry_run']=False
        with patch.dict('os.environ',{},clear=True):b.deliveries(self.con,self.cfg)
        a=self.con.execute('select attempts,status from delivery').fetchall();self.assertTrue(all(x['status']=='sent' and x['attempts']==1 for x in a)) # publication approval disabled
    def test_live_ambiguous_failure_needs_review(self):
        self.create();self.cfg.update(dry_run=False,allow_unvalidated_publication=True)
        with patch.dict('os.environ',{},clear=True):b.deliveries(self.con,self.cfg)
        a=self.con.execute('select attempts,status from delivery').fetchall()
        self.assertTrue(all(x['status']=='needs_review' and x['attempts']==1 for x in a))
    def test_discontinuous_path_not_counted_as_win(self):
        self.create();s=self.con.execute('select * from signals').fetchone()
        bar={'time':s['origin_ts']+600,'close_time':s['origin_ts']+895,'open':100.,'high':110.,'low':99.,'close':108.}
        b.close_signals(self.con,{'BTCUSDT':[bar]},self.cfg)
        out=self.con.execute('select exit_reason,net_pct from signals').fetchone()
        self.assertEqual(out['exit_reason'],'DATA_INVALID');self.assertIsNone(out['net_pct'])
if __name__=='__main__':unittest.main()
