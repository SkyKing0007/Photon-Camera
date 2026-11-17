#!/usr/bin/env python3
"""Replay exact original 26948 real compiler, replacing ONLY its stale live-specific historical math assertion."""
import subprocess,sys,hashlib
from build_26951_incremental import R,parse,sha,fail
P=R/'compile_26948_shaders.sh'
BLOB='2e02b430e62790beaed47d7f0679c63622bab326'
OLD='python3 -S test_26948_sdr_hdr_math.py --live'
NEW='python3 -S test_26948_sdr_hdr_math.py --payload'
CURRENT=('app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl')
def check():
 b=P.read_bytes();git=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\x00'+b).hexdigest()
 if git!=BLOB:fail('26948 executable changed')
 s=b.decode()
 if s.count(OLD)!=1 or NEW in s:fail('26948 historical script no longer exact')
 old=parse(R/'26951_BASE_26949_FULL_APP.sha256');new=parse(R/'26951_EXPECTED_FULL_APP.sha256')
 for name in CURRENT:
  if old[name]==new[name]:fail('26951 required SDR source not changed '+name)
  if '--preflight' not in sys.argv and sha(R/name)!=new[name]:fail('26951 live SDR source wrong '+name)
 v=s.replace(OLD,NEW,1)
 if v.replace(NEW,OLD,1)!=s:fail('26948 compiler body rewrite forbidden')
 return v
if __name__=='__main__':
 try:
  script=check()
  if '--preflight' not in sys.argv:
   for args in ([sys.executable,'-S','build_26948_incremental.py','seal'],[sys.executable,'-S','test_26948_sdr_hdr_math.py','--payload'],[sys.executable,'-S','test_26951_highlight.py','--live']):subprocess.run(args,cwd=R,check=True)
   subprocess.run(['bash','-c',script,str(P)],cwd=R,check=True)
   receipt=R/'photon_26948_outputs/26948_REAL_GLSL_SPIRV_COMPILER.txt'
   if not receipt.is_file() or 'PASS 26948 real pinned GLES/SPIR-V current three shader sources' not in receipt.read_text():fail('26948 original real shader compiler failed')
   for p in CURRENT:
    if sha(R/p) not in receipt.read_text():fail('26948 original compiler omitted current SDR source '+p)
  print('PASS original 26948 full real compiler with sealed historic checker and current 26951 SDR')
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
