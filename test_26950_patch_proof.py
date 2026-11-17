#!/usr/bin/env python3
"""Exact 26950 10-file 7/12/40 full-index git patches both directions, with byte-tamper negative."""
import hashlib,pathlib,subprocess,sys,re,tempfile,shutil
from build_26950_incremental import R,parse,fail,sha
old=parse(R/'26950_BASE_26949_FULL_APP.sha256');new=parse(R/'26950_EXPECTED_FULL_APP.sha256')
C=(R/'26950_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
for kind in ('FORWARD','ROLLBACK'):
 s=(R/f'26950_{kind}_FULLINDEX.patch').read_text()
 if s.count('diff --git a/')!=len(C) or sum(line.startswith('index ') for line in s.splitlines())!=len(C):fail('full-index patch missing file')
 for x in s.splitlines():
  if x.startswith('index ') and not re.fullmatch(r'index [0-9a-f]{40}\.\.[0-9a-f]{40} 100644',x):fail('short patch blob')
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26950_{abbrev}_') as d:
  root=pathlib.Path(d)
  for p in C:
   f=root/p;f.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'handoff_payload_26950'/p,f)
   if sha(f)!=new[p]:fail('candidate payload wrong '+p)
  for phase,source,target in [('ROLLBACK',new,old),('FORWARD',old,new)]:
   patch=str(R/f'26950_{phase}_FULLINDEX.patch')
   for extra in (['--check'],[]):
    cp=subprocess.run(['git','apply','--unsafe-paths','--unidiff-zero']+extra+[patch],cwd=root,capture_output=True,text=True)
    if cp.returncode!=0:fail('exact patch '+phase+' failed '+cp.stderr[:400])
   for p in C:
    if sha(root/p)!=target[p]:fail('patch output mismatch '+phase+' '+p)
  p=root/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp';data=p.read_bytes()
  if b'if (!sr) hdrq.strength = 11.0f;' not in data:fail('expected patch hunk absent')
  p.write_bytes(data.replace(b'if (!sr) hdrq.strength = 11.0f;',b'if (!sr) hdrq.strength = 42.0f;',1))
  cp=subprocess.run(['git','apply','--check',str(R/'26950_ROLLBACK_FULLINDEX.patch')],cwd=root,capture_output=True)
  if cp.returncode==0:fail('tampered patch base accepted')
print('PASS 26950 7/12/40 full-index zero-fuzz patch, rollback, tamper')
