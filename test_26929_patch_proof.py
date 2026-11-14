#!/usr/bin/env python3
"""Full-index 3-file exact, forward/rollback 7,12,40, no fuzz or source commits."""
from pathlib import Path
import subprocess,tempfile,shutil,sys,re
R=Path(__file__).resolve().parent
from build_26929_incremental import scope,sha
changes,added,original,target=scope()
assert len(changes)==3 and not added
fwd=R/'26929_FORWARD_FULLINDEX.patch';back=R/'26929_ROLLBACK_FULLINDEX.patch'
for patch in (fwd,back):
 s=patch.read_text();assert s.count('diff --git ')==3 and s.count('index ')==3
 for k in changes:assert s.count('diff --git a/'+k+' b/'+k)==1
 for line in s.splitlines():
  if line.startswith('index '):assert re.fullmatch(r'index [0-9a-f]{40}\.\.[0-9a-f]{40} [0-7]{6}',line),line
if '--live' in sys.argv:
 base=R/'.photon_26929_work/authority_26928';assert base.is_dir()
 for abbrev in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='p26929_gitproof_') as tmp:
   d=Path(tmp);subprocess.run(['git','init','-q'],cwd=d,check=True)
   for k in changes:
    p=d/k;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/k,p)
   for patch,expected in ((fwd,target),(back,original)):
    subprocess.run(['git','-c',f'core.abbrev={abbrev}','apply','--check','--whitespace=error',str(patch)],cwd=d,check=True)
    subprocess.run(['git','-c',f'core.abbrev={abbrev}','apply','--whitespace=error',str(patch)],cwd=d,check=True)
    for k in changes:assert sha(d/k)==expected[k],(abbrev,k)
 print('PASS 26929 EXACT forward/rollback 7/12/40, positive and postimage SHA, no fuzz')
else:
 for k in changes:assert sha(R/'handoff_payload_26929'/k)==target[k]
 print('PASS full-index exact 3-file patch source and staged SHA, live replay requires Actions authority')
