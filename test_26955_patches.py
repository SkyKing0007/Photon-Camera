#!/usr/bin/env python3
"""Current two-file exact full-40-index 26954 <> 26955 forward/rollback git proof and hostile mutation."""
import pathlib,shutil,subprocess,sys,tempfile,re
from build_26955_incremental import R,scope,sha,fail

def main():
 changed,added,old,new=scope();paths=sorted(changed|added)
 for direction in ('FORWARD','ROLLBACK'):
  lines=(R/f'26955_{direction}_FULLINDEX.patch').read_text().splitlines()
  if sum(s.startswith('diff --git a/') for s in lines)!=len(paths):fail('wrong patch file count '+direction)
  idx=[s for s in lines if s.startswith('index ')]
  if len(idx)!=len(paths) or any(not re.fullmatch(r'index [0-9a-f]{40}\.\.[0-9a-f]{40}(?: 100644)?',s) for s in idx):fail('not exact full git blob SHA '+direction)
 for core in (7,12,40):
  with tempfile.TemporaryDirectory(prefix='26955_patch_core'+str(core)+'_') as temp:
   w=pathlib.Path(temp)
   for p in paths:
    dst=w/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/'handoff_payload_26955'/p,dst)
   for direction,digest in (('ROLLBACK',old),('FORWARD',new)):
    patch=R/f'26955_{direction}_FULLINDEX.patch'
    for check in (True,False):
     cmd=['git','-c',f'core.abbrev={core}','apply','--unidiff-zero','--whitespace=error']+(['--check'] if check else [])+[str(patch)]
     q=subprocess.run(cmd,cwd=w,capture_output=True,text=True)
     if q.returncode:fail('real exact git '+direction+' failed '+str(core)+' '+q.stderr[-500:])
    for p in paths:
     if sha(w/p)!=digest[p]:fail('patched actual source not exact prior/new '+direction+' '+p)
   p=w/'app/src/main/assets/shaders/motionv2/render.glsl'
   original=p.read_bytes()
   if b'mappedPeak=((-0.2530536003804941*x-0.06645431039239985)*x+1.1545694219262823)*x+0.16493848884661177;' not in original:fail('current patch test missing strictly increasing shoulder')
   p.write_bytes(original.replace(b'mappedPeak=((-0.2530536003804941*x-0.06645431039239985)*x+1.1545694219262823)*x+0.16493848884661177;',b'mappedPeak=((-0.2530536003804941*x-0.06645431039239985)*x+1.1545694219262823)*x+0.16493848884661178;',1))
   q=subprocess.run(['git','apply','--check',str(R/'26955_ROLLBACK_FULLINDEX.patch')],cwd=w,capture_output=True)
   if q.returncode==0:fail('git rollback accepted hostile modified +EV shader')
 print('PASS 26955 two source exact full-index 7/12/40 forward rollback and hostile tampered GLSL negative')
if __name__=='__main__':
 try:main()
 except Exception as e:print('26955 PATCH BLOCKED '+str(e),file=sys.stderr);sys.exit(1)
