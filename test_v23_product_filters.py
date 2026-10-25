import unittest
from market_discovery import discover
from product_filters import allowed_crypto_base

class ProductFilterTests(unittest.TestCase):
    def test_block_live_false_positives(self):
        for symbol in ['SPCX5S','NEAR5S','SNDK5S','SKHYNIX5S','SOXLB','BTC3L','ETH5S','DOGEUP','SOLBEAR']:
            with self.subTest(symbol=symbol):self.assertFalse(allowed_crypto_base(symbol))
    def test_keep_ordinary_altcoins(self):
        for symbol in ['PEPE','WIF','BONK','BMT','SUI','FLOKI','AAVE','SOL']:
            with self.subTest(symbol=symbol):self.assertTrue(allowed_crypto_base(symbol))
    def test_no_synthetics_across_all_exchange_discovery(self):
        for exchange in ['Binance','MEXC','Gate']:
            bases=['PEPE','SPCX5S','SNDK5S','SOXLB']
            if exchange=='Gate':
                info=[{'id':b+'_USDT','base':b,'quote':'USDT','trade_status':'tradable'} for b in bases]
                ticks=[{'currency_pair':b+'_USDT','quote_volume':'2000000'} for b in bases]
            else:
                info={'symbols':[{'symbol':b+'USDT','baseAsset':b,'quoteAsset':'USDT','status':'TRADING'} for b in bases]}
                ticks=[{'symbol':b+'USDT','quoteVolume':'2000000'} for b in bases]
            def get(url):return info if ('exchangeInfo' in url or 'currency_pairs' in url) else ticks
            self.assertEqual([x[0] for x in discover(exchange,get)],['PEPEUSDT'])

if __name__=='__main__':unittest.main()
