#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, subprocess, sys, tempfile
if len(sys.argv)!=5: raise SystemExit('usage: verify_26799_patches.py BASE CAND FORWARD ROLLBACK')
BASE,CAND,FWD,RBK=map(Path,sys.argv[1:])
ALLOW=['app/src/main/assets/shaders/motionv2/false_color_classify_26799.glsl','app/src/main/assets/shaders/motionv2/false_color_propagate_26799.glsl','app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/version.properties']
MOD={'app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java','app/version.properties'}
ADD=set(ALLOW)-MOD
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def uni(root): return {str(p.relative_to(root)):sha(p) for p in (root/'app').rglob('*') if p.is_file()}
bu,cu=uni(BASE),uni(CAND)
assert len(bu)==1779 and len(cu)==1781
assert set(cu)-set(bu)==ADD and set(bu)-set(cu)==set()
assert {p for p in set(bu)&set(cu) if bu[p]!=cu[p]}==MOD
for patch in (FWD,RBK):
    t=patch.read_text(errors='strict'); assert not any(x in t for x in ('rename from','rename to','copy from','copy to'))
for core in (7,12,40):
  with tempfile.TemporaryDirectory(prefix=f'iris26799_patch_{core}_') as td:
    w=Path(td); shutil.copytree(BASE/'app',w/'app')
    subprocess.run(['git','init','-q'],cwd=w,check=True); subprocess.run(['git','config','core.abbrev',str(core)],cwd=w,check=True)
    subprocess.run(['git','config','user.email','photon@local.invalid'],cwd=w,check=True); subprocess.run(['git','config','user.name','Photon'],cwd=w,check=True)
    subprocess.run(['git','add','app'],cwd=w,check=True); subprocess.run(['git','commit','-q','-m','base'],cwd=w,check=True)
    p=subprocess.run(['git','apply','--check','--index',str(FWD.resolve())],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); assert p.returncode==0,p.stdout
    p=subprocess.run(['git','apply','--index','--verbose',str(FWD.resolve())],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); assert p.returncode==0,p.stdout; assert 'fuzz' not in p.stdout.lower() and 'offset' not in p.stdout.lower(),p.stdout
    assert uni(w)==cu
    changed=subprocess.check_output(['git','diff','--cached','--name-only'],cwd=w,text=True).splitlines(); assert changed==ALLOW,changed
    subprocess.run(['git','commit','-q','-m','candidate'],cwd=w,check=True)
    p=subprocess.run(['git','apply','--check','--index',str(RBK.resolve())],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); assert p.returncode==0,p.stdout
    p=subprocess.run(['git','apply','--index','--verbose',str(RBK.resolve())],cwd=w,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); assert p.returncode==0,p.stdout; assert 'fuzz' not in p.stdout.lower() and 'offset' not in p.stdout.lower(),p.stdout
    assert uni(w)==bu
    print(f'PASS 26799 full-index forward/rollback core.abbrev={core} fuzz=0 exact rollback; 3 modifications + 2 additions')
print('PASS 26799 canonical patch proof')
