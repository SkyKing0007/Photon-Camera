#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
CHANGED=[
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/version.properties']
def fail(m):raise SystemExit('FAIL: '+m)
def run(cmd,cwd):
 r=subprocess.run(cmd,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if r.returncode:fail(f'{cmd}: {r.stderr}')
 return r.stdout
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def allhash(r):return {str(p.relative_to(r)):sha(p) for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
def init(td,src):
 shutil.copytree(src,td,dirs_exist_ok=True);run(['git','init','-q'],td);run(['git','config','user.name','Proof'],td);run(['git','config','user.email','proof@local'],td);run(['git','add','-A'],td);run(['git','commit','-q','-m','start'],td)
def regen(start,target,abbrev):
 td=Path(tempfile.mkdtemp(prefix='p26582_'))
 try:
  init(td,start)
  for rel in CHANGED:shutil.copy2(target/rel,td/rel)
  run(['git','config','core.abbrev',str(abbrev)],td)
  return run(['git','diff','--binary','--full-index','--no-ext-diff','HEAD','--',*CHANGED],td)
 finally:shutil.rmtree(td)
def applyprove(start,target,patch):
 td=Path(tempfile.mkdtemp(prefix='a26582_'))
 try:
  init(td,start);run(['git','apply','--check','--whitespace=nowarn',str(patch)],td);run(['git','apply','--whitespace=nowarn',str(patch)],td)
  if allhash(td)!=allhash(target):fail('patch apply not byte-identical')
 finally:shutil.rmtree(td)
def main():
 if len(sys.argv)!=5:fail('usage base candidate forward rollback')
 base,cand,fwd,rev=map(Path,sys.argv[1:]);f=[regen(base,cand,a) for a in (7,12,40)];r=[regen(cand,base,a) for a in (7,12,40)]
 if len(set(f))!=1 or len(set(r))!=1:fail('core.abbrev changed patch bytes')
 if fwd.read_text()!=f[0] or rev.read_text()!=r[0]:fail('packaged patch not canonical regeneration')
 applyprove(base,cand,fwd);applyprove(cand,base,rev)
 print('PASS deterministic full-index patches core.abbrev=7/12/40')
 print('PASS FORWARD PATCH FUZZ=0 exact 26582 candidate recreation')
 print('PASS ROLLBACK PATCH FUZZ=0 exact successful 26581 recreation')
if __name__=='__main__':main()
