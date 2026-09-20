"""Audited local-only inference runtime, isolated from the completed first preflight."""
import json
import subprocess
import time
from pathlib import Path
from language_model_pins import ROOT,model_path
from run_language_resource_preflight import save,native_export_complete

BASE_URL='http://127.0.0.1:8317/v1'
MAX_TOTAL_TOKENS=16384
TIMEOUT=360


def count_request(model,messages):
    process=subprocess.run([str(ROOT/'.venv/bin/python'),str(ROOT/'src/count_cross_request_tokens.py'),
        '--model',model],input=json.dumps({'messages':messages}),text=True,capture_output=True,check=True)
    result=json.loads(process.stdout)
    if result['model'] != model or type(result['prompt_tokens']) is not int or result['prompt_tokens'] < 1:
        raise ValueError('Invalid or wrong-model token count')
    return result


class Runtime:
    def __init__(self,model,run,max_calls,counter=count_request):
        self.model=model
        self.path=str(model_path(model))
        self.run=Path(run)
        self.audit=self.run/'request-audit'/model
        self.audit.mkdir(parents=True,exist_ok=True)
        self.max_calls=max_calls
        self.counter=counter

    def instrument(self,client):
        original=client.chat.completions.create
        def audited_create(**params):
            files=sorted(self.audit.glob('attempt-*.json'))
            if len(files)>=self.max_calls:
                raise RuntimeError('Stage request ceiling reached')
            path=self.audit/f'attempt-{len(files)+1:03d}.json'
            # Exclusive reservation prevents a second process reusing this index.
            with path.open('x') as stream:
                json.dump({'params':params,'status':'checking','transport_attempted':False},stream)
            record={'params':params,'status':'checking','transport_attempted':False}
            started=time.perf_counter()
            try:
                allowed={'model','messages','temperature','top_p','max_tokens','response_format'}
                if set(params)-allowed:
                    raise ValueError('Unsupported request fields')
                if params.get('model')!=self.path or params.get('temperature')!=0 or params.get('top_p')!=1:
                    raise ValueError('Wrong model or decoding settings')
                budget=params.get('max_tokens')
                if type(budget) is not int or budget not in (256,2048):
                    raise ValueError('Unexpected output allowance')
                record['tokenizer']=self.counter(self.model,params['messages'])
                if record['tokenizer'].get('model')!=self.model:
                    raise ValueError('Counter used wrong model')
                record['total_token_allowance']=record['tokenizer']['prompt_tokens']+budget
                if record['total_token_allowance']>MAX_TOTAL_TOKENS:
                    raise ValueError('Complete request exceeds resource allowance')
                record.update(status='started',transport_attempted=True)
                save(path,record)
                response=original(**params)
                record['response']=response.model_dump(mode='json')
                if record['response'].get('model')!=self.path:
                    raise ValueError('Server returned the wrong model identity')
                record['status']='completed'
                return response
            except Exception as error:
                record.update(status='error',error=f'{type(error).__name__}: {error}')
                raise
            finally:
                record['seconds']=time.perf_counter()-started
                save(path,record)
        client.chat.completions.create=audited_create
        return client

    def client(self):
        from openai import OpenAI
        client=OpenAI(api_key='local-placeholder',base_url=BASE_URL,max_retries=0,timeout=TIMEOUT)
        return self.instrument(client)

    def request(self,client,path,messages,max_tokens):
        path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
        if path.exists():
            record=json.loads(path.read_text())
            if record['model']!=self.model or record['messages']!=messages or record['max_tokens']!=max_tokens:
                raise ValueError('Cached request is not identical')
            return record
        with path.with_suffix('.started').open('x') as stream:
            stream.write('One request reservation. Do not regenerate after interruption.\n')
        record={'model':self.model,'messages':messages,'max_tokens':max_tokens}
        started=time.perf_counter()
        try:
            response=client.chat.completions.create(model=self.path,messages=messages,temperature=0,top_p=1,max_tokens=max_tokens)
            record.update(status='completed',response=response.model_dump(mode='json'))
        except Exception as error:
            record.update(status='error',error=f'{type(error).__name__}: {error}')
        record['seconds']=time.perf_counter()-started
        save(path,record)
        return record

    def native_write(self,case,history,directory):
        from mem0 import Memory
        directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
        path=directory/'native-writer.json'
        if path.exists():
            record=json.loads(path.read_text())
            if record['model']!=self.model or record['input']!=history or record['case_id']!=case:
                raise ValueError('Native cached request changed')
            return record
        if (directory/'qdrant').exists():
            raise RuntimeError('Existing store without completed record')
        with (directory/'native-writer.started').open('x') as stream:
            stream.write('One native-write reservation. No regeneration.\n')
        traces=[]
        def callback(llm,response,params):
            traces.append({'params':params,'response':response.model_dump(mode='json')})
        config=json.loads((ROOT/'results/mem0-native-complete-preflight.json').read_text())['config']
        config['llm']['config'].update(model=self.path,api_key='local-placeholder',openai_base_url=BASE_URL,
            max_tokens=2048,temperature=0,top_p=1,response_callback=callback)
        config['vector_store']['config'].update(path=str(directory/'qdrant'),collection_name='review_history')
        config['history_db_path']=str(directory/'history.db')
        record={'model':self.model,'case_id':case,'input':history}
        memory=None;started=time.perf_counter()
        try:
            memory=Memory.from_config(config)
            memory.llm.client=self.instrument(memory.llm.client.with_options(max_retries=0,timeout=TIMEOUT))
            if memory.vector_store._get_bm25_encoder() is None:
                raise RuntimeError('Native sparse encoder absent')
            record['add']=memory.add([{'role':'user','content':history}],user_id=case)
            record['stored']=memory.get_all(filters={'user_id':case},top_k=1000)
            record['export_complete']=native_export_complete(record['add'],record['stored'])
            record['status']='completed'
        except Exception as error:
            record.update(status='error',error=f'{type(error).__name__}: {error}')
        finally:
            record.update(traces=traces,seconds=time.perf_counter()-started)
            if memory is not None:
                try:
                    memory.close();memory.vector_store.client.close()
                except Exception as error:
                    record['cleanup_error']=f'{type(error).__name__}: {error}'
            save(path,record)
        return record
