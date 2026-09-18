#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile,re
if len(sys.argv)!=4:raise SystemExit('usage: verify_26661_patches.py ROOT BASE CANDIDATE')
root=Path(sys.argv[1]).resolve();base=Path(sys.argv[2]).resolve();cand=Path(sys.argv[3]).resolve();fwd=(root/'R1_26661_RUNTIME_DELTA_FROM_26660.patch').read_bytes();rev=(root/'R1_26661_RUNTIME_ROLLBACK_TO_26660.patch').read_bytes();allow={x for x in (root/'R1_26661_RUNTIME_CHANGED_PATHS.txt').read_text().splitlines() if x};added={x for x in (root/'R1_26661_ADDED_PATHS_MUST_BE_ABSENT.txt').read_text().splitlines() if x};assert len(allow)==8 and not added
def H(r):return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((r/'app').rglob('*')) if p.is_file()}
def run(a,cwd,**kw):return subprocess.run(a,cwd=cwd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,**kw)
bh,ch=H(base),H(cand);assert len(bh)==len(ch)==1721 and {r for r in set(bh)|set(ch) if bh.get(r)!=ch.get(r)}==allow
for data in (fwd,rev):assert len(re.findall(r'^index ([0-9a-f]{40})\.\.([0-9a-f]{40})',data.decode(),re.M))==8
with tempfile.TemporaryDirectory(prefix='iris26661_patch_') as td:
 repo=Path(td)/'repo';shutil.copytree(base,repo);run(['git','init','-q'],repo);run(['git','config','user.email','iris@local.invalid'],repo);run(['git','config','user.name','Iris Verify'],repo);run(['git','add','-A'],repo);run(['git','commit','-qm','base'],repo)
 for ab in ('7','12','40'):
  run(['git','config','core.abbrev',ab],repo);shutil.rmtree(repo/'app');shutil.copytree(cand/'app',repo/'app');run(['git','add','-A'],repo);got=subprocess.check_output(['git','diff','--cached','--binary','--full-index','--no-ext-diff'],cwd=repo);assert got==fwd,f'forward patch changed at {ab}';run(['git','reset','--hard','HEAD'],repo)
 p=Path(td)/'f.patch';p.write_bytes(fwd);run(['git','apply','--check',str(p)],repo);run(['git','apply',str(p)],repo);assert H(repo)==ch;run(['git','add','-A'],repo);run(['git','commit','-qm','cand'],repo)
 q=Path(td)/'r.patch';q.write_bytes(rev);run(['git','apply','--check',str(q)],repo);run(['git','apply',str(q)],repo);assert H(repo)==bh
print('PASS 26661 deterministic full-index forward/rollback proof: core.abbrev 7/12/40 identical, exact apply/rollback, 8-path allowlist / 0 additions')
