"""Second writer and cross-reader gate, reusing frozen Qwen records byte-for-byte."""
import argparse
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path

from amazon_language_feasibility import digest
from language_model_pins import ROOT,SPECS,verify_model
from language_extension_inputs import writer_history,reader_query
from language_cross_runtime import Runtime,count_request,MAX_TOTAL_TOKENS,TIMEOUT
from run_language_resource_preflight import (save,select_cases,bm25_selection,SUMMARY_SYSTEM,
    summary_text,reader_valid,response_summary,choice,native_export_complete)

RUN=ROOT/'data/language-cross-preflight-v1'
OLD=ROOT/'data/language-extension-resource-v1'
OUT=ROOT/'results/language-cross-preflight.json'
ARMS=['no_history','full_history','native_qwen','summary_qwen','native_phi','summary_phi','bm25_history']
OLD_ARM={'no_history':'no_history','full_history':'full_history','native_memory':'native_qwen',
         'task_summary':'summary_qwen','bm25_history':'bm25_history'}


def inputs_and_manifest():
    preparation=json.loads((ROOT/'results/language-extension-input-preparation.json').read_text())
    original=json.loads((ROOT/'results/language-extension-resource-preflight.json').read_text())
    if not original['complete'] or not original['prototype_pass'] or original['observed_llm_calls']!=21:
        raise ValueError('Original preflight did not pass')
    for record in (preparation,original):
        for name,expected in record['dependencies'].items():
            if digest(ROOT/name)!=expected:raise ValueError('Frozen dependency changed: '+name)
    path=ROOT/'data/language-extension-v1/development-inputs.json'
    if digest(path)!=preparation['input_file_hashes'][str(path.relative_to(ROOT))]:
        raise ValueError('Development inputs changed')
    inputs=json.loads(path.read_text())
    if set(inputs)!=set(preparation['groups']['development']):raise ValueError('Development split mismatch')
    cases=select_cases(preparation)
    if cases!=original['cases']:raise ValueError('Selected cases changed')
    reused={}
    for row in original['writers']:
        for name,key in [('native-writer.json','native_sha256'),('summary-writer.json','summary_sha256')]:
            reused[str((OLD/row['case_id']/name).relative_to(ROOT))]=row[key]
    for row in original['readers']:
        reused[str((OLD/row['case_id']/(row['condition']+'.json')).relative_to(ROOT))]=row['raw_sha256']
    for name,expected in reused.items():
        if digest(ROOT/name)!=expected:raise ValueError('Reused output changed: '+name)
    old_audit=sorted((OLD/'request-audit').glob('attempt-*.json'))
    if len(old_audit)!=21:raise ValueError('Original audit record count changed')
    for audit in old_audit:
        raw=json.loads(audit.read_text())
        if raw['status']!='completed' or not raw['transport_attempted']:
            raise ValueError('Original request was not completed')
        reused[str(audit.relative_to(ROOT))]=digest(audit)
    dependencies=['src/run_language_cross_preflight.py','src/language_cross_runtime.py',
        'src/language_model_pins.py','src/count_cross_request_tokens.py',
        'src/run_language_resource_preflight.py','src/language_extension_inputs.py',
        'src/coat_memory_reader.py','src/mem0_native_preflight.py',
        'docs/language-cross-preflight-protocol.md','results/language-extension-input-preparation.json',
        'results/language-extension-resource-preflight.json','results/mem0-native-complete-preflight.json',
        'references/local-model-manifest.json','references/phi-model-manifest.json',
        'references/mem0-native-complete-environment.txt','references/confirmation-server-environment.txt']
    versions={p:version(p) for p in ('mem0ai','openai','fastembed','qdrant-client','onnxruntime')}
    tokenizers={model:count_request(model,[{'role':'user','content':'Tokenizer compatibility fixture.'}])
                for model in SPECS}
    manifest={'scope':'three development cases; second writer and crossed readers; no accuracy analysis',
        'cases':cases,'arms':ARMS,'old_arm_mapping':OLD_ARM,'reused_raw_hashes':reused,
        'prepared_development_sha256':digest(path),
        'dependencies':{name:digest(ROOT/name) for name in dependencies},
        'new_request_caps':{'phi':27,'qwen':6},'expected_combined_calls':54,
        'temperature':0,'top_p':1,'writer_output_tokens':2048,'reader_output_tokens':256,
        'max_total_tokens':MAX_TOTAL_TOKENS,'timeout_seconds':TIMEOUT,'max_retries':0,
        'native_environment':versions,'tokenizer_environments':tokenizers}
    path=RUN/'manifest.json'
    if path.exists():
        if json.loads(path.read_text())!=manifest:raise ValueError('Cross-preflight manifest changed')
    else:save(path,manifest)
    return inputs,manifest


