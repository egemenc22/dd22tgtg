import sqlite3
import unittest
from unittest.mock import patch

import payment_service as p
import signal_bot as b

RECIPIENT='TR6c5N8GwTF1FKtQsGVTSPdQfh9m74NXYB'
SENDER='TJRabPrwbZy45sbavfcjinPJC18kjpRTv8'
CFG={**b.DEFAULT,'enable_trc20_payments':True,'subscription_price_usdt':'9.90',
     'subscription_days':30,'trc20_recipient_address':RECIPIENT}

def fixture(txid='a'*64,amount=9_900_000,timestamp=1005):
    sender=p.tron_hex(SENDER)[2:];recipient=p.tron_hex(RECIPIENT)[2:]
    contract=p.tron_hex(p.USDT_CONTRACT)[2:]
    return {'id':txid,'blockNumber':123,'blockTimeStamp':timestamp*1000,'receipt':{'result':'SUCCESS'},
      'log':[{'address':contract,'topics':[p.TRANSFER_TOPIC,'0'*24+sender,'0'*24+recipient],
              'data':format(amount,'064x')}]}

class PaymentTests(unittest.TestCase):
 def setUp(self):
  self.c=sqlite3.connect(':memory:');self.c.row_factory=sqlite3.Row;self.c.executescript(b.SCHEMA);p.ensure_tables(self.c)
 def tearDown(self):self.c.close()
 def test_address_and_price(self):
  self.assertTrue(p.tron_hex(RECIPIENT).startswith('41'));self.assertEqual(p.price_atomic('9.90'),9900000)
 def test_confirm_and_no_replay(self):
  p.create_order(self.c,7,'alice',SENDER,CFG,clock=1000)
  expiry=p.claim_order(self.c,7,'a'*64,CFG,fetcher=lambda _:fixture(),clock=1010)
  self.assertEqual(expiry,1010+30*86400)
  self.assertEqual(self.c.execute('select status from members where user_id=7').fetchone()[0],'active')
  p.create_order(self.c,8,'bob',SENDER,CFG,clock=1020)
  with self.assertRaisesRegex(ValueError,'already claimed'):
   p.claim_order(self.c,8,'a'*64,CFG,fetcher=lambda _:fixture(),clock=1030)
 def test_reject_wrong_amount_sender_and_old_payment(self):
  p.create_order(self.c,7,'alice',SENDER,CFG,clock=1000)
  with self.assertRaisesRegex(ValueError,'amount'):
   p.claim_order(self.c,7,'a'*64,CFG,fetcher=lambda _:fixture(amount=1),clock=1010)
  with self.assertRaisesRegex(ValueError,'Transfer event'):
   p.claim_order(self.c,7,'a'*64,CFG,fetcher=lambda _:fixture()|{'log':[]},clock=1010)
  with self.assertRaisesRegex(ValueError,'predates'):
   p.claim_order(self.c,7,'a'*64,CFG,fetcher=lambda _:fixture(timestamp=900),clock=1010)
 def test_private_command_creates_order(self):
  event={'message':{'chat':{'id':7,'type':'private'},'from':{'id':7,'username':'a'},'text':'/subscribe '+SENDER}}
  with patch.object(b,'telegram_send',return_value='1') as send:
   self.assertEqual(b.process_payment_message(self.c,event,CFG,'token',clock=1000),1)
   self.assertIn('9.90 USDT',send.call_args.args[2])
   self.assertIn('Order #',send.call_args.args[2])
 def test_membership_bot_once_polls_once(self):
  with patch.object(b,'DB',':memory:'),patch.object(b,'poll_vip_join_requests',return_value=0) as poll:
   b.run_membership_bot(CFG,once=True)
   poll.assert_called_once()

if __name__=='__main__':unittest.main()
