#!/usr/bin/env python3
"""Immutable trigger and deterministic executed-runner 17-stage negative checks."""
from pathlib import Path
import sys,re,hashlib,subprocess
R=Path(__file__).resolve().parent
f=R/'.github/workflows/build-26899-iris-rawr.yml'
if not f.exists():f=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26899-iris-rawr.yml'
s=f.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
push="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26899.txt'\n"
assert s[a:b]==push
for wrong in ('generate_26899_build.py','handoff_payload_26899/**','.github/workflows/build-26899-iris-rawr.yml'):
 assert (s[:b]+"      - '"+wrong+"'\n"+s[b:])[a:].split('  workflow_dispatch:')[0]!=push
tr=R/'TRIGGER_26899.txt'
if not tr.exists():tr=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26899.txt'
assert tr.read_bytes()==b'RUN_26899_B_OFF_ONLY_ZOOM_LUMA_SHARPEN_V1\n'
for wrong in (b'RUN_26899_B_OFF_ONLY_ZOOM_LUMA_SHARPEN_V2\n',b'RUN_26899_B_OFF_ONLY_ZOOM_LUMA_SHARPEN_V1 ',b'RUN_26898_ISOLATED_SABRE_DNG_BEFORE_B_JPEG_V1\n'):
 assert wrong!=tr.read_bytes()
paths=[(R/f'26899_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
assert paths[1]==['.github/workflows/build-26899-iris-rawr.yml']
assert paths[2]==['TRIGGER_26899.txt']
assert not set(paths[0])&set(paths[1]+paths[2])
assert set(paths[0]+paths[1]+paths[2])==set((R/'26899_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines())
if sys.argv[1:]==['--runner']:
 runner=R/'build_26899_iris_rawr.sh'
 if not runner.exists():runner=R.parent.parent.parent/'build_26899_iris_rawr.sh'
 if not runner.exists():runner=Path('/mnt/data/photon26899work/build_26899_iris_rawr.sh')
 t=runner.read_text()
 stages=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
 assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',t) if x in stages)==stages
 for name,cli in (('compile_languages','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace'),('compile_native',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace"),('assemble','./gradlew :app:assembleDebug --stacktrace')):
  sec=t[t.index('\n'+name+'(){'):];sec=sec[:sec.index('\n}')]
  assert sec.count(cli)==1,(name,cli)
 assert t.count('verify_26899.py patch "$BASE" "$CAND" 26899_FORWARD_FULL_INDEX.patch 26899_ROLLBACK_FULL_INDEX.patch')==2
 assert t.count('verify_26898.py patch "$WORK/historical_26897_from_26898" "$WORK/historical_26898_replayed" 26898_FORWARD_FULL_INDEX.patch 26898_ROLLBACK_FULL_INDEX.patch')>=2
 assert '26898_historical_candidate_app_source.tar.gz' in t and '26899_candidate_app_source.tar.gz' in t
 assert '26899_NEW_SHADER_GLSLANG_16_5_0.txt' in t and 'GLSLANG_VERSION="16.5.0"' in t
 assert subprocess.run(['bash','-n',str(runner)],capture_output=True).returncode==0
 expected=(R/'26899_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
 assert hashlib.sha256(runner.read_bytes()).hexdigest()==expected
 print('PASS exact executed-successful 26898 runner -> 26899 17 same stages, pinned real compilers, two-source historical patch commands, current pinned shader')
else:assert sys.argv[1:]==[]
print('PASS 26899 3-stage separated upload, exact-byte trigger and excluded path filter negative cases')
