#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4: raise SystemExit("usage: verify_26759_patches.py PACKAGE BASE CANDIDATE")
root=Path(sys.argv[1]).resolve(); base=Path(sys.argv[2]); cand=Path(sys.argv[3]); fwd=root/'26759_FORWARD_FULL_INDEX.patch'; rev=root/'26759_ROLLBACK_FULL_INDEX.patch'
allow=sorted(x for x in (root/'26759_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x)
def H(r): return {'app/'+p.relative_to(r/'app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
hb,hc=H(base),H(cand)
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'iris26759_patch_{abbrev}_') as td:
  t=Path(td); shutil.copytree(base/'app',t/'app'); subprocess.run(['git','init','-q'],cwd=t,check=True); subprocess.run(['git','config','user.email','photon@local.invalid'],cwd=t,check=True); subprocess.run(['git','config','user.name','Photon26759'],cwd=t,check=True); subprocess.run(['git','config','core.abbrev',str(abbrev)],cwd=t,check=True); subprocess.run(['git','add','app'],cwd=t,check=True); subprocess.run(['git','commit','-q','-m','base'],cwd=t,check=True)
  subprocess.run(['git','apply','--check',str(fwd)],cwd=t,check=True); subprocess.run(['git','apply',str(fwd)],cwd=t,check=True); assert H(t)==hc; changed=sorted(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=t,text=True).splitlines()); assert changed==allow,(abbrev,changed)
  subprocess.run(['git','add']+allow,cwd=t,check=True); subprocess.run(['git','commit','-q','-m','candidate'],cwd=t,check=True)
  subprocess.run(['git','apply','--check',str(rev)],cwd=t,check=True); subprocess.run(['git','apply',str(rev)],cwd=t,check=True); assert H(t)==hb; changed=sorted(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=t,text=True).splitlines()); assert changed==allow,(abbrev,changed)
  print(f'PASS 26759 full-index forward/rollback core.abbrev={abbrev} fuzz=0 exact rollback allowlist=2')
