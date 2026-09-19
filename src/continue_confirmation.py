"""Continue the already-started frozen local run, then verify complete results.

No model output is regenerated, no accuracy is inspected before all datasets
finish, and any failed command stops the sequence. Process IDs are explicitly
supplied for this local run; this script is not a job scheduler.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def alive(pid):
    try:os.kill(pid,0);return True
    except ProcessLookupError:return False


def complete(name):
    p=ROOT/'results'/name
    return p.exists() and json.loads(p.read_text()).get('complete') is True


def command(args,log):
    print('Running: '+' '.join(args),flush=True)
    with (ROOT/'data'/log).open('w') as stream:
        subprocess.run(args,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,check=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--qwen-run-pid',type=int,required=True);p.add_argument('--qwen-server-pid',type=int,required=True);a=p.parse_args()
    while alive(a.qwen_run_pid):time.sleep(5)
    for dataset in ['confirmation','movie-validation']:
        assert complete(f'{dataset}-evaluation-qwen.json'),f'Qwen {dataset} incomplete; inspect logs, do not skip cases'
    os.kill(a.qwen_server_pid,signal.SIGINT)
    for _ in range(30):
        if not alive(a.qwen_server_pid):break
        time.sleep(1)
    assert not alive(a.qwen_server_pid),'Qwen server did not stop cleanly'
    log=(ROOT/'data/confirmation-phi-server-sequential.log').open('w')
    args=[str(ROOT/'.venv/bin/python'),'-m','mlx_lm.server','--model',str(ROOT/'models/phi-4-4bit'),
      '--host','127.0.0.1','--port','8317','--temp','0','--max-tokens','2048',
      '--decode-concurrency','1','--prompt-concurrency','1','--prompt-cache-size','1','--log-level','WARNING']
    server=subprocess.Popen(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
    try:
        ready=False
        for _ in range(90):
            assert server.poll() is None,'Phi server failed during startup'
            try:
                with urllib.request.urlopen('http://127.0.0.1:8317/v1/models',timeout=3) as response:
                    ready=response.status==200
                if ready:break
            except OSError:pass
            time.sleep(2)
        assert ready,'Phi server readiness timeout'
        client=str(ROOT/'.venv-mem0/bin/python')
        command([client,'src/run_movie_validation.py','--model','phi','--preflight'],'movie-preflight-phi.log')
        command([client,'src/run_confirmation.py','--model','phi'],'confirmation-evaluation-phi.log')
        command([client,'src/run_movie_validation.py','--model','phi'],'movie-evaluation-phi.log')
    finally:
        if server.poll() is None:server.send_signal(signal.SIGINT);server.wait(timeout=30)
        log.close()
    for script,name in [('analyze_confirmation.py','confirmation-analysis.log'),('analyze_movie_validation.py','movie-validation-analysis.log'),
                        ('independent_result_check.py','independent-calculation.log'),('build_confirmation_figures.py','confirmation-figures.log'),('build_confirmation_tables.py','confirmation-tables.log')]:
        command(['/usr/bin/python3','src/'+script],name)
    print('Both domains complete; frozen analyses, independent calculation, figures and tables finished.',flush=True)


if __name__=='__main__':main()
