import unittest
from tools.stream_spans import build_stream, stream_fingerprint, validate_spans, virtual_blocks
class StreamSpanTests(unittest.TestCase):
 def test_lossless_coverage_and_virtual_blocks(self):
  stream=build_stream(['Header','Uma fala continua','na linha seguinte.','', 'Fim.'],['Header'])
  spans=[{'id':'fixture.s1','start':0,'end':stream.index(' Fim.')},{'id':'fixture.s2','start':stream.index(' Fim.'),'end':len(stream)}]
  self.assertEqual(validate_spans(stream,stream_fingerprint(stream),spans),[])
  self.assertEqual(''.join(b['text'] for b in virtual_blocks(stream,'fixture','pt_BR',spans)),stream)
 def test_rejects_gaps_overlaps_and_fingerprint_mismatch(self):
  self.assertTrue(validate_spans('abcdef','bad',[{'id':'a','start':0,'end':2},{'id':'b','start':3,'end':6}]))
 def test_rejects_bounds_order_and_duplicate_ids(self):
  stream='ação — válida'
  cases=[[{'id':'a','start':-1,'end':2}],[{'id':'a','start':0,'end':99}],[{'id':'a','start':2,'end':2}],[{'id':'a','start':0,'end':3},{'id':'b','start':2,'end':len(stream)}],[{'id':'a','start':0,'end':3},{'id':'a','start':3,'end':len(stream)}]]
  for spans in cases: self.assertTrue(validate_spans(stream,stream_fingerprint(stream),spans))
 def test_virtual_blocks_are_deterministic_and_unicode_exact(self):
  stream='“Olá” — disse.'; spans=[{'id':'s1','start':0,'end':7},{'id':'s2','start':7,'end':len(stream)}]
  self.assertEqual(virtual_blocks(stream,'alias','pt_BR',spans),virtual_blocks(stream,'alias','pt_BR',spans))
  self.assertEqual(''.join(x['text'] for x in virtual_blocks(stream,'alias','pt_BR',spans)),stream)
if __name__=='__main__': unittest.main()
