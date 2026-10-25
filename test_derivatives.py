import unittest
from derivatives import contract_symbols, discover_contracts
class DerivativesTest(unittest.TestCase):
    def test_binance(self):
        raw={'symbols':[{'status':'TRADING','contractType':'PERPETUAL','quoteAsset':'USDT','symbol':'FOOUSDT'}, {'status':'BREAK','contractType':'PERPETUAL','quoteAsset':'USDT','symbol':'BADUSDT'}]}
        self.assertEqual(contract_symbols('Binance',lambda _:raw),{'FOOUSDT'})
    def test_mexc(self):
        raw={'success':True,'data':[{'symbol':'FOO_USDT','state':0},{'symbol':'BAD_USDT','state':1}]}
        self.assertEqual(contract_symbols('MEXC',lambda _:raw),{'FOOUSDT'})
    def test_gate(self):
        raw=[{'name':'FOO_USDT','quanto_multiplier':'1','in_delisting':False}, {'name':'BAD_USDT','quanto_multiplier':'1','in_delisting':True}]
        self.assertEqual(contract_symbols('Gate',lambda _:raw),{'FOOUSDT'})
    def test_failure_closed(self):
        good={'symbols':[{'status':'TRADING','contractType':'PERPETUAL','quoteAsset':'USDT','symbol':'FOOUSDT'}]}
        def fetch(url):
            if 'binance' in url:return good
            raise RuntimeError('offline')
        results,errs=discover_contracts(['Binance','Gate'],fetch)
        self.assertEqual(results['Binance'],{'FOOUSDT'})
        self.assertEqual(results['Gate'],set());self.assertIn('Gate',errs)
if __name__=='__main__':unittest.main()
