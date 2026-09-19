"""Native Mem0 smoke check, using only fictional input and local inference."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / 'data/mem0-native-preflight-v2'
OUT = ROOT / 'results/mem0-native-preflight.json'
MODEL = ROOT / 'models/qwen3-4b-instruct-2507-4bit'
COMMIT = 'a39a802bbc93e85b820078cd3c4dbaf53af25dbe'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_files():
    actual = subprocess.check_output(['git', '-C', str(ROOT/'vendor/mem0-native'), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == COMMIT
    import mem0
    installed = Path(mem0.__file__).parent
    for name in ['memory/main.py', 'configs/prompts.py', 'embeddings/fastembed.py', 'llms/openai.py', 'vector_stores/qdrant.py']:
        assert digest(installed/name) == digest(ROOT/'vendor/mem0-native/mem0'/name), name
    for manifest, modeldir in [('references/local-model-manifest.json',MODEL),
        ('references/bge-small-onnx-manifest.json', ROOT/'models/fastembed-cache/models--qdrant--bge-small-en-v1.5-onnx-q/snapshots/52398278842ec682c6f32300af41344b1c0b0bb2')]:
        for f in json.loads((ROOT/manifest).read_text())['files']:
            assert digest(modeldir/f['name']) == f['sha256'], f['name']


def main():
    if RUN.exists() or OUT.exists():
        raise RuntimeError('Refusing to overwrite an existing preflight')
    for key in ['OPENROUTER_API_KEY', 'OPENAI_API_KEY', 'OPENAI_BASE_URL']:
        os.environ.pop(key, None)
    os.environ.update(MEM0_TELEMETRY='false', MEM0_DIR=str(RUN/'mem0'),
                      FASTEMBED_CACHE_PATH=str(ROOT/'models/fastembed-cache'), HF_HUB_OFFLINE='1')
    RUN.mkdir(parents=True)
    from mem0 import Memory
    verify_files()
    traces = []
    def callback(llm, response, params):
        traces.append({'params': params, 'response': response.model_dump(mode='json')})
    config = {
        'llm': {'provider': 'openai', 'config': {
            'model': str(MODEL), 'api_key': 'local-placeholder',
            'openai_base_url': 'http://127.0.0.1:8317/v1',
            'temperature': 0, 'top_p': 1, 'max_tokens': 2048,
            'is_reasoning_model': False, 'response_callback': callback}},
        'embedder': {'provider': 'fastembed', 'config': {'model': 'BAAI/bge-small-en-v1.5', 'embedding_dims': 384}},
        'vector_store': {'provider':'qdrant', 'config': {'path':str(RUN/'qdrant'), 'collection_name':'preflight', 'embedding_model_dims':384, 'on_disk':True}},
        'history_db_path': str(RUN/'history.db'),
    }
    messages = [{'role':'user','content':'This is a fictional smoke-test profile. I like blue rain jackets. I dislike pink fleece jackets. I prefer waterproof coats. I rated item DEMO-17, a black waterproof coat, 4 out of 5.'}]
    query = 'What coat styles and colors does this user like or dislike, and what rating did they give DEMO-17?'
    report = {'scope':'synthetic implementation preflight, not a benchmark', 'commit':COMMIT, 'messages':messages,'query':query,
              'versions':{name:importlib.metadata.version(name) for name in ['mem0ai','fastembed','qdrant-client','openai','onnxruntime']},
              'source_hashes':{str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),ROOT/'docs/mem0-native-preflight.md']}}
    try:
        start=time.perf_counter()
        memory=Memory.from_config(config)
        report['add']=memory.add(messages,user_id='fictional-preflight')
        report['all_before']=memory.get_all(filters={'user_id':'fictional-preflight'})
        report['search']=memory.search(query,filters={'user_id':'fictional-preflight'})
        report['other_user']=memory.search(query,filters={'user_id':'unused-user'})
        memory.close()
        memory.vector_store.client.close()
        reopened=Memory.from_config(config)
        report['all_reopened']=reopened.get_all(filters={'user_id':'fictional-preflight'})
        reopened.close()
        reopened.vector_store.client.close()
        before={x['id'] for x in report['all_before']['results']}
        after={x['id'] for x in report['all_reopened']['results']}
        report['checks']={'nonempty_store':bool(before),'persistent_ids':before==after,
                          'retrieves_memories':bool(report['search']['results']),
                          'separate_user_empty':not report['other_user']['results']}
        report['seconds']=time.perf_counter()-start
        report['status']='passed' if all(report['checks'].values()) else 'failed'
    except Exception as e:
        report['status']='error'
        report['error']=f'{type(e).__name__}: {e}'
        raise
    finally:
        report['llm_traces']=traces
        cfg=json.loads(json.dumps(config,default=lambda _: '<response logging callback>'))
        cfg['llm']['config'].pop('api_key')
        report['config']=cfg
        OUT.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ['status','checks','seconds'] if k in report}))

if __name__=='__main__':
    main()
