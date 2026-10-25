import unittest, json, tempfile
from pathlib import Path
from urllib.error import URLError
from x_local_bridge import validated_origin, encode_form, submit, BridgeError
class Resp:
 def __init__(self,d):self.d=d
 def __enter__(self):return self
 def __exit__(self,*args):pass
 def read(self,*args):return json.dumps(self.d).encode()
class Tests(unittest.TestCase):
 def test_restrict_origin(self):
  for x in ['https://localhost:5000','http://evil.com:5000','http://127.0.0.1:5000@evil.com:5000','http://127.0.0.1:5000/other','http://127.0.0.1']:
   with self.assertRaises(BridgeError):validated_origin(x)
 def test_draft(self):
  urls=[]
  def t(req,timeout):urls.append(req.full_url);return Resp({'id':17})
  self.assertEqual(submit('test',transport=t),'xpm-draft:17');self.assertEqual(len(urls),1)
 def test_publish(self):
  urls=[]
  def t(req,timeout):urls.append(req.full_url);return Resp({'id':17} if len(urls)==1 else {'status':'queued'})
  self.assertEqual(submit('test',transport=t,publish=True),'xpm-queued:17');self.assertEqual(len(urls),2)
 def test_unconfirmed(self):
  def t(req,timeout):raise URLError('oops')
  with self.assertRaisesRegex(BridgeError,'uncertain'):submit('test',transport=t)
 def test_png(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'sample.png';p.write_bytes(b'\x89PNGhello');b,h=encode_form('Hello',p)
   self.assertIn(b'sample.png',b);self.assertIn(b'Hello',b)
if __name__=='__main__': unittest.main()
