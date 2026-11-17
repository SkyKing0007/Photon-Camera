#!/usr/bin/env python3
"""Full original 26949 post-AMaZE real shader compiler, unchanged source SHA; historical checker on payload."""
import subprocess,sys
from build_26951_incremental import R,parse,sha,fail
P=R/'compile_26949_shaders.sh'
EXPECTED_SHA='a38ca81d48161df62c606059a85d99e18424c7397b3e73cab3f57eea0a8c54d2'
CHECK='python3 -S test_26949_restore.py --live'
REPLACE='python3 -S test_26949_restore.py --payload'
SOURCE='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'
def check():
 if not P.is_file() or sha(P)!=EXPECTED_SHA:fail('successful 26949 real compiler body changed')
 src=P.read_text()
 if src.count(CHECK)!=1 or REPLACE in src:fail('unexpected original 26949 compiler checker')
 old=parse(R/'26951_BASE_26949_FULL_APP.sha256');new=parse(R/'26951_EXPECTED_FULL_APP.sha256')
 if old[SOURCE]!=new[SOURCE]:fail('original 26949 AMaZE/FCC changed')
 if '--preflight' not in sys.argv and (not (R/SOURCE).is_file() or sha(R/SOURCE)!=old[SOURCE]):fail('original 26949 AMaZE/FCC live bytes changed')
 rewritten=src.replace(CHECK,REPLACE,1)
 if rewritten.replace(REPLACE,CHECK,1)!=src:fail('original 26949 shader body rewritten')
 return rewritten
if __name__=='__main__':
 try:
  sh=check()
  if '--preflight' not in sys.argv:
   subprocess.run([sys.executable,'-S','build_26949_incremental.py','seal'],cwd=R,check=True)
   subprocess.run([sys.executable,'-S','test_26949_restore.py','--payload'],cwd=R,check=True)
   subprocess.run(['bash','-c',sh,str(P)],cwd=R,check=True)
   receipt=R/'photon_26949_outputs/26949_REAL_GLSL_COMPILER.txt'
   if not receipt.is_file() or 'PASS 26949 real pinned runtime-expanded GLES300 post-AMaZE shader' not in receipt.read_text() or sha(R/SOURCE) not in receipt.read_text():fail('actual 26949 real shader compile receipt absent')
  print('PASS sealed successful 26949 original real GLSL compiler, unchanged AMaZE/FCC')
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
