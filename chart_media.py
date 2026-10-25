"""Local chart generation and image transport. matplotlib needed for rendering."""
import json, os, secrets, urllib.parse, urllib.request, time
from pathlib import Path


def draw_chart(rows, signal, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    if len(rows)<12: raise ValueError('At least 12 genuine OHLC candles required')
    rows=[r for r in rows if int(r['time'])<=int(signal['origin_ts'])][-75:]
    if len(rows)<12 or int(rows[-1]['time'])!=int(signal['origin_ts']):
        raise ValueError('Signal origin candle not present; cannot render truthful chart')
    fig,ax=plt.subplots(figsize=(12,6.75),dpi=130)
    fig.patch.set_facecolor('#0b1220');ax.set_facecolor('#0b1220')
    for i,r in enumerate(rows):
        up=r['close']>=r['open'];color='#31d0aa' if up else '#ff6b80'
        ax.plot((i,i),(r['low'],r['high']),color=color,lw=1.1)
        ax.add_patch(Rectangle((i-.33,min(r['open'],r['close'])),.66,max(abs(r['close']-r['open']),1e-10),color=color))
    color='#31d0aa' if signal['side']=='LONG' else '#ff6b80'
    for title,k,col in [('ENTRY','entry','#91b8ff'),('TARGET','target','#31d0aa'),('STOP','stop','#ff6b80')]:
        y=float(signal[k]);ax.axhline(y,c=col,lw=1.2,ls='--',alpha=.9);ax.text(len(rows)-1,y,f'  {title} {y:.8g}',va='center',color=col,fontsize=9,bbox=dict(facecolor='#0b1220',edgecolor='none',alpha=.9))
    ax.set_xlim(-1,len(rows)+15)
    ax.set_title(f"{signal['symbol']}  |  {signal['side']}  |  {signal.get('exchange','Binance').upper()}  |  SIGNAL #{signal['id']}",color='white',loc='left',fontsize=16,pad=20,fontweight='bold')
    ax.set_xlabel('Completed candles through the signal · NOT future price action',color='#9daaba',fontsize=9)
    ax.tick_params(colors='#aebccc');ax.grid(alpha=.11,color='#c4d4e6');ax.spines[:].set_visible(False)
    fig.text(.02,.02,'DETECTION SNAPSHOT  •  No future candles  •  Levels are references, not guaranteed outcomes',color='#aebccc',fontsize=9)
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(output,facecolor=fig.get_facecolor(),bbox_inches='tight')
    plt.close(fig)
    return output


def multipart(fields, filename, data, file_field="media"):
    boundary='----SignalBot'+secrets.token_hex(12)
    chunks=[]
    for key,value in fields.items():
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\nContent-Type: image/png\r\n\r\n'.encode()+data+b'\r\n')
    chunks.append(f'--{boundary}--\r\n'.encode())
    return b''.join(chunks),f'multipart/form-data; boundary={boundary}'


def telegram_photo(token,chat_id,caption,path):
    payload,ct=multipart({'chat_id':chat_id,'caption':caption[:1024]},'signal.png',Path(path).read_bytes(),file_field='photo')
    req=urllib.request.Request(f'https://api.telegram.org/bot{token}/sendPhoto',data=payload,headers={'Content-Type':ct})
    with urllib.request.urlopen(req,timeout=30) as r:res=json.load(r)
    if not res.get('ok'):raise RuntimeError('Telegram did not accept photo')
    return str(res['result']['message_id'])


def x_photo(text, path, oauth_header):
    """X API v2 image upload workflow: init, append, finalize, create tweet."""
    png=Path(path).read_bytes()
    def call(url,body=None,content_type='application/json',method='POST'):
        req=urllib.request.Request(url,data=body,method=method,headers={'Authorization':oauth_header(method,url),'Content-Type':content_type})
        with urllib.request.urlopen(req,timeout=40) as r:
            payload=r.read()
            return json.loads(payload) if payload else {}
    root='https://api.x.com/2/media/upload'
    obj=call(root+'/initialize',json.dumps({'media_type':'image/png','total_bytes':len(png),'media_category':'tweet_image'}).encode())
    mid=str(obj['data']['id'])
    for i,offset in enumerate(range(0,len(png),4*1024*1024)):
        part,ct=multipart({'segment_index':str(i)},'signal.png',png[offset:offset+4*1024*1024])
        call(f'{root}/{mid}/append',part,ct)
    fin=call(f'{root}/{mid}/finalize')
    info=fin.get('data',{}).get('processing_info')
    for _ in range(10):
        if not info or info.get('state')=='succeeded':break
        if info.get('state')=='failed':raise RuntimeError('X image processing failed')
        time.sleep(min(3,max(1,int(info.get('check_after_secs',1)))))
        status_url=root+'?'+urllib.parse.urlencode({'command':'STATUS','media_id':mid})
        info=call(status_url,None,method='GET').get('data',{}).get('processing_info')
    else:raise RuntimeError('X image processing timed out')
    result=call('https://api.x.com/2/tweets',json.dumps({'text':text[:280],'media':{'media_ids':[mid]}},ensure_ascii=False).encode())
    return str(result['data']['id'])
