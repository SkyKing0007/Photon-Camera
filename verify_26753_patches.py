#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4: raise SystemExit('usage: verify_26753_patches.py PACKAGE BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:]); fwd=root/'26753_FORWARD_FULL_INDEX.patch'; rev=root/'26753_ROLLBACK_FULL_INDEX.patch'
allow=sorted(x for x in (root/'26753_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x)
def H(r): return {'app/'+p.relative_to(r/'app').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
hb,hc=H(base),H(cand)
for abbrev in (7,12,40):
    with tempfile.TemporaryDirectory(prefix=f'iris26753_patch_{abbrev}_') as td:
        t=Path(td); shutil.copytree(base/'app',t/'app');
        subprocess.run(['git','init','-q'],cwd=t,check=True); subprocess.run(['git','config','user.email','photon@local.invalid'],cwd=t,check=True); subprocess.run(['git','config','user.name','Photon26753'],cwd=t,check=True); subprocess.run(['git','config','core.abbrev',str(abbrev)],cwd=t,check=True); subprocess.run(['git','add','app'],cwd=t,check=True); subprocess.run(['git','commit','-q','-m','base'],cwd=t,check=True)
        subprocess.run(['git','apply','--check',str(fwd)],cwd=t,check=True); subprocess.run(['git','apply',str(fwd)],cwd=t,check=True)
        assert H(t)==hc
        changed=sorted(subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=t,text=True).splitlines()); assert changed==allow,(abbrev,changed)
        subprocess.run(['git','apply','--check',str(rev)],cwd=t,check=True); subprocess.run(['git','apply',str(rev)],cwd=t,check=True); assert H(t)==hb
        assert not subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=t,text=True).strip()
        print(f'PASS 26753 full-index forward/rollback core.abbrev={abbrev} fuzz=0 exact rollback allowlist=5')
