"""Conservative product-type gate: spot crypto assets only, not leveraged equity trackers.

This is a name-based fallback, not an assurance that every unblocked asset is a coin.
"""
import re

# Leveraged token suffixes; permit unrelated coin strings ending with 'L'/'S'.
LEVERAGED = re.compile(r'^(?:[A-Z0-9]+?)(?:[235](?:L|S)|(?:UP|DOWN|BULL|BEAR))$')
# Known equity/ETF synthetic identifiers observed in real scanner log.
BLOCKED_BASES = {
    'SOXLB', 'SPCX5S', 'NEAR5S', 'SNDK5S', 'SKHYNIX5S',
    'SNXXB','MRNA','AXTI','AAOIB','SOXSB', 'NVDA','TSLA','AAPL','MSFT','AMZN','GOOGL','GOOG','META','NFLX',
    'AMD','INTC','PLTR','COIN','MSTR','SPY','QQQ','SOXL','SOXS','SQQQ','TQQQ','ARKK','HOOD','GME','SMCI',
    'TSLAX','NVDAX','AAPLX','MSFTX','AMZNX','GOOGLX','METAX','COINX','MSTRX','SPYX','QQQX','AXTIB','MRNAB','SNXX','SPCX','SOXX','USO','GLD','SLV','DIA','IWM','ARKB','IBIT','FBTC','MSTU','MSTX','NVDL','NVDQ','TSLL','TSLQ','TSLS','AAPU','AMZU','GOOU','METU','AMDL','PLTU',
}
# Name-pattern roots are intentionally narrow so we do not discard all small-cap coins.
EQUITY_SYNTHETIC = re.compile(r'^(?:SKHYNIX|SPCX|SNDK|SOXL|SOXS|SNXX|MRNA|AXTI|AAOI|NVDA|TSLA|AAPL|MSFT|AMZN|GOOGL|META|MSTR|SPY|QQQ|PLTR|COIN)(?:[0-9]*[LSBX]?)$')

def allowed_crypto_base(base):
    base = (base or '').upper().strip()
    if not base or base in BLOCKED_BASES:
        return False
    if LEVERAGED.fullmatch(base) or EQUITY_SYNTHETIC.fullmatch(base):
        return False
    return bool(re.fullmatch(r'[A-Z0-9]{2,24}', base))

# Reject tokenized traditional securities; ordinary on-chain tokens and memecoins are welcome.
# Never discard an asset solely for the word "token" or "tokenized" in its description.
SECURITY_PHRASE = re.compile(r"(?:tokeni[sz]ed|synthetic|wrapped|fractional)\s+(?:public\s+)?(?:stocks?|shares?|equities|equity|etfs?|etns?|securities|bonds?|treasur(?:y|ies)|commodit(?:y|ies))|(?:stocks?|shares?|equities|equity|etfs?|etns?|securities|bonds?|treasur(?:y|ies))\s+(?:tokens?|tracker|tracking|index|backed)|(?:exchange.traded fund|stock.market|share.price|equity.index|stock.index|nasdaq\s*100|s&p\s*500|sp500|dow jones|xstocks)", re.I)
SECURITY_TYPES = {'STOCK','STOCK_TOKEN','TOKENIZED_STOCK','EQUITY','EQUITIES','ETF','ETN','SECURITY','SECURITIES','BOND','TOKENIZED_EQUITY','LEVERAGED_ETF','STOCK_INDEX','INDEX_FUND'}

def classify_spot_instrument(base, metadata=None):
    """Return (allowed, reason) for a spot crypto instrument. Unknown metadata stays unverified.

    The exchange spot designation alone cannot establish whether an asset represents a stock.
    """
    if not allowed_crypto_base(base):
        return False, 'blocked_symbol_or_leveraged_product'
    if not isinstance(metadata,dict):
        return True, 'crypto_candidate_unverified'
    for key in ('assetType','asset_type','type','market_type','productType','instrumentType','category'):
        value=metadata.get(key)
        if isinstance(value,str) and value.strip().upper().replace(' ','_') in SECURITY_TYPES:
            return False,'traditional_finance_asset_type'
    fields=('name','fullName','displayName','description','baseAssetName','symbolName','base_name','tag','tags','assetDescription')
    vals=[]
    for k in fields:
        v=metadata.get(k)
        if isinstance(v,(tuple,list)): vals.extend(str(item) for item in v)
        elif isinstance(v,str): vals.append(v)
    if SECURITY_PHRASE.search(' '.join(vals)):
        return False,'traditional_finance_description'
    # Metadata doesn't conclusively prove the asset is native crypto.
    return True,'crypto_candidate_metadata_checked' if vals else 'crypto_candidate_unverified'

def allowed_spot_instrument(base, metadata=None):
    return classify_spot_instrument(base, metadata)[0]
