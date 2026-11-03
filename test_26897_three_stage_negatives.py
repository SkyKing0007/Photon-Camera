#!/usr/bin/env python3
"""26897 single-trigger and original 17-stage runner execution-contract guard."""
from pathlib import Path
import sys,re,subprocess,hashlib
R=Path(__file__).resolve().parent
w=R/'.github/workflows/build-26897-iris-rawr.yml'
if not w.exists():w=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26897-iris-rawr.yml'
s=w.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
assert s[a:b]=="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26897.txt'\n"
for name in ('generate_26897_build.py','handoff_payload_26897/**','.github/workflows/build-26897-iris-rawr.yml'):
 tam=s[:b]+f"      - '{name}'\n"+s[b:]
 assert tam[a:tam.index('  workflow_dispatch:',a)]!=s[a:b]
tr=R/'TRIGGER_26897.txt'
if not tr.exists():tr=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26897.txt'
assert tr.read_bytes()==b'RUN_26897_INDEPENDENT_MOTION_DNG_SABRE_BEFORE_B_V1\n'
for wrong in ('RUN_26896_PIXEL_MOTION_GPU_BUDGET_SPEKTRA_NATIVE_RES_AND_SAVE_V4','RUN_26897_INDEPENDENT_MOTION_DNG_SABRE_BEFORE_B_V2','RUN_26897_INDEPENDENT_MOTION_DNG_SABRE_BEFORE_B_V1 '):
 assert tr.read_text().strip()!=wrong
s1=(R/'26897_STAGE_1_UPLOAD_PATHS.txt').read_text().splitlines()
s2=(R/'26897_STAGE_2_UPLOAD_PATHS.txt').read_text().splitlines()
s3=(R/'26897_STAGE_3_UPLOAD_PATHS.txt').read_text().splitlines()
assert s2==['.github/workflows/build-26897-iris-rawr.yml'] and s3==['TRIGGER_26897.txt']
assert not set(s1)&set(s2+s3)
assert set(s1)|set(s2)|set(s3)==set((R/'26897_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
if sys.argv[1:]==['--runner']:
 f=R/'build_26897_iris_rawr.sh'
 if not f.exists():f=R.parent.parent/'generate_test/build_26897_iris_rawr.sh'
 t=f.read_text();names=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
 assert tuple(x for x in re.findall(r'\n([a-z_]+)\(\)\{',t) if x in names)==names
 assert t.count('python3 -S verify_26897.py patch "$BASE" "$CAND" 26897_FORWARD_FULL_INDEX.patch 26897_ROLLBACK_FULL_INDEX.patch')==2
 for n,cmd in (('compile_languages','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac'),('compile_native',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'"),('assemble','./gradlew :app:assembleDebug --stacktrace')):
  b=t[t.index('\n'+n+'(){'):];b=b[:b.index('\n}')];assert b.count(cmd)==1
 assert '26895_historical_candidate_app_source.tar.gz' in t and '26897_candidate_app_source.tar.gz' in t
 assert subprocess.run(['bash','-n',str(f)],capture_output=True).returncode==0
 assert 'VERSION_BUILD=26895' in t and 'VERSION_BUILD=26897' in t
 assert '2022 protected' in t
 print('PASS 26897 generated 17-stage runner, real compiler calls, 2 version gates, parent historical replay')
else:assert sys.argv[1:]==[]
print('PASS 26897 one trigger, stage partition, negative alterations rejected')
