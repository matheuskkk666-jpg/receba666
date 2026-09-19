import json, unittest
from pathlib import Path
from tools.stream_spans import validate_spans
ROOT=Path(__file__).resolve().parents[1]
class RealPrologueSpanTests(unittest.TestCase):
 def test_maps_and_alignment_schema(self):
  maps={lang:json.loads((ROOT/f'pipeline/arc01/prologue/spans.{lang}.json').read_text(encoding='utf8')) for lang in ('pt_BR','en')}
  alignment=json.loads((ROOT/'pipeline/arc01/prologue/alignment.json').read_text(encoding='utf8'))
  for lang,data in maps.items():
   self.assertEqual(data['spans'][0]['start'],0); self.assertEqual(data['spans'][-1]['end'],data['stream_length'])
   self.assertEqual(len({s['id'] for s in data['spans']}),len(data['spans']))
  refs={lang:[s for unit in alignment['units'] for s in unit[lang]] for lang in maps}
  for lang,data in maps.items(): self.assertEqual(refs[lang],[s['id'] for s in data['spans']])
  self.assertEqual(len({u['narrative_id'] for u in alignment['units']}),len(alignment['units']))
if __name__=='__main__': unittest.main()
