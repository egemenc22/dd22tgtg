import unittest
from product_filters import allowed_spot_instrument, classify_spot_instrument
from market_discovery import discover

class CryptoAssetUniverseTests(unittest.TestCase):
    def test_real_memecoin_and_crypto_tokens_not_removed(self):
        for symbol in ('PEPE','BONK','WIF','FLOKI','SHIB','TURBO','BOME','DOGE','AI','ALT'):
            self.assertTrue(allowed_spot_instrument(symbol, {'description':'Community crypto token on Ethereum'}),symbol)
    def test_traditional_assets_excluded_even_if_spot(self):
        cases=[('FOO',{'description':'Tokenized stock tracking US listed equities'}),('BAR',{'baseAssetName':'Wrapped ETF shares'}),('BAZ',{'assetType':'ETF'}),('QUX',{'description':'Nasdaq 100 index tracker'}),('QUUX',{'description':'Tokenized Treasury bond'}),('NVDA',{}),('AXTI',{})]
        for symbol,metadata in cases:
            self.assertFalse(allowed_spot_instrument(symbol,metadata),(symbol,metadata))
    def test_classification_has_explainable_reason(self):
        ok,reason=classify_spot_instrument('EXAMPLE', {'description':'tokenized equity'})
        self.assertFalse(ok);self.assertEqual(reason,'traditional_finance_description')
        ok,reason=classify_spot_instrument('PEPE', {'description':'meme token'})
        self.assertTrue(ok)
    def test_metadata_gate_all_three_exchanges(self):
        for exchange in ('Binance','MEXC','Gate'):
            if exchange=='Gate':
                info=[{'id':'PEPE_USDT','base':'PEPE','quote':'USDT','trade_status':'tradable'},{'id':'FAKE_USDT','base':'FAKE','quote':'USDT','trade_status':'tradable','description':'Tokenized stock'}]
                ticks=[{'currency_pair':'PEPE_USDT','quote_volume':'75000'},{'currency_pair':'FAKE_USDT','quote_volume':'75000'}]
            else:
                info={'symbols':[{'symbol':'PEPEUSDT','baseAsset':'PEPE','quoteAsset':'USDT','status':'TRADING','isSpotTradingAllowed':True},{'symbol':'FAKEUSDT','baseAsset':'FAKE','quoteAsset':'USDT','status':'TRADING','isSpotTradingAllowed':True,'description':'Tokenized stock'}]}
                ticks=[{'symbol':'PEPEUSDT','quoteVolume':'75000'},{'symbol':'FAKEUSDT','quoteVolume':'75000'}]
            def get(url):return info if ('exchangeInfo' in url or 'currency_pairs' in url) else ticks
            result=discover(exchange,get,15000,500)
            self.assertEqual([x[0] for x in result],['PEPEUSDT'])

if __name__=='__main__': unittest.main()
