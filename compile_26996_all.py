#!/usr/bin/env python3
"""Re-run the actual successful 26989 compiler suite against the sealed 26996 live candidate.
Only the live-source guard and current inventory advance; extraction, compiler,
optimizer, validator, exact counts and diagnostics are the original executed inputs.
The original receipts keep their literal compiler labels and are freshly generated.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,shutil,os
R=Path(__file__).resolve().parent
OLD=R/'photon_26989_outputs'; OUT=R/'photon_26996_outputs'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
blob=lambda p:hashlib.sha1(b'blob '+str(p.stat().st_size).encode()+b'\0'+p.read_bytes()).hexdigest()
def verify_reused(root=R):
 pins=json.loads((R/'26996_REUSED_EXECUTABLES.json').read_text())
 for name,h in pins.items():
  p=root/name
  if not p.is_file() or blob(p)!=h:raise RuntimeError('missing/changed successful executable or inventory '+name)
 print('PASS exact reused successful 26989 executable and inventory Git blobs')
def verify_compiler_transform(original):
 data=original.read_bytes(); old=b'test_26989_source.py --live'
 assert blob(original)=='22adb72cb813f483b5da3756ba4bff494b42029c' and data.count(old)==2
 assert (R/'compile_26996_shaders.sh').read_bytes()==data.replace(old,b'test_26996_source.py --live').replace(b'verify_26989_v6_current_glsl.py',b'verify_26996_v6_current_glsl.py').replace(b'26989_V6_CURRENT_SHADER_INVENTORY.json',b'26996_V6_CURRENT_SHADER_INVENTORY.json')
 auditor=R/'verify_26989_v6_current_glsl.py'
 assert blob(auditor)=='83591c227f0e815efef3e926d9176f66aa97e614'
 assert (R/'verify_26996_v6_current_glsl.py').read_bytes()==auditor.read_bytes().replace(b'26989_V6_CURRENT_SHADER_INVENTORY.json',b'26996_V6_CURRENT_SHADER_INVENTORY.json')
 subprocess.run(['bash','-n',str(R/'compile_26996_shaders.sh')],check=True)
def run(*cmd):subprocess.run(list(cmd),cwd=R,check=True)
RECEIPTS={
 '26989_REAL_GLSL_SPIRV_COMPILER.txt':('PASS actual 26974 24/24 C GLES','PASS inherited historical 24/24 and actual current 299/299 26989 donor/Iris C shader compilation'),
 '26989_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt':('PASS 26989 physical current 299/299 static donor/Iris C ESSL GLSL + SPIR-V opt/val',),
 '26989_CON_REAL_GLSL_SPIRV_COMPILER.txt':('PASS 26989 C ON 14/14 static shader stages real GLSL/SPIR-V opt/val',),
 '26989_NATIVE_REAL_GLSL_SPIRV_COMPILER.txt':('PASS 59/59 private Vulkan variants real compile/opt/val',),
 '26989_PREVIEW_REAL_GLSL.txt':('PASS exact 26989 runtime ESSL300 OES preview pair compile/link',)}
def verify_receipts():
 rec=json.loads((OUT/'26996_CURRENT_SHADER_EXECUTION.json').read_text())
 assert rec['candidate_manifest_sha256']==sha(R/'26996_EXPECTED_FULL_APP.sha256')
 assert rec['reused_executables_sha256']==sha(R/'26996_REUSED_EXECUTABLES.json')
 assert rec['compiler_sha256']==sha(R/'compile_26996_shaders.sh')
 for old,phrases in RECEIPTS.items():
  p=OUT/old.replace('26989','26996',1)
  assert rec['receipts'][p.name]==sha(p) and all(phrase in p.read_text() for phrase in phrases),p
 p=OUT/'26996_SHADOW_REAL_GLSL_SPIRV.txt'
 assert rec['receipts'][p.name]==sha(p) and 'PASS 26996 expanded RAW adjustment pair original/310 GLSL and SPIR-V opt/val' in p.read_text()
if __name__=='__main__':
 verify_reused();verify_compiler_transform(R/'compile_26989_shaders.sh')
 assert not OLD.exists(),'stale 26989 compiler output cannot be accepted as new execution'
 run(sys.executable,'-S','test_26996_source.py','--live')
 run('bash','compile_26996_shaders.sh');run('bash','compile_26989_con_shaders.sh')
 run(sys.executable,'-S','verify_26996_native_glsl.py','--compile');run(sys.executable,'-S','verify_26989_preview_glsl.py','--compile')
 for old,phrases in RECEIPTS.items():
  assert (OLD/old).is_file() and all(p in (OLD/old).read_text() for p in phrases),old
 OUT.mkdir(exist_ok=True)
 # Retain exact compiler output bytes, including original tool labels and phase logs.
 for p in OLD.iterdir():
  dst=OUT/p.name.replace('26989','26996',1);assert not dst.exists(),dst;shutil.move(str(p),str(dst))
 OLD.rmdir()
 rec={'candidate_manifest_sha256':sha(R/'26996_EXPECTED_FULL_APP.sha256'),'reused_executables_sha256':sha(R/'26996_REUSED_EXECUTABLES.json'),'compiler_sha256':sha(R/'compile_26996_shaders.sh'),'receipts':{old.replace('26989','26996',1):sha(OUT/old.replace('26989','26996',1)) for old in RECEIPTS}}
 (OUT/'26996_CURRENT_SHADER_EXECUTION.json').write_text(json.dumps(rec,indent=2)+'\n')
 run(sys.executable,'-S','compile_26996_shadow_expanded.py')
 rec['receipts']['26996_SHADOW_REAL_GLSL_SPIRV.txt']=sha(OUT/'26996_SHADOW_REAL_GLSL_SPIRV.txt')
 (OUT/'26996_CURRENT_SHADER_EXECUTION.json').write_text(json.dumps(rec,indent=2)+'\n')
 verify_receipts();run(sys.executable,'-S','test_26996_source.py','--live')
 print('PASS fresh 26996 real shader compilation using exact previous compilers, current source guard and physical receipt hashes')