def load_writers(case,model):
    directory=OLD/case if model=='qwen' else RUN/case/'phi'
    return (json.loads((directory/'native-writer.json').read_text()),
            json.loads((directory/'summary-writer.json').read_text()))


def handoff(manifest,create=False):
    files={}
    for case in manifest['cases']:
        for name in ('native-writer.json','summary-writer.json'):
            path=RUN/case/'phi'/name
            files[str(path.relative_to(ROOT))]=digest(path)
    value={'manifest_sha256':digest(RUN/'manifest.json'),'phi_writer_files':files}
    path=RUN/'phi-handoff.json'
    if path.exists():
        if json.loads(path.read_text())!=value:raise ValueError('Phi handoff changed')
    elif create:save(path,value)
    else:raise ValueError('Phi stage handoff is absent')
    return value


def native_valid(record):
    add,stored=record.get('add',{}),record.get('stored',{})
    complete=native_export_complete(add,stored)
    traces=record.get('traces',[])
    return bool(record.get('status')=='completed' and complete and stored.get('results') and traces and
        all(choice(t).get('finish_reason')=='stop' for t in traces) and not record.get('cleanup_error') and
        {r['id']:r.get('memory') for r in add['results']}=={r['id']:r.get('memory') for r in stored['results']})


def diagnostic_evidence(arm,writers):
    for model,(native,summary) in writers.items():
        if arm=='native_'+model:return not native_valid(native)
        if arm=='summary_'+model:return summary_text(summary) is None
    return False


def native_text(record):
    if not native_valid(record):
        return 'No stored memories are available.'
    texts=sorted(r['memory'] for r in record['stored']['results'])
    return '\n'.join(texts) or 'No stored memories are available.'


def evidence_views(instance,writers):
    evidence={'no_history':'No earlier personal history is available.',
              'full_history':writer_history(instance)}
    indices=bm25_selection(instance)
    evidence['bm25_history']=writer_history({'history':[instance['history'][i] for i in indices]})
    for model,(native,summary) in writers.items():
        evidence['native_'+model]=native_text(native)
        evidence['summary_'+model]=summary_text(summary) or 'No usable profile was generated.'
    if set(evidence)!=set(ARMS):raise ValueError('Incomplete crossed evidence')
    return evidence


def writer_summary(case,model,native,summary):
    profile=summary_text(summary)
    traces=[response_summary({'status':'completed','seconds':None,'response':t['response']})
            for t in native.get('traces',[])]
    exported=native.get('stored',{}).get('results',[])
    complete=native_export_complete(native.get('add',{}),native.get('stored',{}))
    texts_match=complete and ({r['id']:r.get('memory') for r in native.get('add',{}).get('results',[])}==
                             {r['id']:r.get('memory') for r in exported})
    valid=bool(native.get('status')=='completed' and complete and texts_match and exported and traces and
               all(t['finish_reason']=='stop' for t in traces) and profile is not None and
               not native.get('cleanup_error'))
    return {'case_id':case,'writer':model,'native_status':native.get('status'),
        'export_complete':complete,'insert_export_text_matches':texts_match,
        'native_memories':len(exported),'native_generations':traces,'native_seconds':native['seconds'],
        'summary':response_summary(summary),'summary_words':len(profile.split()) if profile else None,
        'summary_valid':profile is not None,'valid':valid}


def response_identity(raw):
    response=raw.get('response')
    if not isinstance(response,dict) or not isinstance(response.get('id'),str) or not response['id']:
        return None
    serialized=json.dumps(response,sort_keys=True,separators=(',',':')).encode()
    return {'id':response['id'],'sha256':hashlib.sha256(serialized).hexdigest(),'model':response.get('model')}


