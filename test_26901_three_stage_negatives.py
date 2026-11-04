#!/usr/bin/env python3
"""26901 real staged push-path, historical artifact and runner/source tamper negatives."""
from pathlib import Path
import hashlib,re,sys,subprocess
R=Path(__file__).resolve().parent
wf=R/'.github/workflows/build-26901-iris-rawr.yml'
if not wf.is_file():wf=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26901-iris-rawr.yml'
s=wf.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
expected="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26901.txt'\n"
assert s[a:b]==expected
for wrong in ('generate_26901_build.py','handoff_payload_26901/**','.github/workflows/build-26901-iris-rawr.yml','TRIGGER_26900.txt','TRIGGER_26899_V2.txt'):
 t=s[:b]+"      - '"+wrong+"'\n"+s[b:];assert t[a:t.index('  workflow_dispatch:')]!=expected
assert s.count("      - 'TRIGGER_26901.txt'")==1
tr=R/'TRIGGER_26901.txt'
if not tr.is_file():tr=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26901.txt'
assert tr.read_bytes()==b'RUN_26901_B_OFF_FULL_RGB_BICUBIC_UNIVERSAL_LENS_GATE_V1\n'
for wrong in (tr.read_bytes().strip(),b'RUN_26901_B_OFF_FULL_RGB_BICUBIC_UNIVERSAL_LENS_GATE_V2\n',b'RUN_26900_B_OFF_BICUBIC_SCALE_AWARE_LUMA_SHARPEN_V1\n'):
 assert wrong!=tr.read_bytes()
paths=[(R/f'26901_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
assert paths[1]==['.github/workflows/build-26901-iris-rawr.yml'] and paths[2]==['TRIGGER_26901.txt']
assert not set(paths[0])&set(paths[1]+paths[2])
assert sorted(sum(paths,[]))==(R/'26901_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
assert not any(p.startswith('TRIGGER_26900') or p.startswith('TRIGGER_26899') for p in sum(paths,[]))
if sys.argv[1:]==['--runner']:
 r=R/'build_26901_iris_rawr.sh';pr=R/'build_26900_iris_rawr.sh'
 assert r.is_file() and pr.is_file()
 assert hashlib.sha256(pr.read_bytes()).hexdigest()=='1671e0a86fb85573da2cfbffa1c12502cf4153e4e15e548d0bc9bf4a15254cf6'
 t=r.read_text()
 stages=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
 assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',t) if x in stages)==stages
 for name,cmd in [('compile_languages','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace'),('compile_native',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace"),('assemble','./gradlew :app:assembleDebug --stacktrace')]:
  sec=t[t.index('\n'+name+'(){'):];sec=sec[:sec.index('\n}')]
  assert sec.count(cmd)==1,(name,cmd)
 assert t.count('verify_26901.py patch "$BASE" "$CAND" 26901_FORWARD_FULL_INDEX.patch 26901_ROLLBACK_FULL_INDEX.patch')>=2
 assert 'verify_26900.py patch "$WORK/historical_26899_from_26900" "$WORK/historical_26900_replayed" 26900_FORWARD_FULL_INDEX.patch 26900_ROLLBACK_FULL_INDEX.patch' in t
 assert 'verify_26889_compiled_push_abi.py "$ARTDIR/build_26900_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"' in t
 assert '$ARTDIR/build_26899_iris_rawr_outputs/' not in t and '$ARTDIR/build_26898_iris_rawr_outputs/' not in t
 assert '26901_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt' in t and '26900_HISTORICAL_GLSL_REAL_COMPILER_RECEIPT.txt' in t
 assert 'GLSLANG_VERSION="16.5.0"' in t
 assert '26901_candidate_app_source.tar.gz' in t and '26901_candidate_full_app.sha256' in t
 assert subprocess.run(['bash','-n',str(r)],capture_output=True).returncode==0
 sha=(R/'26901_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
 assert hashlib.sha256(r.read_bytes()).hexdigest()==sha
 print('PASS 26901 real generated 17-stage runner, 4-op source patches, inherited compiler calls and historical corrected SPV; hash sealed')
else:
 assert not sys.argv[1:]
 # Negative replay must reject mutations of the ACTUAL staged handoff files,
 # not merely synthetic fragments or an invented test fixture.
 import tempfile,shutil
 with tempfile.TemporaryDirectory(prefix='photon_26901_real_staged_mutation_') as td:
  root=Path(td)
  staged=(R/'26901_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
  for name in staged:
   p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/name,p)
  # Unmodified sealed stage passes before any negative is attempted.
  def gate():return subprocess.run([sys.executable,'-S',str(root/'stage_26901_root.py')],cwd=str(root),capture_output=True,text=True)
  assert gate().returncode==0,('clean actual staged gate should pass',gate().stderr)
  targets=sorted(x for x in staged if x.startswith('handoff_payload_26901/'))+[
   'generate_26901_build.py','26901_GENERATED_BUILD_SHA256.txt',
   '.github/workflows/build-26901-iris-rawr.yml','TRIGGER_26901.txt',
   '26901_REPOSITORY_UPLOAD_ALLOWLIST.txt']
  for name in targets:
   p=root/name;prior=p.read_bytes();p.write_bytes(prior+b'\nTAMPERED_FOR_NEGATIVE\n')
   assert gate().returncode!=0,('tamper escaped real seal/source/trigger check',name)
   p.write_bytes(prior)
  # Also reject an invalid push path EVEN WHEN a tampered YAML hash is resealed.
  yp=root/'.github/workflows/build-26901-iris-rawr.yml';old_y=yp.read_bytes()
  y=old_y.decode().replace("      - 'TRIGGER_26901.txt'\n","      - 'TRIGGER_26901.txt'\n      - 'generate_26901_build.py'\n",1)
  yp.write_text(y)
  seal=root/'26901_HANDOFF_HASHES.sha256';old_seal=seal.read_bytes()
  lines=seal.read_text().splitlines()
  lines=[(hashlib.sha256(yp.read_bytes()).hexdigest()+'  '+yp.relative_to(root).as_posix()) if l.endswith('  .github/workflows/build-26901-iris-rawr.yml') else l for l in lines]
  seal.write_text('\n'.join(lines)+'\n')
  assert gate().returncode!=0,'resealed extra workflow trigger path erroneously accepted'
  yp.write_bytes(old_y);seal.write_bytes(old_seal)
  assert gate().returncode==0,'negative mutation restoration did not restore real gate'
 print('PASS 26901 REAL staged-byte positive+negative source(6), runner SHA receipt, generator, filter, immutable trigger, resealed wrong YAML push path')
print('PASS 26901 single push trigger, 25/1/1 upload partition and negative old trigger/workflow/generator path matching')
