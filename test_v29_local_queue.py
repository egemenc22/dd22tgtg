import io, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import signal_bot as b
from check_x_local import check
from publishing_setup import readiness
class Res:
    def __init__(self, x):self.x=x
    def __enter__(self):return self
    def __exit__(self,*a):pass
    def read(self,*a):return json.dumps(self.x).encode()
class LocalQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.old=b.DB;b.DB=Path(self.tmp.name)/'test.sqlite';self.con=b.db()
        self.cfg=dict(b.DEFAULT);self.cfg.update(enable_x=True,enable_telegram=False,enable_telegram_free=False,enable_telegram_vip=False,dry_run=False,allow_unvalidated_publication=True,x_backend='local_xpm',xpm_auto_publish=False,enable_charts=False)
    def tearDown(self):self.con.close();b.DB=self.old;self.tmp.cleanup()
    def populate(self):
        signal={'side':'LONG','origin_ts':b.now()-900,'entry':100.,'strength':90.,'reason':'test'}
        b.new_signal(self.con,'PEPEUSDT',signal,self.cfg)
    def test_draft_not_sent(self):
        self.populate()
        with patch.object(b,'x_local_submit',return_value='xpm-draft:12'):
            b.deliveries(self.con,self.cfg)
        row=self.con.execute('select status, external_id from delivery where channel="x"').fetchone()
        self.assertEqual((row['status'],row['external_id']),('draft','xpm-draft:12'))
    def test_queued_not_sent(self):
        self.populate();self.cfg['xpm_auto_publish']=True
        with patch.object(b,'x_local_submit',return_value='xpm-queued:13'):b.deliveries(self.con,self.cfg)
        self.assertEqual(self.con.execute('select status from delivery where channel="x"').fetchone()[0],'queued_external')
    def test_local_no_x_keys_required(self):
        self.assertTrue(readiness(self.cfg,{})['x']['ready'])
    def test_health(self):
        res=check(self.cfg,lambda *a,**kw:Res({'status':'ok','version':'1'}))
        self.assertTrue(res['ok'])
    def test_unreachable(self):
        def failed(*a,**k):raise OSError('offline')
        self.assertFalse(check(self.cfg,failed)['ok'])
if __name__=='__main__':unittest.main()
