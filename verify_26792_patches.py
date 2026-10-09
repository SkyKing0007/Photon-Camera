#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, subprocess, sys, tempfile
if len(sys.argv)!=5: raise SystemExit('usage: verify_26792_patches.py BASE CAND FORWARD ROLLBACK')
BASE,CAND,FWD,REV=(Path(x).resolve() for x in sys.argv[1:])
ALLOW=sorted([
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/render/Parameters.java',
'app/src/main/assets/shaders/motionv2/render.glsl',
'app/src/main/assets/shaders/motionv2/gainmap.glsl',
'app/src/main/java/com/particlesdevs/photoncamera/settings/PreferenceKeys.java',
'app/src/main/res/xml/preferences.xml',
'app/src/main/res/values/strings.xml',
'app/src/main/res/values/default_prefs.xml',
'app/version.properties'])
def run(cmd,cwd):
 p=subprocess.run(cmd,cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 if p.returncode: print(p.stdout); raise SystemExit(f'command failed: {cmd}')
 return p.stdout
def U(root): return {str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'app').rglob('*') if p.is_file()}
baseU,candU=U(BASE),U(CAND); assert len(baseU)==len(candU)==1779; assert set(baseU)==set(candU)
assert sorted(k for k in baseU if baseU[k]!=candU[k])==ALLOW
for p in [FWD,REV]:
 txt=p.read_text(); assert not any(x in txt for x in ['rename from ','rename to ','copy from ','copy to '])
 idx=[ln for ln in txt.splitlines() if ln.startswith('index ')]; assert len(idx)==13,(p,len(idx))
 for ln in idx:
  pair=ln.split()[1].split('..'); assert len(pair)==2 and all(len(x)==40 for x in pair),ln
 diffpaths=sorted(ln[13:] for ln in txt.splitlines() if ln.startswith('diff --git a/') for _ in [0])
 # Normalize 'path b/path' tail from diff header.
 got=[]
 for ln in txt.splitlines():
  if ln.startswith('diff --git a/'):
   a=ln.split(' b/',1)[0][13:]; got.append(a)
 assert sorted(got)==ALLOW,(p,sorted(got))
for abbr in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'iris26792_patch_{abbr}_') as td:
  td=Path(td); shutil.copytree(BASE/'app',td/'app'); run(['git','init','-q'],td)
  run(['git','config','user.email','patch@example.invalid'],td); run(['git','config','user.name','patchproof'],td)
  run(['git','config','core.abbrev',str(abbr)],td); run(['git','add','app'],td); run(['git','commit','-q','-m','base'],td)
  run(['git','apply','--check',str(FWD)],td); run(['git','apply','--index',str(FWD)],td); assert U(td)==candU,f'forward mismatch abbrev={abbr}'
  run(['git','apply','--check',str(REV)],td); run(['git','apply','--index',str(REV)],td); assert U(td)==baseU,f'rollback mismatch abbrev={abbr}'
  print(f'PASS 26792 full-index forward/rollback core.abbrev={abbr} fuzz=0 exact rollback; 13 modifications')
print('PASS 26792 canonical patch proof')
