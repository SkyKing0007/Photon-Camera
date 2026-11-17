#!/usr/bin/env python3
"""Full-index forward+rollback patches at 7/12/40 and byte-tamper rejection."""
import hashlib,pathlib,shutil,subprocess,sys,tempfile,re
from build_26952_incremental import R,parse,scope,sha,fail
changed,added,old,new=scope();paths=sorted(changed|added)
for phase in ('FORWARD','ROLLBACK'):
 text=(R/f'26952_{phase}_FULLINDEX.patch').read_text()
 if text.count('diff --git a/')!=len(paths) or sum(x.startswith('index ') for x in text.splitlines())!=len(paths):fail('missing full-index patch '+phase)
 for row in text.splitlines():
  if row.startswith('index ') and not re.fullmatch('index [0-9a-f]{40}\\.\\.[0-9a-f]{40}(?: 100644)?',row):fail('short index patch '+row)
for length in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26952_patch_{length}_') as td:
  work=pathlib.Path(td)
  for p in paths:
   src=R/'handoff_payload_26952'/p
   dst=work/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  for phase,exp in [('ROLLBACK',old),('FORWARD',new)]:
   patch=str(R/f'26952_{phase}_FULLINDEX.patch')
   for check in (True,False):
    cmd=['git','apply','--unsafe-paths','--unidiff-zero']+(['--check'] if check else [])+[patch]
    res=subprocess.run(cmd,cwd=work,capture_output=True,text=True)
    if res.returncode:fail('git apply '+phase+' failed '+res.stderr[:300])
   for p in paths:
    if p in exp and (not (work/p).is_file() or sha(work/p)!=exp[p]):fail('rollback/forward output wrong '+phase+' '+p)
    if p not in exp and (work/p).exists():fail('added asset not removed on rollback')
  # Only canonical candidate bytes are patchable: tampering must be rejected.
  p=work/'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26932RawLensMedian.kt'
  p.write_bytes(p.read_bytes().replace(b'cc_median(p,m0,2)',b'cc_median(p,m0,8)',1))
  ret=subprocess.run(['git','apply','--check',str(R/'26952_ROLLBACK_FULLINDEX.patch')],cwd=work,capture_output=True)
  if ret.returncode==0:fail('tampered chroma overlay illegally accepted')
print('PASS 26952 7/12/40 all 4 changed+1 added full-index git rollback/forward, tamper rejection')
