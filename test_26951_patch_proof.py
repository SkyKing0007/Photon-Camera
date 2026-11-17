#!/usr/bin/env python3
"""Complete full-index exact forward/rollback at core.abbrev 7/12/40, mutated-source rejection."""
import pathlib,re,subprocess,sys,tempfile,shutil
from build_26951_incremental import R,parse,fail,sha,scope
old=parse(R/'26951_BASE_26949_FULL_APP.sha256');new=parse(R/'26951_EXPECTED_FULL_APP.sha256')
paths=(R/'26951_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines()
if len(paths)!=11 or len(paths)!=len(set(paths)):fail('patch source list not exactly 11')
for direction in ('FORWARD','ROLLBACK'):
 p=R/f'26951_{direction}_FULLINDEX.patch';text=p.read_text()
 if sum(x.startswith('diff --git ') for x in text.splitlines())!=11 or sum(line.startswith('index ') for line in text.splitlines())!=11:fail('full-index patch file count differs')
 for line in text.splitlines():
  if line.startswith('index ') and not re.fullmatch(r'index [0-9a-f]{40}\.\.[0-9a-f]{40} 100644',line):fail('short/malformed full-index blob ID')
 if sorted(re.findall(r'^diff --git [ab]/(.*?) [ab]/',text,re.M))!=sorted(paths):fail('irrelevant/missing patch path')
for abbreviation in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'26951_fullindex_{abbreviation}_') as folder:
  root=pathlib.Path(folder)
  for p in paths:
   dst=root/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'handoff_payload_26951'/p,dst)
   if sha(dst)!=new[p]:fail('new 26951 candidate patch base mismatched '+p)
  for phase,target in [('ROLLBACK',old),('FORWARD',new)]:
   patch=str(R/f'26951_{phase}_FULLINDEX.patch')
   for check in (True,False):
    cmd=['git','-c',f'core.abbrev={abbreviation}','apply','--unsafe-paths']
    if check:cmd.append('--check')
    cmd.append(patch)
    ret=subprocess.run(cmd,cwd=root,text=True,capture_output=True)
    if ret.returncode:fail('full-index '+phase+' abbr='+str(abbreviation)+' git apply failed: '+ret.stderr[-400:])
   for p in paths:
    if sha(root/p)!=target[p]:fail('forward/rollback SHA divergence '+phase+' '+p)
  # Deliberately change an overlapping line in the 26951 record to require a true conflict.
  p=root/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp';raw=p.read_bytes()
  orig=b'if (!sr) hdrq.strength = 11.0f;';bad=b'if (!sr) hdrq.strength = 42.0f;'
  if raw.count(orig)!=1:fail('full-index negative anchor lost')
  p.write_bytes(raw.replace(orig,bad,1))
  check=subprocess.run(['git','apply','--check',str(R/'26951_ROLLBACK_FULLINDEX.patch')],cwd=root,capture_output=True)
  if check.returncode==0:fail('tampered 26951 source accepted rollback')
print('PASS 26951 exact 11-file git full-index 7/12/40 forward/rollback with negative tamper rejection')
