"""Read-only public active USDT perpetual contract discovery. Fail closed."""

URLS = {
    'Binance': 'https://fapi.binance.com/fapi/v1/exchangeInfo',
    'MEXC': 'https://contract.mexc.com/api/v1/contract/detail',
    'Gate': 'https://api.gateio.ws/api/v4/futures/usdt/contracts',
}

def contract_symbols(exchange, get_json):
    if exchange not in URLS:
        raise ValueError('Unsupported exchange')
    raw = get_json(URLS[exchange])
    found = set()
    if exchange == 'Binance':
        for item in raw['symbols']:
            if (item.get('status') == 'TRADING' and item.get('contractType') == 'PERPETUAL'
                    and item.get('quoteAsset') == 'USDT' and item.get('symbol', '').endswith('USDT')):
                found.add(item['symbol'])
    elif exchange == 'MEXC':
        if not isinstance(raw, dict) or not raw.get('success') or not isinstance(raw.get('data'), list):
            raise ValueError('MEXC contracts response invalid')
        for item in raw['data']:
            symbol = item.get('symbol', '')
            if symbol.endswith('_USDT') and item.get('state') == 0:
                found.add(symbol.replace('_', ''))
    else:
        if not isinstance(raw, list):
            raise ValueError('Gate contracts response invalid')
        for item in raw:
            name = item.get('name', '')
            if name.endswith('_USDT') and not item.get('in_delisting') and not item.get('quanto_multiplier') is None:
                # Trading disabled entries are not eligible when the API provides this field.
                if item.get('trade_status', 'tradable') == 'tradable':
                    found.add(name.replace('_', ''))
    return found

def discover_contracts(exchanges, get_json):
    eligible = {}; errors = {}
    for exchange in exchanges:
        try: eligible[exchange] = contract_symbols(exchange, get_json)
        except Exception as exc:
            eligible[exchange] = set()
            errors[exchange] = str(exc)
    return eligible, errors
