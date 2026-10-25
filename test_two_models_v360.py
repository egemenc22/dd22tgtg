import unittest, tempfile, pathlib,sqlite3,json
import two_model_engine
from candle_discovery_v5 import barrier_outcomes
class Tests(unittest.TestCase):
 def test_no_models_no_prediction(self):
  self.assertIsNone(two_model_engine.analyze([]))
 def test_features_shape(self):
  rows=[dict(time=i*300,open=1.,high=1.01,low=.99,close=1.,volume=100.,quote_volume=100.) for i in range(100)]
  try:
   x=two_model_engine.features(rows)
  except ImportError:self.skipTest('ML dependencies not installed')
  self.assertEqual(x.shape,(1,336))
 def test_feature_gap(self):
  rows=[dict(time=i*300,open=1.,high=1.01,low=.99,close=1.,volume=100.) for i in range(100)]
  rows[-2]['time']+=10
  try:self.assertIsNone(two_model_engine.features(rows))
  except ImportError:self.skipTest('ML dependencies not installed')
 def test_scalp_barrier_is_stop_first(self):
  rows=[]
  for i in range(80):rows.append([i*300000,100,100.2,99.8,100,1000])
  rows[50][2]=101.3
  rows[51][3]=99.2
  long,short=barrier_outcomes(rows,[48*300000],24,.012,.007)
  self.assertEqual(long.tolist(),[1.0]);self.assertEqual(short.tolist(),[0.0])
  rows[49][2]=101.3;rows[49][3]=99.2
  long,_=barrier_outcomes(rows,[48*300000],24,.012,.007)
  self.assertEqual(long.tolist(),[0.0])
if __name__=='__main__':unittest.main()