def response_bijection(persisted,audited,expected):
    if len(persisted)!=expected or len(audited)!=expected or any(r is None for r in persisted+audited):
        return False
    ids=[r['id'] for r in persisted];other=[r['id'] for r in audited]
    if len(set(ids))!=expected or len(set(other))!=expected:return False
    return sorted(persisted,key=lambda r:r['id'])==sorted(audited,key=lambda r:r['id'])


def audit_rows(model):
    rows=[]
    for path in sorted((RUN/'request-audit'/model).glob('attempt-*.json')):
        raw=json.loads(path.read_text());response=raw.get('response') or {};usage=response.get('usage') or {}
        expected=raw.get('tokenizer',{}).get('prompt_tokens')
        rows.append({'reader_or_writer_model':model,'file':str(path.relative_to(ROOT)),
            'sha256':digest(path),'status':raw['status'],'transport_attempted':raw['transport_attempted'],
            'finish_reason':choice(raw).get('finish_reason'),'seconds':raw.get('seconds'),
            'prompt_tokens':expected,'reported_prompt_tokens':usage.get('prompt_tokens'),
            'completion_tokens':usage.get('completion_tokens'),'response_identity':response_identity(raw),
            'prompt_count_matches':expected is not None and expected==usage.get('prompt_tokens'),
            'total_token_allowance':raw.get('total_token_allowance')})
    return rows


def validate_handoff_state(manifest):
    exists=(RUN/'phi-handoff.json').exists()
    qwen_started=any((RUN/'request-audit'/'qwen').glob('attempt-*.json')) or any(
        (RUN/case/'qwen'/(arm+'.json')).exists()
        for case in manifest['cases'] for arm in ('native_phi','summary_phi'))
    if qwen_started and not exists:raise ValueError('Phi handoff is required for Qwen cross records')
    if exists:handoff(manifest)


def refresh_report(manifest):
    validate_handoff_state(manifest)
    report={**manifest,'writers':[],'readers':[],'new_request_audit':[]}
    complete=True
    persisted_responses=[]
    for case in manifest['cases']:
        available_writers={}
        for model in SPECS:
            try:native,summary=load_writers(case,model)
            except FileNotFoundError:
                complete=False;continue
            persisted_responses.extend(response_identity(t) for t in native.get('traces',[]))
            persisted_responses.append(response_identity(summary))
            available_writers[model]=(native,summary)
            row=writer_summary(case,model,native,summary)
            directory=OLD/case if model=='qwen' else RUN/case/'phi'
            row['native_sha256']=digest(directory/'native-writer.json')
            row['summary_sha256']=digest(directory/'summary-writer.json')
            report['writers'].append(row)
        for model in SPECS:
            for arm in ARMS:
                old_condition=next((k for k,v in OLD_ARM.items() if v==arm),None)
                path=OLD/case/(old_condition+'.json') if model=='qwen' and old_condition else RUN/case/model/(arm+'.json')
                if not path.exists():complete=False;continue
                raw=json.loads(path.read_text())
                persisted_responses.append(response_identity(raw))
                report['readers'].append({'case_id':case,'reader':model,'arm':arm,
                    **response_summary(raw),'valid':reader_valid(raw),'raw_sha256':digest(path),
                    'reused':model=='qwen' and old_condition is not None,
                    'diagnostic_fallback_evidence':diagnostic_evidence(arm,available_writers)})
    report['new_request_audit']=audit_rows('phi')+audit_rows('qwen')
    original_audit=[response_identity(json.loads(p.read_text())) for p in sorted((OLD/'request-audit').glob('attempt-*.json'))]
    audited_responses=original_audit+[r['response_identity'] for r in report['new_request_audit']]
    report['response_bijection']=response_bijection(persisted_responses,audited_responses,54)
    report['planned_new_requests']=33
    report['planned_combined_requests']=54
    report['invalid_writer_cells']=sum(not w['valid'] for w in report['writers'])
    report['invalid_reader_cells']=sum(not r['valid'] for r in report['readers'])
    report['new_transport_attempts']=sum(r['transport_attempted'] for r in report['new_request_audit'])
    report['combined_transport_attempts']=21+report['new_transport_attempts']
    report['new_completed_requests']=sum(r['status']=='completed' for r in report['new_request_audit'])
    report['new_pretransport_rejections']=sum(not r['transport_attempted'] for r in report['new_request_audit'])
    report['new_failed_transport_requests']=sum(r['transport_attempted'] and r['status']!='completed' for r in report['new_request_audit'])
    report['complete']=complete
    report['prototype_pass']=bool(complete and len(report['writers'])==6 and len(report['readers'])==42 and
        all(w['valid'] and len(w['native_generations'])==1 for w in report['writers']) and
        all(r['valid'] and not r['diagnostic_fallback_evidence'] for r in report['readers']) and
        report['response_bijection'] and
        len(audit_rows('phi'))==27 and len(audit_rows('qwen'))==6 and
        all(r['status']=='completed' and r['prompt_count_matches'] and r['finish_reason']=='stop'
            for r in report['new_request_audit']))
    save(OUT,report)
    return report


