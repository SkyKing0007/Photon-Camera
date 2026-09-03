#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
CHANGED=['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java','app/version.properties']
def fail(x):raise SystemExit('FAIL: '+x)
def run(c,w):
 r=subprocess.run(c,cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if r.returncode:fail(str(c)+' '+r.stderr)
 return r.stdout
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ah(r):return {str(p.relative_to(r)):sha(p) for p in sorted((Path(r)/'app').rglob('*')) if p.is_file()}
def init(td,src):
 shutil.copytree(src,td,dirs_exist_ok=True);run(['git','init','-q'],td);run(['git','config','user.name','Proof'],td);run(['git','config','user.email','proof@local'],td);run(['git','add','-A'],td);run(['git','commit','-q','-m','start'],td)
def regen(a,b,abbr):
 td=Path(tempfile.mkdtemp(prefix='p26583v2_'))
 try:
  init(td,a)
  for rel in CHANGED:shutil.copy2(b/rel,td/rel)
  run(['git','config','core.abbrev',str(abbr)],td)
  return run(['git','diff','--binary','--full-index','--no-ext-diff','HEAD','--',*CHANGED],td)
 finally:shutil.rmtree(td)
def apply(a,b,p):
 td=Path(tempfile.mkdtemp(prefix='a26583v2_'))
 try:
  init(td,a);run(['git','apply','--check','--whitespace=nowarn',str(p)],td);run(['git','apply','--whitespace=nowarn',str(p)],td)
  if ah(td)!=ah(b):fail('patch not exact')
 finally:shutil.rmtree(td)
def main():
 if len(sys.argv)!=5:fail('usage base cand fwd rev')
 b,c,f,r=map(Path,sys.argv[1:]);fs=[regen(b,c,x) for x in (7,12,40)];rs=[regen(c,b,x) for x in (7,12,40)]
 if len(set(fs))!=1 or len(set(rs))!=1:fail('abbrev instability')
 if f.read_text()!=fs[0] or r.read_text()!=rs[0]:fail('noncanonical patch')
 apply(b,c,f);apply(c,b,r)
 print('PASS deterministic full-index patches core.abbrev=7/12/40')
 print('PASS FORWARD PATCH FUZZ=0 exact 26583 recreation')
 print('PASS ROLLBACK PATCH FUZZ=0 exact successful 26582 recreation')
if __name__=='__main__':main()
