#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: repair_26697_infrastructure.py BUILD WORKFLOW')
s=Path(sys.argv[1]).read_text(); w=Path(sys.argv[2]).read_text()
MECH='737d521f6b3439dda2e358ba1b44235967e35297'
BLOB='a0d55730e53a0ed4d09f22fc453372663cecf5ee'
WBLOB='5518554e40be2b80382545e05b0efc120f479ce2'
marker='# IRIS_26697_AUTHORITATIVE_ACTIONS_STAGE_ORDER'; assert s.count(marker)==1; main=s[s.index(marker):]
# Exact successful 26696 R1 compiler/build order. Authority acquisition is intentionally reduced
# from two artifacts to the sole latest successful 26696 R1 artifact; this is an authority update,
# not a compiler/build reorder.
anchors=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26696r1_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','verify_compiled_jni_callback',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','verify_apk_jni_contract','postbuild_proof']
pos=-1
for a in anchors:
 n=main.find(a,pos+1); assert n>=0,f'26696 R1 order missing/reordered {a}'; pos=n
assert main.count('verify_candidate_patches')==2 and main.count('./gradlew')==3
for t in ['GLSLANG_VERSION="16.5.0"','actions/checkout@v5','actions/setup-java@v5',"java-version: '17'",'actions/setup-python@v5',"python-version: '3.12'",'actions/upload-artifact@v4','experimental-clean-photon-rebuild']:
 assert t in s+w,t
for t in [
 'RUNTIME_AUTHORITY_COMMIT="737d521f6b3439dda2e358ba1b44235967e35297"',
 'BASE_RUN_ID="35958217220"','BASE_ARTIFACT_ID="10791487190"',
 'BASE_ARTIFACT_SHA="8820658f4b06ceaf0fb328b172a5fb9aac8e1f902bd94d240917a9e0ecc976f1"',
 'BASE_TAR_SHA="e0bc256578e3a4d8c7ce524835fb116b992119051f4695aa26aaa2d4708e1866"',
 'AUTH_26696R1_BUILD_SCRIPT_BLOB="a0d55730e53a0ed4d09f22fc453372663cecf5ee"',
 'AUTH_26696R1_WORKFLOW_BLOB="5518554e40be2b80382545e05b0efc120f479ce2"',
 'python3 -S "$TRANSFORM" "$BASE" "$AFTER"',
 'python3 -S "$AUTHORITY" "$ROOT" "$BASE" "$AFTER"']:
 assert t in s,t
# Obsolete secondary 26694 restore input must not survive once successful 26696 R1 is sole authority.
for forbidden in ['ROLLBACK94','ROLLBACK_ARTZIP','REF94_FULL','10785824126','874928c07ce1aeeddd96f440fcfe4f004fce4fc10dac67f0bf9969872fc9e2d9']:
 assert forbidden not in s,forbidden
# Stage-1 26697 names must not match the already-active 26696 R1 workflow namespace.
assert '26696R1_' not in w and 'handoff_payload_26696r1' not in w
try:
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:build_26696r1_spektra_runtime_parity.sh'],text=True,stderr=subprocess.DEVNULL).strip()==BLOB
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:.github/workflows/build-26696r1-spektra-runtime-parity.yml'],text=True,stderr=subprocess.DEVNULL).strip()==WBLOB
except Exception:
 pass
print('PASS 26697 infrastructure audit: exact successful 26696 R1 build/workflow blobs pinned; compiler/build stage order unchanged; only authority identity/scope/regression wrappers changed and obsolete secondary restore input removed')
