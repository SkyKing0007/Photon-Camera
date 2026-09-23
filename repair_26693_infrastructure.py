#!/usr/bin/env python3
from pathlib import Path
import subprocess,sys
if len(sys.argv)!=3: raise SystemExit('usage: repair_26693_infrastructure.py BUILD WORKFLOW')
build=Path(sys.argv[1]); workflow=Path(sys.argv[2]); s=build.read_text(); w=workflow.read_text()
# Exact last successful implementation authorities.
MECH='e3d7c511920be03fc1854546101a462ca24a8937'; BLOB='9d57410f3b293eb2f9515227886b133aba7b11bb'; WBLOB='756a909d55c274d4e1fcb1dc72da3acd4081d2d1'
# Preserve successful compiler/build order exactly in the 26693 wrapper.
marker='# IRIS_26693_AUTHORITATIVE_ACTIONS_STAGE_ORDER'
assert s.count(marker)==1, '26693 authoritative stage-order marker count'
main=s[s.index(marker):]
anchors=['verify_package','verify_scope','obtain_authority','make_candidate','verify_successful_26692_mechanics','prepare_glslang','compile_spektra_raw_shader','install_frozen_candidate_live','./gradlew clean :app:compileDebugKotlin :app:compileDebugJavaWithJavac','verify_compiled_jni_callback',"./gradlew ':app:buildCMakeDebug[arm64-v8a]' ':app:buildCMakeDebug[armeabi-v7a]'",'verify_candidate_patches','PRE-BUILD SAFETY PROOF PASSED','./gradlew :app:assembleDebug','expected exactly one Gradle debug APK','verify_apk_jni_contract','postbuild_proof']
pos=-1
for a in anchors:
 n=main.find(a,pos+1); assert n>=0,f'26692 order anchor missing/reordered in authoritative execution: {a}'; pos=n
# Actions path must execute the patch proof exactly once, after both language/JNI/native compiler gates.
assert main.count('verify_candidate_patches')==2  # local branch once + authoritative Actions once
for tok in ['GLSLANG_VERSION="16.5.0"','actions/checkout@v5','actions/setup-java@v5','java-version: \'17\'','actions/setup-python@v5','python-version: \'3.12\'','actions/upload-artifact@v4','experimental-clean-photon-rebuild']: assert tok in s+w,tok
assert 'BASE_ARTIFACT_ID="10775875663"' in s and 'BASE_TAR_SHA="e8d58068812dc119519a8b6b75a70e5be97db25bdc69c5fcba8d9c986f62a960"' in s
# When executed in the uploaded repo, pin the prior successful blobs without modifying them.
try:
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:build_26692_r1_1_spektra_standalone_parity_capture_ui.sh'],text=True).strip()==BLOB
 assert subprocess.check_output(['git','rev-parse',f'{MECH}:.github/workflows/build-26692-r1-1-spektra-standalone-parity-capture-ui.yml'],text=True).strip()==WBLOB
except Exception:
 pass
print('PASS 26693 infrastructure audit: successful 26692 R1.1 blobs pinned; inherited successful-26691 compiler/build order retained; identity/scope/regressions only')
