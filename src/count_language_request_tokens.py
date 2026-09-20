"""Count an exact local chat request in the model-serving tokenizer environment."""
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / 'models/qwen3-4b-instruct-2507-4bit'


def main():
    from transformers import AutoTokenizer
    request = json.load(sys.stdin)
    if set(request) != {'messages'}:
        raise ValueError('Only plain chat messages are supported by this budget counter')
    manifest = json.loads((ROOT/'references/local-model-manifest.json').read_text())
    names = {r['name']:r['sha256'] for r in manifest['files']
             if Path(r['name']).suffix in ('.json','.jinja') or r['name'] in ('merges.txt','vocab.txt')}
    if not names:
        raise ValueError('Empty tokenizer pin set')
    for name, expected in names.items():
        if hashlib.sha256((MODEL/name).read_bytes()).hexdigest() != expected:
            raise ValueError('Tokenizer pin mismatch: '+name)
    tokenizer = AutoTokenizer.from_pretrained(MODEL,local_files_only=True,trust_remote_code=False)
    ids = tokenizer.apply_chat_template(request['messages'],tokenize=True,
                                       add_generation_prompt=True,return_dict=False)
    if not isinstance(ids,list) or any(not isinstance(t,int) for t in ids):
        raise ValueError('Expected a flat list of token IDs')
    print(json.dumps({'prompt_tokens':len(ids),'versions':
                     {p:version(p) for p in ('transformers','tokenizers')}}))


if __name__ == '__main__':main()
