#!/usr/bin/env python3
from pathlib import Path
import hashlib,shutil,subprocess,sys,tempfile
EXPECTED=[
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26545SabreProcessor.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawFusion.kt',
'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSpatialStacker.kt',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/IrisMotionSettings.java',
'app/src/main/java/com/particlesdevs/photoncamera/processing/processor/PhotonMotionMgc1271Bridge.kt',
'app/src/main/java/com/particlesdevs/photoncamera/settings/TunableRegistry.java',
'app/version.properties',
]
ROOT=Path(__file__).resolve().parent; FWD=ROOT/'26778_FORWARD_FULL_INDEX.patch'; REV=ROOT/'26778_ROLLBACK_FULL_INDEX.patch'
def run(cwd,*args):
 p=subprocess.run(args,cwd=cwd,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if p.returncode: raise SystemExit(f'command failed {args}\nstdout={p.stdout}\nstderr={p.stderr}')
 return p.stdout
def U(r):
 r=Path(r); return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
def paths(p): return sorted(line.split(' b/',1)[0][len('diff --git a/'):] for line in Path(p).read_text().splitlines() if line.startswith('diff --git a/'))
if len(sys.argv)!=3: raise SystemExit('usage: verify_26778_patches.py BASE CAND')
base,cand=map(Path,sys.argv[1:]); bu,cu=U(base),U(cand); actual=sorted(k for k in set(bu)|set(cu) if bu.get(k)!=cu.get(k)); assert actual==EXPECTED,actual
for p in (FWD,REV):
 t=p.read_text(); assert not any(x in t for x in ('\nrename from ','\nrename to ','\ncopy from ','\ncopy to ')),p
 assert paths(p)==EXPECTED,(p,paths(p))
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory(prefix=f'iris26778_{abbrev}_') as td:
  repo=Path(td)/'repo'; shutil.copytree(base,repo)
  run(repo,'git','init','-q'); run(repo,'git','config','user.name','Iris'); run(repo,'git','config','user.email','iris@example.invalid'); run(repo,'git','config','core.abbrev',str(abbrev)); run(repo,'git','add','-A'); run(repo,'git','commit','-q','-m','base')
  run(repo,'git','apply','--check','--unidiff-zero',str(FWD)); run(repo,'git','apply','--unidiff-zero',str(FWD)); assert U(repo)==cu,f'forward {abbrev}'
  run(repo,'git','apply','--check','--unidiff-zero',str(REV)); run(repo,'git','apply','--unidiff-zero',str(REV)); assert U(repo)==bu,f'rollback {abbrev}'
  print(f'PASS 26778 full-index forward/rollback core.abbrev={abbrev} fuzz=0 exact rollback; 8 modifications')
print('PASS 26778 canonical patch proof: exact 8-path allowlist, no rename/copy inference, byte-exact forward and rollback')
