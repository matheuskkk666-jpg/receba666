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

 def test_canonical_boundaries_follow_shared_semantic_checkpoints(self):
  pt=json.loads((ROOT/'pipeline/arc01/prologue/spans.pt_BR.json').read_text(encoding='utf8'))
  en=json.loads((ROOT/'pipeline/arc01/prologue/spans.en.json').read_text(encoding='utf8'))
  self.assertEqual([(s['start'],s['end']) for s in pt['spans']], [
   (0,636),(636,1314),(1314,2103),(2103,2758),(2758,3118),(3118,3422)
  ])
  self.assertEqual([(s['start'],s['end']) for s in en['spans']], [
   (0,522),(522,965),(965,1443),(1443,1772),(1772,2065),(2065,2265)
  ])
  alignment=json.loads((ROOT/'pipeline/arc01/prologue/alignment.json').read_text(encoding='utf8'))
  self.assertEqual([u['narrative_id'] for u in alignment['units']], [f'arc01.prologue.{i:04d}' for i in range(1,7)])
  self.assertTrue(all(len(u['pt_BR'])==len(u['en'])==1 for u in alignment['units']))
  self.assertTrue(all(u.get('scene_hint')=='arc01.prologue.runtime_placeholder' for u in alignment['units']))

 def test_reimported_translations_preserve_all_span_characters(self):
  for language in ('pt_BR','en'):
   span_map=json.loads((ROOT/f'pipeline/arc01/prologue/spans.{language}.json').read_text(encoding='utf8'))
   rows=json.loads((ROOT/f'game/generated/arc01/prologue/translations/{language}/arc01.prologue.json').read_text(encoding='utf8'))
   self.assertEqual(sum(len(row['text']) for row in rows),span_map['stream_length'])
   self.assertEqual([source_id for row in rows for source_id in row['source_blocks']],[span['id'] for span in span_map['spans']])
if __name__=='__main__': unittest.main()
