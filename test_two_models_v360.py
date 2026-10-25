import unittest, tempfile, pathlib,sqlite3,json
import two_model_engine
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
if __name__=='__main__':unittest.main()
