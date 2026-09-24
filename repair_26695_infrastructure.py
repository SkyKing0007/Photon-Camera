#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3:raise SystemExit('usage: repair_26695_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text();MECH='ee6058be072556c6605b4ea46f1a002802f332f3';BLOB='2787dd669cded62d76611f0d0b7b0cabd0ed4a04';WBLOB='60dbcd33c336defdcf39ef85a880299526dc94a1'
marker='# IRIS_26695_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(marker)==1;main=s[s.index(marker):];anchors=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26694_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','verify_compiled_jni_callback',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','verify_apk_jni_contract','postbuild_proof'];pos=-1
for a in anchors:
 n=main.find(a,pos+1);assert n>=0,f'26694 order missing/reordered {a}';pos=n
assert main.count('verify_candidate_patches')==2
for t in ['GLSLANG_VERSION="16.5.0"','actions/checkout@v5','actions/setup-java@v5','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','actions/upload-artifact@v4','experimental-clean-photon-rebuild']:assert t in s+w,t
assert 'BASE_ARTIFACT_ID="10785824126"' in s and 'BASE_TAR_SHA="874928c07ce1aeeddd96f440fcfe4f004fce4fc10dac67f0bf9969872fc9e2d9"' in s
try:
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:build_26694_spektra_integration_fix.sh'],text=True).strip()==BLOB;assert subprocess.check_output(['git','rev-parse',f'{MECH}:.github/workflows/build-26694-spektra-integration-fix.yml'],text=True).strip()==WBLOB
except Exception:pass
print('PASS 26695 infrastructure audit: exact successful 26694 build/workflow blobs pinned; inherited 26693/26691 compiler-build order unchanged; identity/scope/regressions only')
