"""One-time, explicit run amendment. Run from repository root."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path('src').resolve()))
from personamem_reader import conversation_blocks, build_input
from transformers import AutoTokenizer
root=Path('.')
archive=root/'results/amendments/pilot-002-empty-assistant'
old_spec=importlib.util.spec_from_file_location('old_reader',archive/'reader-before.py')
old=importlib.util.module_from_spec(old_spec)
old_spec.loader.exec_module(old)
examples=json.loads((root/'data/personamem-v2/pilot-002-examples.json').read_text())
rows=[json.loads(line) for line in (archive/'predictions-before.jsonl').read_text().splitlines()]
assert len(rows)==87
by_id={r['id']:r for r in rows}
tokenizer=AutoTokenizer.from_pretrained('models/qwen3-4b-instruct-2507-4bit',trust_remote_code=False)
unchanged=[]
repairs=[]
verified=[]
for e in examples:
 history=json.loads((root/'data/personamem-v2'/e['history_file']).read_text())['chat_history']
 blocks=conversation_blocks(history)
 role_only=[i for i,m in enumerate(history) if m=={'role':'assistant'}]
 if role_only:
  assert e['id'] not in by_id
  repairs.append({'id':e['id'],'positions':role_only})
 else:
  assert blocks==old.conversation_blocks(history)
  unchanged.append(e['id'])
 if e['id'] in by_id:
  for name in ['original','changed']:
   inp=build_input(tokenizer,e['query'],e['options'],blocks,e['id'],changed=name=='changed')
   saved=(root/'data/personamem-v2/pilot-002-prompts'/f"{e['id']}-{name}.txt").read_text()
   assert inp['prompt']==saved
   assert inp['prompt_sha256']==by_id[e['id']][name]['prompt_sha256']
   assert len(inp['tokens'])==by_id[e['id']][name]['prompt_tokens']
  verified.append(e['id'])
assert len(unchanged)==127 and repairs==[{'id':'bd0388a8df0c6d11','positions':[72]}]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((archive/'manifest-before.json').read_text())
assert json.loads((root/'results/pilot-002-run-manifest.json').read_text())==manifest
assert sha(root/'results/pilot-002-predictions.jsonl')==sha(archive/'predictions-before.jsonl')
old_sha=manifest['hashes']['src/personamem_reader.py']
assert sha(archive/'reader-before.py')==old_sha
manifest['hashes']['src/personamem_reader.py']=sha(root/'src/personamem_reader.py')
report={'reason':'One role-only assistant record carries no text; skip precisely that schema.',
 'changed_example':repairs,'unchanged_block_sequences':len(unchanged),
 'completed_examples_with_identical_rendered_prompts_and_token_counts':len(verified),
 'predictions_before_sha256':sha(archive/'predictions-before.jsonl'),
 'reader_before_sha256':old_sha,'reader_after_sha256':manifest['hashes']['src/personamem_reader.py'],
 'outcomes_not_used_to_select_repair':True,'all_128_examples_retained':True}
(archive/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
(root/'results/pilot-002-run-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(report,indent=2))
