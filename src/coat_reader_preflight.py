"""Nine fitting-user generations; completion checks only, no accuracy scoring."""
import json
import os
from pathlib import Path
import time
from coat_memory_reader import ROOT,CONTEXTS,digest,load_data,targets,messages,parse_predictions
from mem0_native_preflight import MODEL


def main():
    out=ROOT/'results/coat-reader-preflight.json'
    rawdir=ROOT/'data/coat-reader-preflight-v1'
    if out.exists() or rawdir.exists():raise RuntimeError('Existing preflight')
    rawdir.mkdir(parents=True)
    from openai import OpenAI
    client=OpenAI(api_key='local-placeholder',base_url='http://127.0.0.1:8317/v1',max_retries=0,timeout=180)
    train,test,features,names=load_data()
    users=json.loads((ROOT/'results/coat-user-split.json').read_text())['users']['fitting'][:3]
    report={'scope':'fitting-user reader preflight; no accuracy scoring','hashes':{p:digest(ROOT/p) for p in
        ['src/coat_reader_preflight.py','src/coat_memory_reader.py','docs/coat-memory-reader-preflight.md']},'records':[]}
    for user in users:
        source=ROOT/f'data/coat-native-resource-preflight-v1/user-{user}.json'
        stored=json.loads(source.read_text())
        contexts={'no_history':'No personal history is available.', 'full_history':stored['input'],
                  'native_memory':'\n'.join(x['memory'] for x in stored['stored']['results'])}
        target_records=targets(train[user],test[user]>0,features,names)
        for context in CONTEXTS:
            prompt=messages(contexts[context],target_records)
            start=time.perf_counter()
            response=client.chat.completions.create(model=str(MODEL),messages=prompt,temperature=0,top_p=1,max_tokens=256)
            seconds=time.perf_counter()-start
            text=response.choices[0].message.content
            parsed=parse_predictions(text,len(target_records))
            raw={'user_row':user,'context':context,'messages':prompt,'response':response.model_dump(mode='json')}
            rawpath=rawdir/f'{user}-{context}.json';rawpath.write_text(json.dumps(raw,indent=2)+'\n')
            row={'user_row':user,'context':context,'target_count':len(target_records),'finish_reason':response.choices[0].finish_reason,
                 'parsed':parsed is not None,'seconds':seconds,'usage':response.usage.model_dump(mode='json'),
                 'raw_sha256':digest(rawpath),'source_sha256':digest(source)}
            report['records'].append(row);out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(row),flush=True)

if __name__=='__main__':main()
