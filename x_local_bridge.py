"""Optional local bridge to X Post Management (third party, browser-based).
Requires separate installed/running application. No X secrets here.
X may prohibit website automation; use at your own discretion.
"""
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

class BridgeError(RuntimeError): pass

def validated_origin(url):
    u=urlsplit(url)
    if u.scheme!='http' or u.hostname not in ('127.0.0.1','localhost') or u.username or u.password or u.query or u.fragment or u.path not in ('','/'):
        raise BridgeError('X Post Management URL must be loopback HTTP origin, e.g. http://127.0.0.1:5000')
    if u.port is None or not 1<=u.port<=65535:raise BridgeError('Local port required')
    return f'http://127.0.0.1:{u.port}'

def encode_form(message, image=None):
    import uuid
    boundary='egonia_'+uuid.uuid4().hex
    body=bytearray()
    def part(name, data, filename=None, content_type=None):
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"'.encode())
        if filename:body.extend(f'; filename="{filename}"'.encode())
        body.extend(b'\r\n')
        if content_type:body.extend(f'Content-Type: {content_type}\r\n'.encode())
        body.extend(b'\r\n');body.extend(data);body.extend(b'\r\n')
    part('text', message.encode('utf-8'))
    part('status',b'draft')
    if image is not None:
        p=Path(image)
        if p.suffix.lower() not in ('.png','.jpg','.jpeg') or not p.is_file():raise BridgeError('Valid PNG/JPEG chart required')
        if p.stat().st_size>5*1024*1024:raise BridgeError('Chart exceeds 5MB')
        part('image',p.read_bytes(),filename=p.name,content_type=mimetypes.guess_type(p.name)[0] or 'image/png')
    body.extend(f'--{boundary}--\r\n'.encode())
    return bytes(body),f'multipart/form-data; boundary={boundary}'

def submit(message,image=None,origin='http://127.0.0.1:5000',publish=False,transport=None):
    """Create local draft, optionally request publish; return local post ID.
    Caveat: post-now is asynchronous, not a confirmed X tweet. No blind retries.
    """
    base=validated_origin(origin)
    transport=transport or urlopen
    body,typ=encode_form(message,image)
    req=Request(base+'/api/posts',data=body,headers={'Content-Type':typ},method='POST')
    try:
        with transport(req,timeout=12) as r:data=json.load(r)
    except Exception as exc:raise BridgeError('Local draft creation uncertain; inspect XPM drafts before retrying') from exc
    pid=int(data['id'])
    if publish:
        req=Request(base+f'/api/posts/{pid}/post-now',data=b'',method='POST')
        try:
            with transport(req,timeout=12) as r:json.load(r)
        except Exception as exc:raise BridgeError(f'Local draft #{pid} created; publish state uncertain; inspect XPM before retry') from exc
    return f'xpm-draft:{pid}' if not publish else f'xpm-queued:{pid}'
