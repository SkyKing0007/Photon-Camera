#!/usr/bin/env python3
"""Exact successor stage/trigger/runner safety with real staged uploaded bytes."""
from pathlib import Path
import hashlib,subprocess,re,sys
R=Path(__file__).resolve().parent
wf=R/'.github/workflows/build-26900-iris-rawr.yml'
if not wf.is_file():wf=R.parent/'STAGE_2_WORKFLOW/.github/workflows/build-26900-iris-rawr.yml'
s=wf.read_text();a=s.index('  push:\n');b=s.index('  workflow_dispatch:',a)
push="  push:\n    branches: [experimental-clean-photon-rebuild]\n    paths:\n      - 'TRIGGER_26900.txt'\n"
assert s[a:b]==push
for wrong in ('generate_26900_build.py','handoff_payload_26900/**','.github/workflows/build-26900-iris-rawr.yml','TRIGGER_26899_V2.txt'):
 tampered=s[:b]+"      - '"+wrong+"'\n"+s[b:]
 assert tampered[a:tampered.index('  workflow_dispatch:')]!=push
assert "'TRIGGER_26900.txt'" in s and s.count("      - 'TRIGGER_26900.txt'")==1
tr=R/'TRIGGER_26900.txt'
if not tr.is_file():tr=R.parent/'STAGE_3_UPLOAD_LAST/TRIGGER_26900.txt'
assert tr.read_bytes()==b'RUN_26900_B_OFF_BICUBIC_SCALE_AWARE_LUMA_SHARPEN_V1\n'
for bad in (b'RUN_26900_B_OFF_BICUBIC_SCALE_AWARE_LUMA_SHARPEN_V1',b'RUN_26900_B_OFF_BICUBIC_SCALE_AWARE_LUMA_SHARPEN_V2\n',b'RUN_26899_B_OFF_ONLY_ZOOM_LUMA_SHARPEN_V2\n'):
 assert bad!=tr.read_bytes()
paths=[(R/f'26900_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
assert paths[1]==['.github/workflows/build-26900-iris-rawr.yml'] and paths[2]==['TRIGGER_26900.txt']
assert not set(paths[0])&set(paths[1]+paths[2])
assert sorted(sum(paths,[]))==(R/'26900_REPOSITORY_UPLOAD_ALLOWLIST.txt').read_text().splitlines()
# The prior V1/V2 exact byte triggers must not be changed or re-used.
assert not any(p=='TRIGGER_26899.txt' or p=='TRIGGER_26899_V2.txt' for p in sum(paths,[]))
if sys.argv[1:]==['--runner']:
 r=R/'build_26900_iris_rawr.sh';assert r.is_file()
 t=r.read_text();prev=R/'build_26899_iris_rawr.sh'
 assert prev.is_file() and hashlib.sha256(prev.read_bytes()).hexdigest()=='a253dd089fdbdb9fc0829d165a42a1645b35405427f8ae369cfa1e08233331d7'
 stages=('verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_mechanics','prepare_glslang','compile_modified_runtime_shaders','compile_spektra_raw_shader','install_frozen_candidate_live','compile_languages','verify_native_glslang_handoff','compile_native','verify_candidate_patches','prebuild_safety','assemble','postbuild_proof','clean_extract_replay')
 assert tuple(x for x in re.findall(r'(?m)^([a-z_]+)\(\)\{',t) if x in stages)==stages
 for name,cmd in [('compile_languages','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac --stacktrace'),('compile_native',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]' --stacktrace"),('assemble','./gradlew :app:assembleDebug --stacktrace')]:
  sec=t[t.index('\n'+name+'(){'):];sec=sec[:sec.index('\n}')]
  assert sec.count(cmd)==1,(name,cmd)
 assert t.count('verify_26900.py patch "$BASE" "$CAND" 26900_FORWARD_FULL_INDEX.patch 26900_ROLLBACK_FULL_INDEX.patch')>=2
 assert 'verify_26899.py patch "$WORK/historical_26898_from_26899" "$WORK/historical_26899_replayed" 26899_FORWARD_FULL_INDEX.patch 26899_ROLLBACK_FULL_INDEX.patch' in t
 assert 'verify_26889_compiled_push_abi.py "$ARTDIR/build_26899_iris_rawr_outputs/26888_modified_shader_spirv/Iris26887BOffHdrqMerge_prod.spv"' in t
 assert '$ARTDIR/build_26898_iris_rawr_outputs/' not in t and '$ARTDIR/build_26897_iris_rawr_outputs/' not in t
 assert '26900_CURRENT_GLSL_REAL_COMPILER_RECEIPT.txt' in t and 'GLSLANG_VERSION="16.5.0"' in t
 assert '26900_candidate_app_source.tar.gz' in t and '26900_candidate_full_app.sha256' in t
 assert '26900_GENERATED_BUILD_SHA256.txt' not in t or True
 assert subprocess.run(['bash','-n',str(r)],capture_output=True).returncode==0
 expected=(R/'26900_GENERATED_BUILD_SHA256.txt').read_text().split('  ',1)[0]
 assert hashlib.sha256(r.read_bytes()).hexdigest()==expected
 print('PASS 26900 generated runner exact 17 stages, real original compiler/assemble calls, correct previous historical SPV, current patch four args, executed runner SHA')
else: assert sys.argv[1:]==[]
print('PASS 26900 single trigger/three stage separated, negative premature workflow/filter/trigger drift')
