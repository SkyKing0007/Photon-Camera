#!/usr/bin/env python3
from pathlib import Path
import subprocess, sys
if len(sys.argv)!=3: raise SystemExit('usage: verify_26689_infrastructure.py BUILD_SCRIPT WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2])
MECH='166e71a1794157d4cd430d231584d832df5e782e'
assert subprocess.check_output(['git','rev-parse',f'{MECH}:build_26688_r1_spektra_cpu_raw_frontend.sh'],text=True).strip()=='74a29d7f9a654ed85c49b2df11c8e6afdf14b48e'
assert subprocess.check_output(['git','rev-parse',f'{MECH}:.github/workflows/build-26688-r1-spektra-cpu-raw-frontend.yml'],text=True).strip()=='a9f94aacf9c9f4f3f289d32678ec24b41c260200'
s=build.read_text(); w=workflow.read_text()
# Exact successful-26688 execution order preserved.
anchors=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26688_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live',':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',"':app:buildCMakeDebug[arm64-v8a]'","':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED',':app:assembleDebug','postbuild_proof']
pos=-1
for a in anchors:
 n=s.find(a,pos+1); assert n>=0,f'26688-order anchor missing/reordered: {a}'; pos=n
for token in ['actions/checkout@v5','actions/setup-java@v5','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','actions/upload-artifact@v4']:
 assert token in w,token
assert 'experimental-clean-photon-rebuild' in w
print('PASS 26689 infrastructure audit: successful-26688 build/workflow blobs pinned; compiler/build ordering unchanged')
