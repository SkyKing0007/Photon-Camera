#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
CHANGED=['app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2ViewfinderExposureMatcher.java','app/version.properties']
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
 td=Path(tempfile.mkdtemp(prefix='p26586v1_'))
 try:
  init(td,a)
  for rel in CHANGED:shutil.copy2(b/rel,td/rel)
  run(['git','config','core.abbrev',str(abbr)],td)
  return run(['git','diff','--binary','--full-index','--no-ext-diff','HEAD','--',*CHANGED],td)
 finally:shutil.rmtree(td)
def apply(a,b,p):
 td=Path(tempfile.mkdtemp(prefix='a26586v1_'))
 try:
  init(td,a);run(['git','apply','--check','--whitespace=nowarn',str(p)],td);run(['git','apply','--whitespace=nowarn',str(p)],td)
  if ah(td)!=ah(b):fail('patch output mismatch '+p.name)
 finally:shutil.rmtree(td)
def main():
 if len(sys.argv)!=5:fail('usage base candidate forward rollback')
 b,c,f,r=map(Path,sys.argv[1:]);ft=f.read_text();rt=r.read_text()
 for ab in (7,12,40):
  if regen(b,c,ab)!=ft:fail(f'forward nondeterministic core.abbrev={ab}')
  if regen(c,b,ab)!=rt:fail(f'rollback nondeterministic core.abbrev={ab}')
 apply(b,c,f);apply(c,b,r)
 print('PASS deterministic full-index forward/rollback core.abbrev=7/12/40 fuzz=0 exact byte equality')
if __name__=='__main__':main()
