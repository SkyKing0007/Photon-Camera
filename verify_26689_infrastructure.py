#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26689_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2])
MECH='166e71a1794157d4cd430d231584d832df5e782e'
assert subprocess.check_output(['git','rev-parse',f'{MECH}:build_26688_r1_spektra_cpu_raw_frontend.sh'],text=True).strip()=='74a29d7f9a654ed85c49b2df11c8e6afdf14b48e'
assert subprocess.check_output(['git','rev-parse',f'{MECH}:.github/workflows/build-26688-r1-spektra-cpu-raw-frontend.yml'],text=True).strip()=='a9f94aacf9c9f4f3f289d32678ec24b41c260200'
s=build.read_text(); w=workflow.read_text()
# 26689 R1.1 native-config failure regression: the inherited 26681 CMake contract
# is a stable interface, not a build-number identity. Successful 26688 exports this
# exact variable and the authority-seeded CMakeLists reads this exact name.
stable_glslang='IRIS26681_SPEKTRA_GLSLANG'
assert s.count(f'export {stable_glslang}=\"$compiler\"')==1, 'stable 26681 glslang export missing/duplicated'
assert s.count(f'$'+stable_glslang)==2, 'stable 26681 glslang shell references must remain exact'
assert s.count(f'local compiler=\"${stable_glslang}\" outspv=')==1, 'stable 26681 glslang consumer missing/duplicated'
assert 'IRIS26689_SPEKTRA_GLSLANG' not in s, '26689 identity must not replace inherited CMake glslang contract'
for token in ['GLSLANG_VERSION=\"16.5.0\"','GLSLANG_ARCHIVE_SHA=\"b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657\"','glslang-16.5.0-linux-x86_64-release.tar.gz']:
 assert token in s, f'pinned glslang authority drift: {token}'
# Exact successful-26688 execution order preserved.
anchors=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26688_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',"':app:buildCMakeDebug[arm64-v8a]'","':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
pos=-1
for a in anchors:
 n=s.find(a,pos+1); assert n>=0,f'26688-order anchor missing/reordered: {a}'; pos=n
for token in ['actions/checkout@v5','actions/setup-java@v5','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','actions/upload-artifact@v4']:
 assert token in w,token
assert 'experimental-clean-photon-rebuild' in w
print('PASS 26689 infrastructure audit: successful-26688 build/workflow blobs pinned; compiler/build ordering unchanged')