def run_stage(stage,inputs,manifest):
    if stage=='qwen_cross':handoff(manifest)
    model='phi' if stage=='phi' else 'qwen'
    runtime=Runtime(model,RUN,manifest['new_request_caps'][model])
    client=runtime.client()
    try:
        for position,case in enumerate(manifest['cases']):
            instance=inputs[case];directory=RUN/case/model;directory.mkdir(parents=True,exist_ok=True)
            if stage=='phi':
                history=writer_history(instance)
                runtime.native_write(case,history,directory)
                runtime.request(client,directory/'summary-writer.json',
                    [{'role':'system','content':SUMMARY_SYSTEM},{'role':'user','content':history}],2048)
            writers={m:load_writers(case,m) for m in SPECS}
            evidence=evidence_views(instance,writers)
            order=ARMS[position:]+ARMS[:position] if stage=='phi' else ['native_phi','summary_phi']
            for arm in order:
                runtime.request(client,directory/(arm+'.json'),reader_query(instance,evidence[arm]),256)
                refresh_report(manifest)
            print(f'{stage}: {position+1}/3 cases complete',flush=True)
    finally:client.close()
    if stage=='phi':handoff(manifest,create=True)
    return refresh_report(manifest)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['phi','qwen_cross','report'],required=True)
    args=parser.parse_args()
    for key in ('OPENAI_API_KEY','OPENROUTER_API_KEY','OPENAI_BASE_URL'):os.environ.pop(key,None)
    os.environ.update(MEM0_TELEMETRY='false',HF_HUB_OFFLINE='1',MEM0_DIR=str(RUN/'runtime'),
                      FASTEMBED_CACHE_PATH=str(ROOT/'models/fastembed-cache'))
    from mem0_native_preflight import verify_files
    verify_files()
    verify_model('phi')
    inputs,manifest=inputs_and_manifest()
    if args.stage=='report':
        report=refresh_report(manifest)
    else:
        stage_path=RUN/('stage-'+args.stage+'.json')
        if stage_path.exists():
            stage=json.loads(stage_path.read_text())
            if stage['status']!='completed':
                raise RuntimeError('Stage was interrupted or failed; inspect before any continuation')
            report=refresh_report(manifest)
        else:
            save(stage_path,{'stage':args.stage,'status':'started'})
            try:
                report=run_stage(args.stage,inputs,manifest)
            except BaseException as error:
                save(stage_path,{'stage':args.stage,'status':'interrupted' if isinstance(error,KeyboardInterrupt) else 'error',
                                 'error':f'{type(error).__name__}: {error}'})
                try:refresh_report(manifest)
                except Exception as reporting_error:
                    save(RUN/'reporting-error.json',{'error':f'{type(reporting_error).__name__}: {reporting_error}'})
                raise
            else:
                save(stage_path,{'stage':args.stage,'status':'completed'})
    print(json.dumps({k:report[k] for k in ('complete','prototype_pass','combined_transport_attempts')}))


if __name__=='__main__':main()
