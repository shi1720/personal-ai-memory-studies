"""Build and check named and anonymous PDFs from the completed manuscript."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf'
PAPER=ROOT/'paper'


def main():
    check=json.loads((ROOT/'results/independent-calculation-check.json').read_text())
    assert all(c['status']=='passed' for c in check['checks'])
    for path,h in check['analysis_hashes'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==h
    required=['main.tex','abstract.tex','introduction-findings.tex','findings.tex','discussion.tex','conclusion.tex',
              'appendix.tex','main-results-table.tex','results.tex','supplementary-tables.tex']
    for name in required:
        text=(PAPER/name).read_text()
        assert '\u2014' not in text and '---' not in text,'Em dash in authored prose: '+name
        assert not any(w in text.lower() for w in ['layout-only draft','todo','tbd','count withheld','results forthcoming']),name
    OUT.mkdir(parents=True,exist_ok=True)
    tectonic=shutil.which('tectonic');assert tectonic,'Tectonic is required'
    results=[]
    for source,title in [('main.tex','Shivam_Gupta_Personal_AI_Memory_Paper'),('anonymous.tex','Personal_AI_Memory_Anonymous')]:
        proc=subprocess.run([tectonic,source,'--keep-logs','--outdir',str(OUT)],cwd=PAPER,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (OUT/(Path(source).stem+'-build.txt')).write_text(proc.stdout)
        assert proc.returncode==0,proc.stdout
        log=(OUT/(Path(source).stem+'.log')).read_text()
        assert 'Overfull' not in log,'Layout overflow; inspect '+source
        assert 'undefined references' not in log.lower() and 'undefined citations' not in log.lower(),source
        raw=OUT/(Path(source).stem+'.pdf');dest=OUT/(title+'.pdf');raw.replace(dest)
        reader=PdfReader(dest);texts=[p.extract_text() or '' for p in reader.pages];text='\n'.join(texts)
        assert 'Layout-only' not in text and 'AUTHORERR' not in text
        assert all(abs(float(p.mediabox.width)-612)<1 and abs(float(p.mediabox.height)-792)<1 for p in reader.pages)
        main_end=next(i+1 for i,t in enumerate(texts) if 'Impact Statement' in t)
        assert main_end<=8,f'Main text exceeds eight pages: {main_end}'
        if source=='main.tex':assert 'Shivam Gupta' in text and 'shivam1720406@gmail.com' in text
        else:
            for marker in ['Shivam','shivam1720406','shi1720','personal-ai-memory-studies','/Users/']:assert marker not in text,marker
            assert 'Shivam' not in str(reader.metadata)
        assert 'Proceedings of the International Conference' not in str(reader.metadata.get('/Subject',''))
        results.append({'file':str(dest.relative_to(ROOT)),'pages':len(reader.pages),'main_text_last_page':main_end,
           'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size})
    report={'pdfs':results,'source_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(PAPER.glob('*.tex'))},
      'status':'compiled and text/layout constraints checked; visual inspection separately required'}
    (ROOT/'results/paper-build-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['pdfs'],indent=2))


if __name__=='__main__':main()
