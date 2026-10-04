#!/usr/bin/env python3
from pathlib import Path
import hashlib,subprocess,tempfile,shutil,sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26764_patches.py BASE CANDIDATE')
b,c=map(Path,sys.argv[1:]); root=Path(__file__).resolve().parent
fwd=root/'26764_FORWARD_FULL_INDEX.patch'; rbk=root/'26764_ROLLBACK_FULL_INDEX.patch'
def H(r): return {str(p.relative_to(r)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'app').rglob('*') if p.is_file()}
hb,hc=H(b),H(c); expected=['app/src/main/java/com/hinnka/mycamera/processor/GlesIris26529SpatialRgbChromaPostprocessor.kt','app/version.properties']
assert sorted(k for k in set(hb)|set(hc) if hb.get(k)!=hc.get(k))==expected
for abbrev in (7,12,40):
 with tempfile.TemporaryDirectory() as td:
  r=Path(td); shutil.copytree(b/'app',r/'app'); subprocess.run(['git','init','-q'],cwd=r,check=True); subprocess.run(['git','config','user.email','a@b.c'],cwd=r,check=True); subprocess.run(['git','config','user.name','photon'],cwd=r,check=True); subprocess.run(['git','add','app'],cwd=r,check=True); subprocess.run(['git','commit','-qm','base'],cwd=r,check=True); subprocess.run(['git','config','core.abbrev',str(abbrev)],cwd=r,check=True)
  subprocess.run(['git','apply','--check','--unidiff-zero',str(fwd)],cwd=r,check=True); subprocess.run(['git','apply','--unidiff-zero',str(fwd)],cwd=r,check=True)
  assert H(r)==hc,f'forward mismatch abbrev {abbrev}'
  subprocess.run(['git','apply','--check','--unidiff-zero',str(rbk)],cwd=r,check=True); subprocess.run(['git','apply','--unidiff-zero',str(rbk)],cwd=r,check=True)
  assert H(r)==hb,f'rollback mismatch abbrev {abbrev}'
 print(f'PASS 26764 full-index forward/rollback core.abbrev={abbrev} fuzz=0 exact rollback')
