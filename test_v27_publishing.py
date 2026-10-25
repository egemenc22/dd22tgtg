import unittest
from publishing_setup import readiness,verify_telegram,verify_x

class PublishingChecks(unittest.TestCase):
 def test_no_credentials_no_live(self):
  r=readiness({'dry_run':True,'enable_x':True,'enable_telegram_free':True,'enable_telegram_vip':False}, {})
  self.assertFalse(r['x']['ready']);self.assertFalse(r['telegram_free']['ready']);self.assertFalse(r['live_allowed'])
 def test_configured(self):
  env={'TELEGRAM_BOT_TOKEN':'token','TELEGRAM_FREE_CHAT_ID':'@free',**{k:'x' for k in ('X_API_KEY','X_API_SECRET','X_ACCESS_TOKEN','X_ACCESS_TOKEN_SECRET')}}
  r=readiness({'dry_run':False,'allow_unvalidated_publication':True,'enable_x':True,'enable_telegram_free':True},env)
  self.assertTrue(r['x']['ready']);self.assertTrue(r['telegram_free']['ready']);self.assertTrue(r['live_allowed'])
 def test_tg_admin_can_post(self):
  def fake(method,token,params=None):
   return {'id':77,'username':'egonia_bot'} if method=='getMe' else {'status':'administrator','can_post_messages':True}
  r=verify_telegram({'enable_telegram_vip':True},{'TELEGRAM_BOT_TOKEN':'x','TELEGRAM_VIP_CHAT_ID':'-1002'},fake)
  self.assertTrue(r['ok']);self.assertTrue(r['channels']['telegram_vip']['can_post'])
 def test_tg_member_cannot_post(self):
  def fake(method,token,params=None):
   return {'id':77} if method=='getMe' else {'status':'member'}
  self.assertFalse(verify_telegram({'enable_telegram_free':True},{'TELEGRAM_BOT_TOKEN':'x','TELEGRAM_FREE_CHAT_ID':'-1002'},fake)['ok'])
 def test_x_absent(self):
  self.assertFalse(verify_x({}, {})['ok'])
if __name__=='__main__': unittest.main()
