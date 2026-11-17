#!/usr/bin/env python3
"""Original 26952 -> 26953 EXACT four-file full-index forward/rollback at 7/12/40 plus corruption rejection."""
import pathlib,shutil,subprocess,sys,tempfile,re
from build_26953_incremental import R,parse,scope,sha,fail
changed,added,old,new=scope();paths=sorted(changed|added)
assert len(paths)==4 and not added
for phase in ('FORWARD','ROLLBACK'):
 t=(R/f'26953_{phase}_FULLINDEX.patch').read_text()
 if t.count('diff --git a/')!=len(paths) or sum(s.startswith('index ') for s in t.splitlines())!=len(paths):fail('patch file count mismatch '+phase)
 for line in t.splitlines():
  if line.startswith('index ') and not re.fullmatch(r'index [0-9a-f]{40}\.\.[0-9a-f]{40}(?: 100644)?',line):fail('patch includes incomplete git blob SHA '+line)
for level in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26953_rollback_{level}_') as td:
  work=pathlib.Path(td)
  for p in paths:
   dst=work/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'handoff_payload_26953'/p,dst)
  for direction,expected in (('ROLLBACK',old),('FORWARD',new)):
   patch=str(R/f'26953_{direction}_FULLINDEX.patch')
   for is_check in (True,False):
    cmd=['git','apply','--unidiff-zero']+(['--check'] if is_check else [])+[patch]
    q=subprocess.run(cmd,cwd=work,capture_output=True,text=True)
    if q.returncode:fail('real full index patch application '+direction+' '+q.stderr[:350])
   for p in paths:
    if sha(work/p)!=expected[p]:fail('runtime patch byte differs from authentic compiled-source SHA '+p)
  path=work/'app/src/main/assets/shaders/motionv2/render.glsl'
  b=path.read_bytes()
  assert b'float globalEv=clamp(0.40*log2' in b
  path.write_bytes(b.replace(b'float globalEv=clamp(0.40*log2',b'float globalEv=clamp(0.42*log2',1))
  q=subprocess.run(['git','apply','--check',str(R/'26953_ROLLBACK_FULLINDEX.patch')],cwd=work,capture_output=True)
  if q.returncode==0:fail('patch accepted tampered new current shader')
print('PASS 26953 4 exact full-index source patches at 7/12/40, forward/rollback and hostile altered GLSL rejected')
