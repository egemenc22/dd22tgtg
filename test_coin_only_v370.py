import unittest,json
from pathlib import Path
from product_filters import allowed_crypto_base,allowed_spot_instrument
from market_discovery import eligible_base
class CoinOnly(unittest.TestCase):
 def test_block_equity(self):
  for x in ['MRNA','AXTI','AXTIB','SNXXB','NVDA','SPY','QQQ','MSTX','NVDL']:
   self.assertFalse(allowed_crypto_base(x),x)
 def test_block_metadata(self):
  self.assertFalse(allowed_spot_instrument('FOO',{'baseAssetName':'Foo tokenized stock'}))
  self.assertFalse(allowed_spot_instrument('FOO',{'category':'ETF'}))
 def test_allow_memes(self):
  for x in ['PEPE','BONK','WIF','FLOKI','BOME','SHIB','TURBO']:
   self.assertTrue(eligible_base(x),x)
 def test_settings(self):
  x=json.loads(Path('config.json').read_text());self.assertGreaterEqual(x['max_pairs_per_exchange'],400);self.assertEqual(x['radar_mode'],True)
if __name__=='__main__':unittest.main()
