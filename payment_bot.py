"""Run the Telegram VIP membership/payment service independently of the scanner."""
import argparse
import json
import logging
from pathlib import Path

import signal_bot

ROOT = Path(__file__).resolve().parent


def configuration():
    path = ROOT / 'config.json'
    saved = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    cfg = {**signal_bot.DEFAULT, **saved}
    cfg.update({
        'enable_trc20_payments': True,
        'enable_vip_member_enforcement': True,
        'vip_join_request_mode': True,
        'subscription_price_usdt': '9.90',
        'subscription_days': 30,
        'payment_order_expiry_minutes': 120,
        'membership_poll_seconds': 3,
        'trc20_recipient_address': 'TR6c5N8GwTF1FKtQsGVTSPdQfh9m74NXYB',
    })
    return cfg


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    cfg=configuration()
    signal_bot.configure_membership_bot(cfg)
    signal_bot.run_membership_bot(cfg, once=args.once)


if __name__ == '__main__':
    main()
