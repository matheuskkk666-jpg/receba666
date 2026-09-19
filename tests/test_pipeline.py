import json, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CLI=ROOT/'tools/content_pipeline.py'; FIX=ROOT/'tests/fixtures/pipeline'
sys.path.insert(0, str(ROOT / 'game/python-packages'))
from foundation.model import load_project, validate as validate_project
from tools.content_pipeline import fingerprint
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
   first={path.relative_to(out): path.read_bytes() for path in out.rglob('*.json') if path.name != 'report.json'}; ledger_first=ledger.read_bytes()
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json','--ledger',ledger,'--output',out)
   second={path.relative_to(out): path.read_bytes() for path in out.rglob('*.json') if path.name != 'report.json'}
   self.assertEqual(first,second); self.assertEqual(ledger_first,ledger.read_bytes())
   before={path.relative_to(out): path.read_bytes() for path in out.rglob('*.json')}
   dry_one=self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json','--ledger',ledger,'--output',out,'--dry-run').stdout
   dry_two=self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json','--ledger',ledger,'--output',out,'--dry-run').stdout
   self.assertEqual(dry_one,dry_two); self.assertEqual(before,{path.relative_to(out): path.read_bytes() for path in out.rglob('*.json')})
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
 def test_duplicate_source_ids_are_never_overwritten(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); data=json.loads(p['pt_BR'].read_text()); data['blocks'].append(dict(data['blocks'][0])); p['pt_BR'].write_text(json.dumps(data),encoding='utf-8')
   result=self.cli('validate','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json',ok=False)
   self.assertIn('duplicate source_id: fixture.pt.ch01.b0001',result.stdout)
   result=self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json','--ledger',d/'ledger.json','--output',d/'out',ok=False)
   self.assertIn('duplicate source_id: fixture.pt.ch01.b0001',result.stdout)
 def test_fingerprint_preserves_source_boundaries(self):
  self.assertNotEqual(fingerprint(['ab','c']),fingerprint(['a','bc']))
  self.assertNotEqual(fingerprint(['A','B']),fingerprint(['A\n\nB']))
 def test_explicit_narrative_id_collision_is_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); alignment=json.loads((FIX/'alignment.json').read_text())
   alignment['units'][0]['narrative_id']='fixture.shared'; alignment['units'][1]['narrative_id']='fixture.shared'; path=d/'alignment.json'; path.write_text(json.dumps(alignment),encoding='utf-8')
   result=self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',path,'--ledger',d/'ledger.json','--output',d/'out',ok=False)
   self.assertIn('narrative_id collision: fixture.shared',result.stdout)
 def test_retirement_keeps_id_reserved_and_requires_declaration(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); ledger=d/'ledger.json'; out=d/'out'; alignment=json.loads((FIX/'alignment.json').read_text())
   path=d/'alignment.json'; path.write_text(json.dumps(alignment),encoding='utf-8')
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',path,'--ledger',ledger,'--output',out)
   for language in ('pt_BR','en'):
    data=json.loads(p[language].read_text()); data['blocks']=[item for item in data['blocks'] if item['source_id'] not in {f'fixture.{language[:2]}.ch01.b0001'}]; p[language].write_text(json.dumps(data),encoding='utf-8')
   alignment['units']=alignment['units'][1:]; path.write_text(json.dumps(alignment),encoding='utf-8')
   self.assertNotEqual(self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',path,'--ledger',ledger,'--output',out,ok=False).returncode,0)
   alignment['retired_units']=['fixture.ch01.u1']; path.write_text(json.dumps(alignment),encoding='utf-8')
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',path,'--ledger',ledger,'--output',out)
   saved=json.loads(ledger.read_text()); self.assertEqual(saved['retired_units']['fixture.ch01.u1']['narrative_id'],'pipeline.fixture.ch01.0001')
   self.assertNotIn('pipeline.fixture.ch01.0001',[item['narrative_id'] for item in saved['units'].values()])
   for language in ('pt_BR','en'):
    data=json.loads(p[language].read_text()); data['blocks'].append({'source_id':f'fixture.{language[:2]}.ch01.new','text':'New fixture text'}); p[language].write_text(json.dumps(data),encoding='utf-8')
   alignment['units'].append({'unit_id':'fixture.ch01.new','chapter_id':'fixture.ch01','pt_BR':['fixture.pt.ch01.new'],'en':['fixture.en.ch01.new'],'scene_hint':'fixture_scene_1'})
   path.write_text(json.dumps(alignment),encoding='utf-8')
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',path,'--ledger',ledger,'--output',out)
   self.assertEqual(json.loads(ledger.read_text())['units']['fixture.ch01.new']['narrative_id'],'pipeline.fixture.ch01.0004')
 def test_explicit_id_cannot_collide_with_existing_ledger_unit(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); ledger=d/'ledger.json'; out=d/'out'; alignment=json.loads((FIX/'alignment.json').read_text()); path=d/'alignment.json'; path.write_text(json.dumps(alignment),encoding='utf-8')
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',path,'--ledger',ledger,'--output',out)
   for language in ('pt_BR','en'):
    data=json.loads(p[language].read_text()); data['blocks'].append({'source_id':f'fixture.{language[:2]}.ch02.new','text':'New fixture text'}); p[language].write_text(json.dumps(data),encoding='utf-8')
   alignment['units'].append({'unit_id':'fixture.ch02.new','chapter_id':'fixture.ch02','pt_BR':['fixture.pt.ch02.new'],'en':['fixture.en.ch02.new'],'narrative_id':'pipeline.fixture.ch02.0001','scene_hint':'fixture_scene_2'})
   path.write_text(json.dumps(alignment),encoding='utf-8')
   self.assertIn('narrative_id collision: pipeline.fixture.ch02.0001',self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',path,'--ledger',ledger,'--output',out,ok=False).stdout)
 def test_missing_translation_produces_review_package_not_runtime_content(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); alignment=json.loads((FIX/'alignment.json').read_text()); alignment['units'][2]['en']=[]; path=d/'alignment.json'; path.write_text(json.dumps(alignment),encoding='utf-8')
   out=d/'out'; result=self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',path,'--ledger',d/'ledger.json','--output',out,ok=False)
   self.assertIn('missing translation: fixture.ch01.u3 (en)',result.stdout)
   package=json.loads((out/'content_package.json').read_text()); self.assertFalse(package['runtime_ready']); self.assertIn({'unit_id':'fixture.ch01.u3','language':'en'},package['missing_translations'])
 def test_generated_fragments_load_and_validate_with_a_manifest(self):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d); p=self.normalize_all(d); game=d/'game'; shutil.copytree(ROOT/'game',game)
   out=game/'generated'; ledger=d/'ledger.json'
   self.cli('import','--pt_BR',p['pt_BR'],'--en',p['en'],'--alignment',FIX/'alignment.json','--ledger',ledger,'--output',out)
   package=json.loads((out/'content_package.json').read_text())
   manifest_path=game/'content/manifest.json'; manifest=json.loads(manifest_path.read_text())
   generated=[]
   for fragment in package['fragments']['narrative']:
    generated.extend(json.loads((out/fragment).read_text())); manifest['fragments']['narrative'].append(f'generated/{fragment}')
   for lang in ('pt_BR','en'):
    manifest['fragments']['translations'][lang].extend(f'generated/{fragment}' for fragment in package['fragments']['translations'][lang])
   defaults=json.loads((game/'scenes/placeholder/scenes.json').read_text())[0]['defaults']
   scenes=[]
   for chapter in package['chapters']:
    scene_id=chapter['scene_hints'][0]
    scenes.append({'id':scene_id,'defaults':defaults,'sequence':[{'dialogue':row['id']} for row in generated if row['id'] in chapter['narrative_ids']]})
   (game/'generated/scenes.json').write_text(json.dumps(scenes),encoding='utf-8'); manifest['fragments']['scenes'].append('generated/scenes.json')
   chapters=json.loads((game/'chapters/placeholder/chapters.json').read_text())
   localized={lang:json.loads((game/f'translations/{lang}/chapters.json').read_text()) for lang in ('pt_BR','en')}
   for number, chapter in enumerate(package['chapters'],1):
    chapters.append({'id':chapter['id'],'arc_id':'fixture.arc','order':number,'first_narrative_id':chapter['first_narrative_id'],'narrative_ids':chapter['narrative_ids'],'scenes':chapter['scene_hints']})
    for lang in ('pt_BR','en'): localized[lang][chapter['id']]={'arc':'Fixture Arc','chapter':f'Chapter {number}','title':f'Fixture {number}','location':'Test Site'}
    manifest['chapter_order'].append(chapter['id'])
   manifest['narrative_order'].extend(package['narrative_order'])
   (game/'chapters/placeholder/chapters.json').write_text(json.dumps(chapters),encoding='utf-8')
   for lang in ('pt_BR','en'): (game/f'translations/{lang}/chapters.json').write_text(json.dumps(localized[lang]),encoding='utf-8')
   manifest_path.write_text(json.dumps(manifest),encoding='utf-8')
   project=load_project(game)
   self.assertEqual(validate_project(project,game),[])
if __name__=='__main__': unittest.main()
