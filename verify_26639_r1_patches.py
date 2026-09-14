#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4: raise SystemExit('usage: verify_26639_r1_patches.py ROOT BASE CANDIDATE')
root,base,cand=map(Path,sys.argv[1:]); changed=[x for x in (root/'R1_26639_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x]
fwd=(root/'R1_26639_RUNTIME_DELTA_FROM_26638_R1.patch').read_bytes(); rev=(root/'R1_26639_RUNTIME_ROLLBACK_TO_26638_R1.patch').read_bytes()
def run(*a,cwd): return subprocess.run(a,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
assert len(changed)==9 and len(set(changed))==9 and not (root/'R1_26639_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().strip()
with tempfile.TemporaryDirectory(prefix='iris26639_patch_') as td:
 t=Path(td); shutil.copytree(base/'app',t/'app'); run('git','init','-q',cwd=t); run('git','config','user.email','x@y',cwd=t); run('git','config','user.name','x',cwd=t); run('git','add','app',cwd=t); run('git','commit','-qm','base',cwd=t); b=run('git','rev-parse','HEAD',cwd=t).decode().strip()
 for rel in changed:
  dst=t/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(cand/rel,dst)
 run('git','add','app',cwd=t); run('git','commit','-qm','cand',cwd=t); c=run('git','rev-parse','HEAD',cwd=t).decode().strip()
 for n in ('7','12','40'):
  got=run('git','-c',f'core.abbrev={n}','diff','--binary','--full-index','--no-ext-diff',b,c,'--',*changed,cwd=t)
  back=run('git','-c',f'core.abbrev={n}','diff','--binary','--full-index','--no-ext-diff',c,b,'--',*changed,cwd=t)
  assert got==fwd and back==rev, f'patch determinism core.abbrev={n}'
 p=t/'f.patch'; p.write_bytes(fwd); run('git','checkout','-q',b,cwd=t); run('git','apply','--check',str(p),cwd=t); run('git','apply',str(p),cwd=t)
 for rel in changed: assert (t/rel).is_file() and sha(t/rel)==sha(cand/rel),rel
 p.write_bytes(rev); run('git','apply','--check',str(p),cwd=t); run('git','apply',str(p),cwd=t)
 for rel in changed: assert sha(t/rel)==sha(base/rel),rel
print('PASS 26639 full-index forward/rollback patch proof: core.abbrev 7/12/40, exact 9-path/0-added allowlist, fuzz=0 exact rollback')
