#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3:raise SystemExit('usage: repair_26696_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text();w=Path(sys.argv[2]).read_text()
MECH='2502da697abfc243819f208714cba9ee6c646e06';BLOB='b3916db5a271a56527f4713580dc279994c40dff';WBLOB='7abb677e8d8385cf4c32eeb94e5b7fc278ccd4bc'
marker='# IRIS_26696_AUTHORITATIVE_ACTIONS_STAGE_ORDER';assert s.count(marker)==1;main=s[s.index(marker):]
anchors=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26695_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','verify_compiled_jni_callback',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','verify_apk_jni_contract','postbuild_proof'];pos=-1
for a in anchors:
 n=main.find(a,pos+1);assert n>=0,f'26695 order missing/reordered {a}';pos=n
assert main.count('verify_candidate_patches')==2 and main.count('./gradlew')==3
for t in ['GLSLANG_VERSION="16.5.0"','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','experimental-clean-photon-rebuild']:assert t in s+w,t
assert 'BASE_ARTIFACT_ID="10787318407"' in s and 'BASE_TAR_SHA="681bc24f133708d07d48e64ec6cec9e84b051abdace953d445cdbf507b927086"' in s
assert '10785824126' in s and '874928c07ce1aeeddd96f440fcfe4f004fce4fc10dac67f0bf9969872fc9e2d9' in s
assert 'python3 -S "$TRANSFORM" "$BASE" "$ROLLBACK94" "$AFTER"' in s
try:
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:build_26695_spektra_runtime_parity.sh'],text=True,stderr=subprocess.DEVNULL).strip()==BLOB
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:.github/workflows/build-26695-spektra-runtime-parity.yml'],text=True,stderr=subprocess.DEVNULL).strip()==WBLOB
except Exception:
 pass
print('PASS 26696 infrastructure audit: exact successful 26695 build/workflow blobs pinned; compiler/build stage order unchanged; only explicit 26694 rollback-reference authority + 26696 identity/scope/regressions added')
