#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4: raise SystemExit('usage: verify_26761_patches.py PACKAGE BASE CANDIDATE')
root=Path(sys.argv[1]).resolve(); base=Path(sys.argv[2]); cand=Path(sys.argv[3]); fwd=root/'26761_FORWARD_FULL_INDEX.patch'; rev=root/'26761_ROLLBACK_FULL_INDEX.patch'
allow=sorted(x for x in (root/'26761_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x)
def H(r): return {'app/'+p.relative_to(r/'app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
hb,hc=H(base),H(cand); assert len(hb)==len(hc)==1823
for patch in (fwd,rev):
 txt=patch.read_text()
 indexes=[x for x in txt.splitlines() if x.startswith('index ')]
 assert indexes and all(len(x.split()[1].split('..')[0])==40 and len(x.split()[1].split('..')[1])==40 for x in indexes)
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'iris26761_patch_{abbrev}_') as td:
  t=Path(td); shutil.copytree(base/'app',t/'app'); subprocess.run(['git','init','-q'],cwd=t,check=True); subprocess.run(['git','config','user.email','photon@local.invalid'],cwd=t,check=True); subprocess.run(['git','config','user.name','Photon26761'],cwd=t,check=True); subprocess.run(['git','config','core.abbrev',str(abbrev)],cwd=t,check=True); subprocess.run(['git','add','app'],cwd=t,check=True); subprocess.run(['git','commit','-q','-m','base'],cwd=t,check=True)
  subprocess.run(['git','apply','--check','--unidiff-zero',str(fwd)],cwd=t,check=True); subprocess.run(['git','apply','--unidiff-zero',str(fwd)],cwd=t,check=True); assert H(t)==hc
  changed=sorted(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=t,text=True).splitlines()); assert changed==allow,(abbrev,changed)
  subprocess.run(['git','add']+allow,cwd=t,check=True); subprocess.run(['git','commit','-q','-m','candidate'],cwd=t,check=True)
  subprocess.run(['git','apply','--check','--unidiff-zero',str(rev)],cwd=t,check=True); subprocess.run(['git','apply','--unidiff-zero',str(rev)],cwd=t,check=True); assert H(t)==hb
  changed=sorted(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=t,text=True).splitlines()); assert changed==allow,(abbrev,changed)
  print(f'PASS 26761 full-index forward/rollback core.abbrev={abbrev} fuzz=0 exact rollback allowlist=5')
