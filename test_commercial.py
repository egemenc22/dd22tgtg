import tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import signal_bot as b

class CommercialTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.patcher=patch.object(b,'DB',Path(self.tmp.name)/'test.sqlite')
        self.patcher.start();self.con=b.db()
        self.cfg={**b.DEFAULT,'enable_telegram_free':True,'enable_telegram_vip':True,'enable_x':True,'free_open_per_day':1,'vip_sales_url':'https://example.com/vip'}
    def tearDown(self):
        self.con.close();self.patcher.stop();self.tmp.cleanup()
    def signal(self,t):
        self.con.execute("INSERT INTO signals(exchange,symbol,side,origin_ts,created_at,entry,target,stop,horizon_minutes,expires_at,status,strength,reason) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",('Binance','BTCUSDT','LONG',t,t,100,105,98,120,t+7200,'ACTIVE',55,'Volume'))
        self.con.commit();return self.con.execute('SELECT last_insert_rowid()').fetchone()[0]
    def test_free_cap_vip_all(self):
        t=b.now();a=self.signal(t);b.queue(self.con,a,self.cfg);v=self.signal(t+300);b.queue(self.con,v,self.cfg)
        counts=dict(self.con.execute("SELECT channel,COUNT(*) FROM delivery WHERE kind='open' GROUP BY channel"))
        self.assertEqual(counts['telegram_free'],1)
        self.assertEqual(counts['telegram_vip'],2)
        self.assertEqual(counts['x'],2)
    def test_sales_free_vs_vip(self):
        id_=self.signal(b.now());s=dict(self.con.execute('SELECT * FROM signals WHERE id=?',(id_,)).fetchone())
        free=b.commercial_msg(s,'open','telegram_free',self.cfg);vip=b.commercial_msg(s,'open','telegram_vip',self.cfg)
        self.assertNotIn('Entry reference:',free)
        self.assertIn('Entry reference:',vip)
        self.assertIn('https://example.com/vip',free)
    def test_membership_manual(self):
        args=SimpleNamespace(members_action='grant',user_id=1234,days=30,username='sample')
        b.members_command(args,self.cfg)
        row=self.con.execute('SELECT * FROM members WHERE user_id=1234').fetchone()
        self.assertEqual(row['status'],'active')
        args.members_action='revoke';b.members_command(args,self.cfg)
        self.assertEqual(self.con.execute('SELECT status FROM members WHERE user_id=1234').fetchone()[0],'revoked')
    def test_dry_run_delivery_for_both_telegram_channels(self):
        id_=self.signal(b.now());b.queue(self.con,id_,self.cfg);b.deliveries(self.con,self.cfg)
        self.assertEqual(self.con.execute("SELECT COUNT(*) FROM delivery WHERE status='sent'").fetchone()[0],3)

if __name__=='__main__':unittest.main()
