#!/usr/bin/env python3
"""Original 26948 compiler/optimizer body replayed against current 26950 V2 B shaders.
Historical 26948 source-only assertion runs on sealed payload; current B shaders
are separately verified and compiled with pinned GLSL 16.5 and SPIR-V in 26950 V2.
"""
import hashlib,subprocess,sys
from build_26950_incremental import R,parse,sha,fail
P=R/'compile_26948_shaders.sh'
BLOB='2e02b430e62790beaed47d7f0679c63622bab326'
OLD='python3 -S test_26948_sdr_hdr_math.py --live'
NEW='python3 -S test_26948_sdr_hdr_math.py --payload'
EXPECTED=('app/src/main/assets/shaders/motionv2/render.glsl',
          'app/src/main/assets/shaders/motionv2/gainmap.glsl')
def run(args):subprocess.run(args,cwd=R,check=True)
def check():
 raw=P.read_bytes();git=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 if git!=BLOB:fail('original 26948 real compiler changed')
 source=raw.decode('utf-8')
 if source.count(OLD)!=1 or NEW in source:fail('26948 historical checker unexpected')
 prior=parse(R/'26950_BASE_26949_FULL_APP.sha256');curr=parse(R/'26950_EXPECTED_FULL_APP.sha256')
 for name in EXPECTED:
  if prior[name]==curr[name] or sha(R/name)!=curr[name]:fail('new 26950 V2 SDR source not current '+name)
 for name in ('app/src/main/assets/shaders/iris26876/b_fused_final_p3_gain.frag',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesIris26856True2xCfa.kt',
 'app/src/main/java/com/hinnka/mycamera/processor/GlesMgcRawSabreShaders.kt'):
  if prior[name]!=curr[name] or sha(R/name)!=prior[name]:fail('26948 protected shader changed '+name)
 output=source.replace(OLD,NEW,1)
 if output.replace(NEW,OLD,1)!=source:fail('26948 compiler body altered')
 return output
if __name__=='__main__':
 try:
  script=check()
  if '--preflight' not in sys.argv:
   run([sys.executable,'-S','build_26948_incremental.py','seal'])
   run([sys.executable,'-S','test_26948_sdr_hdr_math.py','--payload'])
   run([sys.executable,'-S','test_26950_highlight.py','--live'])
   run(['bash','-c',script,str(P)])
   receipt=R/'photon_26948_outputs/26948_REAL_GLSL_SPIRV_COMPILER.txt'
   if not receipt.is_file() or 'PASS 26948 real pinned GLES/SPIR-V current three shader sources' not in receipt.read_text():fail('26948 unchanged shader compiler did not pass')
   for p in EXPECTED:
    if sha(R/p) not in receipt.read_text():fail('26948 original real compiler omitted CURRENT 26950 B shader '+p)
  print('PASS historical 26948 pinned GLSL/SPIR-V compiler body on current source, original old payload validator')
 except Exception as exc:print(str(exc),file=sys.stderr);sys.exit(1)
