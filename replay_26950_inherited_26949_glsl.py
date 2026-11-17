#!/usr/bin/env python3
"""Full real 26949 post-AMaZE GLSL compile on unchanged shader; current B SDR shaders separately compiled."""
import hashlib,pathlib,subprocess,sys
from build_26950_incremental import R,parse,sha,fail
P=R/'compile_26949_shaders.sh'
EXPECTED_SHA='a38ca81d48161df62c606059a85d99e18424c7397b3e73cab3f57eea0a8c54d2'
CHECK='python3 -S test_26949_restore.py --live'
REPLACEMENT='python3 -S test_26949_restore.py --payload'
SOURCE='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'
def run(cmd):subprocess.run(cmd,cwd=R,check=True)
def check():
 if sha(P)!=EXPECTED_SHA:fail('successful 26949 original real compiler script tampered')
 src=P.read_text()
 if src.count(CHECK)!=1 or REPLACEMENT in src:fail('26949 historical live test changed unexpectedly')
 old=parse(R/'26950_BASE_26949_FULL_APP.sha256');new=parse(R/'26950_EXPECTED_FULL_APP.sha256')
 if old[SOURCE]!=new.get(SOURCE) or sha(R/SOURCE)!=old[SOURCE]:fail('26949 actual GLSL no longer byte-identical')
 for p in ['app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag']:
  if old[p]!=new.get(p) or sha(R/p)!=old[p]:fail('26949 inherited shader changed '+p)
 out=src.replace(CHECK,REPLACEMENT,1)
 if out.replace(REPLACEMENT,CHECK,1)!=src:fail('historical GLSL compiler body rewritten')
 return out
def main():
 executable=check()
 if '--preflight' in sys.argv:
  print('PASS original 26949 historical post-AMaZE compiler unchanged; B SDR changes handled by real 26950 V2 shader compiler')
  return
 run([sys.executable,'-S','build_26949_incremental.py','seal'])
 run([sys.executable,'-S','test_26949_restore.py','--payload'])
 run([sys.executable,'-S','test_26950_source.py','--live'])
 run(['bash','-c',executable,str(P)])
 receipt=R/'photon_26949_outputs/26949_REAL_GLSL_COMPILER.txt'
 if not receipt.is_file() or 'PASS 26949 real pinned runtime-expanded GLES300 post-AMaZE shader' not in receipt.read_text() or sha(R/SOURCE) not in receipt.read_text():
  fail('full original 26949 compiled shader receipts absent or wrong')
 run([sys.executable,'-S','test_26950_source.py','--live'])
 print('PASS full 26949 real GLSL/SPIR-V on unchanged shader, current 26950 protected')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
