"""Egonia publication setup and read-only provider checks. No posting from this module."""
import json, os, urllib.request, urllib.parse, urllib.error

ROUTES = {'x': 'enable_x', 'telegram_free': 'enable_telegram_free', 'telegram_vip': 'enable_telegram_vip'}
TG_ROUTES={'telegram_free':'TELEGRAM_FREE_CHAT_ID','telegram_vip':'TELEGRAM_VIP_CHAT_ID'}
X_KEYS=('X_API_KEY','X_API_SECRET','X_ACCESS_TOKEN','X_ACCESS_TOKEN_SECRET')

def readiness(cfg, env=None):
    env=os.environ if env is None else env
    result={}
    for route,flag in ROUTES.items():
        active=bool(cfg.get(flag,False))
        keys=(() if cfg.get('x_backend')=='local_xpm' else X_KEYS) if route=='x' else ('TELEGRAM_BOT_TOKEN',TG_ROUTES[route])
        missing=[key for key in keys if not env.get(key)]
        result[route]={'enabled':active,'credentials_present':not missing,'missing':missing,'ready':active and not missing}
    result['live_allowed']=bool(not cfg.get('dry_run',True) and cfg.get('allow_unvalidated_publication',False))
    return result

def tg_api(method,token,params=None,opener=None):
    opener=opener or urllib.request.urlopen
    query=urllib.parse.urlencode(params or {})
    url=f'https://api.telegram.org/bot{token}/{method}'+('?' +query if query else '')
    with opener(urllib.request.Request(url,method='GET'),timeout=15) as response:
        data=json.load(response)
    if not data.get('ok'):raise RuntimeError('Telegram API returned not ok')
    return data['result']

def verify_telegram(cfg,env=None,call=None):
    env=os.environ if env is None else env
    call=call or tg_api
    token=env.get('TELEGRAM_BOT_TOKEN','')
    if not token:return {'ok':False,'error':'TELEGRAM_BOT_TOKEN missing'}
    try:
        bot=call('getMe',token)
        botid=bot['id']
        channels={}
        for route,key in TG_ROUTES.items():
            if not cfg.get(ROUTES[route],False):continue
            chat=env.get(key,'')
            if not chat:
                channels[route]={'ok':False,'error':key+' missing'};continue
            member=call('getChatMember',token,{'chat_id':chat,'user_id':botid})
            status=member.get('status')
            can_post=status=='administrator' and member.get('can_post_messages',False) or status=='creator'
            channels[route]={'ok':bool(can_post),'status':status,'can_post':bool(can_post)}
        return {'ok':all(v['ok'] for v in channels.values()),'bot_username':bot.get('username'),'channels':channels}
    except (urllib.error.URLError, ValueError, KeyError, RuntimeError) as exc:
        return {'ok':False,'error':f'{type(exc).__name__}: {exc}'}

def verify_x(cfg,env=None,auth=None,opener=None):
    env=os.environ if env is None else env
    missing=[key for key in X_KEYS if not env.get(key)]
    if missing:return {'ok':False,'missing':missing}
    # The signing function reads os.environ. No secrets returned.
    if auth is None:
        from signal_bot import x_auth_header as auth
    opener=opener or urllib.request.urlopen
    url='https://api.x.com/2/users/me'
    try:
        req=urllib.request.Request(url,headers={'Authorization':auth('GET',url)})
        with opener(req,timeout=15) as response: payload=json.load(response)
        obj=payload['data']
        return {'ok':True,'username':obj.get('username'),'id':obj.get('id')}
    except (urllib.error.URLError,ValueError,KeyError,RuntimeError) as exc:
        return {'ok':False,'error':f'{type(exc).__name__}: {exc}'}
