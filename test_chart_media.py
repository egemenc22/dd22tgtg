import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from chart_media import draw_chart, multipart, x_photo, telegram_photo

class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'chart.png'
        self.rows=[{'time':1800000000+i*300,'open':100+i*.05,'high':101+i*.05,'low':99+i*.05,'close':100+i*.06} for i in range(40)]
        self.signal={'origin_ts':self.rows[-1]['time'],'id':42,'symbol':'SOLUSDT','side':'LONG','entry':102,'target':106,'stop':99}
    def tearDown(self):self.temp.cleanup()
    def test_png_render(self):
        draw_chart(self.rows,self.signal,self.path)
        self.assertTrue(self.path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertGreater(self.path.stat().st_size,15000)
    def test_future_data_never_used(self):
        rows=self.rows+[dict(self.rows[-1],time=self.rows[-1]['time']+300,open=10,high=1000,low=1,close=900)]
        draw_chart(rows,self.signal,self.path)
        self.assertTrue(self.path.exists())
    def test_mismatched_origin_rejected(self):
        self.signal['origin_ts']+=300
        with self.assertRaises(ValueError):draw_chart(self.rows,self.signal,self.path)
    def test_multipart(self):
        body,ct=multipart({'chat_id':'123'},'signal.png',b'xyz')
        self.assertIn(b'xyz',body);self.assertIn(b'name="chat_id"',body);self.assertIn('boundary=',ct)
    def test_x_media_flow_mock(self):
        self.path.write_bytes(b'\x89PNGfake')
        class Response:
            def __init__(self,data):self.data=data
            def __enter__(self):return self
            def __exit__(self,*a):pass
            def read(self):return json.dumps(self.data).encode()
        urls=[]
        def mock_urlopen(req,timeout=0):
            urls.append(req.full_url)
            if req.full_url.endswith('/initialize'):return Response({'data':{'id':'12345'}})
            if req.full_url.endswith('/finalize'):return Response({'data':{'id':'12345'}})
            if req.full_url.endswith('/2/tweets'):
                self.assertIn(b'"media_ids": ["12345"]',req.data)
                return Response({'data':{'id':'67890'}})
            return Response({})
        with patch('urllib.request.urlopen',mock_urlopen):
            self.assertEqual(x_photo('Example',self.path,lambda *args:'OAuth fake'),'67890')
        self.assertEqual(len(urls),4)
    def test_telegram_photo_field_name(self):
        self.path.write_bytes(b'\x89PNGfake')
        class R:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return json.dumps({'ok':True,'result':{'message_id':90}}).encode()
        def mocked(req, timeout=0):
            self.assertIn(b'name="photo"',req.data)
            self.assertNotIn(b'name="media"',req.data)
            self.assertIn(b'name="chat_id"',req.data)
            return R()
        with patch('urllib.request.urlopen',mocked):
            self.assertEqual(telegram_photo('token','@EgoniaSignalsFree','caption',self.path),'90')

    def test_telegram_photo_mock(self):
        self.path.write_bytes(b'\x89PNGfake')
        class R:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def read(self):return json.dumps({'ok':True,'result':{'message_id':88}}).encode()
        with patch('urllib.request.urlopen',return_value=R()):
            self.assertEqual(telegram_photo('token','-123','caption',self.path),'88')
if __name__=='__main__':unittest.main()

