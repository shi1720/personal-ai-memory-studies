"""Download a second, pinned model family for development-only controls."""
import hashlib
import json
from pathlib import Path
from huggingface_hub import snapshot_download
ROOT=Path(__file__).resolve().parents[1]
REPO='mlx-community/Mistral-7B-Instruct-v0.3-4bit'
REV='a4b8f870474b0eb527f466a03fbc187830d271f5'
NAMES=['README.md','config.json','model.safetensors','model.safetensors.index.json',
       'special_tokens_map.json','tokenizer.json','tokenizer.model','tokenizer_config.json']

def main():
    directory=ROOT/'models/mistral-7b-instruct-v0.3-4bit'
    snapshot_download(REPO,revision=REV,local_dir=directory,allow_patterns=NAMES,max_workers=2)
    files=[]
    for name in NAMES:
        p=directory/name;h=hashlib.sha256()
        with p.open('rb') as f:
            for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
        files.append({'name':name,'sha256':h.hexdigest(),'bytes':p.stat().st_size})
    manifest={'repository':REPO,'revision':REV,'base_model':'mistralai/Mistral-7B-Instruct-v0.3',
              'license':'Apache-2.0 per community and official base model cards',
              'source':'https://huggingface.co/'+REPO,'quantization':'community MLX 4-bit conversion',
              'trust_remote_code':False,'files':files}
    (ROOT/'references/mistral-model-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Pinned model ready:',directory)
if __name__=='__main__':main()
