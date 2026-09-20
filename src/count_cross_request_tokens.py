"""Exact chat-template count for one explicitly pinned local model."""
import argparse
from importlib.metadata import version
import json
import sys
from language_model_pins import SPECS,model_path,verify_model


def main():
    from transformers import AutoTokenizer
    parser=argparse.ArgumentParser();parser.add_argument('--model',choices=sorted(SPECS),required=True)
    args=parser.parse_args()
    request=json.load(sys.stdin)
    if set(request) != {'messages'}:
        raise ValueError('Only plain chat messages are supported')
    revision=verify_model(args.model,tokenizer_only=True)
    tokenizer=AutoTokenizer.from_pretrained(model_path(args.model),local_files_only=True,trust_remote_code=False)
    ids=tokenizer.apply_chat_template(request['messages'],tokenize=True,add_generation_prompt=True,return_dict=False)
    if not isinstance(ids,list) or any(type(t) is not int for t in ids):
        raise ValueError('Expected a flat list of token IDs')
    print(json.dumps({'model':args.model,'revision':revision,'prompt_tokens':len(ids),
                     'python':sys.version,'versions':{p:version(p) for p in ('mlx','mlx-lm','transformers','tokenizers')}}))


if __name__=='__main__':main()
