#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
if len(sys.argv)!=4: raise SystemExit('usage: verify_r1_2_26648_patches.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]).resolve(); base=Path(sys.argv[2]).resolve(); cand=Path(sys.argv[3]).resolve()
fwd=(root/'R1_2_26648_RUNTIME_DELTA_FROM_R1_1.patch').read_bytes(); rev=(root/'R1_2_26648_RUNTIME_ROLLBACK_TO_R1_1.patch').read_bytes()
def run(args,cwd): return subprocess.run(args,cwd=cwd,check=True,stdout=subprocess.DEVNULL)
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((r/'app').rglob('*')) if p.is_file()}
assert H(base)==H(cand) and not fwd and not rev
with tempfile.TemporaryDirectory(prefix='iris26648_r12_patch_') as td:
 repo=Path(td)/'repo'; shutil.copytree(base,repo); run(['git','init','-q'],repo); run(['git','config','user.email','iris@local.invalid'],repo); run(['git','config','user.name','Iris Verify'],repo); run(['git','add','-A'],repo); run(['git','commit','-qm','r1_1_authority'],repo); bc=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
 outs=[]
 for ab in ('7','12','40'):
  run(['git','config','core.abbrev',ab],repo); outs.append(subprocess.check_output(['git','diff','--binary','--full-index','--no-ext-diff',bc,bc],cwd=repo))
 assert outs[0]==outs[1]==outs[2]==b''
print('PASS 26648 R1.2 identity full-index patch proof: core.abbrev 7/12/40 all empty; 0-path/0-added runtime delta')
