"""Confirmed USDT-TRC20 subscription payments; no wallet private key required."""
import hashlib
import json
import os
import re
import time
import urllib.request
from decimal import Decimal, InvalidOperation

TRON_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
USDT_CONTRACT = 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'
TRANSFER_TOPIC = 'ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'


def _b58decode(value):
    number = 0
    for char in value:
        if char not in TRON_ALPHABET:
            raise ValueError('Invalid TRON address character')
        number = number * 58 + TRON_ALPHABET.index(char)
    raw = number.to_bytes((number.bit_length() + 7) // 8, 'big')
    return b'\0' * (len(value) - len(value.lstrip('1'))) + raw


def tron_hex(address):
    raw = _b58decode(address)
    if len(raw) != 25:
        raise ValueError('Invalid TRON address length')
    payload, checksum = raw[:-4], raw[-4:]
    expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    if checksum != expected or payload[0] != 0x41:
        raise ValueError('Invalid TRON mainnet address')
    return payload.hex()


def price_atomic(price):
    try:
        amount = Decimal(str(price))
    except InvalidOperation as exc:
        raise ValueError('Invalid subscription price') from exc
    atomic = amount * 1_000_000
    if amount <= 0 or atomic != atomic.to_integral_value():
        raise ValueError('USDT price must have at most 6 decimals')
    return int(atomic)


def ensure_tables(con):
    con.executescript('''
    CREATE TABLE IF NOT EXISTS payment_orders (
      id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,username TEXT NOT NULL DEFAULT '',
      sender_address TEXT NOT NULL,recipient_address TEXT NOT NULL,expected_atomic INTEGER NOT NULL,
      created_at INTEGER NOT NULL,expires_at INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'pending',txid TEXT);
    CREATE INDEX IF NOT EXISTS payment_order_user_status ON payment_orders(user_id,status,created_at);
    CREATE TABLE IF NOT EXISTS subscription_payments (
      txid TEXT PRIMARY KEY,order_id INTEGER NOT NULL UNIQUE,user_id INTEGER NOT NULL,
      sender_address TEXT NOT NULL,recipient_address TEXT NOT NULL,amount_atomic INTEGER NOT NULL,
      token_contract TEXT NOT NULL,block_timestamp INTEGER NOT NULL,confirmed_at INTEGER NOT NULL);
    ''')
    con.commit()


def create_order(con, user_id, username, sender_address, cfg, clock=None):
    ensure_tables(con)
    tron_hex(sender_address)
    recipient = cfg['trc20_recipient_address']
    tron_hex(recipient)
    stamp = int(time.time() if clock is None else clock)
    ttl = max(5, int(cfg.get('payment_order_expiry_minutes', 120))) * 60
    con.execute("UPDATE payment_orders SET status='expired' WHERE user_id=? AND status='pending'", (user_id,))
    cur = con.execute('''INSERT INTO payment_orders
      (user_id,username,sender_address,recipient_address,expected_atomic,created_at,expires_at)
      VALUES(?,?,?,?,?,?,?)''',
      (user_id, username or '', sender_address, recipient,
       price_atomic(cfg['subscription_price_usdt']), stamp, stamp + ttl))
    con.commit()
    return con.execute('SELECT * FROM payment_orders WHERE id=?', (cur.lastrowid,)).fetchone()


def _post_json(url, body, api_key='', opener=None):
    opener = opener or urllib.request.urlopen
    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    if api_key:
        headers['TRON-PRO-API-KEY'] = api_key
    request = urllib.request.Request(url, data=json.dumps(body).encode(), headers=headers, method='POST')
    with opener(request, timeout=20) as response:
        return json.load(response)


def fetch_confirmed_tx(txid, opener=None):
    if not re.fullmatch(r'[0-9a-fA-F]{64}', txid or ''):
        raise ValueError('TXID must be 64 hexadecimal characters')
    url = 'https://api.trongrid.io/walletsolidity/gettransactioninfobyid'
    return _post_json(url, {'value': txid.lower()}, os.getenv('TRONGRID_API_KEY', ''), opener)


def verify_transfer(txid, sender_address, recipient_address, expected_atomic, fetcher=None):
    info = (fetcher or fetch_confirmed_tx)(txid)
    if not info or str(info.get('id', '')).lower() != txid.lower() or not info.get('blockNumber') or not info.get('blockTimeStamp'):
        raise ValueError('Transaction is not confirmed on TRON mainnet')
    if info.get('receipt', {}).get('result') not in (None, 'SUCCESS') or info.get('result') not in (None, 'SUCCESS'):
        raise ValueError('Transaction execution was not successful')
    contract = tron_hex(USDT_CONTRACT).lower()
    sender = tron_hex(sender_address).lower()
    recipient = tron_hex(recipient_address).lower()
    matches = []
    for log in info.get('log', []):
        log_contract = str(log.get('address', '')).lower().removeprefix('0x')
        if len(log_contract) == 40:
            log_contract = '41' + log_contract
        topics = [str(x).lower().removeprefix('0x') for x in log.get('topics', [])]
        if log_contract != contract or len(topics) < 3 or topics[0] != TRANSFER_TOPIC:
            continue
        from_hex = '41' + topics[1][-40:]
        to_hex = '41' + topics[2][-40:]
        if from_hex != sender or to_hex != recipient:
            continue
        try:
            amount = int(str(log.get('data', '0')).removeprefix('0x'), 16)
        except ValueError:
            continue
        matches.append(amount)
    if len(matches) != 1:
        raise ValueError('Expected one matching USDT Transfer event')
    if matches[0] != int(expected_atomic):
        raise ValueError('Transfer amount does not match the order')
    return {'txid': txid.lower(), 'amount_atomic': matches[0],
            'token_contract': USDT_CONTRACT,
            'block_timestamp': int(info.get('blockTimeStamp', 0)) // 1000}


def claim_order(con, user_id, txid, cfg, fetcher=None, clock=None):
    ensure_tables(con)
    stamp = int(time.time() if clock is None else clock)
    order = con.execute("SELECT * FROM payment_orders WHERE user_id=? AND status='pending' ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()
    if not order:
        raise ValueError('No pending payment order; use /abonelik first')
    if order['expires_at'] < stamp:
        con.execute("UPDATE payment_orders SET status='expired' WHERE id=?", (order['id'],));con.commit()
        raise ValueError('Payment order expired; create a new order')
    proof = verify_transfer(txid, order['sender_address'], order['recipient_address'],
                            order['expected_atomic'], fetcher)
    if proof['block_timestamp'] < order['created_at'] - 60:
        raise ValueError('Transfer predates this payment order')
    try:
        con.execute('BEGIN IMMEDIATE')
        if con.execute('SELECT 1 FROM subscription_payments WHERE txid=?', (proof['txid'],)).fetchone():
            raise ValueError('This transaction was already claimed')
        current = con.execute('SELECT expires_at FROM members WHERE user_id=?', (user_id,)).fetchone()
        base = max(stamp, int(current['expires_at'])) if current else stamp
        expires = base + max(1, int(cfg.get('subscription_days', 30))) * 86400
        con.execute('''INSERT INTO subscription_payments
          (txid,order_id,user_id,sender_address,recipient_address,amount_atomic,token_contract,block_timestamp,confirmed_at)
          VALUES(?,?,?,?,?,?,?,?,?)''',
          (proof['txid'], order['id'], user_id, order['sender_address'], order['recipient_address'],
           proof['amount_atomic'], proof['token_contract'], proof['block_timestamp'], stamp))
        con.execute("UPDATE payment_orders SET status='paid',txid=? WHERE id=?", (proof['txid'], order['id']))
        con.execute('''INSERT INTO members(user_id,username,expires_at,status,updated_at,invite_link,last_error)
          VALUES(?,?,?,?,?,NULL,NULL) ON CONFLICT(user_id) DO UPDATE SET
          username=excluded.username,expires_at=excluded.expires_at,status='active',updated_at=excluded.updated_at,
          invite_link=NULL,last_error=NULL''',
          (user_id, order['username'], expires, 'active', stamp))
        con.execute('INSERT INTO sales_events(user_id,event,created_at,note) VALUES(?,?,?,?)',
                    (user_id, 'trc20_payment_confirmed', stamp, proof['txid']))
        con.commit()
    except Exception:
        con.rollback()
        raise
    return expires
