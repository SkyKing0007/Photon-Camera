#!/usr/bin/env python3
"""New historical/future trigger, runner and negative SHA tamper contracts."""
from pathlib import Path
import sys,re,subprocess,hashlib
R=Path(__file__).resolve().parent
workflow=R/'.github/workflows/build-26898-iris-rawr.yml'
if not workflow.exists():workflow=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26898-iris-rawr.yml'
s=workflow.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
expected="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26898.txt'\n"
assert s[a:b]==expected
for name in ('generate_26898_build.py','handoff_payload_26898/**','.github/workflows/build-26898-iris-rawr.yml'):
 tam=s[:b]+f"      - '{name}'\n"+s[b:]
 assert tam[a:tam.index('  workflow_dispatch:',a)]!=expected
tr=R/'TRIGGER_26898.txt'
if not tr.exists():tr=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26898.txt'
assert tr.read_bytes()==b'RUN_26898_ISOLATED_SABRE_DNG_BEFORE_B_JPEG_V1\n'
for wrong in (b'RUN_26898_ISOLATED_SABRE_DNG_BEFORE_B_JPEG_V2\n',b'RUN_26897_INDEPENDENT_MOTION_DNG_SABRE_BEFORE_B_V1\n',b'RUN_26898_ISOLATED_SABRE_DNG_BEFORE_B_JPEG_V1 '):
 assert tr.read_bytes()!=wrong
paths=[(R/f'26898_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
assert paths[1]==['.github/workflows/build-26898-iris-rawr.yml'] and paths[2]==['TRIGGER_26898.txt']
assert not set(paths[0]) & set(paths[1]+paths[2])
assert set(paths[0]+paths[1]+paths[2])==set((R/'26898_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
if sys.argv[1:]==['--runner']:
 f=R/'build_26898_iris_rawr.sh'
 if not f.exists():f=R.parent.parent/'generate_test/build_26898_iris_rawr.sh'
 runner=f.read_text();stages=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
 assert tuple(n for n in re.findall(r'(?m)^([a-z_]+)\(\)\{',runner) if n in stages)==stages
 for n,cli in (('compile_languages','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace'),('compile_native',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace"),('assemble','./gradlew :app:assembleDebug --stacktrace')):
  body=runner[runner.index('\n'+n+'(){'):];body=body[:body.index('\n}')]
  assert body.count(cli)==1,(n,'real compiler CLI mismatch')
 assert runner.count('verify_26898.py patch "$BASE" "$CAND" 26898_FORWARD_FULL_INDEX.patch 26898_ROLLBACK_FULL_INDEX.patch')==2
 assert '26897_historical_candidate_app_source.tar.gz' in runner and '26898_candidate_app_source.tar.gz' in runner
 assert runner.count('verify_26897.py candidate "$WORK/historical_26895_from_26897" "$WORK/historical_26897_replayed"')>=2
 assert subprocess.run(['bash','-n',str(f)],capture_output=True).returncode==0
 assert 'VERSION_BUILD=26897' in runner and 'VERSION_BUILD=26898' in runner
 assert '2020 protected' in runner
 sha=hashlib.sha256(f.read_bytes()).hexdigest()
 assert sha==(R/'26898_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
 print('PASS 26898 EXACT executed 26897 17-stage inherited compiler mechanics, actual historical bytes, future compiled 26898 sealed source')
else:assert sys.argv[1:]==[]
print('PASS 26898 single exact trigger, historical stage order, payload path partition, negative filter cases')
