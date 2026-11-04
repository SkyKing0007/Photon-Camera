#!/usr/bin/env python3
"""26902 EXACT final source, runner, workflow, trigger and hash-negative checks.
All mutations apply to real staged bytes copied into temporary clean roots.
"""
from pathlib import Path
import hashlib,re,sys,subprocess,tempfile,shutil
R=Path(__file__).resolve().parent
WF=R/'.github/workflows/build-26902-iris-rawr.yml'
if not WF.is_file():WF=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26902-iris-rawr.yml'
s=WF.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
expected="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26902.txt'\n"
assert s[a:b]==expected
for wrong in ('generate_26902_build.py','handoff_payload_26902/**','.github/workflows/build-26902-iris-rawr.yml','TRIGGER_26901.txt','TRIGGER_26900.txt','TRIGGER_26899_V2.txt'):
 mutated=s[:b]+"      - '"+wrong+"'\n"+s[b:]
 assert mutated[a:mutated.index('  workflow_dispatch:')]!=expected
assert s.count("      - 'TRIGGER_26902.txt'")==1
TR=R/'TRIGGER_26902.txt'
if not TR.is_file():TR=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26902.txt'
assert TR.read_bytes()==b'RUN_26902_B_OFF_LENS_RELATIVE_GENTLE_SHARPEN_V1\n'
for bad in (TR.read_bytes().strip(),b'RUN_26902_B_OFF_LENS_RELATIVE_GENTLE_SHARPEN_V2\n',b'RUN_26901_B_OFF_FULL_RGB_BICUBIC_UNIVERSAL_LENS_GATE_V1\n'):
 assert bad!=TR.read_bytes()
paths=[(R/f'26902_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
assert len(paths[0])==22 and paths[1]==['.github/workflows/build-26902-iris-rawr.yml'] and paths[2]==['TRIGGER_26902.txt']
assert not set(paths[0])&set(paths[1]+paths[2])
assert sorted(sum(paths,[]))==(R/'26902_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert not any(x.startswith('TRIGGER_26901') or x.startswith('TRIGGER_26900') for x in sum(paths,[]))
if sys.argv[1:]==['--runner']:
 current=R/'build_26902_iris_rawr.sh';parent=R/'build_26901_iris_rawr.sh'
 assert current.is_file() and parent.is_file()
 assert hashlib.sha256(parent.read_bytes()).hexdigest()=='bcdd8bb524e5410808b4ecf2ef27760c1c28412d18389ee676c55be3509db6d9'
 t=current.read_text()
 stages=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
 assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',t) if x in stages)==stages
 for n,cmd in [('compile_languages','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace'),('compile_native',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace"),('assemble','./gradlew :app:assembleDebug --stacktrace')]:
  sec=t[t.index('\n'+n+'(){'):];sec=sec[:sec.index('\n}')]
  assert sec.count(cmd)==1,(n,cmd)
 assert t.count('verify_26902.py patch "$BASE" "$CAND" 26902_FORWARD_FULL_INDEX.patch 26902_ROLLBACK_FULL_INDEX.patch')>=2
 assert 'verify_26901.py patch "$WORK/historical_26900_from_26901" "$WORK/historical_26901_replayed" 26901_FORWARD_FULL_INDEX.patch 26901_ROLLBACK_FULL_INDEX.patch' in t
 assert 'verify_26889_compiled_push_abi.py "$ARTDIR/build_26901_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"' in t
 assert '$ARTDIR/build_26900_iris_rawr_outputs/' not in t and '$ARTDIR/build_26899_iris_rawr_outputs/' not in t
 assert '26901_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt' in t
 assert '26902_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt' in t
 assert 'GLSLANG_VERSION="16.5.0"' in t
 assert '26902_candidate_app_source.tar.gz' in t and '26902_candidate_full_app.sha256' in t
 assert 'RUNTIME_ARTIFACT_ID="13297535320"; RUNTIME_ACTIONS_RUN="41774585178"' in t
 assert 'RUNTIME_TAR_SHA="759109721bfc05c70c85d215542333a667107f0e652531ec9966768e8658a615"' in t
 assert 'RUNTIME_ARTIFACT_SHA="6de45e5fa5c26e581c9d010175ed8691941ce14122b64ef13fee2020e70c68a5"' in t
 assert 'VERSION_NAME="0.9726902"; VERSION_BUILD="26902"' in t
 assert subprocess.run(['bash','-n',str(current)],capture_output=True).returncode==0
 sha=(R/'26902_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
 assert hashlib.sha256(current.read_bytes()).hexdigest()==sha
 assert s.count('--expected-sha256 '+sha)==1
 print('PASS 26902 real deterministic exact 17-stage runner, historical corrected SPV and ALL inherited real compiler/assemble invocations, 4-operand patch stage')
else:
 assert not sys.argv[1:]
 with tempfile.TemporaryDirectory(prefix='photon_26902_ACTUAL_STAGED_BYTES_') as td:
  root=Path(td);staged=(R/'26902_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
  for name in staged:
   p=root/name;p.parent.mkdir(parents=True,exist_ok=True)
   src=R/name
   if not src.is_file():src=WF if name.startswith('.github/workflows/') else TR
   shutil.copy2(src,p)
  def gate():return subprocess.run([sys.executable,'-S',str(root/'stage_26902_root.py')],cwd=str(root),capture_output=True,text=True)
  clean=gate();assert clean.returncode==0,('UNMODIFIED real staged bytes must pass',clean.stderr,clean.stdout)
  targets=sorted(x for x in staged if x.startswith('handoff_payload_26902/'))+['generate_26902_build.py','26902_GENERATED_BUILD_SHA256.txt','.github/workflows/build-26902-iris-rawr.yml','TRIGGER_26902.txt','26902_REPOSITORY_UPLOAD_ALLOWLIST.txt','verify_26902.py','test_26902_modes.py']
  for name in targets:
   p=root/name;prior=p.read_bytes();p.write_bytes(prior+b'\nTAMPER_ACTUAL_HANDOFF_BYTES\n')
   assert gate().returncode!=0,('real seal did not reject mutation',name)
   p.write_bytes(prior)
  # Re-sealed forbidden automatic trigger must still be rejected semantically.
  yp=root/'.github/workflows/build-26902-iris-rawr.yml';old_y=yp.read_bytes()
  yp.write_text(yp.read_text().replace("      - 'TRIGGER_26902.txt'\n","      - 'TRIGGER_26902.txt'\n      - 'generate_26902_build.py'\n",1))
  seal=root/'26902_HANDOFF_HASHES.sha256';old_seal=seal.read_bytes()
  seal.write_text(''.join(hashlib.sha256(yp.read_bytes()).hexdigest()+'  .github/workflows/build-26902-iris-rawr.yml\n' if l.endswith('  .github/workflows/build-26902-iris-rawr.yml') else l+'\n' for l in seal.read_text().splitlines()))
  assert gate().returncode!=0,'resealed extra workflow trigger was not rejected'
  yp.write_bytes(old_y);seal.write_bytes(old_seal)
  assert gate().returncode==0,'restored actual staged bytes failed'
 print('PASS 26902 actual 22+1+1 staged bytes; positive and ALL source/runner/generator/validator/trigger/workflow tamper negatives; resealed forbidden extra trigger')
print('PASS 26902 sole Stage3 trigger, previous workflows/generators never auto-trigger')
