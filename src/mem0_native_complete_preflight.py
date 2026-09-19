"""Repeat the fictional smoke check with required hybrid/NLP dependencies present."""
import json
import os
from pathlib import Path
import importlib.metadata
import mem0_native_preflight as base


def main():
    base.RUN = base.ROOT/'data/mem0-native-complete-preflight-v1'
    base.OUT = base.ROOT/'results/mem0-native-complete-preflight.json'
    os.environ.update(MEM0_TELEMETRY='false', MEM0_DIR=str(base.ROOT/'data/mem0-component-check'),
        FASTEMBED_CACHE_PATH=str(base.ROOT/'models/fastembed-cache'),HF_HUB_OFFLINE='1')
    manifest=json.loads((base.ROOT/'references/bm25-manifest.json').read_text())
    path=base.ROOT/'models/fastembed-cache/models--Qdrant--bm25/snapshots'/manifest['revision']
    for f in manifest['files']:
        assert base.digest(path/f['name']) == f['sha256']
    from mem0.utils.spacy_models import get_nlp_full, get_nlp_lemma
    from fastembed import SparseTextEmbedding
    assert get_nlp_full() is not None, 'Missing full NLP pipeline'
    assert get_nlp_lemma() is not None, 'Missing lemmatizer'
    assert len(list(SparseTextEmbedding(model_name='Qdrant/bm25').embed(['blue rain jackets']))[0].indices)>0
    base.main()
    from mem0 import Memory
    result=json.loads(base.OUT.read_text())
    config=result['config']
    config['llm']['config'].pop('response_callback')
    config['llm']['config']['api_key']='local-placeholder'
    memory=Memory.from_config(config)
    hits=memory.vector_store.keyword_search('blue rain jacket',filters={'user_id':'fictional-preflight'})
    result['component_checks']={'nlp_full':get_nlp_full() is not None,'lemmatizer':get_nlp_lemma() is not None,
                               'keyword_hits':len(hits) if hits is not None else None,
                               'bm25_initialized':memory.vector_store._bm25_encoder not in (False,None)}
    assert hits, 'Native keyword search did not retrieve stored text'
    result['component_versions']={n:importlib.metadata.version(n) for n in ['spacy','en-core-web-sm']}
    result['wrapper_sha256']=base.digest(Path(__file__))
    memory.close();memory.vector_store.client.close()
    base.OUT.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['component_checks']))

if __name__=='__main__':
    main()
