"""Download pinned Phi-4 weights and tokenizer, without remote Python."""
import json
from pathlib import Path
from huggingface_hub import snapshot_download
from run_retention_pilot import sha
ROOT = Path(__file__).resolve().parents[1]
REPO = 'mlx-community/phi-4-4bit'
REV = 'fc0f8f23d369dc29b55cad1d65cb5bf0dcbee910'
NAMES = ['README.md', 'config.json', 'merges.txt', 'model-00001-of-00002.safetensors',
         'model-00002-of-00002.safetensors', 'model.safetensors.index.json',
         'special_tokens_map.json', 'tokenizer.json', 'tokenizer_config.json', 'vocab.json']

def main():
    directory = ROOT / 'models/phi-4-4bit'
    snapshot_download(REPO, revision=REV, local_dir=directory, allow_patterns=NAMES, max_workers=2)
    files = [{'name': name, 'sha256': sha(directory / name), 'bytes': (directory / name).stat().st_size} for name in NAMES]
    manifest = {'repository': REPO, 'revision': REV, 'base_model': 'microsoft/phi-4',
                'license': 'MIT per community and official base model cards',
                'source': 'https://huggingface.co/' + REPO,
                'quantization': 'community MLX 4-bit conversion', 'trust_remote_code': False, 'files': files}
    (ROOT / 'references/phi-model-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Pinned model ready:', directory)
if __name__ == '__main__':
    main()
