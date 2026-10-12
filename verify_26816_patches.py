#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,shutil,tempfile,sys,re
if len(sys.argv)!=5: raise SystemExit('usage: verify_26816_patches.py BASE CAND FORWARD ROLLBACK')
BASE,CAND=map(Path,sys.argv[1:3]); F=Path(sys.argv[3]).resolve(); R=Path(sys.argv[4]).resolve()
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(root): return {p.relative_to(root).as_posix():sha(p) for p in (root/'app').rglob('*') if p.is_file()}
def run(cmd,cwd): subprocess.run(cmd,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
base_u,cand_u=uni(BASE),uni(CAND); assert len(base_u)==1782 and len(cand_u)==1783
allow=set(Path('26816_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines())
for patch in (F,R):
    txt=patch.read_text(); paths=set(re.findall(r'^diff --git a/(.+?) b/(.+?)$',txt,re.M)[i][0] for i in range(len(re.findall(r'^diff --git a/(.+?) b/(.+?)$',txt,re.M))))
    assert paths==allow,(patch,sorted(paths^allow))
    assert not re.search(r'^(rename from|rename to|copy from|copy to) ',txt,re.M)
    for line in re.findall(r'^index ([0-9a-f]+)\.\.([0-9a-f]+)',txt,re.M):
        assert all(len(x)==40 for x in line),line
for abbrev in (7,12,40):
    with tempfile.TemporaryDirectory(prefix=f'iris26816_patch_{abbrev}_') as td:
        w=Path(td); shutil.copytree(BASE/'app',w/'app')
        run(['git','init','-q'],w); run(['git','config','user.email','photon@example.invalid'],w); run(['git','config','user.name','Photon'],w)
        run(['git','add','app'],w); run(['git','commit','-q','-m','base'],w); run(['git','config','core.abbrev',str(abbrev)],w)
        run(['git','apply','--check',str(F)],w); run(['git','apply',str(F)],w); assert uni(w)==cand_u,f'forward mismatch core.abbrev={abbrev}'
        assert (w/'app/src/main/res/drawable/ic_logging_document.xml').is_file()
        run(['git','apply','--check',str(R)],w); run(['git','apply',str(R)],w); assert uni(w)==base_u,f'rollback mismatch core.abbrev={abbrev}'
        assert not (w/'app/src/main/res/drawable/ic_logging_document.xml').exists()
        print(f'PASS 26816 patch replay core.abbrev={abbrev} forward=candidate rollback=authority fuzz=0')
print('PASS 26816 canonical patch proof: deterministic full-index forward/rollback at 7/12/40 including exact added-path rollback')
