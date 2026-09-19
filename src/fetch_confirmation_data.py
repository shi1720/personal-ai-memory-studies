"""Acquire original research archives without changing published splits or locks.

Source terms apply. This downloads only; it does not redistribute data or score
ratings. Existing files must match the recorded SHA-256 and are never replaced.
"""
import hashlib
import json
from pathlib import Path
import urllib.request
ROOT=Path(__file__).resolve().parents[1]


def acquire(url,path,expected):
    if path.exists():
        assert hashlib.sha256(path.read_bytes()).hexdigest()==expected,'Existing archive does not match: '+str(path)
        return 'verified existing'
    path.parent.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(url,timeout=120) as response:content=response.read()
    assert hashlib.sha256(content).hexdigest()==expected,'Downloaded archive does not match published manifest'
    temporary=path.with_suffix('.download');temporary.write_bytes(content);temporary.replace(path)
    return 'downloaded and verified'


def main():
    movie=json.loads((ROOT/'references/movie-data-manifest.json').read_text())
    jobs=[('Coat','https://www.cs.cornell.edu/~schnabts/mnar/coat.zip',ROOT/'data/coat/coat.zip','6073d0b515ed1f6e830e4fead66dc76ad7991a7553eaa58e228b234a9d19daed'),
          ('MovieLens',movie['source'],ROOT/'data/movielens/ml-100k.zip',movie['sha256'])]
    for name,url,path,expected in jobs:print(name+': '+acquire(url,path,expected))


if __name__=='__main__':main()
