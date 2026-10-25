import tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import signal_bot as b

class VipJoinTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.p=patch.object(b,'DB',Path(self.temp.name)/'test.db');self.p.start();self.c=b.db()
 def tearDown(self):
  self.c.close();self.p.stop();self.temp.cleanup()
 def test_valid_member_approved_and_other_declined(self):
  self.c.execute('INSERT INTO members(user_id,expires_at,status,updated_at) VALUES(?,?,?,?)',(11,20000,'active',0));self.c.commit()
  req=lambda uid:{'chat_join_request':{'chat':{'id':-123},'from':{'id':uid}}}
  with patch.object(b,'telegram_call',return_value=True) as f:
   self.assertEqual(b.process_vip_join_requests(self.c,[req(11),req(22)],-123,'token',clock=10000),2)
   self.assertEqual([call.args[1] for call in f.call_args_list],['approveChatJoinRequest','declineChatJoinRequest'])
 def test_expired_member_rejected(self):
  self.c.execute('INSERT INTO members(user_id,expires_at,status,updated_at) VALUES(?,?,?,?)',(11,9,'active',0));self.c.commit()
  with patch.object(b,'telegram_call',return_value=True) as f:
   b.process_vip_join_requests(self.c,[{'chat_join_request':{'chat':{'id':-123},'from':{'id':11}}}],-123,'token',clock=10)
   self.assertEqual(f.call_args.args[1],'declineChatJoinRequest')
 def test_unrelated_join_request_ignored(self):
  with patch.object(b,'telegram_call') as f:
   self.assertEqual(b.process_vip_join_requests(self.c,[{'chat_join_request':{'chat':{'id':-222},'from':{'id':11}}}],-123,'token'),0)
   f.assert_not_called()
 def test_no_advance_offset_when_api_fails(self):
  with patch.dict(b.os.environ,{'TELEGRAM_BOT_TOKEN':'t','TELEGRAM_VIP_CHAT_ID':'-123'}):
   with patch.object(b,'telegram_call',side_effect=[ [{'update_id':42,'chat_join_request':{'chat':{'id':-123},'from':{'id':77}}}],Exception('network') ]):
    with self.assertRaises(Exception):b.poll_vip_join_requests(self.c,{**b.DEFAULT,'enable_vip_member_enforcement':True})
    self.assertIsNone(self.c.execute("SELECT value FROM system WHERE key='telegram_update_offset'").fetchone())
if __name__=='__main__':unittest.main()
