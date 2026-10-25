import os,json,urllib.request,re
from pathlib import Path
p=Path(__file__).parent/'CREDENTIALS.cmd'
token=os.getenv('TELEGRAM_BOT_TOKEN')
if not token:raise SystemExit('Run SETUP_TELEGRAM first (token not loaded)')
print('Telegram: Open @EgoniaSignalsBot, press START, and send /start')
input('Then press ENTER here... ')
url='https://api.telegram.org/bot'+token+'/getUpdates?limit=50'
with urllib.request.urlopen(url,timeout=15) as r:data=json.load(r)
ids=[]
for u in data.get('result',[]):
 m=u.get('message',{})
 if m.get('chat',{}).get('type')=='private' and m.get('from',{}).get('is_bot') is False:
  ids.append((m['chat']['id'],m.get('from',{}).get('username','')))
if not ids:raise SystemExit('No private chat found. Send /start to the bot and try again.')
if len(set(i[0] for i in ids))>1:
 print('Private chats:',ids);raw=input('Your Telegram numeric chat ID: ').strip()
else:raw=str(ids[-1][0]);print('Found private chat:',raw)
if not re.fullmatch(r'\d{4,20}',raw):raise SystemExit('Invalid ID')
contents=p.read_text(encoding='utf-8-sig') if p.exists() else ''
contents=re.sub(r'^.*EGONIA_ADMIN_CHAT_ID.*(?:\n|$)','',contents,flags=re.M)
contents+='\nset "EGONIA_ADMIN_CHAT_ID='+raw+'"\n'
p.write_text(contents,encoding='utf-8')
print('Saved. Bot will send you a private X Tweet button for future FREE alerts.')
