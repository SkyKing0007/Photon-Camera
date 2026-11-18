#!/usr/bin/env python3
"""Current three-file exact full-40-index 26957 <> 26958 forward/rollback git proof and hostile mutation."""
import pathlib,shutil,subprocess,sys,tempfile,re
from build_26958_incremental import R,scope,sha,fail

def main():
 changed,added,old,new=scope();paths=sorted(changed|added)
 for direction in ('FORWARD','ROLLBACK'):
  lines=(R/f'26958_{direction}_FULLINDEX.patch').read_text().splitlines()
  if sum(s.startswith('diff --git a/') for s in lines)!=len(paths):fail('wrong patch file count '+direction)
  idx=[s for s in lines if s.startswith('index ')]
  if len(idx)!=len(paths) or any(not re.fullmatch(r'index [0-9a-f]{40}\.\.[0-9a-f]{40}(?: 100644)?',s) for s in idx):fail('not exact full git blob SHA '+direction)
 for core in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='26958_patch_core'+str(core)+'_') as temp:
   w=pathlib.Path(temp)
   for p in paths:
    dst=w/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'handoff_payload_26958'/p,dst)
   for direction,digest in (('ROLLBACK',old),('FORWARD',new)):
    patch=R/f'26958_{direction}_FULLINDEX.patch'
    for check in (True,False):
     cmd=['git','-c',f'core.abbrev={core}','apply','--unidiff-zero','--whitespace=error']+(['--check'] if check else [])+[str(patch)]
     q=subprocess.run(cmd,cwd=w,capture_output=True,text=True)
     if q.returncode:fail('real exact git '+direction+' failed '+str(core)+' '+q.stderr[-500:])
    for p in paths:
     if sha(w/p)!=digest[p]:fail('patched actual source not exact prior/new '+direction+' '+p)
   p=w/'app/src/main/cpp/iris26864/Iris26864RealRawrCoordinator.cpp'
   original=p.read_bytes()
   if b'hdrq.strength = bOffReusable ? 11.0f : 13.0f' not in original:fail('current HDRQ strength contract missing')
   p.write_bytes(original.replace(b'hdrq.strength = bOffReusable ? 11.0f : 13.0f',b'hdrq.strength = 13.0f',1))
   q=subprocess.run(['git','apply','--check',str(R/'26958_ROLLBACK_FULLINDEX.patch')],cwd=w,capture_output=True)
   if q.returncode==0:fail('rollback accepted hostile changed strength')

 print('PASS 26958 three-file exact full-index 7/12/40 forward rollback and hostile changed-strength negative')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26958 PATCH BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
