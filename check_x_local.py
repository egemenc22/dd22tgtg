"""Read-only connection check for optional X Post Management local server."""
import json
from pathlib import Path
from urllib.request import urlopen
from x_local_bridge import validated_origin, BridgeError

def check(cfg, opener=urlopen):
    origin=validated_origin(cfg.get('xpm_origin','http://127.0.0.1:5000'))
    try:
        with opener(origin+'/api/health', timeout=5) as response: data=json.load(response)
    except Exception as exc:
        return {'ok':False,'error':str(exc)[:160], 'origin':origin}
    return {'ok':data.get('status')=='ok','origin':origin,'server_version':data.get('version'),'autopublish':bool(cfg.get('xpm_auto_publish',False))}
if __name__=='__main__':
    cfg=json.loads((Path(__file__).parent/'config.json').read_text(encoding='utf-8'))
    result=check(cfg)
    print(json.dumps(result,indent=2))
    if not result['ok']:raise SystemExit(1)
