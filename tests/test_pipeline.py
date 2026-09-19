import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'tools/content_pipeline.py'; FIX=ROOT/'tests/fixtures/pipeline'
sys.path.insert(0, str(ROOT / 'game/python-packages'))
from foundation.model import load_project, validate as validate_project
class PipelineTests(unittest.TestCase):
 def cli(self,*args,ok=True):
  p=subprocess.run([sys.executable,str(CLI),*map(str,args)],capture_output=True,text=True)
  if ok: self.assertEqual(p.returncode,0,p.stderr+p.stdout)
  return p
 def normalize_all(self, root):
  paths={}
  for lang in ('pt_BR','en'):
   for chapter in ('ch01','ch02'):
    out=root/f'{lang}_{chapter}.json'; self.cli('normalize',FIX/f'{lang[:2]}_{chapter}.txt',out,'--language',lang,'--source-alias',f'fixture-{lang}','--chapter-source-id',f'fixture.{lang[:2]}.{chapter}'); paths[(lang,chapter)]=out
  # combine normalized chapter files for importer
  for lang in ('pt_BR','en'):
   blocks=[]
   for chapter in ('ch01','ch02'): blocks.extend(json.loads(paths[(lang,chapter)].read_text())['blocks'])
   path=root/f'{lang}.json'; path.write_text(json.dumps({'version':1,'blocks':blocks}),encoding='utf-8'); paths[lang]=path
  return paths
 def test_normalize_utf8_and_alignment_import_are_idempotent(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); out=d/'out'; ledger=d/'ledger.json'
   self.cli('validate','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json')
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json','--ledger',ledger,'--output',out)
   first=(out/'narrative/fixture.ch01.json').read_bytes(); self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json','--ledger',ledger,'--output',out)
   self.assertEqual(first,(out/'narrative/fixture.ch01.json').read_bytes())
   en=json.loads((out/'translations/en/fixture.ch01.json').read_text())
   self.assertEqual(en[2]['text'],'I kept the signal.\n\nIn silence.')
 def test_inserting_a_new_unit_preserves_existing_ids(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); out=d/'out'; ledger=d/'ledger.json'; alignment=d/'alignment.json'
   shutil.copy(FIX/'alignment.json',alignment)
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',alignment,'--ledger',ledger,'--output',out)
   original=json.loads(ledger.read_text())['units']['fixture.ch01.u1']['narrative_id']
   for lang in ('pt_BR','en'):
    data=json.loads(p[lang].read_text())
    data['blocks'].append({'source_id':f'fixture.{lang[:2]}.ch01.inserted','chapter_source_id':f'fixture.{lang[:2]}.ch01','kind':'review_required','speaker':None,'text':f'Inserted {lang} text.','source_language':lang,'source_provenance':'fixture','review_notes':'fixture'})
    p[lang].write_text(json.dumps(data),encoding='utf-8')
   data=json.loads(alignment.read_text())
   data['units'].insert(0,{'unit_id':'fixture.ch01.inserted','chapter_id':'fixture.ch01','pt_BR':['fixture.pt.ch01.inserted'],'en':['fixture.en.ch01.inserted'],'kind':'narration','scene_hint':'pipeline_ch01'})
   alignment.write_text(json.dumps(data),encoding='utf-8')
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',alignment,'--ledger',ledger,'--output',out)
   current=json.loads(ledger.read_text())['units']['fixture.ch01.u1']['narrative_id']
   self.assertEqual(original,current)
 def test_dry_run_and_conflict_do_not_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); out=d/'out'; ledger=d/'ledger.json'
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json','--ledger',ledger,'--output',out,'--dry-run')
   self.assertFalse(out.exists()); self.assertFalse(ledger.exists())
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json','--ledger',ledger,'--output',out)
   before=(out/'narrative/fixture.ch01.json').read_bytes()
   data=json.loads(p['pt_BR'].read_text()); data['blocks'][0]['text']='Different original fixture'; p['pt_BR'].write_text(json.dumps(data),encoding='utf-8')
   result=self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json','--ledger',ledger,'--output',out,ok=False)
   self.assertNotEqual(result.returncode,0); self.assertEqual(before,(out/'narrative/fixture.ch01.json').read_bytes())
 def test_unmapped_blocks_fail_coverage(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); data=json.loads(p['en'].read_text()); data['blocks'].append(dict(data['blocks'][0],source_id='extra')) ; p['en'].write_text(json.dumps(data),encoding='utf-8')
   self.assertNotEqual(self.cli('validate','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json',ok=False).returncode,0)
 def test_missing_translation_fails_validation(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); data=json.loads(p['en'].read_text()); data['blocks'].pop(); p['en'].write_text(json.dumps(data),encoding='utf-8')
   self.assertNotEqual(self.cli('validate','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json',ok=False).returncode,0)
 def test_generated_fragments_load_and_validate_with_a_manifest(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); game=d/'game'; shutil.copytree(ROOT/'game',game)
   out=game/'generated'; ledger=d/'ledger.json'
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json','--ledger',ledger,'--output',out)
   manifest_path=game/'content/manifest.json'; manifest=json.loads(manifest_path.read_text())
   generated=[]
   for chapter in ('fixture.ch01','fixture.ch02'):
    rows=json.loads((out/'narrative'/f'{chapter}.json').read_text()); generated.extend(rows)
    manifest['fragments']['narrative'].append(f'generated/narrative/{chapter}.json')
    for lang in ('pt_BR','en'): manifest['fragments']['translations'][lang].append(f'generated/translations/{lang}/{chapter}.json')
   defaults=json.loads((game/'scenes/placeholder/scenes.json').read_text())[0]['defaults']
   scenes=[]
   for chapter in ('fixture.ch01','fixture.ch02'):
    rows=[row for row in generated if row['scene']==f'fixture_scene_{chapter[-1]}']
    scenes.append({'id':f'fixture_scene_{chapter[-1]}','defaults':defaults,'sequence':[{'dialogue':row['id']} for row in rows]})
   (game/'generated/scenes.json').write_text(json.dumps(scenes),encoding='utf-8'); manifest['fragments']['scenes'].append('generated/scenes.json')
   chapters=json.loads((game/'chapters/placeholder/chapters.json').read_text())
   localized={lang:json.loads((game/f'translations/{lang}/chapters.json').read_text()) for lang in ('pt_BR','en')}
   for number, chapter in enumerate(('fixture.ch01','fixture.ch02'),1):
    ids=[row['id'] for row in generated if row['scene']==f'fixture_scene_{number}']
    chapters.append({'id':chapter,'arc_id':'fixture.arc','order':number,'first_narrative_id':ids[0],'narrative_ids':ids,'scenes':[f'fixture_scene_{number}']})
    for lang in ('pt_BR','en'): localized[lang][chapter]={'arc':'Fixture Arc','chapter':f'Chapter {number}','title':f'Fixture {number}','location':'Test Site'}
    manifest['chapter_order'].append(chapter); manifest['narrative_order'].extend(ids)
   (game/'chapters/placeholder/chapters.json').write_text(json.dumps(chapters),encoding='utf-8')
   for lang in ('pt_BR','en'): (game/f'translations/{lang}/chapters.json').write_text(json.dumps(localized[lang]),encoding='utf-8')
   manifest_path.write_text(json.dumps(manifest),encoding='utf-8')
   project=load_project(game)
   self.assertEqual(validate_project(project,game),[])
if __name__=='__main__': unittest.main()
