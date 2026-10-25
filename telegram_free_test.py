"""One explicit Telegram FREE smoke test; never prints token."""
import json,os,urllib.request,urllib.parse,sys
from pathlib import Path
from datetime import datetime, timezone
from publishing_setup import verify_telegram
ROOT=Path(__file__).resolve().parent

def main():
    cfg=json.loads((ROOT/'config.json').read_text(encoding='utf8'))
    if not cfg.get('enable_telegram_free') or cfg.get('enable_x') or cfg.get('enable_telegram_vip'):
        print('ERROR: Expected FREE only configuration.');return 2
    result=verify_telegram(cfg)
    if not result.get('ok') or not result.get('channels',{}).get('telegram_free',{}).get('ok'):
        print('ERROR: Telegram FREE bot permissions not verified.',json.dumps(result));return 2
    token=os.getenv('TELEGRAM_BOT_TOKEN',''); chat=os.getenv('TELEGRAM_FREE_CHAT_ID','')
    text='EGONIA | SYSTEM TEST\nTelegram FREE publishing connection verified.\nThis is a test message, not a trading signal.'
    payload=urllib.parse.urlencode({'chat_id':chat,'text':text,'disable_notification':'true'}).encode()
    req=urllib.request.Request(f'https://api.telegram.org/bot{token}/sendMessage',data=payload,method='POST')
    try:
        with urllib.request.urlopen(req,timeout=20) as response: result=json.load(response)
        if not result.get('ok'):raise RuntimeError('Telegram response not ok')
        print('SUCCESS: Test message posted to @EgoniaSignalsFree. Message ID:',result['result'].get('message_id'))
        return 0
    except Exception as exc:
        print('ERROR:',type(exc).__name__,str(exc).replace(token,'[REDACTED]'));return 1
if __name__=='__main__':sys.exit(main())
