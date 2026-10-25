"""Local Telegram credential installer. Never send a token to chat or write it to logs."""
from __future__ import annotations
import getpass
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / 'CREDENTIALS.cmd'
BOT_PATTERN = re.compile(r'^\d{5,20}:[A-Za-z0-9_-]{20,}$')

def write_credentials(token: str, target: Path = TARGET) -> None:
    if not BOT_PATTERN.fullmatch(token):
        raise ValueError('BotFather token format invalid. Use the full TOKEN, not the @username.')
    # Token charset deliberately excludes CMD metacharacters and quotes.
    content = ('@echo off\r\n'
               'REM Local bot credentials. Keep private; do not publish this file.\r\n'
               f'set "TELEGRAM_BOT_TOKEN={token}"\r\n'
               'set "TELEGRAM_FREE_CHAT_ID=@EgoniaSignalsFree"\r\n'
               'set "TELEGRAM_VIP_CHAT_ID=-1004409446943"\r\n'
               'set "EGONIA_ADMIN_CHAT_ID=1535322949"\r\n'
               'set "X_API_KEY="\r\nset "X_API_SECRET="\r\n'
               'set "X_ACCESS_TOKEN="\r\nset "X_ACCESS_TOKEN_SECRET="\r\n')
    tmp = target.with_suffix('.tmp')
    tmp.write_bytes(content.encode('ascii'))
    os.replace(tmp, target)

def main():
    print('EGONIA Telegram FREE + VIP setup')
    print('Bot: @EgoniaSignalsBot | FREE: @EgoniaSignalsFree | VIP configured')
    print('Paste full BotFather API token (input hidden).')
    token = getpass.getpass('Telegram bot token: ').strip()
    try:
        write_credentials(token)
    except ValueError as exc:
        print('ERROR:', exc)
        return 1
    print('Saved CREDENTIALS.cmd locally. Token not printed.')
    print('Now run CHECK_REMOTE_CONNECTIONS.bat')
    return 0

if __name__ == '__main__':
    sys.exit(main())
