#!/usr/bin/env python3
"""Replay entire original real 26943/44/48/49 GLSL compiler bodies against current source.
Historical assertions read their unchanged sealed payload; live assertions use exact 26952.
Compiler bodies are SHA/Git-blob-verified, changed only at incompatible historical preflight calls.
"""
import hashlib,subprocess,sys
from build_26952_incremental import R,sha,parse,fail

def run(args):subprocess.run(args,cwd=R,check=True)
def gitblob(data):return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def exec_shell(file,expect,changes):
 original=(R/file).read_bytes()
 if gitblob(original)!=expect:fail('original historical real GLSL executable body changed '+file)
 src=original.decode('utf-8');out=src
 for old,new in changes:
  if src.count(old)!=1 or new in src:fail('noncanonical historic preflight '+file+' '+old)
  out=out.replace(old,new,1)
 for old,new in reversed(changes):out=out.replace(new,old,1)
 if out!=src:fail('historical executable transformation changes compiler code '+file)
 script=src
 for old,new in changes:script=script.replace(old,new,1)
 run(['bash','-c',script,str(R/file)])

def main():
 if sys.argv[1:] not in (['43'],['44'],['48'],['49']):fail('usage: python3 replay_26952_inherited_glsl.py 43|44|48|49')
 v=sys.argv[1];old=parse(R/'26952_BASE_26951_FULL_APP.sha256');current=parse(R/'26952_EXPECTED_FULL_APP.sha256')
 if v=='43':
  run([sys.executable,'-S','test_26943_shader_contract.py','--payload'])
  run([sys.executable,'-S','test_26952_source.py','--live'])
  original=(R/'compile_26943_shaders.sh').read_bytes()
  if gitblob(original)!='95cecfd9a98a5a3a8ab3154e785e1d708f9dd876':fail('26943 original shader compiler changed')
  oldcall='python3 -S test_26943_shader_contract.py --live --extract'
  newcall='python3 -S replay_26952_26943_contract.py --live --extract'
  txt=original.decode()
  if txt.count(oldcall)!=1:fail('26943 compiler preflight changed')
  run(['bash','-c',txt.replace(oldcall,newcall,1),str(R/'compile_26943_shaders.sh')])
 elif v=='44':
  run([sys.executable,'-S','test_26944_shader_contract.py','--payload'])
  run([sys.executable,'-S','test_26952_source.py','--live'])
  exec_shell('compile_26944_shaders.sh','7b73fe7b353fdf2e45ba2fe0a79c2b476b59cd2f',[("python3 -S test_26944_shader_contract.py --live", "python3 -S test_26944_shader_contract.py --payload")])
 elif v=='48':
  run([sys.executable,'-S','build_26948_incremental.py','seal'])
  run([sys.executable,'-S','test_26948_sdr_hdr_math.py','--payload'])
  run([sys.executable,'-S','test_26952_source.py','--live'])
  exec_shell('compile_26948_shaders.sh','2e02b430e62790beaed47d7f0679c63622bab326',[("python3 -S test_26948_sdr_hdr_math.py --live", "python3 -S test_26948_sdr_hdr_math.py --payload")])
  receipt=R/'photon_26948_outputs/26948_REAL_GLSL_SPIRV_COMPILER.txt'
  if not receipt.is_file() or 'PASS 26948 real pinned GLES/SPIR-V current three shader sources' not in receipt.read_text():fail('26948 full pinned compiler missing')
  for p in ('app/src/main/assets/shaders/motionv2/render.glsl','app/src/main/assets/shaders/motionv2/gainmap.glsl'):
   if sha(R/p)!=current[p] or sha(R/p) not in receipt.read_text():fail('26948 historical compiler omitted ACTUAL current shader '+p)
 elif v=='49':
  p='compile_26949_shaders.sh'
  if sha(R/p)!='a38ca81d48161df62c606059a85d99e18424c7397b3e73cab3f57eea0a8c54d2':fail('successful original 26949 executable changed')
  source='app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt'
  if old[source]!=current[source] or sha(R/source)!=current[source]:fail('original post-AMaZE FCC altered')
  run([sys.executable,'-S','build_26949_incremental.py','seal'])
  run([sys.executable,'-S','test_26949_restore.py','--payload'])
  oldcall='python3 -S test_26949_restore.py --live';newcall='python3 -S test_26949_restore.py --payload'
  txt=(R/p).read_text()
  if txt.count(oldcall)!=1:fail('26949 historical compile validator altered')
  run(['bash','-c',txt.replace(oldcall,newcall,1),str(R/p)])
  receipt=R/'photon_26949_outputs/26949_REAL_GLSL_COMPILER.txt'
  if not receipt.is_file() or 'PASS 26949 real pinned runtime-expanded GLES300 post-AMaZE shader' not in receipt.read_text() or sha(R/source) not in receipt.read_text():fail('26949 real post-AMaZE shader receipt missing')
 print('PASS full inherited REAL GLSL 269'+v+', unchanged compiler body; restored 26952 source is current')
if __name__=='__main__':
 try:main()
 except Exception as e:print(str(e),file=sys.stderr);sys.exit(1)
